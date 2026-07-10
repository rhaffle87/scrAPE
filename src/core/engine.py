from __future__ import annotations

import re
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, FIRST_COMPLETED
import time
from urllib.parse import urlparse

from tqdm import tqdm

from config import (
    CONCURRENT_PAGES_PER_BATCH,
    MAX_CRAWL_DEPTH,
    MAX_PAGE_FETCHES,
    OUTPUT_DIR,
)
from core.filters import (
    contains_subject_text,
    is_allowed_domain,
    is_allowed_path,
    normalize_url,
    normalize_media_url,
    rejection_reason_for_image,
    rejection_reason_for_video,
    score_image_relevance,
    score_video_relevance,
    looks_like_media,
)
from core.models import (
    EngineOptions,
    ImageItem,
    PageReport,
    RejectedItem,
    ScrapeResult,
    VideoItem,
)
from scraper.google_images import SearchProviderScraper
from scraper.video_scraper import VideoScraper
from storage.file_downloader import MediaDownloader
from utils.logger import get_logger

LOGGER = get_logger(__name__)


def _is_target_met(result: ScrapeResult, options: EngineOptions, max_results: int) -> bool:
    if max_results <= 0:
        return False

    # 1. Analyze domain profiles to see what media types are expected
    expected_types = set()
    if options.domain_profiles:
        for p in options.domain_profiles.values():
            if hasattr(p, "media_type"):
                expected_types.add(p.media_type)
            elif isinstance(p, dict) and "media_type" in p:
                expected_types.add(p["media_type"])

    # If we have profiles, we can use them to restrict expectations
    if expected_types:
        has_image = "image" in expected_types or "mixed" in expected_types
        has_video = "video" in expected_types or "mixed" in expected_types

        image_met = (not has_image) or (len(result.images) >= max_results)
        video_met = (not has_video) or (len(result.videos) >= max_results)
        return image_met and video_met

    # 2. If no profiles (General/Broad Search Scraping or keyword crawl), we check:
    image_met = len(result.images) >= max_results
    video_met = len(result.videos) >= max_results

    if image_met and video_met:
        return True

    # If one of them has reached the limit, and we've scanned at least 3 pages but found 0 of the other:
    if image_met and len(result.videos) == 0 and len(result.scanned_pages) >= 3:
        return True
    if video_met and len(result.images) == 0 and len(result.scanned_pages) >= 3:
        return True

    return False


_VIDEO_RES_RE = re.compile(r"[_\-/](\d{3,4})p", re.IGNORECASE)


def _video_resolution_hint(url: str) -> int:
    """Return numeric resolution (e.g. 1080) from URL path, or 0 if not found."""
    m = _VIDEO_RES_RE.search(url)
    return int(m.group(1)) if m else 0


class ScrapingEngine:
    def __init__(
        self,
        domain_delays: dict[str, float] | None = None,
        workers: int = CONCURRENT_PAGES_PER_BATCH,
        ignore_robots: bool = False,
    ) -> None:
        self.workers = max(1, workers)
        self.search_provider = SearchProviderScraper(
            domain_delays=domain_delays, ignore_robots=ignore_robots
        )
        self.video_scraper = VideoScraper(domain_delays=domain_delays)
        # Share the scraper's HttpClient with the downloader for connection pool reuse
        self.downloader = MediaDownloader(http=self.search_provider.http)

    def run(
        self,
        keyword: str,
        max_results: int,
        output_format: str,
        download_media: bool,
        seed_urls: list[str] | None = None,
        seed_domains: list[str] | None = None,
        allow_domains: list[str] | None = None,
        block_domains: list[str] | None = None,
        entity_tokens: list[str] | None = None,
        use_search: bool = True,
        page_limit: int = MAX_PAGE_FETCHES,
        crawl_depth: int = MAX_CRAWL_DEPTH,
        strict_domain: bool = False,
        site_tree_only: bool = False,
        seed_manifest: object | None = None,
        domain_profiles: dict | None = None,
        run_id: str | None = None,
        ignore_robots: bool = False,
    ) -> ScrapeResult:
        options = EngineOptions(
            keyword=keyword,
            max_results=max_results,
            output_format=output_format,
            download_media=download_media,
            output_dir=OUTPUT_DIR,
            seed_urls=seed_urls or [],
            seed_domains=seed_domains or [],
            allow_domains=allow_domains or [],
            block_domains=block_domains or [],
            entity_tokens=entity_tokens or [],
            use_search=use_search,
            strict_domain=strict_domain,
            site_tree_only=site_tree_only,
            ignore_robots=ignore_robots,
            seed_manifest=seed_manifest,
            domain_profiles=domain_profiles or {},
        )
        result = ScrapeResult(keyword=keyword)
        if run_id:
            result.run_id = run_id

        if options.seed_urls:
            derived_domains = [
                urlparse(url).netloc.lower()
                for url in options.seed_urls
                if urlparse(url).netloc
            ]
            options.seed_domains = list(
                dict.fromkeys([*options.seed_domains, *derived_domains])
            )
        if options.strict_domain and options.seed_domains:
            options.allow_domains = list(
                dict.fromkeys([*options.allow_domains, *options.seed_domains])
            )

        search_pages: list[str] = []
        if options.use_search:
            search_pages = self.search_provider.search_pages(
                keyword,
                max_results,
                allow_domains=options.allow_domains,
                block_domains=options.block_domains,
            )

        candidate_pages = self._build_candidate_pages(search_pages, options)
        resolved_page_limit = float("inf") if page_limit <= 0 else page_limit
        resolved_crawl_depth = float("inf") if crawl_depth <= 0 else crawl_depth
        # Organized by depth -> host -> deque of URLs
        queues: dict[int, dict[str, deque[str]]] = {}
        queued_pages: set[str] = {
            normalize_url(page)
            for page in candidate_pages
            if page and not looks_like_media(normalize_url(page))
        }
        visited_pages: set[str] = set()
        ordered_pages: list[tuple[str, int]] = []
        discovered_links_counts: dict[str, int] = {}

        result_lock = threading.RLock()
        seen_rejected_urls: set[tuple[str, str]] = set()

        def add_rejected(kind: str, url: str, source_page: str, reason: str, score: int = 0) -> bool:
            key = (url, reason)
            with result_lock:
                if key in seen_rejected_urls:
                    return False
                seen_rejected_urls.add(key)
                result.rejected_items.append(
                    RejectedItem(
                        kind=kind,
                        url=url,
                        source_page=source_page,
                        reason=reason,
                        score=score,
                    )
                )
                return True


        # Enqueue candidate pages at depth 0
        for page in candidate_pages:
            if not page or looks_like_media(normalize_url(page)):
                continue
            host = urlparse(page).netloc.lower()
            queues.setdefault(0, {}).setdefault(host, deque()).append(page)

        while len(ordered_pages) < resolved_page_limit:
            # Find the minimum depth that still has pages to crawl
            active_depths = [
                d for d, depth_queues in queues.items() if any(depth_queues.values())
            ]
            if not active_depths:
                break
            current_depth = min(active_depths)
            depth_queues = queues[current_depth]

            # Get the list of hosts that have queued pages at this depth
            active_hosts = [host for host, q in depth_queues.items() if q]

            # Pop one page from each active host in round-robin fashion
            # This balances crawls across multiple hosts at the same depth
            for host in active_hosts:
                if len(ordered_pages) >= resolved_page_limit:
                    break

                page = depth_queues[host].popleft()
                normalized_page = normalize_url(page)
                if normalized_page in visited_pages:
                    continue
                visited_pages.add(normalized_page)
                ordered_pages.append((normalized_page, current_depth))

                profile = options.domain_profiles.get(host)
                domain_depth = profile.effective_crawl_depth if profile else 1
                domain_depth_limit = min(resolved_crawl_depth, domain_depth)
                if current_depth >= domain_depth_limit:
                    continue

                # ── Per-domain crawl strategy ──────────────────────────────
                # 'direct' or skip_link_discovery: skip link discovery
                if profile and (
                    profile.crawl_strategy == "direct"
                    or getattr(profile, "skip_link_discovery", False)
                ):
                    discovered_links = []
                    discovered_links_counts[normalized_page] = 0
                else:
                    discovered_links = self.search_provider.discover_links(
                        normalized_page,
                        allow_domains=options.allow_domains,
                        block_domains=options.block_domains,
                        keyword=options.keyword if current_depth > 0 else None,
                        entity_tokens=options.entity_tokens
                        if current_depth > 0
                        else None,
                    )
                    # 'index→detail': at depth 0 only follow concrete detail links
                    # (deeper path than the seed URL, not pagination siblings)
                    if (
                        profile
                        and profile.crawl_strategy != "direct"
                        and current_depth == 0
                    ):
                        seed_for_host = next(
                            (
                                s
                                for s in options.seed_urls
                                if urlparse(s).netloc.lower() == host
                            ),
                            normalized_page,
                        )
                        discovered_links = [
                            lnk
                            for lnk in discovered_links
                            if self._is_detail_page(
                                lnk,
                                seed_for_host,
                                options.keyword,
                                options.entity_tokens,
                            )
                        ]
                    discovered_links_counts[normalized_page] = len(discovered_links)

                for link in discovered_links:
                    normalized_link = normalize_url(link)
                    if looks_like_media(normalized_link):
                        continue
                    scope_reason = self._scope_rejection_reason(
                        normalized_link, options
                    )
                    if scope_reason:
                        add_rejected("page", normalized_link, normalized_page, scope_reason)
                        continue
                    if (
                        normalized_link in visited_pages
                        or normalized_link in queued_pages
                    ):
                        continue
                    queued_pages.add(normalized_link)

                    # Enqueue link at depth + 1 under its own host
                    link_host = urlparse(normalized_link).netloc.lower()
                    queues.setdefault(current_depth + 1, {}).setdefault(
                        link_host, deque()
                    ).append(normalized_link)

        pages_to_fetch = (
            ordered_pages
            if resolved_page_limit == float("inf")
            else ordered_pages[: int(resolved_page_limit)]
        )

        # --- Concurrent page fetching ---
        # The per-domain RateLimiter is thread-safe, so workers hitting different
        # domains proceed in parallel while same-domain calls are naturally queued.

        # Deduplication maps: norm_key → item (allows URL upgrading from tokenless → tokened)
        seen_images: dict[str, object] = {}
        seen_videos: dict[str, object] = {}
        seed_set = {normalize_url(u) for u in options.seed_urls}
        domain_profiles = options.domain_profiles or {}

        def _fetch_page(page: str, depth: int):
            host = urlparse(page).netloc.lower()
            with result_lock:
                if host not in result.domain_stats:
                    result.domain_stats[host] = {
                        "pages_scanned": 0,
                        "images_kept": 0,
                        "videos_kept": 0,
                        "rejected_count": 0,
                        "error_429_count": 0,
                        "error_other_count": 0,
                    }
                stats = result.domain_stats[host]
                pages_scanned = stats["pages_scanned"]
                total_kept = stats["images_kept"] + stats["videos_kept"]
                total_raw_found = total_kept + stats["rejected_count"]
                
                is_seeded = (host in domain_profiles) or (host in (options.seed_domains or []))

                if not is_seeded and total_raw_found < 50:
                    if pages_scanned >= 20 and total_kept == 0:
                        LOGGER.info("Skipping %s: early zero-yield cutoff from domain %s", page, host)
                        return page, depth, [], [], "low_yield_skipped"

                    if pages_scanned >= 30:
                        yield_rate = total_kept / pages_scanned
                        if yield_rate < 0.05:
                            LOGGER.info("Skipping %s: low yield from domain %s (<5%%)", page, host)
                            return page, depth, [], [], "low_yield_skipped"
                
                stats["pages_scanned"] += 1

            page_images, page_videos, scrape_status = self.search_provider.scrape_page(
                page,
                allow_domains=options.allow_domains,
                block_domains=options.block_domains,
            )
            return page, depth, page_images, page_videos, scrape_status

        current_concurrency = self.workers
        futures = {}
        pages_iter = iter(pages_to_fetch)

        with tqdm(
            total=len(pages_to_fetch), desc="Fetching pages", unit="page"
        ) as pbar:
            with ThreadPoolExecutor(
                max_workers=self.workers, thread_name_prefix="scraper"
            ) as executor:
                
                def submit_next():
                    try:
                        next_page, next_depth = next(pages_iter)
                        fut = executor.submit(_fetch_page, next_page, next_depth)
                        futures[fut] = (next_page, next_depth, time.monotonic())
                        return True
                    except StopIteration:
                        return False

                # Initially submit up to current_concurrency
                for _ in range(current_concurrency):
                    if not submit_next():
                        break

                while futures:
                    done, _ = wait(futures.keys(), return_when=FIRST_COMPLETED)
                    for future in done:
                        if future not in futures:
                            continue
                        page, depth, start_time = futures.pop(future)
                        latency = time.monotonic() - start_time

                        try:
                            page, depth, page_images, page_videos, scrape_status = (
                                future.result()
                            )
                        except Exception as exc:
                            LOGGER.warning("Worker failed for %s: %s", page, exc)
                            page_images, page_videos, scrape_status = (
                                [],
                                [],
                                f"worker_error:{type(exc).__name__}",
                            )

                        # Adjust dynamic concurrency based on health
                        is_block = "429" in scrape_status or "403" in scrape_status or "worker_error" in scrape_status
                        with result_lock:
                            if is_block:
                                current_concurrency = max(1, current_concurrency - 2)
                                LOGGER.warning(
                                    "Dynamic Concurrency: Block/Error on %s. Reducing worker limit to %d.",
                                    page, current_concurrency
                                )
                            elif latency > 2.0:
                                current_concurrency = max(1, current_concurrency - 1)
                                LOGGER.info(
                                    "Dynamic Concurrency: High latency (%.2fs) on %s. Reducing worker limit to %d.",
                                    latency, page, current_concurrency
                                )
                            else:
                                if current_concurrency < self.workers:
                                    current_concurrency += 1
                                    LOGGER.info(
                                        "Dynamic Concurrency: Fast response (%.2fs) on %s. Scaling up worker limit to %d.",
                                        latency, page, current_concurrency
                                    )

                        with result_lock:
                            host = urlparse(page).netloc.lower()
                            if host not in result.domain_stats:
                                result.domain_stats[host] = {
                                    "pages_scanned": 0,
                                    "images_kept": 0,
                                    "videos_kept": 0,
                                    "rejected_count": 0,
                                    "error_429_count": 0,
                                    "error_other_count": 0,
                                }
                            
                            stats = result.domain_stats[host]

                            if scrape_status == "ok":
                                pass
                            elif scrape_status == "low_yield_skipped":
                                pass
                            elif "429" in scrape_status or "cooldown" in scrape_status or "blacklisted" in scrape_status:
                                stats["error_429_count"] += 1
                            else:
                                stats["error_other_count"] += 1

                            result.scanned_pages.append(page)
                            result.page_reports.append(
                                PageReport(
                                    url=page,
                                    depth=depth,
                                    status="success"
                                    if scrape_status == "ok"
                                    else "skipped",
                                    reason="" if scrape_status == "ok" else scrape_status,
                                    discovered_links=discovered_links_counts.get(page, 0),
                                    images_found=len(page_images),
                                    videos_found=len(page_videos),
                                )
                            )

                            # Filtering and deduplication of page_images
                            for item in page_images:
                                item.url = normalize_url(item.url)
                                norm_key = normalize_media_url(item.url)
                                if norm_key in seen_images:
                                    existing = seen_images[norm_key]
                                    if "?" in item.url and "?" not in existing.url:
                                        LOGGER.debug(
                                            "Image URL upgraded from tokenless to tokened: %s -> %s",
                                            existing.url,
                                            item.url,
                                        )
                                        existing.url = item.url
                                    else:
                                        if add_rejected("image", item.url, item.source_page, "duplicate"):
                                            stats["rejected_count"] += 1
                                    continue
                                score = score_image_relevance(
                                    item,
                                    options.keyword,
                                    options.entity_tokens,
                                    seed_set,
                                    domain_profiles,
                                )
                                item.score = score
                                reason = rejection_reason_for_image(
                                    item,
                                    options.keyword,
                                    options.entity_tokens,
                                    seed_set,
                                    domain_profiles,
                                )
                                if reason:
                                    parent_href = getattr(item, "parent_anchor_href", "")
                                    LOGGER.debug(
                                        "Image rejected: %s (reason: %s, score: %d, source: %s, parent_href: %s)",
                                        item.url,
                                        reason,
                                        score,
                                        item.source_page,
                                        parent_href,
                                    )
                                    if add_rejected("image", item.url, item.source_page, reason, score):
                                        stats["rejected_count"] += 1
                                    continue

                                if max_results > 0 and len(result.images) >= max_results:
                                    add_rejected("image", item.url, item.source_page, "max_results_limit", score)
                                    continue

                                seen_images[norm_key] = item
                                result.images.append(item)
                                stats["images_kept"] += 1

                            # Filtering and deduplication of page_videos
                            for item in page_videos:
                                item.url = normalize_url(item.url)
                                norm_key = normalize_media_url(item.url)
                                if norm_key in seen_videos:
                                    existing = seen_videos[norm_key]
                                    # Upgrade to higher-resolution copy if one is available
                                    new_res = _video_resolution_hint(item.url)
                                    old_res = _video_resolution_hint(existing.url)
                                    if new_res > old_res:
                                        LOGGER.debug(
                                            "Video resolution upgrade %dp→%dp: %s",
                                            old_res, new_res, item.url,
                                        )
                                        existing.url = item.url
                                    elif "?" in item.url and "?" not in existing.url:
                                        LOGGER.debug(
                                            "Video URL upgraded from tokenless to tokened: %s -> %s",
                                            existing.url, item.url,
                                        )
                                        existing.url = item.url
                                    else:
                                        if add_rejected("video", item.url, item.source_page, "duplicate"):
                                            stats["rejected_count"] += 1
                                    continue
                                score = score_video_relevance(
                                    item,
                                    options.keyword,
                                    options.entity_tokens,
                                    seed_set,
                                    domain_profiles,
                                )
                                item.score = score
                                reason = rejection_reason_for_video(
                                    item,
                                    options.keyword,
                                    options.entity_tokens,
                                    seed_set,
                                    domain_profiles,
                                )
                                if reason:
                                    parent_href = getattr(item, "parent_anchor_href", "")
                                    LOGGER.debug(
                                        "Video rejected: %s (reason: %s, score: %d, source: %s, parent_href: %s)",
                                        item.url,
                                        reason,
                                        score,
                                        item.source_page,
                                        parent_href,
                                    )
                                    if add_rejected("video", item.url, item.source_page, reason, score):
                                        stats["rejected_count"] += 1
                                    continue

                                if max_results > 0 and len(result.videos) >= max_results:
                                    add_rejected("video", item.url, item.source_page, "max_results_limit", score)
                                    continue

                                seen_videos[norm_key] = item
                                result.videos.append(item)
                                stats["videos_kept"] += 1

                        if max_results > 0 and _is_target_met(result, options, max_results):
                            LOGGER.info(
                                "Target media limits met early (%d images, %d videos). Cancelling remaining page fetches.",
                                len(result.images),
                                len(result.videos),
                            )
                            # Empty the remaining pages iterator so no more get submitted
                            pages_iter = iter([])
                            for f in list(futures.keys()):
                                if not f.done():
                                    f.cancel()
                            pbar.update(pbar.total - pbar.n)
                            break
                        
                        pbar.update(1)

                    # Submit next pages to maintain target concurrency
                    while len(futures) < current_concurrency:
                        if not submit_next():
                            break

        extra_videos = self.video_scraper.search(
            keyword,
            max_results,
            allow_domains=options.allow_domains,
            block_domains=options.block_domains,
        )

        # Process extra videos with same upgrade logic
        for item in extra_videos:
            item.url = normalize_url(item.url)
            norm_key = normalize_media_url(item.url)
            if norm_key in seen_videos:
                existing = seen_videos[norm_key]
                if "?" in item.url and "?" not in existing.url:
                    LOGGER.debug(
                        "Video URL upgraded from tokenless to tokened: %s -> %s",
                        existing.url,
                        item.url,
                    )
                    existing.url = item.url
                else:
                    add_rejected("video", item.url, item.source_page, "duplicate")
                continue
            score = score_video_relevance(
                item, options.keyword, options.entity_tokens, seed_set, domain_profiles
            )
            item.score = score
            reason = rejection_reason_for_video(
                item, options.keyword, options.entity_tokens, seed_set, domain_profiles
            )
            if reason:
                add_rejected("video", item.url, item.source_page, reason, score)
                continue
            if max_results > 0 and len(result.videos) >= max_results:
                add_rejected("video", item.url, item.source_page, "max_results_limit", score)
                continue
            seen_videos[norm_key] = item
            result.videos.append(item)

        # --- Deferred download phase ---
        # All crawl pages have been processed; URL upgrades (tokenless → tokened) are
        # complete, so downloads now use the best available URL for each asset.
        if options.download_media:
            import concurrent.futures as _cf
            from config import (
                DEFAULT_RUNS_SUBDIR,
                DEFAULT_DOWNLOAD_IMAGES_SUBDIR,
                DEFAULT_DOWNLOAD_VIDEOS_SUBDIR,
                CONCURRENT_DOWNLOADS,
            )

            output_root = (
                options.output_dir
                / result.keyword_slug
                / DEFAULT_RUNS_SUBDIR
                / result.run_id
            )
            image_dir = output_root / DEFAULT_DOWNLOAD_IMAGES_SUBDIR
            video_dir = output_root / DEFAULT_DOWNLOAD_VIDEOS_SUBDIR
            image_dir.mkdir(parents=True, exist_ok=True)
            video_dir.mkdir(parents=True, exist_ok=True)

            def get_domain_slug(url: str) -> str:
                parsed = urlparse(url)
                netloc = parsed.netloc.lower()
                if ":" in netloc:
                    netloc = netloc.split(":")[0]
                return netloc

            # Group image items by domain
            images_by_domain: dict[str, list[ImageItem]] = {}
            for item in result.images:
                domain = get_domain_slug(item.source_page)
                images_by_domain.setdefault(domain, []).append(item)

            # Group video items by domain
            videos_by_domain: dict[str, list[VideoItem]] = {}
            for item in result.videos:
                if item.type in {"direct", "hls", "dash"}:
                    domain = get_domain_slug(item.source_page)
                    videos_by_domain.setdefault(domain, []).append(item)

            image_tasks = []
            for domain, items in images_by_domain.items():
                domain_dir = image_dir / domain
                domain_dir.mkdir(parents=True, exist_ok=True)
                domain_prefix = domain.replace(".", "_")
                for idx, item in enumerate(items, start=1):
                    stem_suffix = re.sub(
                        r"[^a-zA-Z0-9]+",
                        "_",
                        (item.alt_text or item.page_title or "image").strip().lower(),
                    ).strip("_")
                    stem_suffix = stem_suffix[:40] if stem_suffix else "asset"
                    stem = f"{domain_prefix}_{idx:03d}_{stem_suffix}"
                    image_tasks.append((item, domain_dir, stem, "image"))

            video_tasks = []
            for domain, items in videos_by_domain.items():
                domain_dir = video_dir / domain
                domain_dir.mkdir(parents=True, exist_ok=True)
                domain_prefix = domain.replace(".", "_")
                for idx, item in enumerate(items, start=1):
                    stem_suffix = re.sub(
                        r"[^a-zA-Z0-9]+",
                        "_",
                        (item.page_title or item.type).strip().lower(),
                    ).strip("_")
                    stem_suffix = stem_suffix[:40] if stem_suffix else "asset"
                    stem = f"{domain_prefix}_{idx:03d}_{stem_suffix}"
                    video_tasks.append((item, domain_dir, stem, "video"))

            all_dl_tasks = image_tasks + video_tasks
            if all_dl_tasks:
                LOGGER.info(
                    "Downloading %d images and %d videos...",
                    len(image_tasks),
                    len(video_tasks),
                )

                # Initialize non-downloadable videos status
                downloaded_video_urls = {item.url for item, _, _, _ in video_tasks}
                for item in result.videos:
                    if item.url not in downloaded_video_urls:
                        item.status = "skipped"
                        item.failure_reason = "non_downloadable_type"

                with _cf.ThreadPoolExecutor(
                    max_workers=CONCURRENT_DOWNLOADS, thread_name_prefix="dl"
                ) as dl_executor:
                    dl_futures = {}
                    for item, directory, stem, media_kind in all_dl_tasks:
                        dl_host = urlparse(item.source_page).netloc.lower()
                        profile = options.domain_profiles.get(dl_host) if options.domain_profiles else None
                        min_size = getattr(profile, "min_image_size", None) if profile else None
                        thumb_pattern = getattr(profile, "thumbnail_prefix_pattern", None) if profile else None
                        needs_referer = getattr(profile, "requires_referer", False) if profile else False
                        referer = item.source_page if needs_referer else None

                        fut = dl_executor.submit(
                            self.downloader._download_file,
                            item.url,
                            directory,
                            stem,
                            media_kind,
                            referer,
                            min_size,
                            thumb_pattern,
                        )
                        dl_futures[fut] = (item, media_kind)
                    for fut in _cf.as_completed(dl_futures):
                        item, media_kind = dl_futures[fut]
                        try:
                            success, download_info = fut.result()
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
                            else:
                                reason = download_info.get("reason", "unknown")
                                item.status = "skipped" if reason in {"low_resolution", "unparseable_dimensions", "duplicate", "invalid_media_type"} else "failed"
                                item.failure_reason = reason

                                add_rejected(
                                    media_kind,
                                    item.url,
                                    item.source_page,
                                    f"download_{reason}",
                                    item.score,
                                )
                                dl_host = urlparse(item.source_page).netloc.lower()
                                if dl_host in result.domain_stats:
                                    result.domain_stats[dl_host]["rejected_count"] += 1
                                    if media_kind == "image":
                                        result.domain_stats[dl_host]["images_kept"] = max(0, result.domain_stats[dl_host]["images_kept"] - 1)
                                    else:
                                        result.domain_stats[dl_host]["videos_kept"] = max(0, result.domain_stats[dl_host]["videos_kept"] - 1)
                        except Exception as exc:
                            LOGGER.warning("Download error for %s: %s", item.url, exc)
                            item.status = "failed"
                            item.failure_reason = f"exception_{type(exc).__name__}"

                            add_rejected(
                                media_kind,
                                item.url,
                                item.source_page,
                                f"download_failed:{type(exc).__name__}",
                                item.score,
                            )
                            dl_host = urlparse(item.source_page).netloc.lower()
                            if dl_host in result.domain_stats:
                                result.domain_stats[dl_host]["rejected_count"] += 1
                                if media_kind == "image":
                                    result.domain_stats[dl_host]["images_kept"] = max(0, result.domain_stats[dl_host]["images_kept"] - 1)
                                else:
                                    result.domain_stats[dl_host]["videos_kept"] = max(0, result.domain_stats[dl_host]["videos_kept"] - 1)

                LOGGER.info("Download phase complete.")

        # Sort the final lists of kept items by score for output consistency
        result.images.sort(
            key=lambda item: (
                item.score,
                contains_subject_text(
                    " ".join(
                        [item.url, item.source_page, item.alt_text, item.page_title]
                    ).lower(),
                    options.keyword,
                    options.entity_tokens,
                ),
            ),
            reverse=True,
        )
        result.videos.sort(
            key=lambda item: (
                item.score,
                contains_subject_text(
                    " ".join([item.url, item.source_page, item.page_title]).lower(),
                    options.keyword,
                    options.entity_tokens,
                ),
            ),
            reverse=True,
        )

        LOGGER.info(
            "Collected %s images and %s videos for '%s'",
            len(result.images),
            len(result.videos),
            keyword,
        )
        return result

    @staticmethod
    def _is_detail_page(
        link: str,
        seed_page: str,
        keyword_or_entity: str | list[str] | None = None,
        entity_tokens: list[str] | None = None,
    ) -> bool:
        """
        Return True if *link* is a concrete detail page relative to *seed_page*.

        A detail page must:
        - NOT be the seed page itself.
        - NOT be a pagination URL (/page/, ?page=, ?p=).
        - NOT be an anchor-only variant of the same page.
        - NOT be a listing/category/tag page of a DIFFERENT subject.
        """
        seed_parsed = urlparse(seed_page)
        seed_path = seed_parsed.path.rstrip("/") or "/"
        link_parsed = urlparse(link)
        link_path = link_parsed.path.rstrip("/") or "/"
        link_query = link_parsed.query.lower()

        # Reject same page
        if link_path == seed_path:
            return False

        # Reject pagination patterns
        pagination_path = {"/page/", "/p/", "/pg/"}
        if any(p in link_path for p in pagination_path):
            return False
        if re.search(r"(?:^|&)(?:page|p|pg)=\d", link_query):
            return False

        if isinstance(keyword_or_entity, list):
            entity_tokens = keyword_or_entity
            keyword = ""
        else:
            keyword = keyword_or_entity or ""

        # Collect all tokens to check relevance
        all_tokens = [keyword.lower()] if keyword else []
        if entity_tokens:
            for token in entity_tokens:
                t = token.lower().strip()
                if t and t not in all_tokens:
                    all_tokens.append(t)

        # If seed path is NOT specific (e.g. root index, query search, or archive list),
        # enforce that detail page links must contain keyword or entity tokens.
        is_seed_specific = seed_path not in {
            "",
            "/",
            "/index.html",
            "/index.php",
        } and not ("search" in seed_path or "archive" in seed_path or "?" in seed_page)

        if not is_seed_specific:
            normalized_link_path = link_path.lower()
            if all_tokens and not any(
                token in normalized_link_path for token in all_tokens
            ):
                return False
        else:
            # If seed path is specific, the link must be a subpath or contain an entity token
            if entity_tokens:
                normalized_seed_path = seed_path.lower()
                normalized_link_path = link_path.lower()
                if not normalized_link_path.startswith(normalized_seed_path + "/"):
                    if not any(
                        token in normalized_link_path for token in entity_tokens
                    ):
                        return False

        # Reject common static nav/info paths
        nav_paths = {
            "",
            "/",
            "/about",
            "/contact",
            "/dmca",
            "/privacy",
            "/terms",
            "/login",
            "/register",
            "/logout",
            "/faq",
            "/support",
            "/help",
        }
        if link_path in nav_paths or link_path.rstrip("/") in nav_paths:
            return False

        # Check listing/index prefixes. If the seed path contains a listing prefix
        # (e.g. /category/, /tag/, /model/, /actor/, /videos/), and the link path also
        # contains a listing prefix, then the link path must contain the subject name/token
        # to be considered relevant (otherwise it's a listing page for another model/tag).
        listing_prefixes = [
            "/category/",
            "/tag/",
            "/model/",
            "/actor/",
            "/videos/",
            "/search/",
            "/tags/",
            "/models/",
            "/actors/",
        ]
        seed_listing = any(lp in seed_path for lp in listing_prefixes)
        link_listing = any(lp in link_path for lp in listing_prefixes)

        if link_listing:
            if entity_tokens and not any(
                token in link_path.lower() for token in entity_tokens
            ):
                return False

        if seed_listing:
            for prefix in listing_prefixes:
                if prefix in link_path:
                    suffix = link_path.split(prefix, 1)[1]
                    if entity_tokens and not any(
                        token in suffix.lower() for token in entity_tokens
                    ):
                        return False

        return True

    @staticmethod
    def _build_candidate_pages(
        search_pages: list[str], options: EngineOptions
    ) -> list[str]:
        ordered_pages: list[str] = []
        seen: set[str] = set()
        for page in [*options.seed_urls, *search_pages]:
            normalized = normalize_url(page)
            if normalized in seen:
                continue
            scope_reason = ScrapingEngine._scope_rejection_reason(normalized, options)
            if scope_reason:
                continue
            seen.add(normalized)
            ordered_pages.append(normalized)
        return ordered_pages

    @staticmethod
    def _scope_rejection_reason(url: str, options: EngineOptions) -> str | None:
        if not is_allowed_domain(url, options.allow_domains, options.block_domains):
            return "domain_policy"
        if not is_allowed_path(url):
            return "structural_path"
        host = urlparse(url).netloc.lower()
        path = urlparse(url).path or "/"
        if options.strict_domain and options.seed_domains:
            if host not in options.seed_domains and not any(
                host.endswith(f".{domain}") for domain in options.seed_domains
            ):
                return "strict_domain"
        if options.site_tree_only and options.seed_urls:
            if not any(
                host == urlparse(seed).netloc.lower()
                and path.startswith((urlparse(seed).path or "/").rstrip("/") or "/")
                for seed in options.seed_urls
            ):
                return "site_tree"
        return None

    @staticmethod
    def _finalize_images(
        result: ScrapeResult, options: EngineOptions
    ) -> list[ImageItem]:
        seed_set: set[str] = {normalize_url(u) for u in options.seed_urls}
        domain_profiles = options.domain_profiles or {}
        seen: set[str] = set()
        kept: list[ImageItem] = []
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
                parent_href = getattr(item, "parent_anchor_href", "")
                LOGGER.debug(
                    "Image rejected: %s (reason: %s, score: %d, source: %s, parent_href: %s)",
                    item.url,
                    reason,
                    score,
                    item.source_page,
                    parent_href,
                )
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
                    " ".join(
                        [item.url, item.source_page, item.alt_text, item.page_title]
                    ).lower(),
                    options.keyword,
                    options.entity_tokens,
                ),
            ),
            reverse=True,
        )
        return kept

    @staticmethod
    def _finalize_videos(
        result: ScrapeResult, options: EngineOptions
    ) -> list[VideoItem]:
        seed_set: set[str] = {normalize_url(u) for u in options.seed_urls}
        domain_profiles = options.domain_profiles or {}
        seen: set[str] = set()
        kept: list[VideoItem] = []
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
            reason = rejection_reason_for_video(
                item, options.keyword, options.entity_tokens, seed_set, domain_profiles
            )
            if reason:
                parent_href = getattr(item, "parent_anchor_href", "")
                LOGGER.debug(
                    "Video rejected: %s (reason: %s, score: %d, source: %s, parent_href: %s)",
                    item.url,
                    reason,
                    score,
                    item.source_page,
                    parent_href,
                )
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
                    " ".join([item.url, item.source_page, item.page_title]).lower(),
                    options.keyword,
                    options.entity_tokens,
                ),
            ),
            reverse=True,
        )
        return kept
