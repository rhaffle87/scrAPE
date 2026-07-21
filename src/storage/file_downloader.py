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
        self._dead_urls: set[str] = set()
        self._dead_urls_lock = threading.Lock()
        self._seen_hashes: set[str] = set()
        self._hash_lock = threading.Lock()

    def _is_hotlink_protected(self, url: str) -> bool:
        """Check if URL is from a domain that requires Referer header."""
        from config import HOTLINK_PROTECTED_DOMAINS

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
                getattr(item, "original_url", item.url) or item.url,
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
                item.url,
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
            url, directory, prefix, media_kind, referer, original_url = task
            from core.filters import transform_to_highres

            upscaled_url, orig = transform_to_highres(url)

            success, result = self._download_file(
                upscaled_url, directory, prefix, media_kind, referer=referer
            )
            if not success and upscaled_url != orig:
                LOGGER.info(
                    "High-res upscale failed for %s, falling back to original: %s",
                    upscaled_url,
                    orig,
                )
                success, result = self._download_file(
                    orig, directory, prefix, media_kind, referer=referer
                )
            return success, result

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

    def _make_download_headers(
        self, url: str, referer: str | None = None
    ) -> dict[str, str]:
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
                    LOGGER.info(
                        "Enriched download headers with %d session cookies for host: %s",
                        len(cookies),
                        host,
                    )

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
        with self._dead_urls_lock:
            if url in self._dead_urls:
                LOGGER.info("Skipping download of known dead URL: %s", url)
                return False, {"reason": "404_dead_url"}

        if thumbnail_prefix_pattern and url.lower().startswith(
            thumbnail_prefix_pattern.lower()
        ):
            LOGGER.info(
                "Skipping URL matching thumbnail prefix pattern %s: %s",
                thumbnail_prefix_pattern,
                url,
            )
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
        _is_cdn = (
            is_cdn_asset_domain(url, allow_hosts=cdn_hosts) if cdn_hosts else False
        )

        w, h = None, None

        candidate_suffix = self._determine_suffix(url, "")
        temp_target = directory / f"{prefix}{candidate_suffix}.tmp"

        max_attempts = 3
        use_curl_cffi = False
        for attempt in range(1, max_attempts + 1):
            try:
                # Rate-limit gate: skip for CDN hosts, use fast limiter otherwise.
                if not _is_cdn:
                    _fast_limiter_for(_url_host).wait()

                bytes_written = 0
                if media_kind == "video" and temp_target.exists():
                    bytes_written = temp_target.stat().st_size

                req_headers = self._make_download_headers(safe_url, safe_referer)
                if bytes_written > 0:
                    req_headers["Range"] = f"bytes={bytes_written}-"
                    LOGGER.info(
                        "Resuming video download from byte %d (attempt %d/%d) for %s",
                        bytes_written,
                        attempt,
                        max_attempts,
                        url,
                    )

                if attempt > 1:
                    req_headers["Connection"] = "close"

                content = b""
                content_type = ""
                
                import contextlib
                @contextlib.contextmanager
                def _do_request():
                    if use_curl_cffi:
                        try:
                            from curl_cffi import requests as c_requests
                        except ImportError:
                            raise RuntimeError("curl_cffi not installed")
                        
                        proxy = self.http.get_proxy() if hasattr(self.http, "get_proxy") else None
                        proxies = {"http": proxy, "https": proxy} if proxy else None
                        session = c_requests.Session(impersonate="chrome120", proxies=proxies)
                        resp = session.get(safe_url, headers=req_headers, stream=True, timeout=60.0)
                        try:
                            resp.raise_for_status()
                            # patch iter_bytes for compatibility with httpx
                            resp.iter_bytes = lambda chunk_size=8192: resp.iter_content(chunk_size=chunk_size)
                            yield resp
                        finally:
                            resp.close()
                    else:
                        dl_timeout = httpx.Timeout(30.0, read=60.0, connect=15.0)
                        with self.http.client.stream("GET", safe_url, headers=req_headers, timeout=dl_timeout) as resp:
                            resp.raise_for_status()
                            yield resp

                with _do_request() as response:
                    content_type = response.headers.get("content-type", "")

                    # Check content-length early if available (only if we did not send a Range request)
                    content_length_header = response.headers.get("content-length")
                    if bytes_written == 0 and content_length_header and content_length_header.isdigit():
                        cl = int(content_length_header)
                        if media_kind == "image" and cl < MIN_IMAGE_DOWNLOAD_BYTES:
                            LOGGER.info(
                                "Skipping tiny image asset %s (Content-Length=%d)",
                                url,
                                cl,
                            )
                            return False, {"reason": "low_resolution"}
                        if (
                            media_kind == "video"
                            and cl < MIN_VIDEO_DOWNLOAD_BYTES
                            and not self._is_manifest_url(url)
                        ):
                            LOGGER.info(
                                "Skipping tiny video asset %s (Content-Length=%d)",
                                url,
                                cl,
                            )
                            return False, {"reason": "low_resolution"}

                    suffix = self._determine_suffix(url, content_type)
                    target = directory / f"{prefix}{suffix}"
                    temp_target = target.with_suffix(suffix + ".tmp")

                    is_partial = response.status_code == 206
                    if bytes_written > 0 and not is_partial:
                        LOGGER.info(
                            "Server returned HTTP %d instead of 206 for %s. Truncating temp file and downloading from scratch.",
                            response.status_code,
                            url,
                        )
                        bytes_written = 0

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
                                    limit_w = (
                                        min_image_size[0]
                                        if min_image_size
                                        else MIN_IMAGE_WIDTH
                                    )
                                    limit_h = (
                                        min_image_size[1]
                                        if min_image_size
                                        else MIN_IMAGE_HEIGHT
                                    )
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
                                        return False, {
                                            "reason": "unparseable_dimensions"
                                        }
                                    dimensions_checked = True
                        content = b"".join(chunks)
                        content_length = len(content)
                    else:
                        write_mode = "ab" if bytes_written > 0 else "wb"
                        bytes_read = bytes_written
                        header_bytes = b""
                        try:
                            with open(temp_target, write_mode) as f:
                                for chunk in response.iter_bytes(chunk_size=65536):
                                    if bytes_read < 1024:
                                        header_bytes += chunk
                                    f.write(chunk)
                                    bytes_read += len(chunk)
                        except Exception as e:
                            # Do not delete temp file on error to support resumes
                            raise e
                        content = header_bytes
                        content_length = bytes_read

                if media_kind == "image" and content_length < MIN_IMAGE_DOWNLOAD_BYTES:
                    LOGGER.info("Skipping tiny image asset %s", url)
                    return False, {"reason": "low_resolution"}
                if (
                    media_kind == "video"
                    and content_length < MIN_VIDEO_DOWNLOAD_BYTES
                    and not self._is_manifest_url(url)
                ):
                    LOGGER.info(
                        "Skipping tiny video asset %s (size=%d bytes)",
                        url,
                        content_length,
                    )
                    if media_kind == "video":
                        temp_target.unlink(missing_ok=True)
                    return False, {"reason": "low_resolution"}

                if not self._looks_like_expected_media(
                    content, content_type, suffix, media_kind, url
                ):
                    LOGGER.info(
                        "Skipping invalid %s media %s (content-type=%s)",
                        media_kind,
                        url,
                        content_type,
                    )
                    if media_kind == "video":
                        temp_target.unlink(missing_ok=True)
                    return False, {"reason": "invalid_media_type"}

                import hashlib
                if media_kind == "image":
                    content_hash = hashlib.sha256(content).hexdigest()
                else:
                    temp_target.rename(target)
                    # Compute hash of the fully downloaded target file
                    hasher = hashlib.sha256()
                    with open(target, "rb") as f:
                        for chunk in iter(lambda: f.read(65536), b""):
                            hasher.update(chunk)
                    content_hash = hasher.hexdigest()
                    content_length = target.stat().st_size

                with self._hash_lock:
                    if content_hash in self._seen_hashes:
                        LOGGER.info(
                            "Skipping duplicate content hash %s for %s",
                            content_hash,
                            url,
                        )
                        if media_kind == "video":
                            target.unlink(missing_ok=True)
                        return False, {"reason": "duplicate"}
                    self._seen_hashes.add(content_hash)

                if media_kind == "image":
                    w, h = get_image_dimensions(content)
                    if w is not None and h is not None:
                        limit_w = (
                            min_image_size[0] if min_image_size else MIN_IMAGE_WIDTH
                        )
                        limit_h = (
                            min_image_size[1] if min_image_size else MIN_IMAGE_HEIGHT
                        )
                        if w < limit_w or h < limit_h:
                            LOGGER.info(
                                "Skipping low-resolution image asset %s (%dx%d)",
                                url,
                                w,
                                h,
                            )
                            return False, {"reason": "low_resolution"}
                    elif suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                        LOGGER.info(
                            "Skipping image with unparseable dimensions %s", url
                        )
                        return False, {"reason": "unparseable_dimensions"}

                if media_kind == "image":
                    try:
                        from PIL import Image
                        import io
                        
                        img = Image.open(io.BytesIO(content))
                        out_buffer = io.BytesIO()
                        save_format = img.format if img.format else "JPEG"
                        
                        kwargs = {}
                        if getattr(img, "is_animated", False):
                            kwargs["save_all"] = True
                            
                        # Strip EXIF and re-encode to sanitize image
                        img.save(out_buffer, format=save_format, **kwargs)
                        target.write_bytes(out_buffer.getvalue())
                    except Exception as e:
                        LOGGER.warning("Image sanitization failed for %s: %s", url, e)
                        return False, {"reason": "sanitization_failed"}
                else:
                    # Target is already renamed
                    pass
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
                    "mime_type": content_type
                    or mimetypes.guess_type(target.name)[0]
                    or "",
                }

            except Exception as exc:
                status = None
                if hasattr(exc, "response") and hasattr(exc.response, "status_code"):
                    status = exc.response.status_code
                elif isinstance(exc, httpx.HTTPStatusError):
                    status = exc.response.status_code
                    
                if status is not None:
                    if status == 416:
                        LOGGER.warning("Range not satisfiable (HTTP 416) for %s. Truncating temp file and retrying from scratch.", url)
                        temp_target.unlink(missing_ok=True)
                        time.sleep(1.0)
                        continue
                    if status in (403, 401) and not use_curl_cffi and attempt < max_attempts:
                        LOGGER.info("HTTP %d on %s. Retrying with curl_cffi TLS spoofing...", status, url)
                        use_curl_cffi = True
                        time.sleep(1.0)
                        continue
                    if status in (403, 401) and use_curl_cffi and attempt < max_attempts:
                        from config import ENABLE_DRISSIONPAGE_FALLBACK
                        if ENABLE_DRISSIONPAGE_FALLBACK:
                            LOGGER.info("Tier-3 DrissionPage fallback for %s (HTTP %d)...", url, status)
                            try:
                                dp_success, dp_result = self._download_with_drissionpage(
                                    url, directory, prefix, media_kind, 
                                    min_image_size, req_headers.get("Referer")
                                )
                                if dp_success:
                                    return True, dp_result
                                else:
                                    return False, dp_result
                            except Exception as e:
                                LOGGER.warning("DrissionPage download fallback failed for %s: %s", url, e)
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
                    if status == 404:
                        LOGGER.info("HTTP 404 downloading %s: %s", url, exc)
                        with self._dead_urls_lock:
                            self._dead_urls.add(url)
                    else:
                        LOGGER.warning("HTTP %d downloading %s: %s", status, url, exc)
                    return False, {"reason": f"http_error:{status}"}
                
                # Network or unexpected error
                if attempt < max_attempts:
                    # Cloudflare sometimes drops connections instead of 403
                    if not use_curl_cffi and type(exc).__name__ in ("ConnectError", "ConnectionError", "ReadError", "StreamError"):
                        LOGGER.info("Network drop on %s. Retrying with curl_cffi TLS spoofing...", url)
                        use_curl_cffi = True
                    
                    sleep_time = 2.0**attempt
                    LOGGER.warning(
                        "Error downloading %s: %s (attempt %d/%d). Retrying in %.1fs...",
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

        # All retry attempts exhausted without a definitive return (should not happen in practice)
        return False, {"reason": "max_retries_exceeded"}

    @staticmethod
    def _build_file_stem(index: int, label: str) -> str:
        normalized = re.sub(r"[^a-zA-Z0-9]+", "_", label.strip().lower()).strip("_")
        suffix = normalized[:40] if normalized else "asset"
        return f"{index:03d}_{suffix}"

    @staticmethod
    def _determine_suffix(url: str, content_type: str) -> str:
        import mimetypes
        url_suffix = Path(urlparse(url).path).suffix
        if url_suffix:
            return url_suffix
        guessed = None
        if content_type:
            guessed = mimetypes.guess_extension(content_type.split(";")[0].strip())
        return guessed or ".bin"

    def _download_with_drissionpage(
        self,
        url: str,
        directory: Path,
        prefix: str,
        media_kind: str,
        min_image_size: tuple[int, int] | None = None,
        referer: str | None = None,
    ) -> tuple[bool, dict]:
        import re
        import mimetypes
        from DrissionPage import ChromiumOptions, ChromiumPage
        from config import FORCE_HEADLESS, MIN_IMAGE_DOWNLOAD_BYTES, MIN_VIDEO_DOWNLOAD_BYTES, MIN_IMAGE_WIDTH, MIN_IMAGE_HEIGHT, OUTPUT_DIR
        import sys

        host = urlparse(url).netloc
        domain_slug = re.sub(r"[^\w\-]", "_", host)
        profile_path = Path("data/drission_profiles") / domain_slug

        co = ChromiumOptions()
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-gpu")
        # Enforce headless mode so it doesn't bother the user
        co.headless(True)

        if profile_path.exists():
            co.set_user_data_path(str(profile_path.resolve()))

        proxy = self.http.get_proxy() if hasattr(self.http, "get_proxy") else None
        if proxy:
            co.set_proxy(proxy)

        page = None
        try:
            page = ChromiumPage(co)
            headers = {}
            if referer:
                headers["Referer"] = referer

            resp = page.session.get(url, stream=True, headers=headers, timeout=self.http.timeout)
            resp.raise_for_status()

            content = b""
            content_type = resp.headers.get("content-type", "")
            
            # Determine suffix and target now that we have content_type
            suffix = self._determine_suffix(url, content_type)
            target = directory / f"{prefix}{suffix}"
            temp_target = target.with_suffix(suffix + ".tmp")
            
            content_length_header = resp.headers.get("content-length")
            
            if content_length_header and content_length_header.isdigit():
                cl = int(content_length_header)
                if media_kind == "image" and cl < MIN_IMAGE_DOWNLOAD_BYTES:
                    return False, {"reason": "low_resolution"}
                if media_kind == "video" and cl < MIN_VIDEO_DOWNLOAD_BYTES and not self._is_manifest_url(url):
                    return False, {"reason": "low_resolution"}

            import hashlib
            hasher = hashlib.sha256()

            if media_kind == "image":
                chunks = []
                for chunk in resp.iter_content(chunk_size=8192):
                    if chunk:
                        chunks.append(chunk)
                content = b"".join(chunks)
                content_length = len(content)
                hasher.update(content)
            else:
                bytes_read = 0
                header_bytes = b""
                try:
                    with open(temp_target, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=65536):
                            if chunk:
                                if bytes_read < 1024:
                                    header_bytes += chunk
                                f.write(chunk)
                                hasher.update(chunk)
                                bytes_read += len(chunk)
                except Exception as e:
                    temp_target.unlink(missing_ok=True)
                    raise e
                content = header_bytes
                content_length = bytes_read

            if media_kind == "image" and content_length < MIN_IMAGE_DOWNLOAD_BYTES:
                return False, {"reason": "low_resolution"}
            if media_kind == "video" and content_length < MIN_VIDEO_DOWNLOAD_BYTES and not self._is_manifest_url(url):
                temp_target.unlink(missing_ok=True)
                return False, {"reason": "low_resolution"}

            if not self._looks_like_expected_media(content, content_type, suffix, media_kind, url):
                if media_kind == "video":
                    temp_target.unlink(missing_ok=True)
                return False, {"reason": "invalid_media_type"}

            content_hash = hasher.hexdigest()

            with self._hash_lock:
                if content_hash in self._seen_hashes:
                    if media_kind == "video":
                        temp_target.unlink(missing_ok=True)
                    return False, {"reason": "duplicate"}
                self._seen_hashes.add(content_hash)

            w, h = None, None
            if media_kind == "image":
                from core.filters import get_image_dimensions
                w, h = get_image_dimensions(content)
                if w is not None and h is not None:
                    limit_w = min_image_size[0] if min_image_size else MIN_IMAGE_WIDTH
                    limit_h = min_image_size[1] if min_image_size else MIN_IMAGE_HEIGHT
                    if w < limit_w or h < limit_h:
                        return False, {"reason": "low_resolution"}
                elif suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                    return False, {"reason": "unparseable_dimensions"}

                try:
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(content))
                    out_buffer = io.BytesIO()
                    save_format = img.format if img.format else "JPEG"
                    kwargs = {}
                    if getattr(img, "is_animated", False):
                        kwargs["save_all"] = True
                    img.save(out_buffer, format=save_format, **kwargs)
                    target.write_bytes(out_buffer.getvalue())
                except Exception:
                    return False, {"reason": "sanitization_failed"}
            else:
                temp_target.rename(target)

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
        finally:
            if page:
                try:
                    page.quit()
                except Exception:
                    pass

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
