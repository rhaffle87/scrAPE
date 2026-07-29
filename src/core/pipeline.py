import logging
import threading
import queue
from urllib.parse import urlparse
from typing import Dict, Set

from core.models import ImageItem, VideoItem, ScrapeResult
from core.filters import (
    normalize_url,
    normalize_media_url,
    score_image_relevance,
    rejection_reason_for_image,
    score_video_relevance,
    rejection_reason_for_video,
)
from core.engine import _video_resolution_hint

LOGGER = logging.getLogger(__name__)

def get_domain_slug(url: str) -> str:
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if ":" in netloc:
        netloc = netloc.split(":")[0]
    return netloc

class MediaPipeline:
    """
    Decoupled pipeline for processing media items (images and videos).
    It runs in a dedicated thread to consume raw media from a queue,
    deduplicate, score, filter, and append to the final ScrapeResult.
    """
    def __init__(
        self,
        result: ScrapeResult,
        result_lock: threading.RLock,
        options,
        media_queue: queue.Queue,
        add_rejected_cb,
    ):
        self.result = result
        self.result_lock = result_lock
        self.options = options
        self.media_queue = media_queue
        self.add_rejected = add_rejected_cb
        
        self.seen_images: Dict[str, ImageItem] = {}
        self.seen_videos: Dict[str, VideoItem] = {}
        self.processed_media_urls: Set[str] = set()
        
        self.seed_set = {normalize_url(u) for u in (self.options.seed_urls or [])}
        self.domain_profiles = self.options.domain_profiles or {}
        self.max_results = getattr(self.options, "max_results", 0)

        self.is_running = False
        self._thread = None

    def start(self):
        self.is_running = True
        self._thread = threading.Thread(target=self._run, name="MediaPipelineThread", daemon=True)
        self._thread.start()

    def stop(self):
        self.is_running = False
        self.media_queue.put(None)
        if self._thread:
            self._thread.join(timeout=2.0)

    def _run(self):
        while self.is_running:
            try:
                batch = self.media_queue.get(timeout=1.0)
                if batch is None:
                    break
                
                page, images, videos = batch
                self._process_batch(page, images, videos)
                self.media_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                LOGGER.exception(f"Error in MediaPipeline: {e}")

    def _process_batch(self, page: str, images: list, videos: list):
        host = urlparse(page).netloc.lower()
        
        with self.result_lock:
            if host not in self.result.domain_stats:
                self.result.domain_stats[host] = {
                    "pages_scanned": 0,
                    "images_kept": 0,
                    "videos_kept": 0,
                    "rejected_count": 0,
                    "error_429_count": 0,
                    "error_other_count": 0,
                }
            stats = self.result.domain_stats[host]

        for item in images:
            item.url = normalize_url(item.url)
            norm_key = normalize_media_url(item.url)
            
            with self.result_lock:
                if norm_key in self.seen_images:
                    existing = self.seen_images[norm_key]
                    if "?" in item.url and "?" not in existing.url:
                        existing.url = item.url
                    else:
                        if self.add_rejected("image", item.url, item.source_page, "duplicate"):
                            stats["rejected_count"] += 1
                    continue

                if norm_key in self.processed_media_urls:
                    continue
                self.processed_media_urls.add(norm_key)

            score = score_image_relevance(
                item, self.options.keyword, self.options.entity_tokens,
                self.seed_set, self.domain_profiles
            )
            item.score = score
            reason = rejection_reason_for_image(
                item, self.options.keyword, self.options.entity_tokens,
                self.seed_set, self.domain_profiles
            )
            
            with self.result_lock:
                if reason:
                    if self.add_rejected("image", item.url, item.source_page, reason, score):
                        stats["rejected_count"] += 1
                    continue

                if self.max_results > 0 and len(self.result.images) >= self.max_results:
                    self.add_rejected("image", item.url, item.source_page, "max_results_limit", score)
                    continue

                self.seen_images[norm_key] = item
                item.source_domain = get_domain_slug(item.source_page)
                self.result.images.append(item)
                stats["images_kept"] += 1

        for item in videos:
            item.url = normalize_url(item.url)
            norm_key = normalize_media_url(item.url)
            
            with self.result_lock:
                if norm_key in self.seen_videos:
                    existing = self.seen_videos[norm_key]
                    new_res = _video_resolution_hint(item.url)
                    old_res = _video_resolution_hint(existing.url)
                    if new_res > old_res:
                        existing.url = item.url
                    elif "?" in item.url and "?" not in existing.url:
                        existing.url = item.url
                    else:
                        if self.add_rejected("video", item.url, item.source_page, "duplicate"):
                            stats["rejected_count"] += 1
                    continue

                if norm_key in self.processed_media_urls:
                    continue
                self.processed_media_urls.add(norm_key)
                
            score = score_video_relevance(
                item, self.options.keyword, self.options.entity_tokens,
                self.seed_set, self.domain_profiles
            )
            item.score = score
            reason = rejection_reason_for_video(
                item, self.options.keyword, self.options.entity_tokens,
                self.seed_set, self.domain_profiles
            )
            
            with self.result_lock:
                if reason:
                    if self.add_rejected("video", item.url, item.source_page, reason, score):
                        stats["rejected_count"] += 1
                    continue

                if self.max_results > 0 and len(self.result.videos) >= self.max_results:
                    self.add_rejected("video", item.url, item.source_page, "max_results_limit", score)
                    continue

                self.seen_videos[norm_key] = item
                item.source_domain = get_domain_slug(item.source_page)
                self.result.videos.append(item)
                stats["videos_kept"] += 1
