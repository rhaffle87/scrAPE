from __future__ import annotations

import re
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse


from tqdm import tqdm

from config import (
    CONCURRENT_PAGES_PER_BATCH,
    DEFAULT_RUNS_SUBDIR,
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
from core.models import EngineOptions, ImageItem, PageReport, RejectedItem, ScrapeResult, VideoItem
from scraper.google_images import SearchProviderScraper
from scraper.video_scraper import VideoScraper
from storage.file_downloader import MediaDownloader
from utils.logger import get_logger

LOGGER = get_logger(__name__)


class ScrapingEngine:
    def __init__(
        self,
        domain_delays: dict[str, float] | None = None,
        workers: int = CONCURRENT_PAGES_PER_BATCH,
    ) -> None:
        self.workers = max(1, workers)
        self.search_provider = SearchProviderScraper(domain_delays=domain_delays)
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
            seed_manifest=seed_manifest,
            domain_profiles=domain_profiles or {},
        )
        result = ScrapeResult(keyword=keyword)
        if run_id:
            result.run_id = run_id

        if options.seed_urls:
            derived_domains = [urlparse(url).netloc.lower() for url in options.seed_urls if urlparse(url).netloc]
            options.seed_domains = list(dict.fromkeys([*options.seed_domains, *derived_domains]))
        if options.strict_domain and options.seed_domains:
            options.allow_domains = list(dict.fromkeys([*options.allow_domains, *options.seed_domains]))

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
        queued_pages: set[str] = {normalize_url(page) for page in candidate_pages if page and not looks_like_media(normalize_url(page))}
        visited_pages: set[str] = set()
        ordered_pages: list[tuple[str, int]] = []
        discovered_links_counts: dict[str, int] = {}

        # Enqueue candidate pages at depth 0
        for page in candidate_pages:
            if not page or looks_like_media(normalize_url(page)):
                continue
            host = urlparse(page).netloc.lower()
            queues.setdefault(0, {}).setdefault(host, deque()).append(page)

        while len(ordered_pages) < resolved_page_limit:
            # Find the minimum depth that still has pages to crawl
            active_depths = [d for d, depth_queues in queues.items() if any(depth_queues.values())]
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
                if profile and (profile.crawl_strategy == "direct" or getattr(profile, "skip_link_discovery", False)):
                    discovered_links = []
                    discovered_links_counts[normalized_page] = 0
                else:
                    discovered_links = self.search_provider.discover_links(
                        normalized_page,
                        allow_domains=options.allow_domains,
                        block_domains=options.block_domains,
                        keyword=options.keyword if current_depth > 0 else None,
                        entity_tokens=options.entity_tokens if current_depth > 0 else None,
                    )
                    # 'index→detail': at depth 0 only follow concrete detail links
                    # (deeper path than the seed URL, not pagination siblings)
                    if profile and profile.crawl_strategy != "direct" and current_depth == 0:
                        seed_for_host = next(
                            (s for s in options.seed_urls if urlparse(s).netloc.lower() == host),
                            normalized_page,
                        )
                        discovered_links = [
                            lnk for lnk in discovered_links
                            if self._is_detail_page(lnk, seed_for_host, options.entity_tokens)
                        ]
                    discovered_links_counts[normalized_page] = len(discovered_links)

                for link in discovered_links:
                    normalized_link = normalize_url(link)
                    if looks_like_media(normalized_link):
                        continue
                    scope_reason = self._scope_rejection_reason(normalized_link, options)
                    if scope_reason:
                        result.rejected_items.append(
                            RejectedItem(
                                kind="page",
                                url=normalized_link,
                                source_page=normalized_page,
                                reason=scope_reason,
                            )
                        )
                        continue
                    if normalized_link in visited_pages or normalized_link in queued_pages:
                        continue
                    queued_pages.add(normalized_link)
                    
                    # Enqueue link at depth + 1 under its own host
                    link_host = urlparse(normalized_link).netloc.lower()
                    queues.setdefault(current_depth + 1, {}).setdefault(link_host, deque()).append(normalized_link)

        pages_to_fetch = ordered_pages if resolved_page_limit == float("inf") else ordered_pages[: int(resolved_page_limit)]

        # --- Concurrent page fetching ---
        # The per-domain RateLimiter is thread-safe, so workers hitting different
        # domains proceed in parallel while same-domain calls are naturally queued.
        result_lock = threading.Lock()

        # Deduplication maps: norm_key → item (allows URL upgrading from tokenless → tokened)
        seen_images: dict[str, object] = {}
        seen_videos: dict[str, object] = {}
        seed_set = {normalize_url(u) for u in options.seed_urls}
        domain_profiles = options.domain_profiles or {}

        def _fetch_page(page: str, depth: int):
            page_images, page_videos, scrape_status = self.search_provider.scrape_page(
                page,
                allow_domains=options.allow_domains,
                block_domains=options.block_domains,
            )
            return page, depth, page_images, page_videos, scrape_status

        with tqdm(total=len(pages_to_fetch), desc="Fetching pages", unit="page") as pbar:
            with ThreadPoolExecutor(max_workers=self.workers, thread_name_prefix="scraper") as executor:
                futures = {
                    executor.submit(_fetch_page, page, depth): (page, depth)
                    for page, depth in pages_to_fetch
                }
                for future in as_completed(futures):
                    try:
                        page, depth, page_images, page_videos, scrape_status = future.result()
                    except Exception as exc:
                        page, depth = futures[future]
                        LOGGER.warning("Worker failed for %s: %s", page, exc)
                        page_images, page_videos, scrape_status = [], [], f"worker_error:{type(exc).__name__}"
                    with result_lock:
                        result.scanned_pages.append(page)
                        result.page_reports.append(
                            PageReport(
                                url=page,
                                depth=depth,
                                status="success" if scrape_status == "ok" else "skipped",
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
                                # Upgrade: if new URL has query params (auth token) but stored one doesn't
                                if "?" in item.url and "?" not in existing.url:
                                    LOGGER.debug(
                                        "Image URL upgraded from tokenless to tokened: %s -> %s",
                                        existing.url, item.url,
                                    )
                                    existing.url = item.url
                                else:
                                    result.rejected_items.append(RejectedItem("image", item.url, item.source_page, "duplicate"))
                                continue
                            score = score_image_relevance(item, options.keyword, options.entity_tokens, seed_set, domain_profiles)
                            item.score = score
                            reason = rejection_reason_for_image(item, options.keyword, options.entity_tokens, seed_set, domain_profiles)
                            if reason:
                                parent_href = getattr(item, "parent_anchor_href", "")
                                LOGGER.debug("Image rejected: %s (reason: %s, score: %d, source: %s, parent_href: %s)", item.url, reason, score, item.source_page, parent_href)
                                result.rejected_items.append(RejectedItem("image", item.url, item.source_page, reason, score))
                                continue

                            # Max results check
                            if max_results > 0 and len(result.images) >= max_results:
                                result.rejected_items.append(RejectedItem("image", item.url, item.source_page, "max_results_limit", score))
                                continue

                            seen_images[norm_key] = item
                            result.images.append(item)

                        # Filtering and deduplication of page_videos
                        for item in page_videos:
                            item.url = normalize_url(item.url)
                            norm_key = normalize_media_url(item.url)
                            if norm_key in seen_videos:
                                existing = seen_videos[norm_key]
                                # Upgrade: if new URL has query params (auth token) but stored one doesn't
                                if "?" in item.url and "?" not in existing.url:
                                    LOGGER.debug(
                                        "Video URL upgraded from tokenless to tokened: %s -> %s",
                                        existing.url, item.url,
                                    )
                                    existing.url = item.url
                                else:
                                    result.rejected_items.append(RejectedItem("video", item.url, item.source_page, "duplicate"))
                                continue
                            score = score_video_relevance(item, options.keyword, options.entity_tokens, seed_set, domain_profiles)
                            item.score = score
                            reason = rejection_reason_for_video(item, options.keyword, options.entity_tokens, seed_set, domain_profiles)
                            if reason:
                                parent_href = getattr(item, "parent_anchor_href", "")
                                LOGGER.debug("Video rejected: %s (reason: %s, score: %d, source: %s, parent_href: %s)", item.url, reason, score, item.source_page, parent_href)
                                result.rejected_items.append(RejectedItem("video", item.url, item.source_page, reason, score))
                                continue

                            # Max results check
                            if max_results > 0 and len(result.videos) >= max_results:
                                result.rejected_items.append(RejectedItem("video", item.url, item.source_page, "max_results_limit", score))
                                continue

                            seen_videos[norm_key] = item
                            result.videos.append(item)
                    pbar.update(1)

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
                        existing.url, item.url,
                    )
                    existing.url = item.url
                else:
                    result.rejected_items.append(RejectedItem("video", item.url, item.source_page, "duplicate"))
                continue
            score = score_video_relevance(item, options.keyword, options.entity_tokens, seed_set, domain_profiles)
            item.score = score
            reason = rejection_reason_for_video(item, options.keyword, options.entity_tokens, seed_set, domain_profiles)
            if reason:
                result.rejected_items.append(RejectedItem("video", item.url, item.source_page, reason, score))
                continue
            if max_results > 0 and len(result.videos) >= max_results:
                result.rejected_items.append(RejectedItem("video", item.url, item.source_page, "max_results_limit", score))
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
            output_root = options.output_dir / result.keyword_slug / DEFAULT_RUNS_SUBDIR / result.run_id
            image_dir = output_root / DEFAULT_DOWNLOAD_IMAGES_SUBDIR
            video_dir = output_root / DEFAULT_DOWNLOAD_VIDEOS_SUBDIR
            image_dir.mkdir(parents=True, exist_ok=True)
            video_dir.mkdir(parents=True, exist_ok=True)

            image_tasks = [
                (item.url, image_dir, self.downloader._build_file_stem(idx, item.alt_text or item.page_title or "image"), "image", item.source_page)
                for idx, item in enumerate(result.images, start=1)
            ]
            video_tasks = [
                (item.url, video_dir, self.downloader._build_file_stem(idx, item.page_title or item.type), "video", item.source_page)
                for idx, item in enumerate(result.videos, start=1)
                if item.type in {"direct", "hls", "dash"}
            ]
            all_dl_tasks = image_tasks + video_tasks
            if all_dl_tasks:
                LOGGER.info("Downloading %d images and %d videos...", len(image_tasks), len(video_tasks))
                with _cf.ThreadPoolExecutor(max_workers=CONCURRENT_DOWNLOADS, thread_name_prefix="dl") as dl_executor:
                    dl_futures = {
                        dl_executor.submit(
                            self.downloader._download_file,
                            url, directory, stem, media_kind, source_page,
                        ): url
                        for url, directory, stem, media_kind, source_page in all_dl_tasks
                    }
                    for fut in _cf.as_completed(dl_futures):
                        try:
                            fut.result()
                        except Exception as exc:
                            LOGGER.warning("Download error for %s: %s", dl_futures[fut], exc)
                LOGGER.info("Download phase complete.")

        # Sort the final lists of kept items by score for output consistency
        result.images.sort(key=lambda item: (item.score, contains_subject_text(" ".join([item.url, item.source_page, item.alt_text, item.page_title]).lower(), options.keyword, options.entity_tokens)), reverse=True)
        result.videos.sort(key=lambda item: (item.score, contains_subject_text(" ".join([item.url, item.source_page, item.page_title]).lower(), options.keyword, options.entity_tokens)), reverse=True)

        LOGGER.info(
            "Collected %s images and %s videos for '%s'",
            len(result.images),
            len(result.videos),
            keyword,
        )
        return result

    @staticmethod
    def _is_detail_page(link: str, seed_page: str, entity_tokens: list[str] | None = None) -> bool:
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

        # If seed path is specific, the link must be a subpath or contain an entity token
        is_seed_specific = seed_path not in {"", "/", "/index.html", "/index.php"}
        if is_seed_specific and entity_tokens:
            normalized_seed_path = seed_path.lower()
            normalized_link_path = link_path.lower()
            if not normalized_link_path.startswith(normalized_seed_path + "/"):
                if not any(token in normalized_link_path for token in entity_tokens):
                    return False

        # Reject common static nav/info paths
        nav_paths = {
            "", "/", "/about", "/contact", "/dmca", "/privacy", "/terms",
            "/login", "/register", "/logout", "/faq", "/support", "/help"
        }
        if link_path in nav_paths or link_path.rstrip("/") in nav_paths:
            return False

        # Check listing/index prefixes. If the seed path contains a listing prefix
        # (e.g. /category/, /tag/, /model/, /actor/, /videos/), and the link path also
        # contains a listing prefix, then the link path must contain the subject name/token
        # to be considered relevant (otherwise it's a listing page for another model/tag).
        listing_prefixes = ["/category/", "/tag/", "/model/", "/actor/", "/videos/", "/search/", "/tags/", "/models/", "/actors/"]
        seed_listing = any(lp in seed_path for lp in listing_prefixes)
        link_listing = any(lp in link_path for lp in listing_prefixes)

        if link_listing:
            if entity_tokens and not any(token in link_path.lower() for token in entity_tokens):
                return False

        if seed_listing:
            for prefix in listing_prefixes:
                if prefix in link_path:
                    suffix = link_path.split(prefix, 1)[1]
                    if entity_tokens and not any(token in suffix.lower() for token in entity_tokens):
                        return False

        return True

    @staticmethod
    def _build_candidate_pages(search_pages: list[str], options: EngineOptions) -> list[str]:
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
            if host not in options.seed_domains and not any(host.endswith(f".{domain}") for domain in options.seed_domains):
                return "strict_domain"
        if options.site_tree_only and options.seed_urls:
            if not any(
                host == urlparse(seed).netloc.lower() and path.startswith((urlparse(seed).path or "/").rstrip("/") or "/")
                for seed in options.seed_urls
            ):
                return "site_tree"
        return None

    @staticmethod
    def _finalize_images(result: ScrapeResult, options: EngineOptions) -> list[ImageItem]:
        seed_set: set[str] = {normalize_url(u) for u in options.seed_urls}
        domain_profiles = options.domain_profiles or {}
        seen: set[str] = set()
        kept: list[ImageItem] = []
        for item in result.images:
            item.url = normalize_url(item.url)
            if item.url in seen:
                result.rejected_items.append(RejectedItem("image", item.url, item.source_page, "duplicate"))
                continue
            score = score_image_relevance(item, options.keyword, options.entity_tokens, seed_set, domain_profiles)
            item.score = score
            reason = rejection_reason_for_image(item, options.keyword, options.entity_tokens, seed_set, domain_profiles)
            if reason:
                parent_href = getattr(item, "parent_anchor_href", "")
                LOGGER.debug("Image rejected: %s (reason: %s, score: %d, source: %s, parent_href: %s)", item.url, reason, score, item.source_page, parent_href)
                result.rejected_items.append(RejectedItem("image", item.url, item.source_page, reason, score))
                continue
            seen.add(item.url)
            kept.append(item)
        kept.sort(key=lambda item: (item.score, contains_subject_text(" ".join([item.url, item.source_page, item.alt_text, item.page_title]).lower(), options.keyword, options.entity_tokens)), reverse=True)
        return kept

    @staticmethod
    def _finalize_videos(result: ScrapeResult, options: EngineOptions) -> list[VideoItem]:
        seed_set: set[str] = {normalize_url(u) for u in options.seed_urls}
        domain_profiles = options.domain_profiles or {}
        seen: set[str] = set()
        kept: list[VideoItem] = []
        for item in result.videos:
            item.url = normalize_url(item.url)
            if item.url in seen:
                result.rejected_items.append(RejectedItem("video", item.url, item.source_page, "duplicate"))
                continue
            score = score_video_relevance(item, options.keyword, options.entity_tokens, seed_set, domain_profiles)
            item.score = score
            reason = rejection_reason_for_video(item, options.keyword, options.entity_tokens, seed_set, domain_profiles)
            if reason:
                parent_href = getattr(item, "parent_anchor_href", "")
                LOGGER.debug("Video rejected: %s (reason: %s, score: %d, source: %s, parent_href: %s)", item.url, reason, score, item.source_page, parent_href)
                result.rejected_items.append(RejectedItem("video", item.url, item.source_page, reason, score))
                continue
            seen.add(item.url)
            kept.append(item)
        kept.sort(key=lambda item: (item.score, contains_subject_text(" ".join([item.url, item.source_page, item.page_title]).lower(), options.keyword, options.entity_tokens)), reverse=True)
        return kept