"""
url_classifier.py — URL Classification, Domain Scope Matching, and Path Filtering Engine.

Handles URL canonicalization, search/archive page detection, CDN host evaluation,
domain rule resolution, and path filtering.
"""

from __future__ import annotations

import logging
import re
from urllib.parse import urljoin, urlparse, urlunparse

from config import (
    ALWAYS_BLOCK_DOMAINS,
    DASH_EXTENSIONS,
    HLS_EXTENSIONS,
    IMAGE_EXTENSIONS,
    PREVIEW_MARKERS,
    VIDEO_EXTENSIONS,
)
from core.models import ImageItem, VideoItem

_log = logging.getLogger(__name__)

CDN_DOMAINS = ("cdn", "static", "media", "images", "img", "assets", "content")
JUNK_SUBSTRINGS = {"/login", "/signup", "/cart", "/terms", "/privacy", "/contact", "/about", "/help", "/faq", "/subscribe"}
JUNK_URL_PATTERNS = [r"/login", r"/signup", r"/register", r"/logout", r"/cart", r"/checkout"]
SOCIAL_LOGIN_WALL_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "faceit.com",
    "linkedin.com",
    "pinterest.com",
}
BACKGROUND_IMAGE_PATTERN = re.compile(
    r"""background(?:-image)?\s*:\s*[^;]*?url\((['\"]?)(.*?)\1\)""", re.IGNORECASE
)
_PAGE_LABEL_RE = re.compile(r"page\s+\d+\s*:", re.IGNORECASE)

__all__ = [
    "safe_join",
    "clean_attr",
    "extract_background_image",
    "BACKGROUND_IMAGE_PATTERN",
    "absolutize_url",
    "normalize_url",
    "normalize_media_url",
    "is_probable_image",
    "is_probable_video",
    "is_thumbnail_url",
    "is_cdn_asset_domain",
    "_get_allowed_hosts",
    "media_type_matches_domain_expectation",
    "is_http_url",
    "is_broken_media_url",
    "looks_like_media",
    "domain_matches",
    "is_allowed_domain",
    "is_search_page_url",
    "is_archive_or_index_page",
    "is_detail_page",
    "is_allowed_path",
    "is_pagination_url",
    "is_junk_url",
    "is_rejected_url",
    "extract_domain_from_url",
    "is_same_domain",
    "is_subdomain_of",
    "_aliases_for",
    "SOCIAL_LOGIN_WALL_DOMAINS",
]


def safe_join(items: list[str | None], sep: str = " ") -> str:
    """Safely join a list of strings filtering out None items."""
    return sep.join(item for item in items if item is not None)


def clean_attr(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.split())


def extract_background_image(style_value: str | None) -> str | None:
    if not style_value:
        return None
    match = BACKGROUND_IMAGE_PATTERN.search(style_value)
    if not match:
        return None
    return match.group(2)


def absolutize_url(candidate: str, base_url: str) -> str:
    """Resolve a candidate URL against a base URL."""
    if not candidate:
        return base_url
    return urljoin(base_url, candidate.strip())


def normalize_url(url: str) -> str:
    """Normalize a URL by stripping tracking params and applying normalisation rules."""
    from urllib.parse import unquote, quote
    import config

    try:
        url = url.strip()
        rules = config.URL_NORMALISATION_RULES
        if not rules:
            config._load_dynamic_config()
            rules = config.URL_NORMALISATION_RULES
        for pattern, replacement in rules:
            url = pattern.sub(replacement, url)
        unquoted = unquote(url)
        parsed = urlparse(unquoted)
        if parsed.query:
            from urllib.parse import parse_qsl, urlencode
            tracking_params = {
                "hl", "lang", "locale", "utm_source", "utm_medium", "utm_campaign",
                "utm_term", "utm_content", "fbclid", "gclid", "ref", "source", "ncid", "mc_eid"
            }
            kept = [
                (k, v)
                for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                if k.lower() not in tracking_params
            ]
            query = urlencode(kept) if kept else ""
        else:
            query = parsed.query
        quoted_path = quote(parsed.path, safe="/")
        quoted_query = quote(query, safe="=&%")
        cleaned = parsed._replace(fragment="", path=quoted_path, query=quoted_query)
        return urlunparse(cleaned)
    except Exception as exc:
        _log.debug("Failed canonicalizing URL '%s': %s", url, exc)
        return url.strip()



def normalize_media_url(url: str) -> str:
    """Normalize a media URL for deduplication check."""
    from urllib.parse import unquote
    try:
        parsed = urlparse(url.strip())
        scheme = "https"
        netloc = parsed.netloc.lower()
        path = unquote(parsed.path).lower().rstrip("/")
        return f"{scheme}://{netloc}{path}"
    except Exception as exc:
        _log.debug("Failed normalizing media URL '%s': %s", url, exc)
        return url.strip()



def is_probable_image(url: str) -> bool:
    try:
        path = urlparse(url).path.lower().rstrip("/")
    except Exception as exc:
        _log.debug("Failed parsing URL for image probability check '%s': %s", url, exc)
        path = ""

    if _PAGE_LABEL_RE.search(path):
        return False
    basename = path.rsplit("/", 1)[-1]
    if " " in basename:
        return False
    return any(path.endswith(ext) for ext in IMAGE_EXTENSIONS)


def is_probable_video(url: str) -> bool:
    try:
        path = urlparse(url).path.lower().rstrip("/")
    except Exception as exc:
        _log.debug("Failed parsing URL for video probability check '%s': %s", url, exc)
        path = ""

    return any(
        path.endswith(ext)
        for ext in VIDEO_EXTENSIONS | HLS_EXTENSIONS | DASH_EXTENSIONS
    )


def is_thumbnail_url(url: str) -> bool:
    from core.media_filter import has_low_res_path_pattern
    try:
        path = urlparse(url).path.lower().rstrip("/")
    except Exception as exc:
        _log.debug("Failed parsing URL for thumbnail check '%s': %s", url, exc)
        path = ""

    if re.search(r"\.pic\d+\.jpe?g", path):
        _log.debug("Thumbnail detected (Booru picN): %s", url)
        return True
    if re.search(r"-\d+x\d+\.(?:jpe?g|png|gif|webp|avif)$", path):
        _log.debug("Thumbnail detected (dimensions suffix): %s", url)
        return True
    if has_low_res_path_pattern(url, min_width=300, min_height=300):
        _log.debug("Thumbnail detected (low res path pattern): %s", url)
        return True
    if any(marker in path for marker in PREVIEW_MARKERS):
        _log.debug("Thumbnail detected (preview marker): %s", url)
        return True
    if path.endswith("/loading.gif"):
        return True
    if re.search(r"/thumbs?[_/]", path):
        _log.debug("Thumbnail detected (thumb path): %s", url)
        return True
    if re.search(r"_(?:poster|thumb|preview|small)\.", path):
        _log.debug("Thumbnail detected (poster/thumb suffix): %s", url)
        return True
    return False


def is_cdn_asset_domain(url: str, allow_hosts: list[str] | None = None) -> bool:
    if not allow_hosts:
        return False
    host = urlparse(url).netloc.lower()
    for allowed in allow_hosts:
        if host == allowed or host.endswith(f".{allowed}"):
            return True
    return False


def _get_allowed_hosts(domain_profiles: dict | None) -> list[str] | None:
    if not domain_profiles:
        return None
    hosts = []
    seen = set()
    for domain, profile in domain_profiles.items():
        if domain not in seen:
            seen.add(domain)
            hosts.append(domain)
        cdn_hosts = None
        if hasattr(profile, "cdn_hosts"):
            cdn_hosts = profile.cdn_hosts
        elif isinstance(profile, dict) and "cdn_hosts" in profile:
            cdn_hosts = profile["cdn_hosts"]

        if cdn_hosts:
            for host in cdn_hosts:
                if host not in seen:
                    seen.add(host)
                    hosts.append(host)
    return hosts


def media_type_matches_domain_expectation(
    item: ImageItem | VideoItem,
    domain_profiles: dict | None,
) -> bool:
    if not domain_profiles:
        return True
    source_host = urlparse(item.source_page).netloc.lower()
    profile = domain_profiles.get(source_host)
    if profile is None:
        return True
    if getattr(profile, "media_type", None) == "image" and isinstance(item, VideoItem):
        return False
    if getattr(profile, "media_type", None) == "video" and isinstance(item, ImageItem):
        return False
    return True


def is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}


def is_broken_media_url(url: str) -> bool:
    lower_url = url.lower()
    if "placeholder" in lower_url or "404" in lower_url or "notfound" in lower_url:
        return True
    if "error-image" in lower_url or "default-thumbnail" in lower_url:
        return True
    return False


def looks_like_media(url: str) -> bool:
    if is_broken_media_url(url):
        return False
    return is_probable_image(url) or is_probable_video(url)


def domain_matches(url: str, domain_rules: list[str]) -> bool:
    hostname = urlparse(url).netloc.lower()
    for rule in domain_rules:
        normalized = rule.lower().strip()
        if not normalized:
            continue
        if hostname == normalized or hostname.endswith(f".{normalized}"):
            return True
    return False


def is_allowed_domain(
    url: str, allow_domains: list[str], block_domains: list[str]
) -> bool:
    if ALWAYS_BLOCK_DOMAINS and domain_matches(url, list(ALWAYS_BLOCK_DOMAINS)):
        return False
    if domain_matches(url, list(SOCIAL_LOGIN_WALL_DOMAINS)):
        return False
    if block_domains and domain_matches(url, block_domains):
        return False
    if allow_domains:
        return domain_matches(url, allow_domains)
    return True


def is_search_page_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    query = parsed.query.lower()
    if any(s in path for s in ("/search", "/find", "/results", "/query")):
        return True
    if any(q in query for q in ("q=", "search=", "query=", "keyword=", "k=")):
        return True
    return False


def is_archive_or_index_page(url: str, title: str | None = None) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    query = parsed.query.lower()
    title_low = title.lower() if title else ""

    path_clean = path.strip("/")
    if not path_clean or path_clean in {
        "index.html",
        "index.php",
        "index.htm",
        "home",
        "homepage",
    }:
        return True

    archive_paths = {
        "/category/",
        "/tag/",
        "/tags/",
        "/search",
        "/actor/",
        "/models/",
        "/archives/",
        "/page/",
        "/model/",
        "/actors/",
        "/categories/",
    }
    if any(p in path for p in archive_paths):
        for seg in archive_paths:
            if seg in path:
                after = path.split(seg, 1)[1].strip("/")
                if "/" in after:
                    parts = after.split("/")
                    if len(parts) >= 2 and parts[1] not in ("page", "p", "sort", "filter"):
                        return False
        return True
    if any(q in query for q in ("q=", "s=", "cat=", "tag=", "p=")):
        return True

    archive_titles = {
        "archives",
        "category",
        "tag",
        "search results",
        "actor",
        "models",
        "actors",
        "model profile",
        "all post",
        "tag:",
        "category:",
    }
    if any(t in title_low for t in archive_titles):
        return True

    return False


def is_detail_page(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    if not path or path == "/":
        return False
    if is_search_page_url(url) or is_pagination_url(url):
        return False
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2:
        return True
    if "." in parts[-1] if parts else False:
        return True
    return False


def is_allowed_path(url: str) -> bool:
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()

        if path.endswith((".json", ".xml", ".css", ".js")):
            return False

        skip_patterns = {
            "/wp-json",
            "/wp-json/",
            "/xmlrpc.php",
            "/feed/",
            "/cdn-cgi/",
            "/cdn-cgi/l/",
            "/feed",
            "/account",
            "/cart",
            "/checkout",
            "goto/account",
            "/shop/account",
            "/store/account",
        }
        for pattern in skip_patterns:
            if pattern in path or path.endswith(pattern):
                return False
        if "feed=" in query:
            return False
        return True
    except Exception as exc:
        _log.debug("Failed validating path allowed '%s': %s", url, exc)
        return False



def is_pagination_url(url: str) -> bool:
    parsed = urlparse(url)
    query = parsed.query.lower()
    path = parsed.path.lower()
    if any(param in query for param in ("page=", "p=", "start=", "offset=", "paged=")):
        return True
    if re.search(r"/page/\d+", path) or re.search(r"/p/\d+", path):
        return True
    return False


def is_junk_url(url: str) -> bool:
    return not is_allowed_path(url)


def is_rejected_url(url: str) -> bool:
    return is_junk_url(url)


def extract_domain_from_url(url: str) -> str:
    return urlparse(url).netloc.lower()


def is_same_domain(url1: str, url2: str) -> bool:
    return extract_domain_from_url(url1) == extract_domain_from_url(url2)


def is_subdomain_of(child_url: str, parent_domain: str) -> bool:
    child_host = extract_domain_from_url(child_url)
    parent_host = parent_domain.lower()
    return child_host == parent_host or child_host.endswith(f".{parent_host}")


def _aliases_for(source_page: str, domain_profiles: dict | None) -> list[str] | None:
    if not domain_profiles:
        return None
    host = urlparse(source_page).netloc.lower()
    profile = domain_profiles.get(host)
    if not profile:
        return None
    aliases = getattr(profile, "subject_aliases", None)
    return aliases or None
