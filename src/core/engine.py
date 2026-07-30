from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.seed_manifest import SeedManifest

import re
import time
from pathlib import Path


from config import (
    CONCURRENT_PAGES_PER_BATCH,
    OUTPUT_DIR,
)
from core.models import (
    EngineOptions,
    ScrapeResult,
)
from scraper.google_images import SearchProviderScraper
from scraper.video_scraper import VideoScraper
from storage.file_downloader import MediaDownloader
from storage.state_cache import StateCache
from monitoring.logger import get_logger

LOGGER = get_logger(__name__)


def _is_target_met(
    result: ScrapeResult, options: EngineOptions, max_results: int
) -> bool:
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
        use_state_cache: bool = False,
        proxy: str | None = None,
        proxy_list: str | None = None,
        captcha_provider: str | None = None,
        captcha_key: str | None = None,
        max_captcha_spend: float | None = None,
        dl_speed_limit_kbps: int = 0,
        global_rate_limit_rps: float = 0.0,
    ) -> None:
        self.workers = max(1, workers)
        self.domain_yield = {}

        self.search_provider = SearchProviderScraper(
            domain_delays=domain_delays,
            ignore_robots=ignore_robots,
            proxy=proxy,
            proxy_list=proxy_list,
            captcha_provider=captcha_provider,
            captcha_key=captcha_key,
            max_captcha_spend=max_captcha_spend,
        )
        if global_rate_limit_rps > 0.0:
            self.search_provider.http.global_rate_limit_rps = global_rate_limit_rps

        self.video_scraper = VideoScraper(domain_delays=domain_delays, proxy=proxy, proxy_list=proxy_list, captcha_provider=captcha_provider, captcha_key=captcha_key, max_captcha_spend=max_captcha_spend)
        # Share the scraper's HttpClient with the downloader for connection pool reuse
        self.downloader = MediaDownloader(http=self.search_provider.http, speed_limit_kbps=dl_speed_limit_kbps)
        self.state_cache = StateCache() if use_state_cache else None

        from core.managers import DomainRulesManager
        self.rules_manager = DomainRulesManager()

    def track_domain_yield(self, domain, kept_delta, pages_delta):
        stats = self.domain_yield.get(domain, [0, 0])
        stats[0] += kept_delta
        stats[1] += pages_delta
        self.domain_yield[domain] = stats

        # Throttling logic
        if stats[1] > 20 and (stats[0] / stats[1]) < 0.02:
            LOGGER.warning(
                f"Deprioritizing low-yield domain: {domain} ({stats[0] / stats[1]:.1%})"
            )
            # This is a passive deprioritization signal
            self.domain_yield[domain] = [-1000, 0]

    def should_deep_scrape(self, domain: str) -> bool:
        return self.rules_manager.should_deep_scrape(domain)

    def handle_domain_links(self, soup, domain):
        """Extract links matching the configured link_pattern for a domain."""
        return self.rules_manager.handle_domain_links(soup, domain)

    def filter_domains_by_profile(self, domains, profile_name):
        """Filter list of domains based on subject profile."""
        return self.rules_manager.filter_domains_by_profile(domains, profile_name)

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
        page_limit: int = 20,
        crawl_depth: int = 2,
        strict_domain: bool = False,
        site_tree_only: bool = False,
        seed_manifest: SeedManifest | None = None,
        domain_profiles: dict | None = None,
        run_id: str | None = None,
        ignore_robots: bool = False,
    ):
        run_output_dir = Path(OUTPUT_DIR)

        options = EngineOptions(
            keyword=keyword,
            max_results=max_results,
            output_format=output_format,
            download_media=download_media,
            output_dir=run_output_dir,
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
            ignore_robots=ignore_robots,
        )

        result = ScrapeResult(keyword=keyword)
        if run_id:
            result.run_id = run_id

        # Wire persistent pHash state into downloader for cross-run deduplication
        if self.state_cache is not None and (
            self.downloader._state_cache is None
            or self.downloader._keyword != keyword.strip().lower()
        ):
            self.downloader._state_cache = self.state_cache
            self.downloader._keyword = keyword.strip().lower()
            try:
                persisted = self.state_cache.load_phashes(subject=self.downloader._keyword)
                if persisted:
                    with self.downloader._hash_lock:
                        self.downloader._seen_phashes.update(persisted)
                    LOGGER.info(
                        "ScrapingEngine: seeded %d pHashes from StateCache for keyword '%s'.",
                        len(persisted),
                        keyword,
                    )
            except Exception as exc:
                LOGGER.warning("ScrapingEngine: failed to seed pHashes: %s", exc)

        start_time = time.time()

        # Initialize domain rules manager & media processor
        from core.managers import MediaProcessor, CrawlOrchestrator
        rules_manager = self.rules_manager

        media_processor = MediaProcessor(
            downloader=self.downloader,
        )

        # Initialize orchestrator
        orchestrator = CrawlOrchestrator(
            search_provider=self.search_provider,
            video_scraper=self.video_scraper,
            state_cache=self.state_cache,
            workers=self.workers,
            rules_manager=rules_manager,
        )
        orchestrator.media_processor = media_processor

        # Execute crawl
        orchestrator.execute_crawl(
            keyword=keyword,
            options=options,
            result=result,
            page_limit=page_limit,
            crawl_depth=crawl_depth,
        )

        result.images = media_processor.finalize_images(result, options)
        result.videos = media_processor.finalize_videos(result, options)

        # Download media
        if options.download_media:
            media_processor.execute_deferred_downloads(result, options)

        end_time = time.time()
        result.run_metadata["total_duration_seconds"] = (
            end_time - start_time
        )
        result.duration_seconds = int(end_time - start_time)
        return result
