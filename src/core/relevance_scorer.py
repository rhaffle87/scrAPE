"""
relevance_scorer.py — Relevance Scoring and Text Matching Engine.

Computes keyword relevance scores for images and videos based on page context,
alt text, titles, URLs, and fuzzy token matching.
"""

from __future__ import annotations

import re
from urllib.parse import urlparse

from config import (
    GENERIC_ASSET_TERMS,
    PREVIEW_MARKERS,
    UTILITY_ASSET_TERMS,
)
from core.models import ImageItem, VideoItem
from core.url_classifier import (
    _aliases_for,
    _get_allowed_hosts,
    is_archive_or_index_page,
    is_cdn_asset_domain,
    is_probable_image,
    is_probable_video,
    safe_join,
)

__all__ = [
    "normalize_token",
    "keyword_tokens",
    "subject_tokens",
    "weighted_subject_score",
    "contains_subject_text",
    "score_image_relevance",
    "score_video_relevance",
]


def normalize_token(value: str) -> str:
    """Normalize a token string by lowercasing and stripping non-alphanumeric chars."""
    return re.sub(r"[^\w]", "", value.lower())


def keyword_tokens(keyword: str | set | list) -> set[str]:
    """Tokenize a search keyword (or set/list of keywords) into a normalized set of words."""
    if isinstance(keyword, (set, list)):
        tokens = set()
        for item in keyword:
            tokens.update(keyword_tokens(item))
        return tokens
    if not isinstance(keyword, str):
        return set()
    return {normalize_token(t) for t in keyword.split() if normalize_token(t)}


def subject_tokens(keyword: str | set | list, entity_tokens: list[str] | None = None) -> set[str]:
    """Combine search keyword tokens with optional extra entity alias tokens."""
    tokens = keyword_tokens(keyword)
    if entity_tokens:
        for et in entity_tokens:
            tokens.update(keyword_tokens(et))
    return tokens


def weighted_subject_score(
    text: str,
    keyword: str | set | list,
    entity_tokens: list[str] | None = None,
    subject_aliases: list[str] | None = None,
) -> int:
    """Calculate weighted match score between text context and subject/aliases."""
    if not text:
        return 0
    tokens = subject_tokens(keyword, entity_tokens)
    if subject_aliases:
        for alias in subject_aliases:
            tokens.update(keyword_tokens(alias))
    if not tokens:
        return 0
    score = 0
    for token in tokens:
        if token in text:
            score += 2
        elif len(token) > 3 and token in text:
            score += 1
    return score


def contains_subject_text(
    text: str,
    keyword: str | set | list,
    entity_tokens: list[str] | None = None,
    subject_aliases: list[str] | None = None,
) -> bool:
    """Check if text contains the subject string or any alias."""
    return weighted_subject_score(text, keyword, entity_tokens, subject_aliases) > 0


def _preview_penalty(text: str) -> int:
    """Calculate penalty points for preview/sample/thumbnail indicators in text."""
    return sum(6 for marker in PREVIEW_MARKERS if marker in text)


def score_image_relevance(
    item: ImageItem,
    keyword: str | set | list,
    entity_tokens: list[str] | None = None,
    seed_urls: set[str] | None = None,
    domain_profiles: dict | None = None,
) -> int:
    """Calculate relevance score for an image asset against search keyword."""
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

    if domain_profiles:
        source_host = urlparse(item.source_page).netloc.lower()
        profile = domain_profiles.get(source_host)
        if profile and getattr(profile, "media_type", None) == "image":
            score += 3

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
    keyword: str | set | list,
    entity_tokens: list[str] | None = None,
    seed_urls: set[str] | None = None,
    domain_profiles: dict | None = None,
) -> int:
    """Calculate relevance score for a video asset against search keyword."""
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

    score -= _preview_penalty(item.url.lower())

    context_text = safe_join([item.source_page, item.page_title]).lower()
    if _preview_penalty(context_text) >= 4:
        score -= 2

    if domain_profiles:
        source_host = urlparse(item.source_page).netloc.lower()
        profile = domain_profiles.get(source_host)
        if profile and getattr(profile, "media_type", None) == "video":
            score += 3

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
