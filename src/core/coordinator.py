import logging
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from urllib.parse import urlparse
from typing import Optional, List, Tuple

from core.governor import CrawlGovernor
from core.pipeline import MediaPipeline
from core.models import ScrapeResult, PageReport
from core.filters import normalize_url
from scraper.specialized import SpecializedExtractor

LOGGER = logging.getLogger(__name__)

class CrawlCoordinator:
    """
    Coordinates the multi-threaded crawl process.
    Uses a thread pool to fetch pages, governed by the CrawlGovernor,
    and pushes extracted media to the MediaPipeline queue.
    """
    def __init__(
        self,
        search_provider,
        video_scraper,
        options,
        result: ScrapeResult,
        state_cache,
        workers: int = 12
    ):
        self.search_provider = search_provider
        self.video_scraper = video_scraper
        self.options = options
        self.result = result
        self.state_cache = state_cache
        
        self.max_results = getattr(options, "max_results", 0)
        self.workers = workers
        
        self.governor = CrawlGovernor(initial_concurrency=workers)
        
        self.media_queue = queue.Queue(maxsize=1000)
        self.result_lock = threading.RLock()
        
        self.seen_rejected_urls = set()
        
    def add_rejected(self, kind: str, url: str, source_page: str, reason: str, score: int = 0) -> bool:
        from core.models import RejectedItem
        norm_url = normalize_url(url)
        key = (norm_url, reason)
        with self.result_lock:
            if key in self.seen_rejected_urls:
                return False
            self.seen_rejected_urls.add(key)
            self.result.rejected_items.append(
                RejectedItem(kind=kind, url=norm_url, source_page=source_page, reason=reason, score=score)
            )
            return True

    async def _run_preflight(self, urls: List[str]) -> List[str]:
        import httpx
        import asyncio
        valid_urls = []
        
        async def check_url(client, url):
            try:
                resp = await client.head(url, follow_redirects=True, timeout=3.0)
                if resp.status_code < 400 or resp.status_code == 405: # allow Method Not Allowed for HEAD
                    valid_urls.append(url)
                else:
                    LOGGER.info(f"Pre-flight failed for {url} (status {resp.status_code})")
            except Exception as e:
                LOGGER.info(f"Pre-flight failed for {url} (error {e})")

        async with httpx.AsyncClient(verify=False) as client:
            tasks = [check_url(client, u) for u in urls]
            await asyncio.gather(*tasks)
            
        return valid_urls

    def execute(self, ordered_pages: List[Tuple[str, int]], discovered_links_counts: dict) -> ScrapeResult:
        """Execute the fetching and media extraction using a controlled ThreadPool."""
        import asyncio
        if ordered_pages:
            urls = [p for p, d in ordered_pages]
            LOGGER.info(f"Running lightweight pre-flight probes for {len(urls)} URLs...")
            valid_urls = set(asyncio.run(self._run_preflight(urls)))
            ordered_pages = [(p, d) for p, d in ordered_pages if p in valid_urls]
            LOGGER.info(f"Pre-flight complete. {len(ordered_pages)} URLs passed.")

        from core.engine import _is_target_met
        
        # 1. Start the MediaPipeline thread
        pipeline = MediaPipeline(
            result=self.result,
            result_lock=self.result_lock,
            options=self.options,
            media_queue=self.media_queue,
            add_rejected_cb=self.add_rejected
        )
        pipeline.start()

        from collections import deque
        pages_queue = deque(ordered_pages)
        
        futures = {}
        current_concurrency = self.workers
        
        with ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="scraper") as executor:
            def submit_next():
                while True:
                    skipped = []
                    while pages_queue:
                        next_page, next_depth = pages_queue.popleft()
                        host = urlparse(next_page).netloc.lower()
                        
                        if not self.governor.is_host_available(host):
                            with self.governor.lock:
                                is_failed = host in self.governor.failed_hosts
                            if not is_failed:
                                skipped.append((next_page, next_depth))
                            else:
                                with self.result_lock:
                                    self.result.page_reports.append(
                                        PageReport(
                                            url=next_page, depth=next_depth,
                                            status="skipped", reason="host_failed_skipped",
                                            discovered_links=0, images_found=0, videos_found=0
                                        )
                                    )
                            continue
                        if not self.governor.can_acquire_worker(host):
                            skipped.append((next_page, next_depth))
                            continue
                        
                        self.governor.increment_worker(host)
                        pages_queue.extend(skipped)
                        fut = executor.submit(self._fetch_page, next_page, next_depth)
                        futures[fut] = (next_page, next_depth, time.monotonic())
                        return True
                        
                    if skipped:
                        pages_queue.extend(skipped)
                        if not futures:
                            time.sleep(0.5)
                            continue
                        return False
                    return False

            for _ in range(self.workers):
                if not submit_next():
                    break

            while futures or pages_queue:
                if futures:
                    done, _ = wait(futures.keys(), return_when=FIRST_COMPLETED)
                    for future in done:
                        if future not in futures:
                            continue
                        page, depth, start_time = futures.pop(future)
                        latency = time.monotonic() - start_time
                        host = urlparse(page).netloc.lower()

                        self.governor.decrement_worker(host)

                        try:
                            page, depth, page_images, page_videos, scrape_status = future.result()
                            self.governor.report_yield(host, len(page_images) + len(page_videos))
                        except Exception as exc:
                            LOGGER.warning("Worker failed for %s: %s", page, exc)
                            page_images, page_videos, scrape_status = [], [], f"worker_error:{type(exc).__name__}"

                        is_block = "429" in scrape_status or "403" in scrape_status or "cooldown" in scrape_status or "blacklisted" in scrape_status
                        is_worker_error = "worker_error" in scrape_status or "fetch_error" in scrape_status
                    
                        if is_block:
                            self.governor.report_429(host)
                            current_concurrency = max(1, current_concurrency - 2)
                        elif scrape_status == "fetch_error:login_wall":
                            self.governor.report_error(host, is_login_wall=True)
                        elif is_worker_error:
                            self.governor.report_error(host)
                        elif scrape_status == "ok":
                            self.governor.report_success(host)
                        
                        net_latency = self.search_provider.http.last_net_latency
                        if not isinstance(net_latency, (int, float)):
                            net_latency = 0.0
                        effective_latency = net_latency if net_latency > 0.0 else latency
                    
                        if not is_block:
                            if effective_latency > 2.0:
                                current_concurrency = max(1, current_concurrency - 1)
                            else:
                                if current_concurrency < self.workers:
                                    current_concurrency += 1

                        with self.result_lock:
                            if host not in self.result.domain_stats:
                                self.result.domain_stats[host] = {
                                    "pages_scanned": 0, "images_kept": 0, "videos_kept": 0,
                                    "rejected_count": 0, "error_429_count": 0, "error_other_count": 0,
                                }
                            stats = self.result.domain_stats[host]
                            if scrape_status == "ok":
                                pass 
                            elif is_block:
                                stats["error_429_count"] += 1
                            elif is_worker_error:
                                stats["error_other_count"] += 1
                            
                            self.result.scanned_pages.append(page)
                            self.result.page_reports.append(
                                PageReport(
                                    url=page, depth=depth,
                                    status="success" if scrape_status == "ok" else "skipped",
                                    reason="" if scrape_status == "ok" else scrape_status,
                                    discovered_links=discovered_links_counts.get(page, 0),
                                    images_found=len(page_images), videos_found=len(page_videos)
                                )
                            )
                            if scrape_status == "ok" and self.state_cache:
                                self.state_cache.mark_processed(normalize_url(page))

                        if scrape_status == "ok":
                            self.media_queue.put((page, page_images, page_videos))

                        with self.result_lock:
                            target_met = self.max_results > 0 and _is_target_met(self.result, self.options, self.max_results)
                        
                        if target_met:
                            LOGGER.info("Target media limits met early. Cancelling remaining page fetches.")
                            pages_queue.clear()
                            for f in list(futures.keys()):
                                if not f.done():
                                    f.cancel()
                            break

                while len(futures) < current_concurrency:
                    if not submit_next():
                        break

        pipeline.stop()
        
        if self.max_results > 0:
            extra_videos = self.video_scraper.search(
                self.options.keyword, self.max_results,
                allow_domains=self.options.allow_domains, block_domains=self.options.block_domains
            )
            if extra_videos:
                pipeline._process_batch("extra_videos_search", [], extra_videos)
                
        return self.result

    def _fetch_page(self, page: str, depth: int):
        host = urlparse(page).netloc.lower()
        with self.result_lock:
            if host not in self.result.domain_stats:
                self.result.domain_stats[host] = {
                    "pages_scanned": 0, "images_kept": 0, "videos_kept": 0,
                    "rejected_count": 0, "error_429_count": 0, "error_other_count": 0,
                }
            stats = self.result.domain_stats[host]
            pages_scanned = stats["pages_scanned"]
            total_kept = stats["images_kept"] + stats["videos_kept"]
            
            is_seeded = (host in (self.options.domain_profiles or {})) or (host in (self.options.seed_domains or []))
            if not is_seeded:
                if pages_scanned >= 15 and total_kept == 0:
                    return page, depth, [], [], "low_yield_skipped"
                if pages_scanned >= 20 and (total_kept / pages_scanned) < 0.05:
                    return page, depth, [], [], "low_yield_skipped"
            
            profile = (self.options.domain_profiles or {}).get(host)
            if profile and getattr(profile, "max_pages", None) is not None:
                if pages_scanned >= profile.max_pages:
                    return page, depth, [], [], "max_pages_capped"
            
            stats["pages_scanned"] += 1
            
        if SpecializedExtractor.is_supported(page):
            LOGGER.info(f"Routing {page} to specialized extractor.")
            spec_result = SpecializedExtractor.extract(page)
            from core.models import ImageItem, VideoItem
            page_images = [ImageItem(url=u, source_page=page, status="pending") for u in spec_result.images]
            page_videos = [VideoItem(url=u, source_page=page, type="direct", status="pending") for u in spec_result.videos]
            scrape_status = "ok"
        else:
            page_images, page_videos, scrape_status = self.search_provider.scrape_page(
                page, allow_domains=self.options.allow_domains, block_domains=self.options.block_domains
            )
            
        return page, depth, page_images, page_videos, scrape_status
