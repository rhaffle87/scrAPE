from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse

import json as _json
import os as _os
from pathlib import Path as _Path

from config import (
    DASH_EXTENSIONS,
    GENERIC_ASSET_TERMS,
    UTILITY_ASSET_TERMS,
    HLS_EXTENSIONS,
    IMAGE_EXTENSIONS,
    PREVIEW_MARKERS,
    VIDEO_EXTENSIONS,
    ALWAYS_BLOCK_DOMAINS,
)
from core.models import ImageItem, VideoItem

BACKGROUND_IMAGE_PATTERN = re.compile(
    r"""background(?:-image)?\s*:\s*[^;]*?url\((['\"]?)(.*?)\1\)"""
)
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def safe_join(items: list[str | None], sep: str = " ") -> str:
    return sep.join(s for s in items if s is not None)


def absolutize_url(candidate: str, base_url: str) -> str:
    return urljoin(base_url, candidate.strip())


def is_search_page_url(url: str) -> bool:
    """Return True if the URL is a generic search results page endpoint (e.g. /search?q=...)."""
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()
        # Path-based detection: /search/, /results, /query, /find
        if re.search(r"/(?:search|find|query|results)(?:/|\?|$)", path):
            return True
        # Query-based detection: common search param names on any host
        if any(qp in query for qp in ("search_query=", "search=", "q=", "query=", "text=")):
            return True
        # Platform-specific: Flickr / Vimeo search via ?q= or similar
        if (parsed.netloc in ("flickr.com", "vimeo.com")
                or parsed.netloc.endswith((".flickr.com", ".vimeo.com"))):
            if any(qp in query for qp in ("q=", "text=", "search_query=")):
                return True
    except Exception:
        pass
    return False


def normalize_url(url: str) -> str:
    from urllib.parse import unquote, quote
    from config import URL_NORMALISATION_RULES

    try:
        url = url.strip()
        # Apply all domain-specific URL normalisation rules from config.
        # Rules collapse variant URLs (e.g. locale-prefixed paths) to a single
        # canonical form before the URL enters the crawl queue.
        for pattern, replacement in URL_NORMALISATION_RULES:
            url = pattern.sub(replacement, url)
        unquoted = unquote(url)
        parsed = urlparse(unquoted)
        # Strip content-neutral locale query params (hl, lang, locale) so
        # /media/0338?hl=ru and /media/0338 collapse to one canonical URL,
        # preventing duplicate fetches/downloads on any domain.
        if parsed.query:
            from urllib.parse import parse_qsl, urlencode
            kept = [
                (k, v)
                for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                if k.lower() not in {"hl", "lang", "locale"}
            ]
            query = urlencode(kept) if kept else ""
        else:
            query = parsed.query
        # Re-quote path and query parameters to ensure canonical escaping
        quoted_path = quote(parsed.path, safe="/")
        quoted_query = quote(query, safe="=&%")
        cleaned = parsed._replace(fragment="", path=quoted_path, query=quoted_query)
        return urlunparse(cleaned)
    except Exception:
        return url.strip()


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


# Compiled once: matches gallery navigation pseudo-URLs like
# "Page 1: _1.jpg" that some gallery sites inject into div title attributes.
_PAGE_LABEL_RE = re.compile(r"page\s+\d+\s*:", re.IGNORECASE)


def is_probable_image(url: str) -> bool:
    try:
        path = urlparse(url).path.lower().rstrip("/")
    except Exception:
        path = ""
    # Reject gallery-navigation pseudo-paths such as "Page 1: _1.jpg" that some
    # gallery sites store in div title attributes.  These are never
    # valid HTTP resource paths.
    if _PAGE_LABEL_RE.search(path):
        return False
    # Real CDN image paths never contain spaces; paths with spaces before the
    # extension are almost certainly mis-parsed text attributes.
    basename = path.rsplit("/", 1)[-1]
    if " " in basename:
        return False
    return any(path.endswith(ext) for ext in IMAGE_EXTENSIONS)


def is_thumbnail_url(url: str) -> bool:
    """Return True if URL is a known thumbnail or low-res pattern."""
    import logging
    _log = logging.getLogger(__name__)

    try:
        path = urlparse(url).path.lower().rstrip("/")
    except Exception:
        path = ""
    # Booru-style picN thumbnails (pic256, pic512, etc.)
    if re.search(r"\.pic\d+\.jpe?g", path):
        _log.debug("Thumbnail detected (Booru picN): %s", url)
        return True
    # WordPress/CDN dimensions suffix (e.g. -320x180.jpg)
    if re.search(r"-\d+x\d+\.(?:jpe?g|png|gif|webp|avif)$", path):
        _log.debug("Thumbnail detected (dimensions suffix): %s", url)
        return True
    # Check for general low-resolution directory structures or query parameters
    if has_low_res_path_pattern(url, min_width=300, min_height=300):
        _log.debug("Thumbnail detected (low res path pattern): %s", url)
        return True
    # Common thumbnail patterns
    if any(marker in path for marker in PREVIEW_MARKERS):
        _log.debug("Thumbnail detected (preview marker): %s", url)
        return True
    # loading.gif placeholders
    if path.endswith("/loading.gif"):
        return True
    # Low-res preview thumbnails (e.g. /thumbs/ or /thumb_ in path)
    if re.search(r"/thumbs?[_/]", path):
        _log.debug("Thumbnail detected (thumb path): %s", url)
        return True
    # Low-res poster and preview suffix images
    if re.search(r"_(?:poster|thumb|preview|small)\.", path):
        _log.debug("Thumbnail detected (poster/thumb suffix): %s", url)
        return True
    return False


def is_probable_video(url: str) -> bool:
    try:
        path = urlparse(url).path.lower().rstrip("/")
    except Exception:
        path = ""
    return any(
        path.endswith(ext)
        for ext in VIDEO_EXTENSIONS | HLS_EXTENSIONS | DASH_EXTENSIONS
    )


def is_cdn_asset_domain(url: str, allow_hosts: list[str] | None = None) -> bool:
    """
    Return True if the URL's host is a known CDN host for one of our seed domains.

    When *allow_hosts* is provided (built from SeedManifest.all_allowed_hosts)
    the check is exact: the host must be in the allow-list.  When omitted the
    function conservatively returns False (permissive mode no longer applies
    since the hardcoded KNOWN_CDN_PARENT_DOMAINS dict has been removed).
    """
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
    """
    Return False if the item's media type contradicts the domain profile.

    - profile.media_type == 'image' → reject VideoItem
    - profile.media_type == 'video' → reject ImageItem
    - profile.media_type == 'mixed' or no profile → accept everything
    """
    if not domain_profiles:
        return True
    source_host = urlparse(item.source_page).netloc.lower()
    profile = domain_profiles.get(source_host)
    if profile is None:
        return True
    if profile.media_type == "image" and isinstance(item, VideoItem):
        return False
    if profile.media_type == "video" and isinstance(item, ImageItem):
        return False
    return True


def is_http_url(url: str) -> bool:
    return urlparse(url).scheme in {"http", "https"}


def is_broken_media_url(url: str) -> bool:
    """Return True if the URL matches known broken, error, placeholder, or 404 media patterns."""
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


SOCIAL_LOGIN_WALL_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "twitter.com",
    "x.com",
    "faceit.com",
    "linkedin.com",
    "pinterest.com",
}


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


def is_allowed_path(url: str) -> bool:
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()

        # Reject non-HTML extensions from BFS crawling
        if path.endswith((".json", ".xml", ".css", ".js")):
            return False

        # WordPress JSON API endpoints, XML-RPC, feed, Cloudflare email protection, etc.
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
    except Exception:
        return False


def is_pagination_url(url: str) -> bool:
    """Return True if *url* looks like a pagination/index offset link.

    Matches the same shapes the detail-page classifier rejects as pagination
    (/page/N, /p/N, ?page=N, ?p=N) so callers can re-admit subject-scoped
    pagination links as crawlable index nodes.
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.lower()
        query = parsed.query.lower()
        if any(p in path for p in ("/page/", "/p/", "/pg/")):
            return True
        if re.search(r"(?:^|&)(?:page|p|pg)=\d", query):
            return True
        return False
    except Exception:
        return False


def normalize_token(value: str) -> str:
    return "".join(TOKEN_PATTERN.findall(value.lower()))


def keyword_tokens(keyword: str) -> set[str]:
    return {token for token in TOKEN_PATTERN.findall(keyword.lower()) if len(token) > 1}


def subject_tokens(keyword: str, entity_tokens: list[str] | None = None) -> set[str]:
    raw_terms = set(keyword_tokens(keyword))
    for token in entity_tokens or []:
        normalized = normalize_token(token)
        if normalized:
            raw_terms.add(normalized)
            raw_terms.update(keyword_tokens(token))
    compact = {normalize_token(term) for term in raw_terms if normalize_token(term)}
    return raw_terms | compact


def _fuzzy_similarity(a: str, b: str) -> float:
    """Dice coefficient for character bigrams; 0.0 .. 1.0."""
    if a == b:
        return 1.0
    if len(a) < 2 or len(b) < 2:
        return 0.0
    ab = {a[i : i + 2] for i in range(len(a) - 1)}
    bb = {b[i : i + 2] for i in range(len(b) - 1)}
    inter = len(ab & bb)
    if inter == 0:
        return 0.0
    return 2.0 * inter / (len(ab) + len(bb))


# Minimum Dice similarity for a seed-derived alias to count as a subject match.
# Conservative: a loose alias (one extra/repeated character, e.g. a site's slug
# differing from the canonical keyword) scores ~0.88; unrelated slugs drop well
# below this. Tune down only with care, as raising it risks over-allowance
# across all domains.
ALIAS_FUZZY_THRESHOLD = 0.75


def weighted_subject_score(
    text: str,
    keyword: str,
    entity_tokens: list[str] | None = None,
    subject_aliases: list[str] | None = None,
) -> int:
    lowered = text.lower()
    compact_text = normalize_token(lowered)
    score = 0
    for token in subject_tokens(keyword, entity_tokens):
        if len(token) < 2:
            continue
        exact_matches = re.findall(
            rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", lowered
        )
        if exact_matches:
            score += 5 * len(exact_matches)
            continue
        if token in compact_text:
            score += 3
    # Seed-derived aliases add weak positive signal when fuzzy-matched against
    # raw slug segments (URL paths, filenames). Handles sites that spell the
    # subject's handle slightly differently from the canonical keyword
    # (fuzzy-name mismatch). Segments preserve the slug boundary that
    # normalize_token would otherwise merge.
    if score == 0 and subject_aliases:
        raw_tokens = {t for t in re.split(r"[^a-z0-9]+", lowered) if len(t) >= 3}
        for alias in subject_aliases:
            for tok in raw_tokens:
                if _fuzzy_similarity(alias, tok) >= ALIAS_FUZZY_THRESHOLD:
                    score += 3
                    break
    return score


def contains_subject_text(
    text: str,
    keyword: str,
    entity_tokens: list[str] | None = None,
    subject_aliases: list[str] | None = None,
) -> bool:
    return weighted_subject_score(text, keyword, entity_tokens, subject_aliases) > 0


def _preview_penalty(text: str) -> int:
    return sum(6 for marker in PREVIEW_MARKERS if marker in text)


def is_archive_or_index_page(url: str, title: str | None) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    query = parsed.query.lower()
    title_low = title.lower() if title else ""

    # Consider empty/root paths or index files as homepages, which are index pages
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
        # Allow if there is a meaningful slug *after* the archive segment
        # e.g. /actor/subject_name/some-specific-post — not a pure listing page
        for seg in archive_paths:
            if seg in path:
                after = path.split(seg, 1)[1].strip("/")
                if "/" in after:
                    parts = after.split("/")
                    # If depth >= 2 beyond archive key, and it's not just pagination, it's a detail page
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


def score_image_relevance(
    item: ImageItem,
    keyword: str,
    entity_tokens: list[str] | None = None,
    seed_urls: set[str] | None = None,
    domain_profiles: dict | None = None,
) -> int:
    text = safe_join(
        [item.url, item.source_page, item.alt_text, item.page_title]
    ).lower()
    score = weighted_subject_score(text, keyword, entity_tokens)
    if item.alt_text:
        score += 1
    if item.page_title:
        score += 1
    if any(term in text for term in GENERIC_ASSET_TERMS):
        score -= 3
    if any(token in text for token in {"captcha", "blank", "placeholder", "spacer"}):
        score -= 4
    score -= _preview_penalty(text)
    if any(
        token in text
        for token in {"photo", "image", "gallery", "media", "post"}
    ):
        score += 1
    if is_probable_image(item.url):
        score += 2
    if re.search(r"(?:^|[?&])(width|height|w|h)=\d{1,3}(?:$|&)", item.url, re.I):
        score -= 3

    if getattr(item, "in_layout_container", False):
        score -= 20

    if item.width is not None and item.width < 300:
        score -= 20
    if item.height is not None and item.height < 300:
        score -= 20

    # Boost when domain profile expects exactly this media type
    if domain_profiles:
        source_host = urlparse(item.source_page).netloc.lower()
        profile = domain_profiles.get(source_host)
        if profile and profile.media_type == "image":
            score += 3

    # Skip archive/index penalty if this page was explicitly seeded (depth-0 entry point)
    # or if the asset itself comes from a known CDN host.
    explicitly_seeded = seed_urls and item.source_page in seed_urls
    cdn_asset = is_cdn_asset_domain(
        item.url,
        allow_hosts=_get_allowed_hosts(domain_profiles),
    )
    if (
        not explicitly_seeded
        and not cdn_asset
        and is_archive_or_index_page(item.source_page, item.page_title)
    ):
        asset_text = safe_join(
            [
                item.url,
                item.alt_text,
                getattr(item, "parent_anchor_text", ""),
                getattr(item, "parent_anchor_href", ""),
            ]
        ).lower()
        if not contains_subject_text(asset_text, keyword, entity_tokens):
            score -= 15

    return score


def score_video_relevance(
    item: VideoItem,
    keyword: str,
    entity_tokens: list[str] | None = None,
    seed_urls: set[str] | None = None,
    domain_profiles: dict | None = None,
) -> int:
    text = safe_join([item.url, item.source_page, item.type, item.page_title]).lower()
    score = weighted_subject_score(text, keyword, entity_tokens)
    if item.page_title:
        score += 1
    if item.type in {"youtube", "vimeo", "direct", "hls", "dash"}:
        score += 2
    if any(
        token in text
        for token in {
            "video",
            "clip",
            "embed",
            "watch",
            "movie",
            "stream",
            "media",
            "post",
        }
    ):
        score += 1
    if is_probable_video(item.url):
        score += 2

    if getattr(item, "in_layout_container", False):
        score -= 20

    # Apply preview penalty to the video URL itself
    score -= _preview_penalty(item.url.lower())

    # Apply a minor penalty if the page title or source page contains preview markers
    context_text = safe_join([item.source_page, item.page_title]).lower()
    if _preview_penalty(context_text) >= 4:
        score -= 2

    # Boost when domain profile expects exactly this media type
    if domain_profiles:
        source_host = urlparse(item.source_page).netloc.lower()
        profile = domain_profiles.get(source_host)
        if profile and profile.media_type == "video":
            score += 3

    # Skip archive/index penalty if this page was explicitly seeded or asset is from a CDN.
    explicitly_seeded = seed_urls and item.source_page in seed_urls
    cdn_asset = is_cdn_asset_domain(
        item.url,
        allow_hosts=_get_allowed_hosts(domain_profiles),
    )
    if (
        not explicitly_seeded
        and not cdn_asset
        and is_archive_or_index_page(item.source_page, item.page_title)
    ):
        asset_text = safe_join(
            [
                item.url,
                getattr(item, "parent_anchor_text", ""),
                getattr(item, "parent_anchor_href", ""),
            ]
        ).lower()
        if not contains_subject_text(asset_text, keyword, entity_tokens):
            score -= 15

    return score


def has_low_res_query_param(url: str, min_size: int = 400) -> bool:
    for match in re.finditer(r"(?:^|[?&])(width|height|w|h)=(\d+)", url, re.I):
        try:
            val = int(match.group(2))
            if val < min_size:
                return True
        except ValueError:
            pass
    return False


def has_low_res_path_pattern(
    url: str, min_width: int = 400, min_height: int = 300
) -> bool:
    try:
        path = urlparse(url).path.lower()
    except Exception:
        return False

    # 1. Double dimensions matching: e.g. -150x150, _200x300, /150x150/
    double_dim_match = re.search(r"[-_/](\d+)x(\d+)\b", path)
    if double_dim_match:
        try:
            w = int(double_dim_match.group(1))
            h = int(double_dim_match.group(2))
            if w < min_width or h < min_height:
                return True
        except ValueError:
            pass

    # 2. Resizer paths matching: e.g. /w_150,h_150/ or /w_150/h_150/ or /resize/150/150/
    resizer_match1 = re.search(r"/(?:resize|fit|crop)/(\d+)/(\d+)", path)
    if resizer_match1:
        try:
            w = int(resizer_match1.group(1))
            h = int(resizer_match1.group(2))
            if w < min_width or h < min_height:
                return True
        except ValueError:
            pass

    resizer_match2 = re.search(r"/(?:w|width)_?(\d+)[,/](?:h|height)_?(\d+)", path)
    if resizer_match2:
        try:
            w = int(resizer_match2.group(1))
            h = int(resizer_match2.group(2))
            if w < min_width or h < min_height:
                return True
        except ValueError:
            pass

    # 3. Single dimension matching ending in extension: e.g. _150x.jpg or _x150.jpg
    single_w_match = re.search(r"[-_](\d+)x\.[a-z0-9]{3,4}$", path)
    if single_w_match:
        try:
            w = int(single_w_match.group(1))
            if w < min_width:
                return True
        except ValueError:
            pass

    single_h_match = re.search(r"[-_]x(\d+)\.[a-z0-9]{3,4}$", path)
    if single_h_match:
        try:
            h = int(single_h_match.group(1))
            if h < min_height:
                return True
        except ValueError:
            pass

    return False




# ---------------------------------------------------------------------------
# G1: Module-level mtime-cached loader for highres_transforms in domain_config.json.
# Prevents one disk-read per image download — reads once and re-reads only when
# the file changes on disk.
# ---------------------------------------------------------------------------
_HIGHRES_CFG_CACHE: dict = {}
_HIGHRES_CFG_MTIME: float = 0.0
_HIGHRES_CFG_PATH: _Path | None = None


def _get_highres_transforms() -> dict:
    """Return the highres_transforms section of domain_config.json, mtime-cached.

    Cache invalidation is based on file mtime. When mtime is unavailable (file
    absent from the real FS but Path.read_text may be monkeypatched in tests),
    we attempt a direct read so the test isolation layer still works.
    """
    global _HIGHRES_CFG_CACHE, _HIGHRES_CFG_MTIME, _HIGHRES_CFG_PATH
    if _HIGHRES_CFG_PATH is None:
        p = _Path("data/domain_config.json")
        if not p.exists():
            p = _Path(__file__).resolve().parent.parent.parent / "data" / "domain_config.json"
        _HIGHRES_CFG_PATH = p
    try:
        mtime = _os.path.getmtime(str(_HIGHRES_CFG_PATH))
        if mtime != _HIGHRES_CFG_MTIME:
            raw = _json.loads(_HIGHRES_CFG_PATH.read_text(encoding="utf-8"))
            _HIGHRES_CFG_CACHE = raw.get("highres_transforms", {})
            _HIGHRES_CFG_MTIME = mtime
    except OSError:
        # File absent on real FS — but Path.read_text may be monkeypatched
        # (e.g. in tests). Attempt a direct read and cache the result.
        try:
            raw = _json.loads(_HIGHRES_CFG_PATH.read_text(encoding="utf-8"))
            _HIGHRES_CFG_CACHE = raw.get("highres_transforms", {})
        except Exception:
            pass
    except Exception:
        pass
    return _HIGHRES_CFG_CACHE


def _reset_highres_cache() -> None:
    """Reset the mtime-cache so the next call to _get_highres_transforms() re-reads
    the file from disk. Intended for use in tests that monkeypatch Path.read_text."""
    global _HIGHRES_CFG_CACHE, _HIGHRES_CFG_MTIME, _HIGHRES_CFG_PATH
    _HIGHRES_CFG_CACHE = {}
    _HIGHRES_CFG_MTIME = 0.0
    _HIGHRES_CFG_PATH = None


def transform_to_highres(url: str) -> tuple[str, str]:
    """
    Attempt to heuristically upscale a URL from a thumbnail to its original high-res version.
    Returns (upscaled_url, original_url).
    """
    original = url
    try:
        parsed = urlparse(url)
        path = parsed.path
        query = parsed.query
        host = parsed.netloc.lower()

        # Domain-specific highres transforms — loaded once via mtime-cache
        _dc = _get_highres_transforms()
        for _rg in _dc.values():
            if any(p in host for p in _rg.get("host_contains", [])):
                for _rule in _rg.get("rules", []):
                    if _rule.get("target") == "path":
                        path = re.sub(_rule["pattern"], _rule["replacement"], path, flags=re.I)

        # WordPress / generic style dimension pattern e.g. -150x150.jpg, -300x200.jpg, -1024x768.png, -scaled.jpg
        wp_match = re.search(r"(-\d{2,4}x\d{2,4}|-scaled)(\.[a-zA-Z0-9]{3,4})$", path, re.I)
        if wp_match:
            path = path[: wp_match.start(1)] + wp_match.group(2)

        # _thumb or .thumb suffix
        thumb_match = re.search(r"([._-]thumb(?:nail)?s?|\.thumb)(\.[a-zA-Z0-9]{3,4})$", path, re.I)
        if thumb_match:
            path = path[: thumb_match.start(1)] + thumb_match.group(2)

        # Generic path directory replacements
        path = re.sub(r"/(?:thumbs|preview|previews|thumbnails)/", "/images/", path, flags=re.I)
        path = re.sub(r"/video_thumbs/", "/video_sources/", path, flags=re.I)

        # 7. Twitter name=small / name=medium -> name=large
        if "name=small" in query:
            query = query.replace("name=small", "name=large")
        elif "name=medium" in query:
            query = query.replace("name=medium", "name=large")

        # Combine
        if path != parsed.path or query != parsed.query:
            upscaled = urlunparse(parsed._replace(path=path, query=query))
            return upscaled, original

    except Exception:
        pass

    return url, url


def rejection_reason_for_image(
    item: ImageItem,
    keyword: str,
    entity_tokens: list[str] | None = None,
    seed_urls: set[str] | None = None,
    domain_profiles: dict | None = None,
) -> str | None:
    text = safe_join(
        [item.url, item.source_page, item.alt_text, item.page_title]
    ).lower()

    # Check thumbnail prefix pattern early to classify as preview_or_thumbnail
    if domain_profiles:
        source_host = urlparse(item.source_page).netloc.lower()
        item_host = urlparse(item.url).netloc.lower()
        for host in (source_host, item_host):
            profile = domain_profiles.get(host)
            if profile:
                thumb_pattern = getattr(profile, "thumbnail_prefix_pattern", None)
                if thumb_pattern:
                    try:
                        if re.search(thumb_pattern, item.url):
                            return "preview_or_thumbnail"
                    except Exception:
                        pass

    score = score_image_relevance(
        item, keyword, entity_tokens, seed_urls, domain_profiles
    )

    # Wrong media type for this domain
    if not media_type_matches_domain_expectation(item, domain_profiles):
        return "wrong_media_type_for_domain"

    if getattr(item, "in_layout_container", False):
        return "layout_decoration"

    if item.width is not None and item.width < 300:
        return "low_resolution"
    if item.height is not None and item.height < 300:
        return "low_resolution"

    # Skip index-page rejection for explicitly seeded pages or CDN asset URLs.
    explicitly_seeded = seed_urls and item.source_page in seed_urls
    cdn_asset = is_cdn_asset_domain(
        item.url,
        allow_hosts=_get_allowed_hosts(domain_profiles),
    )
    if (
        not explicitly_seeded
        and not cdn_asset
        and is_archive_or_index_page(item.source_page, item.page_title)
    ):
        asset_text = safe_join(
            [
                item.url,
                item.alt_text,
                getattr(item, "parent_anchor_text", ""),
                getattr(item, "parent_anchor_href", ""),
            ]
        ).lower()
        if not contains_subject_text(
            asset_text, keyword, entity_tokens, _aliases_for(item.source_page, domain_profiles)
        ):
            return "low_subject_relevance"

    # Hard-reject only unambiguous site-chrome (UTILITY_ASSET_TERMS).
    # GENERIC_ASSET_TERMS items are soft-penalty only (score -3 in score_image_relevance).
    if any(term in text for term in UTILITY_ASSET_TERMS):
        return "generic_asset"
    if any(token in text for token in {"captcha", "blank", "placeholder", "spacer"}):
        return "placeholder_asset"
    if _preview_penalty(text) >= 6:
        return "preview_or_thumbnail"
    if has_low_res_query_param(item.url, min_size=300) or has_low_res_path_pattern(
        item.url, min_width=300, min_height=250
    ):
        return "low_resolution_hint"
    if not contains_subject_text(
        text, keyword, entity_tokens, _aliases_for(item.source_page, domain_profiles)
    ):
        return "low_subject_relevance"
    if score < 1:
        return "low_score"
    return None


def rejection_reason_for_video(
    item: VideoItem,
    keyword: str,
    entity_tokens: list[str] | None = None,
    seed_urls: set[str] | None = None,
    domain_profiles: dict | None = None,
) -> str | None:
    text = safe_join([item.url, item.source_page, item.type, item.page_title]).lower()
    score = score_video_relevance(
        item, keyword, entity_tokens, seed_urls, domain_profiles
    )

    # Wrong media type for this domain
    if not media_type_matches_domain_expectation(item, domain_profiles):
        return "wrong_media_type_for_domain"

    if getattr(item, "in_layout_container", False):
        return "layout_decoration"

    # Skip index-page rejection for explicitly seeded pages or CDN asset URLs.
    explicitly_seeded = seed_urls and item.source_page in seed_urls
    cdn_asset = is_cdn_asset_domain(
        item.url,
        allow_hosts=_get_allowed_hosts(domain_profiles),
    )
    if (
        not explicitly_seeded
        and not cdn_asset
        and is_archive_or_index_page(item.source_page, item.page_title)
    ):
        asset_text = safe_join(
            [
                item.url,
                getattr(item, "parent_anchor_text", ""),
                getattr(item, "parent_anchor_href", ""),
            ]
        ).lower()
        if not contains_subject_text(
            asset_text, keyword, entity_tokens, _aliases_for(item.source_page, domain_profiles)
        ):
            return "low_subject_relevance"

    if any(token in text for token in {"captcha", "blank", "placeholder", "spacer"}):
        return "placeholder_asset"
    if _preview_penalty(item.url.lower()) >= 6:
        return "preview_or_thumbnail"
    if not contains_subject_text(
        text, keyword, entity_tokens, _aliases_for(item.source_page, domain_profiles)
    ):
        return "low_subject_relevance"
    if score < 1:
        return "low_score"
    return None


def _aliases_for(source_page: str, domain_profiles: dict | None) -> list[str] | None:
    """Return the seed-derived subject aliases for the host of source_page."""
    if not domain_profiles:
        return None
    host = urlparse(source_page).netloc.lower()
    profile = domain_profiles.get(host)
    if not profile:
        return None
    aliases = getattr(profile, "subject_aliases", None)
    return aliases or None


def should_keep_image(
    item: ImageItem,
    keyword: str,
    entity_tokens: list[str] | None = None,
    seed_urls: set[str] | None = None,
    domain_profiles: dict | None = None,
) -> bool:
    return (
        rejection_reason_for_image(
            item, keyword, entity_tokens, seed_urls, domain_profiles
        )
        is None
    )


def should_keep_video(
    item: VideoItem,
    keyword: str,
    entity_tokens: list[str] | None = None,
    seed_urls: set[str] | None = None,
    domain_profiles: dict | None = None,
) -> bool:
    return (
        rejection_reason_for_video(
            item, keyword, entity_tokens, seed_urls, domain_profiles
        )
        is None
    )


def normalize_media_url(url: str) -> str:
    """Normalize a media URL for deduplication check by stripping query params and scheme differences.

    Percent-encoded paths are decoded before comparison so that URLs differing
    only in encoding (e.g. space vs %20) are treated as the same asset.
    """
    from urllib.parse import unquote

    try:
        parsed = urlparse(url.strip())
        scheme = "https"
        netloc = parsed.netloc.lower()
        # Decode percent-encoding, then normalise case and trailing slash
        path = unquote(parsed.path).lower().rstrip("/")
        return f"{scheme}://{netloc}{path}"
    except Exception:
        return url.strip()
