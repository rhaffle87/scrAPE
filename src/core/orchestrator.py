from __future__ import annotations
from typing import Any
import time
from urllib.parse import urlparse

from monitoring.logger import get_logger

from core.models import (
    EngineOptions,
    ScrapeResult,
)
from core.domain_rules import DomainRulesManager
from core.filters import (
    normalize_url,
    contains_subject_text,
    looks_like_media,
    safe_join,
)

LOGGER = get_logger(__name__)


class CrawlOrchestrator:
    """Coordinates the concurrent breadth-first search and page crawling."""

    def __init__(
        self,
        search_provider,
        video_scraper,
        state_cache,
        workers: int,
        rules_manager: DomainRulesManager,
    ):
        self.search_provider = search_provider
        self.video_scraper = video_scraper
        self.state_cache = state_cache
        self.workers = workers
        self.rules_manager = rules_manager
        self.media_processor: Any = None

    def _build_candidate_pages(
        self,
        search_pages: list[str], options: EngineOptions
    ) -> list[str]:
        ordered_pages: list[str] = []
        seen: set[str] = set()
        for page in [*options.seed_urls, *search_pages]:
            normalized = normalize_url(page)
            if normalized in seen:
                continue
            scope_reason = self.rules_manager.scope_rejection_reason(normalized, options)
            if scope_reason:
                continue
            seen.add(normalized)
            ordered_pages.append(normalized)
        return ordered_pages



    def execute_crawl(
        self,
        keyword: str,
        options: EngineOptions,
        result: ScrapeResult,
        page_limit: int = 20,
        crawl_depth: int = 2,
        media_processor=None,
        task_state: dict | None = None,
    ) -> ScrapeResult:
        from core.filters import (
            normalize_url,
        )
        max_results = options.max_results
        _crawl_start_time = time.monotonic()

        # Fix 3: Register Cloudflare-blocked domains early so the HttpClient
        # skips all browser fallback tiers immediately for protected domains.
        # This prevents ~30s timeouts per page when Turnstile is active.
        from network.http_client import HttpClient

        if options.domain_profiles:
            for _domain, _profile in options.domain_profiles.items():
                if getattr(_profile, "cloudflare_blocked", False):
                    HttpClient.register_cloudflare_blocked(_domain)
                    LOGGER.info(
                        "Registered Cloudflare-blocked domain at startup: %s", _domain
                    )

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

        from core.coordinator import CrawlCoordinator
        coordinator = CrawlCoordinator(
            search_provider=self.search_provider,
            video_scraper=self.video_scraper,
            options=options,
            result=result,
            state_cache=self.state_cache,
            workers=self.workers,
            rules_manager=self.rules_manager,
            page_limit=resolved_page_limit,
            crawl_depth=resolved_crawl_depth,
            media_processor=media_processor or self.media_processor,
            task_state=task_state,
        )
        
        # We start coordinator with candidate pages at depth 0
        ordered_pages = [(normalize_url(p), 0) for p in candidate_pages if p and not looks_like_media(normalize_url(p))]
        
        result = coordinator.execute(ordered_pages)
        
        # Sort the final lists of kept items by score for output consistency (as was done in the original)
        result.images.sort(
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
        result.videos.sort(
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

        LOGGER.info(
            "Collected %s images and %s videos for '%s'",
            len(result.images),
            len(result.videos),
            keyword,
        )
        result.run_metadata["crawl_duration_seconds"] = time.monotonic() - _crawl_start_time
        return result


