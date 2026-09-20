import logging
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from urllib.parse import urlparse
from typing import List, Tuple
from pathlib import Path

from core.governor import CrawlGovernor
from core.pipeline import MediaPipeline
from core.models import ScrapeResult, PageReport
from core.filters import normalize_url, looks_like_media, is_pagination_url
from core.priority_queue import AdaptiveCrawlQueue, DomainBudgetGovernor
from scraper.specialized import SpecializedExtractor
from core.profiler import DomainProfiler

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
        workers: int = 12,
        rules_manager = None,
        page_limit: float = float('inf'),
        crawl_depth: float = 2,
        media_processor=None,
        task_state: dict | None = None,
    ):
        self.search_provider = search_provider
        self.video_scraper = video_scraper
        self.options = options
        self.result = result
        self.state_cache = state_cache
        
        self.rules_manager = rules_manager
        self.page_limit = page_limit
        self.crawl_depth = crawl_depth
        self.media_processor = media_processor
        self.task_state = task_state or {}
        
        self.max_results = getattr(options, "max_results", 0)
        self.workers = workers
        
        self.governor = CrawlGovernor(initial_concurrency=workers)
        self.budget_governor = DomainBudgetGovernor()
        self.profiler = DomainProfiler(state_cache=self.state_cache)
        
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
                if resp.status_code not in (404, 410):
                    valid_urls.append(url)
                else:
                    LOGGER.info(f"Pre-flight failed for {url} (status {resp.status_code})")
                    if self.state_cache:
                        self.state_cache.mark_dead(url, status=resp.status_code)
            except Exception as e:
                LOGGER.info(f"Pre-flight exception for {url} ({type(e).__name__}: {repr(e)}). Allowing to pass to stealth pipeline.")
                valid_urls.append(url)

        async with httpx.AsyncClient(verify=False) as client:  # nosec B501
            tasks = [check_url(client, u) for u in urls]
            await asyncio.gather(*tasks)
            
        return valid_urls

    def execute(self, ordered_pages: List[Tuple[str, int]]) -> ScrapeResult:
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
            add_rejected_cb=self.add_rejected,
            media_processor=self.media_processor,
        )
        pipeline.start()

        # Checkpoint restoration if resuming
        resume_id = getattr(self.options, "resume_run_id", None)
        checkpoint_data = None
        if resume_id and self.state_cache and hasattr(self.state_cache, "load_crawl_checkpoint"):
            checkpoint_data = self.state_cache.load_crawl_checkpoint(resume_id)

        pages_queue = AdaptiveCrawlQueue()
        visited_pages = set()

        if checkpoint_data:
            LOGGER.info("Resuming crawl from checkpoint '%s' (%d saved items).", resume_id, len(checkpoint_data["queue_items"]))
            total_pages_scanned = checkpoint_data.get("total_pages_scanned", 0)
            current_concurrency = checkpoint_data.get("current_concurrency", self.workers)
            pages_queue.from_checkpoint_items(checkpoint_data["queue_items"])
            for q_item in checkpoint_data["queue_items"]:
                visited_pages.add(q_item["url"])
        else:
            for p, d in ordered_pages:
                pages_queue.push(
                    url=p,
                    depth=d,
                    retry_count=0,
                    release_at=0.0,
                    keyword=getattr(self.options, "keyword", ""),
                )
                visited_pages.add(p)
            total_pages_scanned = 0
            current_concurrency = self.workers

        last_checkpoint_time = time.monotonic()
        self.profiling_domains = set()
        self.quarantined_domains = {}

        futures = {}

        with ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="scraper") as executor:
            def submit_next():
                nonlocal total_pages_scanned
                while True:
                    # Sync telemetry state
                    self.task_state["images_found"] = len(self.result.images)
                    self.task_state["videos_found"] = len(self.result.videos)
                    if self.page_limit and self.page_limit > 0 and self.page_limit != float('inf'):
                        self.task_state["progress"] = min(100, int((total_pages_scanned / self.page_limit) * 100))
                    elif self.max_results and self.max_results > 0:
                        total_media = self.task_state["images_found"] + self.task_state["videos_found"]
                        self.task_state["progress"] = min(100, int((total_media / (self.max_results * 2)) * 100))

                    if self.task_state.get("abort_requested"):
                        LOGGER.warning("Hard abort requested via Telegram. Halting instantly.")
                        if self.state_cache and hasattr(self.state_cache, "save_crawl_checkpoint"):
                            self.state_cache.save_crawl_checkpoint(
                                run_id=self.result.run_id,
                                keyword=self.result.keyword,
                                total_pages_scanned=total_pages_scanned,
                                current_concurrency=current_concurrency,
                                queue_items=pages_queue.to_checkpoint_items(),
                                state_metadata={"progress": self.task_state.get("progress", 0), "aborted": True},
                            )
                        pages_queue.clear()
                        return False

                    if self.task_state.get("stop_requested"):
                        LOGGER.info("Graceful stop requested via Telegram. Clearing queue and waiting for active workers to finish.")
                        if self.state_cache and hasattr(self.state_cache, "save_crawl_checkpoint"):
                            self.state_cache.save_crawl_checkpoint(
                                run_id=self.result.run_id,
                                keyword=self.result.keyword,
                                total_pages_scanned=total_pages_scanned,
                                current_concurrency=current_concurrency,
                                queue_items=pages_queue.to_checkpoint_items(),
                                state_metadata={"progress": self.task_state.get("progress", 0), "stopped": True},
                            )
                        pages_queue.clear()
                        return False

                    if self.task_state.get("status") == "paused":
                        time.sleep(1.0)
                        continue

                    skipped = []
                    while pages_queue:
                        if total_pages_scanned >= self.page_limit:
                            pages_queue.clear()
                            return False

                        score, next_depth, next_retry, release_at, time_enqueued, next_page = pages_queue.pop()

                        # D: release-gate — park entries that aren't ready yet
                        if release_at > time.monotonic():
                            skipped.append((score, next_depth, next_retry, release_at, time.monotonic(), next_page))
                            continue

                        if self.state_cache and self.state_cache.is_dead(next_page):
                            continue

                        host = urlparse(next_page).netloc.lower()

                        # -- AUTO-PROFILER INTERCEPTION START --

                        # 1. Check if quarantined (waiting for auth)
                        if host in self.quarantined_domains:
                            q_state = self.quarantined_domains[host]
                            if time.monotonic() > q_state['expires_at']:
                                LOGGER.warning(f"Timeout waiting for auth on {host}. Setting 24h cooldown.")
                                if self.state_cache:
                                    self.state_cache.set_profiler_cooldown(host, cooldown_hours=24)
                                if getattr(self.profiler, 'notifier', None):
                                    self.profiler.notifier.notify_watchdog_status(f"[TIMEOUT] <b>Timeout Reached:</b> {host} has been skipped for this run.")
                                del self.quarantined_domains[host]
                                continue # Drop this URL

                            session_file = Path("data/sessions") / f"{host.replace('.', '_')}.json"
                            if session_file.exists():
                                LOGGER.info(f"Auto-Profiler: Cookie received for {host}. Resuming crawl.")
                                self.profiler._mark_domain_mapped(host)
                                del self.quarantined_domains[host]
                            else:
                                release_at = time.monotonic() + 10.0
                                skipped.append((score, next_depth, next_retry, release_at, time.monotonic(), next_page))
                                continue

                        # 2. Check if unmapped
                        self.profiler._load_configs()
                        is_mapped = (
                            host in self.profiler.domain_config.get("auto_mapped", []) or
                            host in self.profiler.domain_config.get("rate_limits", {}) or
                            host in self.profiler.domain_config.get("referer_overrides", {}) or
                            (getattr(self, "options", None) and host in getattr(self.options, "domain_profiles", {}))
                        )

                        if not is_mapped:
                            if host in self.profiling_domains:
                                release_at = time.monotonic() + 5.0
                                skipped.append((score, next_depth, next_retry, release_at, time.monotonic(), next_page))
                                continue

                            self.profiling_domains.add(host)

                            def _run_profiler(d=host):
                                import asyncio
                                try:
                                    res = asyncio.run(self.profiler.evaluate_domain(d))
                                    if res == "AWAITING_AUTH":
                                        self.quarantined_domains[d] = {
                                            'status': 'AWAITING_AUTH',
                                            'expires_at': time.monotonic() + 900
                                        }
                                except Exception as e:
                                    LOGGER.error(f"Profiler failed on {d}: {e}")
                                finally:
                                    self.profiling_domains.discard(d)

                            executor.submit(_run_profiler)
                            release_at = time.monotonic() + 5.0
                            skipped.append((score, next_depth, next_retry, release_at, time.monotonic(), next_page))
                            continue

                        # -- AUTO-PROFILER INTERCEPTION END --

                        if not self.governor.is_host_available(host):
                            with self.governor.lock:
                                is_failed = host in self.governor.failed_hosts
                            if not is_failed:
                                skipped.append((score, next_depth, next_retry, release_at, time.monotonic(), next_page))
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
                            skipped.append((score, next_depth, next_retry, release_at, time.monotonic(), next_page))
                            continue

                        self.governor.increment_worker(host)
                        for item in skipped:
                            pages_queue.push(url=item[5], depth=item[1], retry_count=item[2], release_at=item[3], score=item[0])

                        total_pages_scanned += 1
                        fut = executor.submit(self._fetch_page, next_page, next_depth)
                        futures[fut] = (next_page, next_depth, next_retry, time.monotonic())
                        return True

                    if skipped:
                        for item in skipped:
                            pages_queue.push(url=item[5], depth=item[1], retry_count=item[2], release_at=item[3], score=item[0])
                        if not futures:
                            time.sleep(1.0)
                            continue
                        return False
                    return False

            for _ in range(self.workers):
                if not submit_next():
                    break

            while futures or pages_queue:
                now_check = time.monotonic()
                if now_check - last_checkpoint_time >= 30.0:
                    if self.state_cache and hasattr(self.state_cache, "save_crawl_checkpoint"):
                        self.state_cache.save_crawl_checkpoint(
                            run_id=self.result.run_id,
                            keyword=self.result.keyword,
                            total_pages_scanned=total_pages_scanned,
                            current_concurrency=current_concurrency,
                            queue_items=pages_queue.to_checkpoint_items(),
                            state_metadata={"progress": self.task_state.get("progress", 0)},
                        )
                    last_checkpoint_time = now_check

                if futures:
                    done, _ = wait(futures.keys(), return_when=FIRST_COMPLETED)
                    for future in done:
                        if future not in futures:
                            continue
                        page, depth, retry_count, start_time = futures.pop(future)
                        latency = time.monotonic() - start_time
                        host = urlparse(page).netloc.lower()

                        self.governor.decrement_worker(host)

                        discovered_links = []
                        content = ""
                        content_type = ""
                        try:
                            page, depth, page_images, page_videos, scrape_status, content, content_type = future.result()
                            if scrape_status in ("fetch_error:404", "fetch_error:410"):
                                status_code = 404 if "404" in scrape_status else 410
                                if self.state_cache:
                                    self.state_cache.mark_dead(page, status=status_code)
                            self.governor.report_yield(host, len(page_images) + len(page_videos))
                            
                            # Link discovery in Phase 2
                            if scrape_status == "ok" and content:
                                profile = (self.options.domain_profiles or {}).get(host)
                                domain_depth_limit = (
                                    profile.crawl_depth if profile and profile.crawl_depth is not None 
                                    else self.crawl_depth
                                )
                                if depth < domain_depth_limit:
                                    if not (profile and (profile.crawl_strategy == "direct" or getattr(profile, "skip_link_discovery", False))):
                                        discovered_links = self.search_provider.discover_links_from_content(
                                            url=page, content=content, content_type=content_type,
                                            allow_domains=self.options.allow_domains,
                                            block_domains=self.options.block_domains
                                        )
                                        # Smart pagination detection
                                        try:
                                            from core.microdata import detect_smart_pagination
                                            smart_pages = detect_smart_pagination(content, page)
                                            for sp in smart_pages:
                                                if not any(lnk.get("url") == sp for lnk in discovered_links):
                                                    discovered_links.append({"url": sp, "anchor_text": "pagination_next"})
                                        except Exception as exc:
                                            LOGGER.debug("Smart pagination detection error on %s: %s", page, exc)

                                        # index→detail filtering — applied at every
                                        # depth, not just depth 0, so off-model/utility
                                        # links discovered on POST pages are filtered too
                                        if profile and profile.crawl_strategy != "direct":
                                            seed_for_host = next((s for s in self.options.seed_urls if urlparse(s).netloc.lower() == host), page)
                                            # Normalise so locale-prefixed profile seeds
                                            # collapse to their canonical
                                            # bare form and still trigger the profile rule.
                                            discovered_links = [
                                                lnk for lnk in discovered_links
                                                if (
                                                    self.rules_manager and self.rules_manager.is_detail_page(lnk["url"], seed_for_host, self.options.keyword, self.options.entity_tokens, anchor_text=lnk.get("anchor_text", ""), profile=profile)
                                                )
                                                or (
                                                    # Pagination links are legal index nodes for
                                                    # traversing a multi-page profile index. They
                                                    # are rejected by is_detail_page by design, so
                                                    # re-admit them here only when they are
                                                    # subject-scoped (same host, share the seed's
                                                    # first path segment). Keeps off-subject
                                                    # pagination (/page/2 site-wide) out.
                                                    is_pagination_url(lnk["url"])
                                                    and lnk["url"].startswith(seed_for_host.rstrip("/") + "/")
                                                )
                                            ]

                                        # Domain handler link_pattern whitelist (config-driven)
                                        if self.rules_manager:
                                            discovered_links = [
                                                lnk for lnk in discovered_links
                                                if self.rules_manager.link_pattern_allows(lnk["url"], host)
                                            ]
                                        
                                        # Enqueue new links
                                        for link in discovered_links:
                                            normalized_link = normalize_url(link["url"])
                                            if looks_like_media(normalized_link):
                                                continue
                                            
                                            scope_reason = None
                                            if self.rules_manager:
                                                scope_reason = self.rules_manager.scope_rejection_reason(normalized_link, self.options)
                                                
                                            if scope_reason:
                                                self.add_rejected("page", normalized_link, page, scope_reason)
                                                continue

                                            if normalized_link not in visited_pages:
                                                visited_pages.add(normalized_link)
                                                if self.state_cache and self.state_cache.is_dead(normalized_link):
                                                    self.add_rejected("page", normalized_link, page, "404_negative_cache")
                                                    continue

                                                l_host = urlparse(normalized_link).netloc.lower()
                                                profile = (self.options.domain_profiles or {}).get(l_host)
                                                max_p = getattr(profile, "max_pages", None)

                                                if self.budget_governor.is_domain_capped(l_host, max_p):
                                                    self.add_rejected("page", normalized_link, page, "domain_budget_capped")
                                                    continue

                                                b_penalty = self.budget_governor.get_budget_penalty(l_host, max_p)
                                                host_stats = self.result.domain_stats.get(l_host, {})
                                                h_scanned = host_stats.get("pages_scanned", 0)
                                                h_kept = host_stats.get("images_kept", 0) + host_stats.get("videos_kept", 0)
                                                h_yield_ratio = (h_kept / h_scanned) if h_scanned > 0 else 0.5

                                                pages_queue.push(
                                                    url=normalized_link,
                                                    depth=depth + 1,
                                                    retry_count=0,
                                                    release_at=0.0,
                                                    host_yield_ratio=h_yield_ratio,
                                                    keyword=getattr(self.options, "keyword", ""),
                                                    budget_penalty=b_penalty,
                                                )
                                                
                                                try:
                                                    from monitoring.telemetry import broadcast_telemetry_event
                                                    broadcast_telemetry_event("crawl_graph_node", {
                                                        "url": normalized_link,
                                                        "domain": urlparse(normalized_link).netloc.lower(),
                                                        "parent": page,
                                                        "depth": depth + 1,
                                                        "type": "link_discovered",
                                                    })
                                                except Exception:
                                                    pass

                        except Exception as exc:
                            LOGGER.warning("Worker failed for %s: %s", page, exc)
                            page_images, page_videos, scrape_status = [], [], f"worker_error:{type(exc).__name__}"

                        is_block = "429" in scrape_status or "403" in scrape_status or "cooldown" in scrape_status or "blacklisted" in scrape_status
                        is_worker_error = "worker_error" in scrape_status or "fetch_error" in scrape_status
                    
                        if is_block:
                            self.governor.report_429(host)
                            self._auto_remediate_host(host)
                            with self.result_lock:
                                if host not in self.result.domain_stats:
                                    self.result.domain_stats[host] = {
                                        "pages_scanned": 0, "images_kept": 0, "videos_kept": 0,
                                        "rejected_count": 0, "error_429_count": 0, "error_other_count": 0,
                                    }
                                self.result.domain_stats[host]["error_429_count"] += 1
                            if retry_count < 3:
                                # D: set release_at based on governor cooldown so the
                                # retry fires only after the host cooldown expires.
                                cd = self.governor.cooldown_remaining(host)
                                release_at = time.monotonic() + cd + 0.5
                                LOGGER.info("Retrying %s (attempt %d/3) after block; release in %.1fs.", page, retry_count + 1, cd + 0.5)
                                pages_queue.push(
                                    url=page,
                                    depth=depth,
                                    retry_count=retry_count + 1,
                                    release_at=release_at,
                                    keyword=getattr(self.options, "keyword", ""),
                                )
                                continue
                        elif scrape_status == "fetch_error:login_wall":
                            self.governor.report_error(host, is_login_wall=True)
                            with self.result_lock:
                                if host not in self.result.domain_stats:
                                    self.result.domain_stats[host] = {
                                        "pages_scanned": 0, "images_kept": 0, "videos_kept": 0,
                                        "rejected_count": 0, "error_429_count": 0, "error_other_count": 0,
                                    }
                                self.result.domain_stats[host]["error_other_count"] += 1
                        elif scrape_status == "login_redirect_skipped":
                            # Per-URL login redirect (deleted/age-gated item). 
                            # Skip this URL only; keep the host available.
                            # Prevents one bad item from poisoning the whole domain.
                            if self.state_cache:
                                self.state_cache.mark_dead(page)
                        elif is_worker_error:
                            self.governor.report_error(host)
                            self._auto_remediate_host(host)
                            with self.result_lock:
                                if host not in self.result.domain_stats:
                                    self.result.domain_stats[host] = {
                                        "pages_scanned": 0, "images_kept": 0, "videos_kept": 0,
                                        "rejected_count": 0, "error_429_count": 0, "error_other_count": 0,
                                    }
                                self.result.domain_stats[host]["error_other_count"] += 1
                            if retry_count < 3:
                                # D: 2s release gate on generic error retry
                                release_at = time.monotonic() + 2.0
                                LOGGER.info("Retrying %s (attempt %d/3) after error; release in 2.0s.", page, retry_count + 1)
                                pages_queue.push(
                                    url=page,
                                    depth=depth,
                                    retry_count=retry_count + 1,
                                    release_at=release_at,
                                    keyword=getattr(self.options, "keyword", ""),
                                )
                                continue
                        net_latency = getattr(getattr(self.search_provider, "http", None), "last_net_latency", 0.0)
                        if not isinstance(net_latency, (int, float)):
                            net_latency = 0.0
                        effective_latency = net_latency if net_latency > 0.0 else latency

                        if scrape_status == "ok":
                            self.governor.report_success(host, latency_s=effective_latency)
                    
                        if not is_block:
                            global_cap = self.governor.get_global_concurrency_limit()
                            if effective_latency > 2.0:
                                current_concurrency = max(1, current_concurrency - 1)
                            else:
                                if current_concurrency < min(self.workers, global_cap):
                                    current_concurrency += 1
                                elif current_concurrency > global_cap:
                                    current_concurrency = max(1, global_cap)


                        with self.result_lock:
                            if host not in self.result.domain_stats:
                                self.result.domain_stats[host] = {
                                    "pages_scanned": 0, "images_kept": 0, "videos_kept": 0,
                                    "rejected_count": 0, "error_429_count": 0, "error_other_count": 0,
                                }
                            # error counts are now incremented when the error is reported,
                            # even if the page is going to be retried (and thus loops with `continue`).
                            
                            self.result.scanned_pages.append(page)
                            self.result.page_reports.append(
                                PageReport(
                                    url=page, depth=depth,
                                    status="success" if scrape_status == "ok" else "skipped",
                                    reason="" if scrape_status == "ok" else scrape_status,
                                    discovered_links=len(discovered_links),
                                    images_found=len(page_images), videos_found=len(page_videos)
                                )
                            )
                            if scrape_status == "ok" and self.state_cache:
                                self.state_cache.mark_processed(page)

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

        # Clear checkpoint upon clean non-interrupted completion
        if self.state_cache and hasattr(self.state_cache, "clear_crawl_checkpoint"):
            if not (self.task_state.get("abort_requested") or self.task_state.get("stop_requested")):
                self.state_cache.clear_crawl_checkpoint(self.result.run_id)

        if self.max_results > 0:
            extra_videos = self.video_scraper.search(
                self.options.keyword, self.max_results,
                allow_domains=self.options.allow_domains, block_domains=self.options.block_domains
            )
            if extra_videos:
                pipeline._process_batch("extra_videos_search", [], extra_videos)

        return self.result

    def resume_from_checkpoint(self, run_id: str) -> dict | None:
        """Load persistent crawl checkpoint details for a specific run ID."""
        if not self.state_cache or not hasattr(self.state_cache, "load_crawl_checkpoint"):
            return None
        return self.state_cache.load_crawl_checkpoint(run_id)

    def _fetch_page(self, page: str, depth: int):
        host = urlparse(page).netloc.lower()
        self.budget_governor.record_page(host)
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
                    return page, depth, [], [], "low_yield_skipped", "", ""
                if pages_scanned >= 20 and (total_kept / pages_scanned) < 0.05:
                    return page, depth, [], [], "low_yield_skipped", "", ""
            
            profile = (self.options.domain_profiles or {}).get(host)
            if profile and getattr(profile, "max_pages", None) is not None:
                if pages_scanned >= profile.max_pages:
                    return page, depth, [], [], "max_pages_capped", "", ""
            
            stats["pages_scanned"] += 1
            
        if SpecializedExtractor.is_supported(page):
            LOGGER.info(f"Routing {page} to specialized extractor.")
            spec_result = SpecializedExtractor.extract(page, self.search_provider.http)
            from core.models import ImageItem, VideoItem
            page_images = [ImageItem(url=u, source_page=page, status="pending") for u in spec_result.images]
            page_videos = [VideoItem(url=u, source_page=page, type="direct", status="pending") for u in spec_result.videos]
            scrape_status = "ok"
            content = ""
            content_type = ""
        else:
            page_images, page_videos, scrape_status, content, content_type = self.search_provider.scrape_page(
                page, allow_domains=self.options.allow_domains, block_domains=self.options.block_domains
            )
            if scrape_status == "ok" and content:
                try:
                    from core.microdata import extract_jsonld_media
                    j_images, j_videos = extract_jsonld_media(content, page)
                    if j_images:
                        existing_img_urls = {img.url for img in page_images}
                        for ji in j_images:
                            if ji.url not in existing_img_urls:
                                page_images.append(ji)
                                existing_img_urls.add(ji.url)
                    if j_videos:
                        existing_vid_urls = {vid.url for vid in page_videos}
                        for jv in j_videos:
                            if jv.url not in existing_vid_urls:
                                page_videos.append(jv)
                                existing_vid_urls.add(jv.url)
                except Exception as exc:
                    LOGGER.debug("Error extracting JSON-LD microdata from %s: %s", page, exc)
            
        return page, depth, page_images, page_videos, scrape_status, content, content_type

    def _auto_remediate_host(self, host: str) -> None:
        """Trigger dynamic multi-tier stealth remediation when host health degrades."""
        health = self.governor.get_host_health_state(host)
        if health in ("CRITICAL", "PARKED"):
            http_client = getattr(self.search_provider, "http", None)
            if http_client and hasattr(http_client, "rotate_tls_profile"):
                try:
                    new_prof = http_client.rotate_tls_profile(host)
                    LOGGER.warning(
                        "Governor auto-remediation (%s health for %s): Rotated TLS profile to %s",
                        health,
                        host,
                        new_prof,
                    )
                except Exception as exc:
                    LOGGER.debug("TLS profile auto-rotation error: %s", exc)
            self.governor.report_latency(host, 3.5)


