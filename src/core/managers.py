from __future__ import annotations
from typing import Any
import os
import re
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from urllib.parse import urlparse

from tqdm import tqdm

from core.models import (
    EngineOptions,
    ImageItem,
    PageReport,
    ScrapeResult,
    RejectedItem,
    VideoItem,
)
from core.engine import _video_resolution_hint
from monitoring.logger import get_logger
from core.filters import (
    normalize_url,
    score_image_relevance,
    rejection_reason_for_image,
    score_video_relevance,
    rejection_reason_for_video,
    contains_subject_text,
    looks_like_media,
    normalize_media_url,
    is_allowed_domain,
    is_allowed_path,
)
from scraper.specialized import SpecializedExtractor
import json

LOGGER = get_logger(__name__)


class DomainRulesManager:
    """Manages domain-specific routing rules, blocklists, and crawling scopes."""

    def __init__(self, config_path: str = "data/domain_config.json", profile_path: str = "src/config/subject_profiles.json"):
        self.config_path = config_path
        self.profile_path = profile_path
        self._lock = threading.RLock()
        self._config_mtime: float | None = None
        self._profile_mtime: float | None = None
        self._cached_config: dict = {}
        self._cached_profiles: dict = {}

    def _get_config(self) -> dict:
        with self._lock:
            try:
                current_mtime = os.path.getmtime(self.config_path)
                if self._config_mtime is None or current_mtime != self._config_mtime:
                    with open(self.config_path, "r", encoding="utf-8") as f:
                        self._cached_config = json.load(f)
                    self._config_mtime = current_mtime
            except Exception as e:
                if self._config_mtime is None:
                    LOGGER.warning(f"Failed to load domain config from {self.config_path}: {e}")
                    self._cached_config = {}
            return self._cached_config

    def _get_profiles(self) -> dict:
        with self._lock:
            try:
                current_mtime = os.path.getmtime(self.profile_path)
                if self._profile_mtime is None or current_mtime != self._profile_mtime:
                    with open(self.profile_path, "r", encoding="utf-8") as f:
                        self._cached_profiles = json.load(f)
                    self._profile_mtime = current_mtime
            except Exception as e:
                if self._profile_mtime is None:
                    LOGGER.warning(f"Failed to load subject profiles from {self.profile_path}: {e}")
                    self._cached_profiles = {}
            return self._cached_profiles

    def should_deep_scrape(self, domain: str) -> bool:
        cfg = self._get_config()
        return domain in cfg.get("deep_scrape", [])

    def handle_domain_links(self, soup, domain: str) -> list[str]:
        """Extract links matching the configured link_pattern for a domain."""
        cfg = self._get_config()
        handler = cfg.get("domain_handlers", {}).get(domain, {})
        pattern = handler.get("link_pattern", "/post/")
        try:
            return [a["href"] for a in soup.find_all("a", href=re.compile(pattern))]
        except Exception:
            return []

    def filter_domains_by_profile(self, domains: list[str], profile_name: str) -> list[str]:
        """Filter list of domains based on subject profile blocklists."""
        profiles = self._get_profiles()
        if profile_name not in profiles:
            return domains

        profile = profiles.get(profile_name, {})
        block = profile.get("block_image_only_domains", [])

        return [d for d in domains if not any(b in d for b in block)]

    def scope_rejection_reason(self, url: str, options: EngineOptions) -> str | None:
        """Determines if a URL is out of scope based on strict domain or site tree constraints."""
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
    def is_detail_page(
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



class MediaProcessor:
    """Handles filtering, deduplication, scoring, and deferred downloading of media."""

    def __init__(self, downloader):
        self.downloader = downloader

    def finalize_images(self, result, options) -> list:
        from core.filters import normalize_url
        from core.models import RejectedItem

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
        from core.filters import contains_subject_text, safe_join
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
        from core.filters import normalize_url
        from core.models import RejectedItem

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
        from core.filters import contains_subject_text, safe_join
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
            import json
            from monitoring.logger import get_logger
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

    def execute_deferred_downloads(self, result, options) -> None:
        import time
        import re
        import concurrent.futures as _cf
        from urllib.parse import urlparse
        from config import (
            DEFAULT_RUNS_SUBDIR,
            DEFAULT_DOWNLOAD_IMAGES_SUBDIR,
            DEFAULT_DOWNLOAD_VIDEOS_SUBDIR,
            CONCURRENT_DOWNLOADS,
        )
        from monitoring.logger import get_logger

        LOGGER = get_logger(__name__)

        _download_start_time = time.monotonic()
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

        # Load known dead URLs for this subject
        dead_urls_file = options.output_dir / result.keyword_slug / "dead_urls.json"
        if dead_urls_file.exists():
            try:
                import json
                with open(dead_urls_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        with self.downloader._dead_urls_lock:
                            self.downloader._dead_urls.update(loaded)
                LOGGER.info("Loaded %d known dead URLs from %s", len(self.downloader._dead_urls), dead_urls_file)
            except Exception as e:
                LOGGER.warning("Failed to load dead URLs from %s: %s", dead_urls_file, e)

        def get_domain_slug(url: str) -> str:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            if ":" in netloc:
                netloc = netloc.split(":")[0]
            return netloc

        # Group image items by domain
        images_by_domain = {}
        for item in result.images:
            domain = get_domain_slug(item.source_page)
            images_by_domain.setdefault(domain, []).append(item)

        # Group video items by domain
        videos_by_domain = {}
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

        # Pre-dedup: skip media items whose normalized URL is already queued
        from core.filters import normalize_url as _norm_dl_url
        _seen_download_urls: set[str] = set()
        deduped_dl_tasks = []
        for task in all_dl_tasks:
            item, directory, stem, media_kind = task
            norm = _norm_dl_url(item.url)
            if norm in _seen_download_urls:
                item.status = "skipped"
                item.failure_reason = "duplicate_url_precheck"
                result.download_stats["download_duplicate_url_precheck"] = (
                    result.download_stats.get("download_duplicate_url_precheck", 0) + 1
                )
                continue
            _seen_download_urls.add(norm)
            deduped_dl_tasks.append(task)
        if len(all_dl_tasks) != len(deduped_dl_tasks):
            LOGGER.info(
                "Pre-dedup removed %d duplicate download URLs.",
                len(all_dl_tasks) - len(deduped_dl_tasks),
            )
        all_dl_tasks = deduped_dl_tasks

        if not all_dl_tasks:
            result.run_metadata["download_duration_seconds"] = 0.0
            self._save_dead_urls(result, options, output_root)
            return

        LOGGER.info(
            "Downloading %d images and %d videos...",
            len(image_tasks),
            len(video_tasks),
        )

        downloaded_video_urls = {item.url for item, _, _, _ in video_tasks}
        for item in result.videos:
            if item.url not in downloaded_video_urls:
                item.status = "skipped"
                item.failure_reason = "non_downloadable_type"

        _cdn_hosts = []
        if options.seed_manifest is not None:
            _cdn_hosts.extend(getattr(options.seed_manifest, "all_allowed_hosts", []))
        elif options.domain_profiles:
            for _dp in options.domain_profiles.values():
                _cdn_hosts.extend(getattr(_dp, "cdn_hosts", []))
                
        _seen_cdn = set()
        _cdn_hosts_deduped = []
        for _h in _cdn_hosts:
            if _h not in _seen_cdn:
                _seen_cdn.add(_h)
                _cdn_hosts_deduped.append(_h)

        def add_rejected(kind, url, source_page, reason, score):
            from core.models import RejectedItem
            result.rejected_items.append(
                RejectedItem(
                    kind=kind, url=url, source_page=source_page, reason=reason, score=score
                )
            )

        completed_dl_count = 0
        import gc

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
                    _cdn_hosts_deduped,
                )
                dl_futures[fut] = (item, media_kind)
                
            for fut in _cf.as_completed(dl_futures):
                completed_dl_count += 1
                if completed_dl_count % 250 == 0:
                    gc.collect()
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
                        result.download_stats["downloaded"] = result.download_stats.get("downloaded", 0) + 1
                    else:
                        reason = download_info.get("reason", "unknown")
                        item.status = (
                            "skipped"
                            if reason in {"low_resolution", "unparseable_dimensions", "duplicate", "invalid_media_type"}
                            else "failed"
                        )
                        item.failure_reason = reason
                        key = f"download_{reason}"
                        result.download_stats[key] = result.download_stats.get(key, 0) + 1
                        add_rejected(media_kind, item.url, item.source_page, f"download_{reason}", item.score)
                        
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
                    add_rejected(media_kind, item.url, item.source_page, f"download_failed:{type(exc).__name__}", item.score)
                    
                    dl_host = urlparse(item.source_page).netloc.lower()
                    if dl_host in result.domain_stats:
                        result.domain_stats[dl_host]["rejected_count"] += 1
                        if media_kind == "image":
                            result.domain_stats[dl_host]["images_kept"] = max(0, result.domain_stats[dl_host]["images_kept"] - 1)
                        else:
                            result.domain_stats[dl_host]["videos_kept"] = max(0, result.domain_stats[dl_host]["videos_kept"] - 1)

        LOGGER.info("Download phase complete.")
        download_duration = time.monotonic() - _download_start_time
        result.run_metadata["download_duration_seconds"] = download_duration

        self._save_dead_urls(result, options, output_root)


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
    ) -> ScrapeResult:
        from core.engine import _is_target_met
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
        failed_run_hosts: set[str] = set()
        consecutive_host_failures: dict[str, int] = {}

        def add_rejected(
            kind: str, url: str, source_page: str, reason: str, score: int = 0
        ) -> bool:
            norm_url = normalize_url(url)
            key = (norm_url, reason)
            with result_lock:
                if key in seen_rejected_urls:
                    return False
                seen_rejected_urls.add(key)
                result.rejected_items.append(
                    RejectedItem(
                        kind=kind,
                        url=norm_url,
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
                if self.state_cache and self.state_cache.is_processed(normalized_page):
                    LOGGER.debug(f"Skipping already processed page: {normalized_page}")
                    continue
                visited_pages.add(normalized_page)
                ordered_pages.append((normalized_page, current_depth))

                try:
                    from monitoring.telemetry import broadcast_telemetry_event
                    broadcast_telemetry_event("crawl_graph_node", {
                        "url": normalized_page,
                        "domain": host,
                        "depth": current_depth,
                        "type": "page_visited",
                    })
                except Exception:
                    pass

                profile = options.domain_profiles.get(host)
                if profile and profile.crawl_depth is not None:
                    domain_depth_limit = profile.crawl_depth
                else:
                    domain_depth_limit = resolved_crawl_depth
                
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
                            if self.rules_manager.is_detail_page(
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
                    scope_reason = self.rules_manager.scope_rejection_reason(
                        normalized_link, options
                    )
                    if scope_reason:
                        add_rejected(
                            "page", normalized_link, normalized_page, scope_reason
                        )
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

                    try:
                        from monitoring.telemetry import broadcast_telemetry_event
                        broadcast_telemetry_event("crawl_graph_node", {
                            "url": normalized_link,
                            "domain": link_host,
                            "parent": normalized_page,
                            "depth": current_depth + 1,
                            "type": "link_discovered",
                        })
                    except Exception:
                        pass

        pages_to_fetch = (
            ordered_pages
            if resolved_page_limit == float("inf")
            else ordered_pages[: int(resolved_page_limit)]
        )

        from core.coordinator import CrawlCoordinator
        coordinator = CrawlCoordinator(
            search_provider=self.search_provider,
            video_scraper=self.video_scraper,
            options=options,
            result=result,
            state_cache=self.state_cache,
            workers=self.workers
        )
        
        # We need to pass the method add_rejected if it is required by the original execute_crawl
        # Wait, the add_rejected in CrawlCoordinator replaces the old one. We don't need to pass the old one.
        result = coordinator.execute(pages_to_fetch, discovered_links_counts)
        
        # Sort the final lists of kept items by score for output consistency (as was done in the original)
        from core.filters import contains_subject_text, safe_join
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


