from __future__ import annotations
import re
import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from urllib.parse import urlparse

from tqdm import tqdm

from core.models import (
    EngineOptions,
    PageReport,
    ScrapeResult,
    RejectedItem,
)
from core.engine import _video_resolution_hint
from utils.logger import get_logger
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

    def should_deep_scrape(self, domain: str) -> bool:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            return domain in cfg.get("deep_scrape", [])
        except Exception:
            return False

    def handle_domain_links(self, soup, domain: str) -> list[str]:
        """Extract links matching the configured link_pattern for a domain."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            handler = cfg.get("domain_handlers", {}).get(domain, {})
            pattern = handler.get("link_pattern", "/post/")
            return [a["href"] for a in soup.find_all("a", href=re.compile(pattern))]
        except Exception:
            return []

    def filter_domains_by_profile(self, domains: list[str], profile_name: str) -> list[str]:
        """Filter list of domains based on subject profile blocklists."""
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                profiles = json.load(f)

            if profile_name not in profiles:
                return domains

            profile = profiles[profile_name]
            block = profile.get("block_image_only_domains", [])

            return [d for d in domains if not any(b in d for b in block)]
        except Exception:
            return domains

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
        kept.sort(
            key=lambda item: (
                item.score,
                contains_subject_text(
                    " ".join(
                        [item.url, item.source_page, item.alt_text or "", item.page_title or ""]
                    ).lower(),
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
        kept.sort(
            key=lambda item: (
                item.score,
                contains_subject_text(
                    " ".join([item.url, item.source_page, item.page_title or ""]).lower(),
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
            from utils.logger import get_logger
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
        from utils.logger import get_logger

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
        from utils.http_client import HttpClient

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
        processed_media_urls: set[str] = set()
        seed_set = {normalize_url(u) for u in options.seed_urls}
        domain_profiles = options.domain_profiles or {}

        def get_domain_slug(url: str) -> str:
            parsed = urlparse(url)
            netloc = parsed.netloc.lower()
            if ":" in netloc:
                netloc = netloc.split(":")[0]
            return netloc

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

                is_seeded = (host in domain_profiles) or (
                    host in (options.seed_domains or [])
                )

                if not is_seeded:
                    if pages_scanned >= 15 and total_kept == 0:
                        LOGGER.info(
                            "Skipping %s: zero-yield cutoff after %d pages from domain %s",
                            page,
                            pages_scanned,
                            host,
                        )
                        return page, depth, [], [], "low_yield_skipped"

                    if pages_scanned >= 20:
                        yield_rate = total_kept / pages_scanned
                        if yield_rate < 0.05:
                            LOGGER.info(
                                "Skipping %s: low yield (%.1f%%) after %d pages from domain %s",
                                page,
                                yield_rate * 100,
                                pages_scanned,
                                host,
                            )
                            return page, depth, [], [], "low_yield_skipped"

                # Per-domain max_pages hard cap (set via 'max_pages: N' in seed file)
                profile = domain_profiles.get(host)
                if profile is not None:
                    max_pages_cap = getattr(profile, "max_pages", None)
                    if max_pages_cap is not None and pages_scanned >= max_pages_cap:
                        LOGGER.info(
                            "Skipping %s: domain '%s' reached max_pages cap (%d).",
                            page,
                            host,
                            max_pages_cap,
                        )
                        return page, depth, [], [], "max_pages_capped"

                stats["pages_scanned"] += 1

            if SpecializedExtractor.is_supported(page):
                LOGGER.info(f"Routing {page} to specialized extractor.")
                spec_result = SpecializedExtractor.extract(page)

                # Convert the raw URLs into generic ImageItem/VideoItem so downstream works
                from core.models import ImageItem, VideoItem

                page_images = [
                    ImageItem(url=u, source_page=page, status="pending")
                    for u in spec_result.images
                ]
                page_videos = [
                    VideoItem(url=u, source_page=page, type="direct", status="pending")
                    for u in spec_result.videos
                ]
                scrape_status = "ok"
            else:
                page_images, page_videos, scrape_status = (
                    self.search_provider.scrape_page(
                        page,
                        allow_domains=options.allow_domains,
                        block_domains=options.block_domains,
                    )
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

                        # Fix 1: Use the pure network latency reported by the HttpClient
                        # (which excludes rate-limiter sleep) for the concurrency scaler.
                        # Using wall-clock time caused concurrency to collapse to 1 whenever
                        # a slow-rate-limited domain was in flight, throttling all domains.
                        net_latency = self.search_provider.http.last_net_latency
                        # Handle mocks/MagicMocks in unit tests where search_provider.http is a mock
                        if not isinstance(net_latency, (int, float)):
                            net_latency = 0.0
                        # Fall back to wall-clock latency only when net_latency is 0 (cache
                        # hit or robots block — no real network request was made).
                        effective_latency = (
                            net_latency if net_latency > 0.0 else latency
                        )

                        # Adjust dynamic concurrency based on health
                        is_block = (
                            "429" in scrape_status
                            or "403" in scrape_status
                            or "worker_error" in scrape_status
                        )
                        with result_lock:
                            if is_block:
                                current_concurrency = max(1, current_concurrency - 2)
                                LOGGER.warning(
                                    "Dynamic Concurrency: Block/Error on %s. Reducing worker limit to %d.",
                                    page,
                                    current_concurrency,
                                )
                            elif effective_latency > 2.0:
                                current_concurrency = max(1, current_concurrency - 1)
                                LOGGER.info(
                                    "Dynamic Concurrency: High latency (%.2fs net) on %s. Reducing worker limit to %d.",
                                    effective_latency,
                                    page,
                                    current_concurrency,
                                )
                            else:
                                if current_concurrency < self.workers:
                                    current_concurrency += 1
                                    LOGGER.info(
                                        "Dynamic Concurrency: Fast response (%.2fs net) on %s. Scaling up worker limit to %d.",
                                        effective_latency,
                                        page,
                                        current_concurrency,
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
                            elif (
                                "429" in scrape_status
                                or "cooldown" in scrape_status
                                or "blacklisted" in scrape_status
                            ):
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
                                    reason=""
                                    if scrape_status == "ok"
                                    else scrape_status,
                                    discovered_links=discovered_links_counts.get(
                                        page, 0
                                    ),
                                    images_found=len(page_images),
                                    videos_found=len(page_videos),
                                )
                            )
                            if scrape_status == "ok" and self.state_cache:
                                self.state_cache.mark_processed(normalize_url(page))

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
                                        if add_rejected(
                                            "image",
                                            item.url,
                                            item.source_page,
                                            "duplicate",
                                        ):
                                            stats["rejected_count"] += 1
                                    continue

                                if norm_key in processed_media_urls:
                                    continue
                                processed_media_urls.add(norm_key)
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
                                    parent_href = getattr(
                                        item, "parent_anchor_href", ""
                                    )
                                    LOGGER.debug(
                                        "Image rejected: %s (reason: %s, score: %d, source: %s, parent_href: %s)",
                                        item.url,
                                        reason,
                                        score,
                                        item.source_page,
                                        parent_href,
                                    )
                                    if add_rejected(
                                        "image",
                                        item.url,
                                        item.source_page,
                                        reason,
                                        score,
                                    ):
                                        stats["rejected_count"] += 1
                                    continue

                                if (
                                    max_results > 0
                                    and len(result.images) >= max_results
                                ):
                                    add_rejected(
                                        "image",
                                        item.url,
                                        item.source_page,
                                        "max_results_limit",
                                        score,
                                    )
                                    continue

                                seen_images[norm_key] = item
                                item.source_domain = get_domain_slug(item.source_page)
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
                                            old_res,
                                            new_res,
                                            item.url,
                                        )
                                        existing.url = item.url
                                    elif "?" in item.url and "?" not in existing.url:
                                        LOGGER.debug(
                                            "Video URL upgraded from tokenless to tokened: %s -> %s",
                                            existing.url,
                                            item.url,
                                        )
                                        existing.url = item.url
                                    else:
                                        if add_rejected(
                                            "video",
                                            item.url,
                                            item.source_page,
                                            "duplicate",
                                        ):
                                            stats["rejected_count"] += 1
                                    continue

                                if norm_key in processed_media_urls:
                                    continue
                                processed_media_urls.add(norm_key)
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
                                    parent_href = getattr(
                                        item, "parent_anchor_href", ""
                                    )
                                    LOGGER.debug(
                                        "Video rejected: %s (reason: %s, score: %d, source: %s, parent_href: %s)",
                                        item.url,
                                        reason,
                                        score,
                                        item.source_page,
                                        parent_href,
                                    )
                                    if add_rejected(
                                        "video",
                                        item.url,
                                        item.source_page,
                                        reason,
                                        score,
                                    ):
                                        stats["rejected_count"] += 1
                                    continue

                                if (
                                    max_results > 0
                                    and len(result.videos) >= max_results
                                ):
                                    add_rejected(
                                        "video",
                                        item.url,
                                        item.source_page,
                                        "max_results_limit",
                                        score,
                                    )
                                    continue

                                seen_videos[norm_key] = item
                                item.source_domain = get_domain_slug(item.source_page)
                                result.videos.append(item)
                                stats["videos_kept"] += 1

                        if max_results > 0 and _is_target_met(
                            result, options, max_results
                        ):
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
                add_rejected(
                    "video", item.url, item.source_page, "max_results_limit", score
                )
                continue
            seen_videos[norm_key] = item
            item.source_domain = get_domain_slug(item.source_page)
            result.videos.append(item)

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
        result.run_metadata["crawl_duration_seconds"] = time.monotonic() - _crawl_start_time
        return result


