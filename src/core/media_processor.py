from __future__ import annotations
import re
import threading
from typing import Any
from urllib.parse import urlparse
import json

import queue
import concurrent.futures as _cf

from config import CONCURRENT_DOWNLOADS, DEFAULT_DOWNLOAD_IMAGES_SUBDIR, DEFAULT_DOWNLOAD_VIDEOS_SUBDIR
from monitoring.logger import get_logger

from core.models import (
    RejectedItem,
)
from core.filters import (
    normalize_url,
    score_image_relevance,
    rejection_reason_for_image,
    score_video_relevance,
    rejection_reason_for_video,
    contains_subject_text,
    safe_join,
)

LOGGER = get_logger(__name__)


def parse_image_candidates(
    tag_or_elem: Any,
    page_url: str,
) -> list[dict[str, Any]]:
    """Extract multi-source candidate image URLs and quality rankings from an element.

    Parses:
      - `data-zoom-image`, `data-highres`, `data-orig-file`, `data-original`, `data-large-file`, `data-full-url`
      - `srcset` responsive candidate sets (extracts width / descriptor)
      - Standard `data-src`, `data-lazy-src`, and `src`
      - Parent `<a>` href pointing to raw image formats
    """
    from core.filters import absolutize_url, is_http_url, normalize_url

    candidates: list[dict[str, Any]] = []
    seen_urls: set[str] = set()

    def _add_candidate(url_str: str, source: str, width: int | None = None, score: int = 500) -> None:
        clean = (url_str or "").strip()
        if not clean or clean.startswith("data:"):
            return
        abs_u = normalize_url(absolutize_url(clean, page_url))
        if not is_http_url(abs_u) or abs_u in seen_urls:
            return
        seen_urls.add(abs_u)
        candidates.append({
            "url": abs_u,
            "source": source,
            "width": width,
            "score": score,
        })

    # 1. High-resolution zoom/original attributes (highest priority)
    zoom_attrs = [
        ("data-zoom-image", 1600),
        ("data-highres", 1500),
        ("data-orig-file", 1400),
        ("data-original", 1300),
        ("data-large-file", 1200),
        ("data-full-url", 1200),
    ]
    for attr, base_score in zoom_attrs:
        val = tag_or_elem.get(attr) if hasattr(tag_or_elem, "get") else None
        if val and isinstance(val, str):
            _add_candidate(val, attr, score=base_score)

    # 2. Responsive srcset parsing
    srcset_val = tag_or_elem.get("srcset") if hasattr(tag_or_elem, "get") else None
    if srcset_val and isinstance(srcset_val, str):
        for part in srcset_val.split(","):
            tokens = part.strip().split()
            if not tokens:
                continue
            src_url = tokens[0].strip()
            width_val = None
            srcset_score = 600
            if len(tokens) > 1:
                desc = tokens[1].lower().strip()
                if desc.endswith("w") and desc[:-1].isdigit():
                    width_val = int(desc[:-1])
                    srcset_score = 600 + width_val
                elif desc.endswith("x"):
                    try:
                        multiplier = float(desc[:-1])
                        srcset_score = int(700 * multiplier)
                    except ValueError:
                        pass
            _add_candidate(src_url, "srcset", width=width_val, score=srcset_score)

    # 3. Standard and lazy-loading src attributes
    for attr in ["data-src", "data-lazy-src", "src"]:
        val = tag_or_elem.get(attr) if hasattr(tag_or_elem, "get") else None
        if val and isinstance(val, str):
            _add_candidate(val, attr, score=500)

    # 4. Parent anchor target (often contains the original uncompressed image)
    if hasattr(tag_or_elem, "find_parent"):
        parent_a = tag_or_elem.find_parent("a")
        if parent_a and hasattr(parent_a, "get"):
            href = parent_a.get("href")
            if href and isinstance(href, str):
                ext = href.split("?")[0].lower()
                if any(ext.endswith(img_ext) for img_ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"]):
                    _add_candidate(href, "parent_anchor", score=1350)

    return candidates


def rank_media_candidates(candidates: list[dict[str, Any]]) -> tuple[str, list[str]]:
    """Sort candidate media items by score and return (primary_url, fallback_urls)."""
    if not candidates:
        return "", []
    sorted_candidates = sorted(candidates, key=lambda c: c.get("score", 0), reverse=True)
    primary = sorted_candidates[0]["url"]
    fallbacks = [c["url"] for c in sorted_candidates[1:] if c["url"] != primary]
    return primary, fallbacks


def _download_candidate_with_fallbacks(
    downloader: Any,
    item: Any,
    directory: Any,
    stem: str,
    media_kind: str,
    referer: str | None,
    min_size: Any,
    thumb_pattern: Any,
    cdn_hosts: Any,
) -> tuple[bool, dict]:
    """Execute download with automated candidate fallback traversal."""
    urls_to_try = [item.url]
    for fb in getattr(item, "fallback_urls", []):
        if fb not in urls_to_try:
            urls_to_try.append(fb)

    last_info: dict = {"reason": "failed"}
    for idx, target_url in enumerate(urls_to_try):
        success, info = downloader._download_file(
            target_url,
            directory,
            stem,
            media_kind,
            referer=referer,
            min_image_size=min_size,
            thumbnail_prefix_pattern=thumb_pattern,
            cdn_hosts=cdn_hosts,
        )
        if success:
            if idx > 0:
                LOGGER.info("Successfully recovered media for %s using fallback candidate #%d: %s", item.url, idx, target_url)
                item.url = target_url
            return True, info
        last_info = info

    return False, last_info


class MediaProcessor:
    """Handles filtering, deduplication, scoring, and deferred downloading of media."""

    def __init__(self, downloader):
        self.downloader = downloader

    def finalize_images(self, result, options) -> list:

        seed_set = {normalize_url(u) for u in options.seed_urls}
        domain_profiles = options.domain_profiles or {}
        seen = set()
        kept = []
        for item in result.images:
            item.url = normalize_url(item.url)
            if item.url in seen:
                result.rejected_items.append(
                    RejectedItem("image", item.url, item.source_page, "duplicate")
                )
                continue
            score = score_image_relevance(
                item, options.keyword, options.entity_tokens, seed_set, domain_profiles
            )
            item.score = score
            reason = rejection_reason_for_image(
                item, options.keyword, options.entity_tokens, seed_set, domain_profiles
            )
            if reason:
                result.rejected_items.append(
                    RejectedItem("image", item.url, item.source_page, reason, score)
                )
                continue
            seen.add(item.url)
            kept.append(item)
        kept.sort(
            key=lambda item: (
                item.score,
                contains_subject_text(
                    safe_join([item.url, item.source_page, item.alt_text, item.page_title]).lower(),
                    options.keyword,
                    options.entity_tokens,
                ),
            ),
            reverse=True,
        )
        return kept

    def finalize_videos(self, result, options) -> list:

        seed_set = {normalize_url(u) for u in options.seed_urls}
        domain_profiles = options.domain_profiles or {}
        seen = set()
        kept = []
        for item in result.videos:
            item.url = normalize_url(item.url)
            if item.url in seen:
                result.rejected_items.append(
                    RejectedItem("video", item.url, item.source_page, "duplicate")
                )
                continue
            score = score_video_relevance(
                item, options.keyword, options.entity_tokens, seed_set, domain_profiles
            )
            item.score = score
            if reason := rejection_reason_for_video(
                item,
                options.keyword,
                options.entity_tokens,
                seed_set,
                domain_profiles,
            ):
                result.rejected_items.append(
                    RejectedItem("video", item.url, item.source_page, reason, score)
                )
                continue
            seen.add(item.url)
            kept.append(item)
        kept.sort(
            key=lambda item: (
                item.score,
                contains_subject_text(
                    safe_join([item.url, item.source_page, item.page_title]).lower(),
                    options.keyword,
                    options.entity_tokens,
                ),
            ),
            reverse=True,
        )
        return kept

    def _save_dead_urls(self, result, options, output_root) -> None:
        with self.downloader._dead_urls_lock:
            dead_urls_list = sorted(list(self.downloader._dead_urls))
        if dead_urls_list:
            LOGGER = get_logger(__name__)
            # 1. Save to subject directory (persistent)
            subject_dead_file = options.output_dir / result.keyword_slug / "dead_urls.json"
            try:
                subject_dead_file.parent.mkdir(parents=True, exist_ok=True)
                with open(subject_dead_file, "w", encoding="utf-8") as f:
                    json.dump(dead_urls_list, f, indent=2)
            except Exception as e:
                LOGGER.warning("Failed to save dead URLs to subject dir: %s", e)
            # 2. Save copy to run directory
            run_dead_file = output_root / "dead_urls.json"
            try:
                run_dead_file.parent.mkdir(parents=True, exist_ok=True)
                with open(run_dead_file, "w", encoding="utf-8") as f:
                    json.dump(dead_urls_list, f, indent=2)
            except Exception as e:
                LOGGER.warning("Failed to save dead URLs to run dir: %s", e)

    def start_downloads(self, result, options, output_root) -> None:

        self.LOGGER = get_logger(__name__)
        self.options = options
        self.result = result
        self.output_root = output_root

        # Load known dead URLs
        dead_urls_file = options.output_dir / result.keyword_slug / "dead_urls.json"
        if dead_urls_file.exists():
            try:
                with open(dead_urls_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        with self.downloader._dead_urls_lock:
                            self.downloader._dead_urls.update(loaded)
                self.LOGGER.info("Loaded %d known dead URLs", len(self.downloader._dead_urls))
            except Exception as e:
                self.LOGGER.warning("Failed to load dead URLs: %s", e)

        # Setup CDN hosts
        self._cdn_hosts_deduped = []
        _cdn_hosts = []
        if options.seed_manifest is not None:
            _cdn_hosts.extend(getattr(options.seed_manifest, "all_allowed_hosts", []))
        elif options.domain_profiles:
            for _dp in options.domain_profiles.values():
                _cdn_hosts.extend(getattr(_dp, "cdn_hosts", []))
        
        _seen_cdn = set()
        for _h in _cdn_hosts:
            if _h not in _seen_cdn:
                _seen_cdn.add(_h)
                self._cdn_hosts_deduped.append(_h)

        # State for pipelining
        self.download_queue = queue.Queue(maxsize=5000)
        self.domain_counters = {}
        self._seen_download_urls = set()
        self._is_running = True
        
        self.dl_executor = _cf.ThreadPoolExecutor(
            max_workers=CONCURRENT_DOWNLOADS, thread_name_prefix="dl"
        )
        
        # Start a manager thread that consumes the queue and submits to the executor
        self._manager_thread = threading.Thread(target=self._download_manager_loop, name="DlManagerThread", daemon=True)
        self._manager_thread.start()
        self.LOGGER.info("Started pipelined media downloader with max %d workers.", CONCURRENT_DOWNLOADS)

    def enqueue_download(self, item, media_kind: str) -> None:
        """Called by MediaPipeline to push an item for immediate download."""
        if getattr(self, "download_queue", None) is None:
            return  # Downloads not active

        
        if media_kind == "video" and item.type not in {"direct", "hls", "dash"}:
            item.status = "skipped"
            item.failure_reason = "non_downloadable_type"
            return

        norm = normalize_url(item.url)
        if norm in self._seen_download_urls:
            item.status = "skipped"
            item.failure_reason = "duplicate_url_precheck"
            return
        self._seen_download_urls.add(norm)

        domain = urlparse(item.source_page).netloc.lower()
        if ":" in domain:
            domain = domain.split(":")[0]
            
        self.domain_counters[domain] = self.domain_counters.get(domain, 0) + 1
        idx = self.domain_counters[domain]
        domain_prefix = domain.replace(".", "_")
        
        stem_suffix = re.sub(
            r"[^a-zA-Z0-9]+", "_",
            (getattr(item, "alt_text", "") or item.page_title or media_kind).strip().lower(),
        ).strip("_")
        stem_suffix = stem_suffix[:40] if stem_suffix else "asset"
        stem = f"{domain_prefix}_{idx:03d}_{stem_suffix}"

        # Determine directory
        sub_dir = DEFAULT_DOWNLOAD_IMAGES_SUBDIR if media_kind == "image" else DEFAULT_DOWNLOAD_VIDEOS_SUBDIR
        domain_dir = self.output_root / sub_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)

        task = (item, domain_dir, stem, media_kind)
        # Block if queue is full (Soft Cap Backpressure)
        self.download_queue.put(task)

    def _download_manager_loop(self):

        def add_rejected(kind, url, source_page, reason, score):
            self.result.rejected_items.append(
                RejectedItem(kind=kind, url=url, source_page=source_page, reason=reason, score=score)
            )

        futures_map = {}
        
        while self._is_running or not self.download_queue.empty() or futures_map:
            try:
                task = self.download_queue.get(timeout=0.5)
                if task is None:
                    continue
                item, directory, stem, media_kind = task
                
                dl_host = urlparse(item.source_page).netloc.lower()
                profile = self.options.domain_profiles.get(dl_host) if self.options.domain_profiles else None
                min_size = getattr(profile, "min_image_size", None) if profile else None
                thumb_pattern = getattr(profile, "thumbnail_prefix_pattern", None) if profile else None
                needs_referer = getattr(profile, "requires_referer", False) if profile else False
                referer = item.source_page if needs_referer else None

                fut = self.dl_executor.submit(
                    _download_candidate_with_fallbacks,
                    self.downloader,
                    item,
                    directory,
                    stem,
                    media_kind,
                    referer,
                    min_size,
                    thumb_pattern,
                    self._cdn_hosts_deduped,
                )
                futures_map[fut] = (item, media_kind)
                self.download_queue.task_done()
                
            except queue.Empty:
                pass
            
            # Periodically check for completed futures to avoid memory leaks
            done = [f for f in futures_map if f.done()]
            for f in done:
                item, media_kind = futures_map.pop(f)
                try:
                    success, download_info = f.result()
                    if success:
                        item.status = "downloaded"
                        item.file_path = download_info.get("file_path", "")
                        item.hash = download_info.get("hash", "")
                        item.file_size_bytes = download_info.get("file_size_bytes")
                        item.mime_type = download_info.get("mime_type", "")
                        if download_info.get("width") is not None:
                            item.width = download_info.get("width")
                        if download_info.get("height") is not None:
                            item.height = download_info.get("height")
                        self.result.download_stats["downloaded"] = self.result.download_stats.get("downloaded", 0) + 1
                    else:
                        reason = download_info.get("reason", "unknown")
                        item.status = "skipped" if reason in {"low_resolution", "unparseable_dimensions", "duplicate", "invalid_media_type"} else "failed"
                        item.failure_reason = reason
                        key = f"download_{reason}"
                        self.result.download_stats[key] = self.result.download_stats.get(key, 0) + 1
                        add_rejected(media_kind, item.url, item.source_page, f"download_{reason}", item.score)
                        
                        dl_host = urlparse(item.source_page).netloc.lower()
                        if dl_host in self.result.domain_stats:
                            self.result.domain_stats[dl_host]["rejected_count"] += 1
                            if media_kind == "image":
                                self.result.domain_stats[dl_host]["images_kept"] = max(0, self.result.domain_stats[dl_host]["images_kept"] - 1)
                            else:
                                self.result.domain_stats[dl_host]["videos_kept"] = max(0, self.result.domain_stats[dl_host]["videos_kept"] - 1)
                except Exception as exc:
                    self.LOGGER.warning("Download error for %s: %s", item.url, exc)
                    item.status = "failed"
                    item.failure_reason = f"exception_{type(exc).__name__}"
                    add_rejected(media_kind, item.url, item.source_page, f"download_failed:{type(exc).__name__}", item.score)

    def stop_downloads(self) -> None:
        if getattr(self, "_is_running", False):
            self._is_running = False
            self.LOGGER.info("Waiting for pipelined downloads to complete...")
            if getattr(self, "_manager_thread", None):
                self._manager_thread.join()
            if getattr(self, "dl_executor", None):
                self.dl_executor.shutdown(wait=True)
            self._save_dead_urls(self.result, self.options, self.output_root)
            self.LOGGER.info("Download pipeline fully stopped.")


