from __future__ import annotations
from typing import Any
import os
import re
import threading
import time
from urllib.parse import urlparse


from core.models import (
    EngineOptions,
    ScrapeResult,
    RejectedItem,
)
from monitoring.logger import get_logger
from core.filters import (
    normalize_url,
    score_image_relevance,
    rejection_reason_for_image,
    score_video_relevance,
    rejection_reason_for_video,
    contains_subject_text,
    looks_like_media,
    is_allowed_domain,
    is_allowed_path,
)
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
        
        # TTL for checking file modification on disk
        self._TTL_SECONDS = 10.0
        self._config_last_checked = 0.0
        self._profile_last_checked = 0.0

    def clear_cache(self) -> None:
        """Invalidate in-memory TTL cache, forcing fresh reload from disk on next access."""
        with self._lock:
            self._config_last_checked = 0.0
            self._profile_last_checked = 0.0
            self._config_mtime = None
            self._profile_mtime = None

    def _get_config(self) -> dict:
        now = time.monotonic()
        if now - self._config_last_checked < self._TTL_SECONDS:
            return self._cached_config
            
        with self._lock:
            # Double check inside the lock
            now = time.monotonic()
            if now - self._config_last_checked < self._TTL_SECONDS:
                return self._cached_config
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
            self._config_last_checked = time.monotonic()
            return self._cached_config

    def _get_profiles(self) -> dict:
        now = time.monotonic()
        if now - self._profile_last_checked < self._TTL_SECONDS:
            return self._cached_profiles
            
        with self._lock:
            now = time.monotonic()
            if now - self._profile_last_checked < self._TTL_SECONDS:
                return self._cached_profiles
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
            self._profile_last_checked = time.monotonic()
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

    def link_pattern_allows(self, url: str, domain: str) -> bool:
        """Return True if *url* matches the configured link_pattern for *domain*.

        Domains without a configured link_pattern allow all URLs. A configured
        pattern acts as a whitelist: only URLs matching it are considered
        in-scope for crawling. Used by the coordinator to filter discovered
        links before enqueueing them.
        """
        cfg = self._get_config()
        handler = cfg.get("domain_handlers", {}).get(domain, {})
        pattern = handler.get("link_pattern")
        if not pattern:
            return True
        try:
            # Match against the URL path only (scheme+host stripped) so that
            # anchored patterns (^/$) behave predictably and unanchored
            # substring patterns (e.g. "/video/") keep working.
            from urllib.parse import urlparse
            path = urlparse(url).path or "/"
            return re.search(pattern, path) is not None
        except re.error:
            LOGGER.warning("Invalid link_pattern for %s: %r", domain, pattern)
            return True

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
            "/about-us",
            "/privacy-policy",
            "/terms-of-service",
            "/terms-of-use",
            "/cookie-policy",
            "/cookie-policy/",
            "/refund-policy",
            "/disclaimer",
            "/sitemap",
            "/sitemap.xml",
            "/robots.txt",
            "/rss",
            "/feed",
            "/feed.xml",
            "/news",
            "/blog",
            "/advertise",
            "/advertising",
            "/careers",
            "/jobs",
            "/press",
            "/affiliate",
            "/partners",
            "/dmca-policy",
            "/2257",
            "/2257-compliance",
            "/18-usc-2257",
            "/compliance",
            "/trust-and-safety",
            "/welcome",
            "/welcome-to",
            "/welcome-to-the-site",
            "/getting-started",
            "/guidelines",
            "/community-guidelines",
            "/rules",
            "/tos",
            "/api",
            "/docs",
            "/developers",
            "/statistics",
            "/stats",
            "/rankings",
            "/trending",
            "/trending-profiles",
            "/trending-medias",
            "/daily-search-ranking",
            "/most-liked",
            "/most-viewed",
            "/popular",
            "/featured",
            "/random",
            "/discover",
            "/explore",
            "/user-posts",
            "/comments",
            "/messages",
            "/notifications",
            "/settings",
            "/account",
            "/profile",
            "/search",
            "/uploads",
            "/request",
            "/contact-us",
            "/submit",
            "/report",
            "/flags",
            "/moderation",
            "/banned",
            "/suspended",
            "/deleted",
            "/error",
            "/404",
            "/500",
            "/page-not-found",
            "/maintenance",
            "/coming-soon",
            "/under-construction",
            "/forums",
            "/community",
            "/top",
            "/new",
            "/fresh",
            "/recent",
            "/latest",
            "/updates",
            "/changelog",
            "/version",
            "/status",
            "/health",
            "/cdn-cgi",
            "/icons",
            "/img",
            "/images",
            "/assets",
            "/static",
            "/fonts",
            "/css",
            "/js",
            "/favicon.ico",
            "/manifest.webmanifest",
            "/manifest.json",
            "/site.webmanifest",
            "/apple-touch-icon.png",
        }
        if link_path in nav_paths or link_path.rstrip("/") in nav_paths:
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

        # Generic multi-segment utility/account prefix block. Many sites serve
        # nav/info/auth pages under a short prefix segment (e.g.
        # /s/faq, /o/menu-1, /user/login, /login/google, /version/all).
        # These are /PREFIX/<subpage> shapes with a non-media first segment.
        # Allow them if the subject token appears anywhere in the path (so a
        # subject-scoped page like /user/<subject> still passes).
        utility_prefix_segments = {
            "s", "o", "user", "users", "account", "accounts", "auth", "login",
            "logout", "register", "version", "settings", "admin", "moderation",
            "member", "members", "help", "support", "info",
            "list",
            "rss", "feeds", "embed", "widget",
        }
        if all_tokens:
            path_lower = link_path.lower()
            first_seg = path_lower.lstrip("/").split("/", 1)[0] if path_lower != "/" else ""
            if (
                first_seg in utility_prefix_segments
                # C: delegate token presence to contains_subject_text so fuzzy aliases apply
                and not contains_subject_text(path_lower, keyword, entity_tokens)
            ):
                return False

        # Check listing/index prefixes. If the link path contains a listing prefix,
        # it must contain the subject name/token to be considered relevant
        # (otherwise it's a listing page for another model/tag).
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
        link_listing = any(lp in link_path for lp in listing_prefixes)

        if link_listing:
            # C: delegate token presence to contains_subject_text so fuzzy aliases apply
            if all_tokens and not contains_subject_text(link_path.lower(), keyword, entity_tokens):
                return False

        # If it's a bare root seed, we must be strict since everything is linked from root
        is_bare_root = seed_path in {
            "",
            "/",
            "/index.html",
            "/index.php",
        } and "?" not in seed_page
        
        if is_bare_root:
            normalized_link_path = link_path.lower()
            # C: delegate token presence to contains_subject_text so fuzzy aliases apply
            if all_tokens and not contains_subject_text(normalized_link_path, keyword, entity_tokens):
                return False

        # Profile-scope rule: when the seed is a single-segment profile slug
        # that contains a subject token (e.g. <host>/<subject-slug>),
        # OR a search URL whose query value contains a subject token (e.g.
        # <host>/search?q=<subject>), reject same-host links whose first
        # path segment differs from the seed's and contains no subject token —
        # they are profile/media pages of OTHER models (e.g. /<other-slug>
        # or /models/<letter>/<letter>/<other-model>). Gated on
        # the seed containing a token so generic single-segment seeds (e.g.
        # /start) are not treated as profiles.
        seed_segments = [seg for seg in seed_path.split("/") if seg]
        query_tokens = [
            t.lower()
            for t in re.findall(r"[?&]q=([^&]+)", seed_page.lower())
            if t
        ]
        is_profile_seed = (
            len(seed_segments) == 1
            and all_tokens
            and any(t in seed_segments[0].lower() for t in all_tokens)
        ) or (
            len(seed_segments) == 1
            and seed_segments[0].lower() in {"search", "query", "results", "find"}
            and all_tokens
            and any(any(t in qt for t in all_tokens) for qt in query_tokens)
        )
        if is_profile_seed:
            link_segments = [seg for seg in link_path.split("/") if seg]
            if (
                link_segments
                and urlparse(link).netloc.lower() == seed_parsed.netloc.lower()
                and link_segments[0].lower() != seed_segments[0].lower()
                and not any(t in link_segments[0].lower() for t in all_tokens)
                # For a profile-slug seed (<host>/<subject>), block links at
                # any depth (/models/*). For a search-query seed, only
                # block single-segment other-creator slugs (/<other>) — opaque
                # multi-segment content paths (/a/<id>) are subject posts.
                and (
                    len(link_segments) == 1
                    or seed_segments[0].lower() not in {"search", "query", "results", "find"}
                )
            ):
                return False

        return True



class MediaProcessor:
    """Handles filtering, deduplication, scoring, and deferred downloading of media."""

    def __init__(self, downloader):
        self.downloader = downloader

    def finalize_images(self, result, options) -> list:
        from core.filters import normalize_url

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

    def start_downloads(self, result, options, output_root) -> None:
        import queue
        import threading
        import concurrent.futures as _cf
        import json
        from config import CONCURRENT_DOWNLOADS
        from monitoring.logger import get_logger

        self.LOGGER = get_logger(__name__)
        self.options = options
        self.result = result
        self.output_root = output_root

        # Load known dead URLs
        dead_urls_file = options.output_dir / result.keyword_slug / "dead_urls.json"
        if dead_urls_file.exists():
            try:
                with open(dead_urls_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, list):
                        with self.downloader._dead_urls_lock:
                            self.downloader._dead_urls.update(loaded)
                self.LOGGER.info("Loaded %d known dead URLs", len(self.downloader._dead_urls))
            except Exception as e:
                self.LOGGER.warning("Failed to load dead URLs: %s", e)

        # Setup CDN hosts
        self._cdn_hosts_deduped = []
        _cdn_hosts = []
        if options.seed_manifest is not None:
            _cdn_hosts.extend(getattr(options.seed_manifest, "all_allowed_hosts", []))
        elif options.domain_profiles:
            for _dp in options.domain_profiles.values():
                _cdn_hosts.extend(getattr(_dp, "cdn_hosts", []))
        
        _seen_cdn = set()
        for _h in _cdn_hosts:
            if _h not in _seen_cdn:
                _seen_cdn.add(_h)
                self._cdn_hosts_deduped.append(_h)

        # State for pipelining
        self.download_queue = queue.Queue(maxsize=5000)
        self.domain_counters = {}
        self._seen_download_urls = set()
        self._is_running = True
        
        self.dl_executor = _cf.ThreadPoolExecutor(
            max_workers=CONCURRENT_DOWNLOADS, thread_name_prefix="dl"
        )
        
        # Start a manager thread that consumes the queue and submits to the executor
        self._manager_thread = threading.Thread(target=self._download_manager_loop, name="DlManagerThread", daemon=True)
        self._manager_thread.start()
        self.LOGGER.info("Started pipelined media downloader with max %d workers.", CONCURRENT_DOWNLOADS)

    def enqueue_download(self, item, media_kind: str) -> None:
        """Called by MediaPipeline to push an item for immediate download."""
        if getattr(self, "download_queue", None) is None:
            return  # Downloads not active

        from urllib.parse import urlparse
        import re
        from core.filters import normalize_url as _norm_dl_url
        from config import DEFAULT_DOWNLOAD_IMAGES_SUBDIR, DEFAULT_DOWNLOAD_VIDEOS_SUBDIR

        if media_kind == "video" and item.type not in {"direct", "hls", "dash"}:
            item.status = "skipped"
            item.failure_reason = "non_downloadable_type"
            return

        norm = _norm_dl_url(item.url)
        if norm in self._seen_download_urls:
            item.status = "skipped"
            item.failure_reason = "duplicate_url_precheck"
            return
        self._seen_download_urls.add(norm)

        domain = urlparse(item.source_page).netloc.lower()
        if ":" in domain:
            domain = domain.split(":")[0]
            
        self.domain_counters[domain] = self.domain_counters.get(domain, 0) + 1
        idx = self.domain_counters[domain]
        domain_prefix = domain.replace(".", "_")
        
        stem_suffix = re.sub(
            r"[^a-zA-Z0-9]+", "_",
            (getattr(item, "alt_text", "") or item.page_title or media_kind).strip().lower(),
        ).strip("_")
        stem_suffix = stem_suffix[:40] if stem_suffix else "asset"
        stem = f"{domain_prefix}_{idx:03d}_{stem_suffix}"

        # Determine directory
        sub_dir = DEFAULT_DOWNLOAD_IMAGES_SUBDIR if media_kind == "image" else DEFAULT_DOWNLOAD_VIDEOS_SUBDIR
        domain_dir = self.output_root / sub_dir / domain
        domain_dir.mkdir(parents=True, exist_ok=True)

        task = (item, domain_dir, stem, media_kind)
        # Block if queue is full (Soft Cap Backpressure)
        self.download_queue.put(task)

    def _download_manager_loop(self):
        import time
        from urllib.parse import urlparse
        from core.models import RejectedItem

        def add_rejected(kind, url, source_page, reason, score):
            self.result.rejected_items.append(
                RejectedItem(kind=kind, url=url, source_page=source_page, reason=reason, score=score)
            )

        futures_map = {}
        
        while self._is_running or not self.download_queue.empty():
            import queue
            try:
                task = self.download_queue.get(timeout=0.5)
                if task is None:
                    continue
                item, directory, stem, media_kind = task
                
                dl_host = urlparse(item.source_page).netloc.lower()
                profile = self.options.domain_profiles.get(dl_host) if self.options.domain_profiles else None
                min_size = getattr(profile, "min_image_size", None) if profile else None
                thumb_pattern = getattr(profile, "thumbnail_prefix_pattern", None) if profile else None
                needs_referer = getattr(profile, "requires_referer", False) if profile else False
                referer = item.source_page if needs_referer else None

                fut = self.dl_executor.submit(
                    self.downloader._download_file,
                    item.url, directory, stem, media_kind, referer, min_size, thumb_pattern, self._cdn_hosts_deduped
                )
                futures_map[fut] = (item, media_kind)
                self.download_queue.task_done()
                
            except queue.Empty:
                pass
            
            # Periodically check for completed futures to avoid memory leaks
            done = [f for f in futures_map if f.done()]
            for f in done:
                item, media_kind = futures_map.pop(f)
                try:
                    success, download_info = f.result()
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
                        self.result.download_stats["downloaded"] = self.result.download_stats.get("downloaded", 0) + 1
                    else:
                        reason = download_info.get("reason", "unknown")
                        item.status = "skipped" if reason in {"low_resolution", "unparseable_dimensions", "duplicate", "invalid_media_type"} else "failed"
                        item.failure_reason = reason
                        key = f"download_{reason}"
                        self.result.download_stats[key] = self.result.download_stats.get(key, 0) + 1
                        add_rejected(media_kind, item.url, item.source_page, f"download_{reason}", item.score)
                        
                        dl_host = urlparse(item.source_page).netloc.lower()
                        if dl_host in self.result.domain_stats:
                            self.result.domain_stats[dl_host]["rejected_count"] += 1
                            if media_kind == "image":
                                self.result.domain_stats[dl_host]["images_kept"] = max(0, self.result.domain_stats[dl_host]["images_kept"] - 1)
                            else:
                                self.result.domain_stats[dl_host]["videos_kept"] = max(0, self.result.domain_stats[dl_host]["videos_kept"] - 1)
                except Exception as exc:
                    self.LOGGER.warning("Download error for %s: %s", item.url, exc)
                    item.status = "failed"
                    item.failure_reason = f"exception_{type(exc).__name__}"
                    add_rejected(media_kind, item.url, item.source_page, f"download_failed:{type(exc).__name__}", item.score)

    def stop_downloads(self) -> None:
        if getattr(self, "_is_running", False):
            self._is_running = False
            self.LOGGER.info("Waiting for pipelined downloads to complete...")
            if getattr(self, "_manager_thread", None):
                self._manager_thread.join()
            if getattr(self, "dl_executor", None):
                self.dl_executor.shutdown(wait=True)
            self._save_dead_urls(self.result, self.options, self.output_root)
            self.LOGGER.info("Download pipeline fully stopped.")



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
            media_processor=self.media_processor
        )
        
        # We start coordinator with candidate pages at depth 0
        ordered_pages = [(normalize_url(p), 0) for p in candidate_pages if p and not looks_like_media(normalize_url(p))]
        
        result = coordinator.execute(ordered_pages)
        
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


