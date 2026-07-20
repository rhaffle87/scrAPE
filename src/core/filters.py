from __future__ import annotations

import re
from urllib.parse import urljoin, urlparse, urlunparse

from config import (
    DASH_EXTENSIONS,
    GENERIC_ASSET_TERMS,
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
        # Re-quote path and query parameters to ensure canonical escaping
        quoted_path = quote(parsed.path, safe="/")
        quoted_query = quote(parsed.query, safe="=&%")
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
    try:
        path = urlparse(url).path.lower()
    except Exception:
        path = ""
    # Booru-style picN thumbnails (pic256, pic512, etc.)
    if re.search(r"\.pic\d+\.jpe?g", path):
        return True
    # WordPress/CDN dimensions suffix (e.g. -320x180.jpg)
    if re.search(r"-\d+x\d+\.(?:jpe?g|png|gif|webp|avif)$", path):
        return True
    # Common thumbnail patterns
    if any(marker in path for marker in PREVIEW_MARKERS):
        return True
    # loading.gif placeholders
    if path.endswith("/loading.gif"):
        return True
    # erothots / erocdn preview thumbnails (e.g. /thumbs/ or /thumb_ in path)
    if re.search(r"/thumbs?[_/]", path):
        return True
    # erocdn low-res poster images
    url_lower = url.lower()
    if "erocdn" in url_lower and re.search(r"_(?:poster|thumb|preview|small)\.", path):
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


def weighted_subject_score(
    text: str, keyword: str, entity_tokens: list[str] | None = None
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
    return score


def contains_subject_text(
    text: str, keyword: str, entity_tokens: list[str] | None = None
) -> bool:
    return weighted_subject_score(text, keyword, entity_tokens) > 0


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
                after = path.split(seg, 1)[1].rstrip("/")
                if (
                    "/" in after and after.split("/")[1]
                ):  # depth >= 2 beyond the archive key
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

        # 1. WordPress style -150x150.jpg
        wp_match = re.search(r"(-\d{2,4}x\d{2,4})(\.[a-zA-Z0-9]{3,4})$", path, re.I)
        if wp_match:
            path = path[: wp_match.start(1)] + wp_match.group(2)

        # 2. _thumb suffix
        thumb_match = re.search(r"(_thumb)(\.[a-zA-Z0-9]{3,4})$", path, re.I)
        if thumb_match:
            path = path[: thumb_match.start(1)] + thumb_match.group(2)

        # 3. Twitter name=small -> name=large
        if "name=small" in query:
            query = query.replace("name=small", "name=large")

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
        if not contains_subject_text(asset_text, keyword, entity_tokens):
            return "low_subject_relevance"

    if any(term in text for term in GENERIC_ASSET_TERMS):
        return "generic_asset"
    if any(token in text for token in {"captcha", "blank", "placeholder", "spacer"}):
        return "placeholder_asset"
    if _preview_penalty(text) >= 6:
        return "preview_or_thumbnail"
    if has_low_res_query_param(item.url, min_size=300) or has_low_res_path_pattern(
        item.url, min_width=300, min_height=250
    ):
        return "low_resolution_hint"
    if not contains_subject_text(text, keyword, entity_tokens):
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
        if not contains_subject_text(asset_text, keyword, entity_tokens):
            return "low_subject_relevance"

    if any(token in text for token in {"captcha", "blank", "placeholder", "spacer"}):
        return "placeholder_asset"
    if _preview_penalty(item.url.lower()) >= 6:
        return "preview_or_thumbnail"
    if not contains_subject_text(text, keyword, entity_tokens):
        return "low_subject_relevance"
    if score < 1:
        return "low_score"
    return None


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
