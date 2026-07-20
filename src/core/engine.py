from __future__ import annotations

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
from utils.logger import get_logger

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
        capsolver_key: str | None = None,
    ) -> None:
        self.workers = max(1, workers)
        self.domain_yield = {}

        self.search_provider = SearchProviderScraper(
            domain_delays=domain_delays, ignore_robots=ignore_robots, proxy=proxy, proxy_list=proxy_list, capsolver_key=capsolver_key
        )
        self.video_scraper = VideoScraper(domain_delays=domain_delays, proxy=proxy, proxy_list=proxy_list, capsolver_key=capsolver_key)
        # Share the scraper's HttpClient with the downloader for connection pool reuse
        self.downloader = MediaDownloader(http=self.search_provider.http)
        self.state_cache = StateCache() if use_state_cache else None

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
        import json

        with open("data/domain_config.json", "r") as f:
            cfg = json.load(f)
        return domain in cfg.get("deep_scrape", [])

    def handle_domain_links(self, soup, domain):
        """Extract links matching the configured link_pattern for a domain."""
        import json

        with open("data/domain_config.json", "r") as f:
            cfg = json.load(f)
        handler = cfg.get("domain_handlers", {}).get(domain, {})
        pattern = handler.get("link_pattern", "/post/")
        return [a["href"] for a in soup.find_all("a", href=re.compile(pattern))]

    def filter_domains_by_profile(self, domains, profile_name):
        """Filter list of domains based on subject profile."""
        try:
            import json

            profile_path = "src/config/subject_profiles.json"
            with open(profile_path, "r", encoding="utf-8") as f:
                profiles = json.load(f)

            if profile_name not in profiles:
                return domains

            profile = profiles[profile_name]
            block = profile.get("block_image_only_domains", [])

            filtered = [d for d in domains if not any(b in d for b in block)]
            return filtered
        except Exception:
            return domains

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
        seed_manifest: object | None = None,
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
            
        start_time = time.time()

        # Initialize domain rules manager
        from core.managers import DomainRulesManager, MediaProcessor, CrawlOrchestrator
        rules_manager = DomainRulesManager()

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
