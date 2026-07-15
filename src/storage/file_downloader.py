"""
file_downloader.py — Concurrent media downloader with MIME/signature validation.
"""

from __future__ import annotations

import mimetypes
import random
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlparse

import httpx

from config import (
    CONCURRENT_DOWNLOADS,
    DEFAULT_DOWNLOAD_IMAGES_SUBDIR,
    DEFAULT_DOWNLOAD_VIDEOS_SUBDIR,
    HLS_EXTENSIONS,
    MIN_IMAGE_DOWNLOAD_BYTES,
    MIN_IMAGE_HEIGHT,
    MIN_IMAGE_WIDTH,
    MIN_VIDEO_DOWNLOAD_BYTES,
    REFERER_OVERRIDES,
)
from core.filters import should_keep_image, should_keep_video
from core.models import ScrapeResult
from utils.image_helper import get_image_dimensions
from utils.http_client import HttpClient
from utils.logger import get_logger
from utils.rate_limiter import RateLimiter


LOGGER = get_logger(__name__)

# Per-hostname rate limiters used exclusively during the download phase.
# These run at DOWNLOAD_RATE_LIMIT_RPS (5 req/s) and are independent of the
# crawl-phase limiters so that concurrent download workers are not serialized
# by a slow crawl rate (e.g. 0.1 req/s) on the same domain.
_FAST_DOWNLOAD_LIMITERS: dict[str, RateLimiter] = {}
_FAST_DL_LOCK = threading.Lock()
DOWNLOAD_RATE_LIMIT_RPS = 5.0  # Max requests/sec for non-CDN download hosts


def _fast_limiter_for(host: str) -> RateLimiter:
    """Return (or lazily create) the fast download-phase RateLimiter for *host*.

    These limiters cap at ``DOWNLOAD_RATE_LIMIT_RPS`` and are not shared with
    the main crawl-phase limiters, so download threads never block on crawl
    rate limits and vice-versa.
    """
    with _FAST_DL_LOCK:
        if host not in _FAST_DOWNLOAD_LIMITERS:
            _FAST_DOWNLOAD_LIMITERS[host] = RateLimiter(DOWNLOAD_RATE_LIMIT_RPS)
        return _FAST_DOWNLOAD_LIMITERS[host]

IMAGE_SIGNATURES = (
    b"\xff\xd8\xff",
    b"\x89PNG\r\n\x1a\n",
    b"GIF87a",
    b"GIF89a",
    b"RIFF",
)
VIDEO_SIGNATURES = (
    b"\x00\x00\x00",
    b"RIFF",
    b"\x1a\x45\xdf\xa3",
    b"OggS",
)


class MediaDownloader:
    """Downloads media files concurrently with MIME/signature validation.

    Args:
        http: Optional shared ``HttpClient``. When provided, the downloader
              reuses the caller's connection pool instead of opening its own.
        workers: Number of concurrent download threads.
    """

    def __init__(
        self,
        http: HttpClient | None = None,
        workers: int = CONCURRENT_DOWNLOADS,
    ) -> None:
        self.http = http if http is not None else HttpClient()
        self.workers = max(1, workers)
        self._seen_hashes: set[str] = set()
        self._hash_lock = threading.Lock()


    def _is_hotlink_protected(self, url: str) -> bool:
        """Check if URL is from a domain that requires Referer header."""
        from src.config import HOTLINK_PROTECTED_DOMAINS
        try:
            import re
            domain_match = re.search(r"https?://([^/]+)", url)
            if domain_match:
                return domain_match.group(1) in HOTLINK_PROTECTED_DOMAINS
        except Exception:
            pass
        return False
    def download(self, result: ScrapeResult, output_root: Path) -> None:
        """Download all accepted images and videos in parallel."""
        with self._hash_lock:
            self._seen_hashes.clear()

        image_dir = output_root / DEFAULT_DOWNLOAD_IMAGES_SUBDIR
        video_dir = output_root / DEFAULT_DOWNLOAD_VIDEOS_SUBDIR
        image_dir.mkdir(parents=True, exist_ok=True)
        video_dir.mkdir(parents=True, exist_ok=True)

        # Build task lists
        image_tasks = [
            (
                item.url,
                image_dir,
                self._build_file_stem(idx, item.alt_text or item.page_title or "image"),
                "image",
                item.source_page,
            )
            for idx, item in enumerate(result.images, start=1)
            if should_keep_image(item, result.keyword)
        ]
        video_tasks = [
            (
                item.url,
                video_dir,
                self._build_file_stem(idx, item.page_title or item.type),
                "video",
                item.source_page,
            )
            for idx, item in enumerate(result.videos, start=1)
            if item.type in {"direct", "hls", "dash"}
            and should_keep_video(item, result.keyword)
        ]

        all_tasks = image_tasks + video_tasks
        if not all_tasks:
            return

        LOGGER.info(
            "Downloading %d images and %d videos (%d workers)...",
            len(image_tasks),
            len(video_tasks),
            self.workers,
        )

        # Index counter per directory — thread-safe via lock
        _counter_lock = threading.Lock()
        _counters: dict[Path, int] = {}

        def _run(task):
            url, directory, prefix, media_kind, referer = task
            self._download_file(url, directory, prefix, media_kind, referer=referer)

        with ThreadPoolExecutor(
            max_workers=self.workers, thread_name_prefix="dl"
        ) as executor:
            futures = {executor.submit(_run, task): task[0] for task in all_tasks}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    LOGGER.warning(
                        "Download worker error for %s: %s", futures[future], exc
                    )

        LOGGER.info("Download phase complete.")

    def _make_download_headers(self, url: str, referer: str | None = None) -> dict[str, str]:
        """Build browser-like headers for a direct binary media fetch.

        Using a dedicated header set (separate from HttpClient) avoids triggering
        the WAF/Crawl4AI fallback path, which is designed for HTML pages and
        returns unusable content for binary media URLs.
        """
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        # Get sticky user agent from http client's session pool if available
        user_agent = None
        if self.http and hasattr(self.http, "_session_pool"):
            session = self.http._session_pool.get_session(host)
            user_agent = session.get_headers().get("User-Agent")

        if not user_agent:
            from config import USER_AGENTS
            user_agent = random.choice(USER_AGENTS)

        origin = (
            f"{parsed.scheme}://{parsed.netloc}"
            if referer is None
            else urlparse(referer).scheme + "://" + urlparse(referer).netloc
        )
        headers: dict[str, str] = {
            "User-Agent": user_agent,
            "Accept": "video/webm,video/mp4,video/*,image/webp,image/*,*/*;q=0.8",
            "Accept-Encoding": "identity;q=1, *;q=0",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
        if referer:
            headers["Referer"] = referer
            headers["Origin"] = origin
        for ref_host, ref_val in REFERER_OVERRIDES.items():
            if ref_host in host:
                headers["Referer"] = ref_val
                parsed_ref = urlparse(ref_val)
                if parsed_ref.netloc:
                    headers["Origin"] = f"{parsed_ref.scheme}://{parsed_ref.netloc}"
                break

        # Attach any active session cookies from the http client's session manager
        if self.http and hasattr(self.http, "session_manager"):
            cookies = self.http.session_manager.load_session(host)
            if cookies:
                cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items())
                if cookie_str:
                    headers["Cookie"] = cookie_str
                    LOGGER.info("Enriched download headers with %d session cookies for host: %s", len(cookies), host)

        return headers


    def _download_file(
        self,
        url: str,
        directory: Path,
        prefix: str,
        media_kind: str,
        referer: str | None = None,
        min_image_size: tuple[int, int] | None = None,
        thumbnail_prefix_pattern: str | None = None,
        cdn_hosts: list[str] | None = None,
    ) -> tuple[bool, dict]:
        """Fetch a single media binary and persist it to *directory*.

        Uses the shared ``self.http.client`` (an ``httpx.Client``) — bypassing
        HttpClient.get() — so that the WAF/Crawl4AI fallback is never triggered
        for binary media assets. The shared client reuses the connection pool and
        any session cookies across concurrent download workers.
        CDN 403s are resolved by sending a full browser-like Referer + Origin
        header pair derived from the source page URL.

        Rate-limiting strategy:
        - If *url* belongs to a known CDN host (``cdn_hosts``), skip the
          rate-limiter entirely — CDN servers handle high concurrency natively
          and rate-limiting them serializes all 16 download threads.
        - Otherwise, use a fast download-specific limiter (5 req/s) that is
          independent of the crawl limiter, preventing serialization caused by
          very slow crawl rates (e.g. 0.1 req/s) on the same hostname.
        """
        if thumbnail_prefix_pattern and url.lower().startswith(thumbnail_prefix_pattern.lower()):
            LOGGER.info("Skipping URL matching thumbnail prefix pattern %s: %s", thumbnail_prefix_pattern, url)
            return False, {"reason": "low_resolution"}

        from config import OUTPUT_DIR  # noqa: F401 — kept for potential future use
        directory.mkdir(parents=True, exist_ok=True)
        from urllib.parse import quote
        import time

        safe_url = quote(url, safe="/:?=&%#~()[],;")
        safe_referer = quote(referer, safe="/:?=&%#~()[],;") if referer else None

        # Determine rate-limiting strategy for this URL.
        # CDN hosts are exempt from rate-limiting; all other hosts get a fast
        # download-only limiter that doesn't interact with the crawl limiters.
        from core.filters import is_cdn_asset_domain
        _url_host = urlparse(url).netloc.lower()
        _is_cdn = is_cdn_asset_domain(url, allow_hosts=cdn_hosts) if cdn_hosts else False

        w, h = None, None

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                # Rate-limit gate: skip for CDN hosts, use fast limiter otherwise.
                if not _is_cdn:
                    _fast_limiter_for(_url_host).wait()

                req_headers = self._make_download_headers(safe_url, safe_referer)
                if attempt > 1:
                    req_headers["Connection"] = "close"

                content = b""
                content_type = ""
                with self.http.client.stream(
                    "GET", safe_url, headers=req_headers
                ) as response:
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "")

                    # Check content-length early if available
                    content_length_header = response.headers.get("content-length")
                    if content_length_header and content_length_header.isdigit():
                        cl = int(content_length_header)
                        if media_kind == "image" and cl < MIN_IMAGE_DOWNLOAD_BYTES:
                            LOGGER.info(
                                "Skipping tiny image asset %s (Content-Length=%d)", url, cl
                            )
                            return False, {"reason": "low_resolution"}
                        if (
                            media_kind == "video"
                            and cl < MIN_VIDEO_DOWNLOAD_BYTES
                            and not self._is_manifest_url(url)
                        ):
                            LOGGER.info(
                                "Skipping tiny video asset %s (Content-Length=%d)", url, cl
                            )
                            return False, {"reason": "low_resolution"}

                    suffix = self._determine_suffix(url, content_type)

                    if media_kind == "image":
                        chunks = []
                        bytes_read = 0
                        dimensions_checked = False
                        for chunk in response.iter_bytes(chunk_size=8192):
                            chunks.append(chunk)
                            bytes_read += len(chunk)

                            if not dimensions_checked:
                                # Try parsing dimensions early on the accumulated bytes
                                current_bytes = b"".join(chunks)
                                w, h = get_image_dimensions(current_bytes)
                                if w is not None and h is not None:
                                    limit_w = min_image_size[0] if min_image_size else MIN_IMAGE_WIDTH
                                    limit_h = min_image_size[1] if min_image_size else MIN_IMAGE_HEIGHT
                                    if w < limit_w or h < limit_h:
                                        LOGGER.info(
                                            "Skipping low-resolution image asset %s (%dx%d)",
                                            url,
                                            w,
                                            h,
                                        )
                                        return False, {"reason": "low_resolution"}
                                    dimensions_checked = True
                                elif bytes_read >= 65536:
                                    if suffix.lower() in {
                                        ".jpg",
                                        ".jpeg",
                                        ".png",
                                        ".webp",
                                        ".gif",
                                    }:
                                        LOGGER.info(
                                            "Skipping image with unparseable dimensions %s",
                                            url,
                                        )
                                        return False, {"reason": "unparseable_dimensions"}
                                    dimensions_checked = True
                        content = b"".join(chunks)
                    else:
                        chunks = []
                        for chunk in response.iter_bytes(chunk_size=65536):
                            chunks.append(chunk)
                        content = b"".join(chunks)

                content_length = len(content)
                if media_kind == "image" and content_length < MIN_IMAGE_DOWNLOAD_BYTES:
                    LOGGER.info("Skipping tiny image asset %s", url)
                    return False, {"reason": "low_resolution"}
                if (
                    media_kind == "video"
                    and content_length < MIN_VIDEO_DOWNLOAD_BYTES
                    and not self._is_manifest_url(url)
                ):
                    LOGGER.info(
                        "Skipping tiny video asset %s (size=%d bytes)", url, content_length
                    )
                    return False, {"reason": "low_resolution"}

                suffix = self._determine_suffix(url, content_type)
                if not self._looks_like_expected_media(
                    content, content_type, suffix, media_kind, url
                ):
                    LOGGER.info(
                        "Skipping invalid %s media %s (content-type=%s)",
                        media_kind,
                        url,
                        content_type,
                    )
                    return False, {"reason": "invalid_media_type"}

                import hashlib

                hasher = hashlib.sha256(content)
                content_hash = hasher.hexdigest()

                with self._hash_lock:
                    if content_hash in self._seen_hashes:
                        LOGGER.info(
                            "Skipping duplicate content hash %s for %s", content_hash, url
                        )
                        return False, {"reason": "duplicate"}
                    self._seen_hashes.add(content_hash)

                if media_kind == "image":
                    w, h = get_image_dimensions(content)
                    if w is not None and h is not None:
                        limit_w = min_image_size[0] if min_image_size else MIN_IMAGE_WIDTH
                        limit_h = min_image_size[1] if min_image_size else MIN_IMAGE_HEIGHT
                        if w < limit_w or h < limit_h:
                            LOGGER.info(
                                "Skipping low-resolution image asset %s (%dx%d)", url, w, h
                            )
                            return False, {"reason": "low_resolution"}
                    elif suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                        LOGGER.info("Skipping image with unparseable dimensions %s", url)
                        return False, {"reason": "unparseable_dimensions"}

                target = directory / f"{prefix}{suffix}"
                target.write_bytes(content)
                LOGGER.info("Downloaded %s", target)

                relative_path = ""
                try:
                    relative_path = str(target.relative_to(OUTPUT_DIR.resolve()))
                except ValueError:
                    try:
                        relative_path = str(target.relative_to(OUTPUT_DIR))
                    except ValueError:
                        relative_path = str(target)

                return True, {
                    "reason": "ok",
                    "file_path": relative_path,
                    "hash": content_hash,
                    "width": w,
                    "height": h,
                    "file_size_bytes": content_length,
                    "mime_type": content_type or mimetypes.guess_type(target.name)[0] or "",
                }

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status >= 500 and attempt < max_attempts:
                    sleep_time = 2.0**attempt
                    LOGGER.warning(
                        "HTTP %d downloading %s (attempt %d/%d). Retrying in %.1fs...",
                        status,
                        url,
                        attempt,
                        max_attempts,
                        sleep_time,
                    )
                    time.sleep(sleep_time)
                    continue
                LOGGER.warning(
                    "HTTP %d downloading %s: %s", status, url, exc
                )
                return False, {"reason": f"http_error:{status}"}

            except (httpx.HTTPError, httpx.StreamError, ConnectionError, TimeoutError) as exc:
                if attempt < max_attempts:
                    sleep_time = 2.0**attempt
                    LOGGER.warning(
                        "Network error downloading %s: %s (attempt %d/%d). Retrying in %.1fs...",
                        url,
                        exc,
                        attempt,
                        max_attempts,
                        sleep_time,
                    )
                    time.sleep(sleep_time)
                    continue
                LOGGER.warning("Failed to download %s: %s", url, exc)
                return False, {"reason": f"download_error:{type(exc).__name__}"}

            except Exception as exc:
                LOGGER.warning("Failed to download %s due to unexpected error: %s", url, exc)
                return False, {"reason": f"download_error:{type(exc).__name__}"}

    @staticmethod
    def _build_file_stem(index: int, label: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", label.strip().lower()).strip("_")
        suffix = normalized[:40] if normalized else "asset"
        return f"{index:03d}_{suffix}"

    @staticmethod
    def _determine_suffix(url: str, content_type: str) -> str:
        url_suffix = Path(urlparse(url).path).suffix
        if url_suffix:
            return url_suffix
        guessed = None
        if content_type:
            guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        return guessed or ".bin"

    @staticmethod
    def _is_manifest_url(url: str) -> bool:
        lowered = url.lower()
        return any(
            lowered.endswith(ext) or f"{ext}?" in lowered
            for ext in HLS_EXTENSIONS | {".mpd"}
        )

    @staticmethod
    def _looks_like_expected_media(
        content: bytes,
        content_type: str,
        suffix: str,
        media_kind: str,
        url: str,
    ) -> bool:
        lowered_type = content_type.lower()
        lowered_suffix = suffix.lower()
        if media_kind == "image":
            if lowered_type.startswith("image/"):
                return True
            if (
                lowered_suffix == ".webp"
                and content[:4] == b"RIFF"
                and content[8:12] == b"WEBP"
            ):
                return True
            return any(content.startswith(sig) for sig in IMAGE_SIGNATURES)

        if lowered_type.startswith("video/"):
            return True
        if MediaDownloader._is_manifest_url(url):
            return (
                lowered_type.startswith("application/")
                or lowered_type.startswith("text/")
                or b"#EXTM3U" in content[:64]
            )
        if lowered_suffix in {".mp4", ".m4v"}:
            return b"ftyp" in content[:32]
        if lowered_suffix in {".webm", ".mkv"}:
            return content.startswith(b"\x1a\x45\xdf\xa3")
        if lowered_suffix == ".ogv":
            return content.startswith(b"OggS")
        return any(content.startswith(sig) for sig in VIDEO_SIGNATURES)
