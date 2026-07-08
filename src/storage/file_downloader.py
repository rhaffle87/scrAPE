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
)
from core.filters import should_keep_image, should_keep_video
from core.models import ScrapeResult
from utils.image_helper import get_image_dimensions
from utils.http_client import HttpClient
from utils.logger import get_logger

LOGGER = get_logger(__name__)

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
            (item.url, image_dir, self._build_file_stem(idx, item.alt_text or item.page_title or "image"), "image", item.source_page)
            for idx, item in enumerate(result.images, start=1)
            if should_keep_image(item, result.keyword)
        ]
        video_tasks = [
            (item.url, video_dir, self._build_file_stem(idx, item.page_title or item.type), "video", item.source_page)
            for idx, item in enumerate(result.videos, start=1)
            if item.type in {"direct", "hls", "dash"} and should_keep_video(item, result.keyword)
        ]

        all_tasks = image_tasks + video_tasks
        if not all_tasks:
            return

        LOGGER.info(
            "Downloading %d images and %d videos (%d workers)...",
            len(image_tasks), len(video_tasks), self.workers,
        )

        # Index counter per directory — thread-safe via lock
        _counter_lock = threading.Lock()
        _counters: dict[Path, int] = {}

        def _run(task):
            url, directory, prefix, media_kind, referer = task
            self._download_file(url, directory, prefix, media_kind, referer=referer)

        with ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="dl") as executor:
            futures = {executor.submit(_run, task): task[0] for task in all_tasks}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    LOGGER.warning("Download worker error for %s: %s", futures[future], exc)

        LOGGER.info("Download phase complete.")

    @staticmethod
    def _make_download_headers(url: str, referer: str | None = None) -> dict[str, str]:
        """Build browser-like headers for a direct binary media fetch.

        Using a dedicated header set (separate from HttpClient) avoids triggering
        the WAF/Crawl4AI fallback path, which is designed for HTML pages and
        returns unusable content for binary media URLs.
        """
        from config import USER_AGENTS
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}" if referer is None else urlparse(referer).scheme + "://" + urlparse(referer).netloc
        headers: dict[str, str] = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "video/webm,video/mp4,video/*,image/webp,image/*,*/*;q=0.8",
            "Accept-Encoding": "identity;q=1, *;q=0",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
        }
        if referer:
            headers["Referer"] = referer
            headers["Origin"] = origin
        return headers

    def _download_file(self, url: str, directory: Path, prefix: str, media_kind: str, referer: str | None = None) -> bool:
        """Fetch a single media binary and persist it to *directory*.

        Uses the shared ``self.http.client`` (an ``httpx.Client``) — bypassing
        HttpClient.get() — so that the WAF/Crawl4AI fallback is never triggered
        for binary media assets. The shared client reuses the connection pool and
        any session cookies across concurrent download workers.
        CDN 403s are resolved by sending a full browser-like Referer + Origin
        header pair derived from the source page URL.
        """
        from urllib.parse import quote
        safe_url = quote(url, safe='/:?=&%#~()[],;')
        safe_referer = quote(referer, safe='/:?=&%#~()[],;') if referer else None

        try:
            req_headers = self._make_download_headers(safe_url, safe_referer)
            response = self.http.client.get(safe_url, headers=req_headers)
            response.raise_for_status()
            content = response.content
            content_type = response.headers.get("content-type", "")
            content_length = len(content)

            if media_kind == "image" and content_length < MIN_IMAGE_DOWNLOAD_BYTES:
                LOGGER.info("Skipping tiny image asset %s", url)
                return False
            if media_kind == "video" and content_length < MIN_VIDEO_DOWNLOAD_BYTES and not self._is_manifest_url(url):
                LOGGER.info("Skipping tiny video asset %s (size=%d bytes)", url, content_length)
                return False

            suffix = self._determine_suffix(url, content_type)
            if not self._looks_like_expected_media(content, content_type, suffix, media_kind, url):
                LOGGER.info("Skipping invalid %s media %s (content-type=%s)", media_kind, url, content_type)
                return False

            import hashlib
            hasher = hashlib.sha256()
            hasher.update(content[:65536])
            content_hash = hasher.hexdigest()

            with self._hash_lock:
                if content_hash in self._seen_hashes:
                    LOGGER.info("Skipping duplicate content hash %s for %s", content_hash, url)
                    return False
                self._seen_hashes.add(content_hash)

            if media_kind == "image":
                w, h = get_image_dimensions(content)
                if w is not None and h is not None:
                    if w < MIN_IMAGE_WIDTH or h < MIN_IMAGE_HEIGHT:
                        LOGGER.info("Skipping low-resolution image asset %s (%dx%d)", url, w, h)
                        return False
                elif suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
                    LOGGER.info("Skipping image with unparseable dimensions %s", url)
                    return False

            target = directory / f"{prefix}{suffix}"
            target.write_bytes(content)
            LOGGER.info("Downloaded %s", target)
            return True
        except httpx.HTTPStatusError as exc:
            LOGGER.warning("HTTP %d downloading %s: %s", exc.response.status_code, url, exc)
            return False
        except Exception as exc:
            LOGGER.warning("Failed to download %s: %s", url, exc)
            return False

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
        return any(lowered.endswith(ext) or f"{ext}?" in lowered for ext in HLS_EXTENSIONS | {".mpd"})

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
            if lowered_suffix == ".webp" and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
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