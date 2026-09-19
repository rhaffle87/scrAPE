from __future__ import annotations
import os
import re
import threading
import time
from urllib.parse import urlparse
import json

from monitoring.logger import get_logger

from core.models import (
    EngineOptions,
)
from core.filters import (
    contains_subject_text,
    is_allowed_domain,
    is_allowed_path,
)

LOGGER = get_logger(__name__)


class DomainRulesManager:
    """Manages domain-specific routing rules, blocklists, and crawling scopes."""

    def __init__(self, config_path: str = "data/domain_config.json", profile_path: str = "data/subject_profiles.json"):
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
        anchor_text: str = "",
        profile=None,
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

        skip_relevance = profile and getattr(profile, "skip_detail_relevance_check", False)

        if link_listing:
            # C: delegate token presence to contains_subject_text so fuzzy aliases apply
            if all_tokens:
                if skip_relevance:
                    if not link_path.startswith(seed_path):
                        return False
                elif not contains_subject_text(link_path.lower(), keyword, entity_tokens):
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
            if all_tokens:
                if skip_relevance:
                    pass
                elif not contains_subject_text(normalized_link_path, keyword, entity_tokens):
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

        # Fast-Fail Sibling Gallery Rejection:
        # If we are on ANY page and discover a link to the same host,
        # but the path does not contain the subject token and it's NOT a pagination link,
        # check the anchor text. If the anchor text also doesn't contain the token,
        # we reject it, UNLESS the seed is already an opaque search seed or we have no tokens.
        # But we only apply this strictness if we HAVE tokens and it's a same-host link.
        if all_tokens and urlparse(link).netloc.lower() == seed_parsed.netloc.lower():
            normalized_link_path = link_path.lower()
            
            # If the path has the token, it's fine.
            path_has_token = contains_subject_text(normalized_link_path, keyword, entity_tokens)
            
            # If the anchor has the token, it's fine.
            anchor_has_token = False
            if anchor_text:
                anchor_has_token = contains_subject_text(anchor_text, keyword, entity_tokens)
                
            # Allow pagination and root
            is_pag_or_root = any(p in normalized_link_path for p in {"/page/", "/p/", "/pg/"}) or normalized_link_path == ""

            # If neither the path nor the anchor text indicates relevance, and it's not a generic listing/pagination,
            # we reject it to prevent wandering into unrelated galleries.
            if not path_has_token and not anchor_has_token and not is_pag_or_root:
                # One exception: if the URL is an opaque post ID (e.g. /post/12345) and anchor_text is completely empty
                # (e.g. a naked image link without alt text), we might want to allow it if it's on a known profile.
                # But to be strict and improve yield, if there's no evidence it's relevant, we drop it.
                
                # To prevent breaking sites where everything is opaque, we only apply this strict filter 
                # if the seed page ITSELF had the token in the URL. If the seed didn't have the token in the URL,
                # then we must be on a site that relies on opaque URLs, so we shouldn't strictly block them.
                seed_has_token = contains_subject_text(seed_path.lower(), keyword, entity_tokens)
                if seed_has_token:
                    return False

        return True


