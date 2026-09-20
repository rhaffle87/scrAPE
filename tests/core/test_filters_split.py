"""
tests/test_filters_split.py
Unit tests verifying the core/filters 3-way split:
  - core.url_classifier
  - core.relevance_scorer
  - core.media_filter
  - core.filters backward-compatibility re-export shim
"""
from __future__ import annotations

from core.url_classifier import is_search_page_url, normalize_url
from core.relevance_scorer import score_image_relevance, weighted_subject_score
from core.media_filter import transform_to_highres, should_keep_image
import core.filters as filters_shim


def test_direct_submodule_imports():
    """Verify direct imports from url_classifier, relevance_scorer, and media_filter."""
    assert is_search_page_url("https://example.com/search?q=test") is True
    assert normalize_url("https://example.com/page?utm_source=test") == "https://example.com/page"
    assert weighted_subject_score("cat photo", "cat") > 0.0
    upscaled, _ = transform_to_highres("https://example.com/wp-content/uploads/2026/01/image-150x150.jpg")
    assert upscaled == "https://example.com/wp-content/uploads/2026/01/image.jpg"


def test_filters_shim_reexports_all_symbols():
    """Verify that core.filters re-exports all symbols from submodules."""
    expected_symbols = [
        "is_search_page_url",
        "normalize_url",
        "safe_join",
        "weighted_subject_score",
        "score_image_relevance",
        "transform_to_highres",
        "should_keep_image",
        "should_keep_video",
    ]
    for symbol in expected_symbols:
        assert hasattr(filters_shim, symbol), (
            f"core.filters shim is missing re-exported symbol '{symbol}'"
        )
