"""
media_filter.py — Media Acceptance Filtering and High-Res Asset Transformation.

Evaluates image/video items against resolution thresholds, quality patterns,
high-res transformation rules, and rejection criteria.
"""

from __future__ import annotations

import json as _json
import os as _os
from pathlib import Path as _Path
import re
from urllib.parse import urlparse, urlunparse

from config import (
    UTILITY_ASSET_TERMS,
)
from core.models import ImageItem, VideoItem
from core.relevance_scorer import (
    _preview_penalty,
    contains_subject_text,
    score_image_relevance,
    score_video_relevance,
)
from core.url_classifier import (
    _aliases_for,
    _get_allowed_hosts,
    is_archive_or_index_page,
    is_cdn_asset_domain,
    media_type_matches_domain_expectation,
    safe_join,
)

LOW_RES_PATH_PATTERNS = [r"/\d+x\d+/", r"-\d+x\d+\.", r"_thumb\.", r"-thumb\.", r"/thumbs/"]
HIGHRES_SUBSTITUTIONS = {"-150x150.": ".", "-300x300.": ".", "-600x600.": "."}

__all__ = [
    "has_low_res_query_param",
    "has_low_res_path_pattern",
    "transform_to_highres",
    "rejection_reason_for_image",
    "rejection_reason_for_video",
    "should_keep_image",
    "should_keep_video",
    "_reset_highres_cache",
]

_HIGHRES_CFG_CACHE: dict = {}
_HIGHRES_CFG_MTIME: float = 0.0
_HIGHRES_CFG_PATH: _Path | None = None


def has_low_res_query_param(url: str, min_size: int = 400) -> bool:
    """Check if URL query string specifies image dimensions smaller than *min_size*."""
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
    """Check if URL path matches common thumbnail or low-resolution filename patterns."""
    try:
        path = urlparse(url).path.lower()
    except Exception:
        return False

    double_dim_match = re.search(r"[-_/](\d+)x(\d+)\b", path)
    if double_dim_match:
        try:
            w = int(double_dim_match.group(1))
            h = int(double_dim_match.group(2))
            if w < min_width or h < min_height:
                return True
        except ValueError:
            pass

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


def _get_highres_transforms() -> dict:
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
        try:
            raw = _json.loads(_HIGHRES_CFG_PATH.read_text(encoding="utf-8"))
            _HIGHRES_CFG_CACHE = raw.get("highres_transforms", {})
        except Exception:
            pass
    except Exception:
        pass
    return _HIGHRES_CFG_CACHE


def _reset_highres_cache() -> None:
    global _HIGHRES_CFG_CACHE, _HIGHRES_CFG_MTIME, _HIGHRES_CFG_PATH
    _HIGHRES_CFG_CACHE = {}
    _HIGHRES_CFG_MTIME = 0.0
    _HIGHRES_CFG_PATH = None


def transform_to_highres(url: str) -> tuple[str, str]:
    """Attempt to heuristically upscale a URL from a thumbnail to its original high-res version."""
    original = url
    try:
        parsed = urlparse(url)
        path = parsed.path
        query = parsed.query
        host = parsed.netloc.lower()

        _dc = _get_highres_transforms()
        for _rg in _dc.values():
            if any(p in host for p in _rg.get("host_contains", [])):
                for _rule in _rg.get("rules", []):
                    if _rule.get("target") == "path":
                        path = re.sub(_rule["pattern"], _rule["replacement"], path, flags=re.I)

        wp_match = re.search(r"(-\d{2,4}x\d{2,4}|-scaled)(\.[a-zA-Z0-9]{3,4})$", path, re.I)
        if wp_match:
            path = path[: wp_match.start(1)] + wp_match.group(2)

        thumb_match = re.search(r"([._-]thumb(?:nail)?s?|\.thumb)(\.[a-zA-Z0-9]{3,4})$", path, re.I)
        if thumb_match:
            path = path[: thumb_match.start(1)] + thumb_match.group(2)

        path = re.sub(r"/(?:thumbs|preview|previews|thumbnails)/", "/images/", path, flags=re.I)
        path = re.sub(r"/video_thumbs/", "/video_sources/", path, flags=re.I)

        if "name=small" in query:
            query = query.replace("name=small", "name=large")
        elif "name=medium" in query:
            query = query.replace("name=medium", "name=large")

        if path != parsed.path or query != parsed.query:
            upscaled = urlunparse(parsed._replace(path=path, query=query))
            return upscaled, original

    except Exception:
        pass
    return original, original


def rejection_reason_for_image(
    item: ImageItem,
    keyword: str | set | list,
    entity_tokens: list[str] | None = None,
    seed_urls: set[str] | None = None,
    domain_profiles: dict | None = None,
) -> str | None:
    text = safe_join(
        [item.url, item.source_page, item.alt_text, item.page_title]
    ).lower()

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

    if not media_type_matches_domain_expectation(item, domain_profiles):
        return "wrong_media_type_for_domain"

    if getattr(item, "in_layout_container", False):
        return "layout_decoration"

    if item.width is not None and item.width < 300:
        return "low_resolution"
    if item.height is not None and item.height < 300:
        return "low_resolution"

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
        
        is_upscaled = False
        upscaled_url, orig = transform_to_highres(item.url)
        if upscaled_url != orig:
            is_upscaled = True
            
        if not is_upscaled and not contains_subject_text(
            asset_text, keyword, entity_tokens, _aliases_for(item.source_page, domain_profiles)
        ):
            return "low_subject_relevance"

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
    keyword: str | set | list,
    entity_tokens: list[str] | None = None,
    seed_urls: set[str] | None = None,
    domain_profiles: dict | None = None,
) -> str | None:
    text = safe_join([item.url, item.source_page, item.type, item.page_title]).lower()
    score = score_video_relevance(
        item, keyword, entity_tokens, seed_urls, domain_profiles
    )

    if not media_type_matches_domain_expectation(item, domain_profiles):
        return "wrong_media_type_for_domain"

    if getattr(item, "in_layout_container", False):
        return "layout_decoration"

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


def should_keep_image(
    item: ImageItem,
    keyword: str | set | list,
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
    keyword: str | set | list,
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
