"""
filters.py — Backward-compatible re-export shim for core filter modules.
# ruff: noqa: F405

Re-exports all public symbols from:
  - core.url_classifier (URL normalization, search/archive page detection, domain rules)
  - core.relevance_scorer (Relevance scoring, keyword matching)
  - core.media_filter (Media acceptance filters, high-res URL transformation)
"""

from __future__ import annotations

from core.url_classifier import *  # noqa: F403
from core.relevance_scorer import *  # noqa: F403
from core.media_filter import *  # noqa: F403

__all__ = [
    # url_classifier
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
    # relevance_scorer
    "normalize_token",
    "keyword_tokens",
    "subject_tokens",
    "weighted_subject_score",
    "contains_subject_text",
    "score_image_relevance",
    "score_video_relevance",
    # media_filter
    "has_low_res_query_param",
    "has_low_res_path_pattern",
    "transform_to_highres",
    "rejection_reason_for_image",
    "rejection_reason_for_video",
    "should_keep_image",
    "should_keep_video",
    "_reset_highres_cache",
]
