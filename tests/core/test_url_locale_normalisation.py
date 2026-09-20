"""Regression: normalize_url strips content-neutral locale query params
(hl/lang/locale) so locale variants collapse to one canonical URL."""
from __future__ import annotations

from core.filters import normalize_url


def test_locale_query_params_stripped():
    assert (
        normalize_url("https://example.com/media/0338?hl=ru")
        == "https://example.com/media/0338"
    )
    assert (
        normalize_url("https://example.com/media/0338?lang=en")
        == "https://example.com/media/0338"
    )
    assert (
        normalize_url("https://example.com/media/0338?locale=fr")
        == "https://example.com/media/0338"
    )


def test_non_locale_params_preserved():
    assert (
        normalize_url("https://example.com/page?foo=bar")
        == "https://example.com/page?foo=bar"
    )
    assert (
        normalize_url("https://example.com/page?q=hello")
        == "https://example.com/page?q=hello"
    )


def test_mixed_params():
    # locale stripped, real params kept
    assert (
        normalize_url("https://example.com/media/0338?hl=ru&page=2")
        == "https://example.com/media/0338?page=2"
    )
    assert (
        normalize_url("https://example.com/page?lang=en&id=5")
        == "https://example.com/page?id=5"
    )
