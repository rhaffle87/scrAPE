"""
test_flaresolverr_docker_opt.py — Unit tests for FlareSolverr container integration & post-run optimizations.
"""

from __future__ import annotations

import pytest
from core.filters import is_search_page_url, transform_to_highres
from utils.http_client import HttpClient


def test_is_search_page_url_query_params():
    assert is_search_page_url("https://vimeo.com/search?q=apple") is True
    assert is_search_page_url("https://www.flickr.com/search/?text=apple") is True
    assert is_search_page_url("https://www.youtube.com/results?search_query=apple") is True
    assert is_search_page_url("https://epawg.com/search/meenfox/") is True
    assert is_search_page_url("https://example.com/posts/123") is False


def test_transform_to_highres_erome_and_wordpress():
    # Erome thumbnail replacement
    erome_thumb = "https://www.erome.com/t/12345/image.jpg"
    upscaled_erome, _ = transform_to_highres(erome_thumb)
    assert "/v/" in upscaled_erome

    # WordPress -scaled replacement
    wp_scaled = "https://example.com/wp-content/uploads/2026/07/photo-scaled.jpg"
    upscaled_wp, _ = transform_to_highres(wp_scaled)
    assert upscaled_wp == "https://example.com/wp-content/uploads/2026/07/photo.jpg"


def test_flaresolverr_endpoint_initialization():
    from config import FLARESOLVERR_URL
    assert "127.0.0.1" in FLARESOLVERR_URL
