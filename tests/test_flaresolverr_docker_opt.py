"""
test_flaresolverr_docker_opt.py — Unit tests for FlareSolverr container integration & post-run optimizations.
"""

from __future__ import annotations

import pytest
from core.filters import is_search_page_url, transform_to_highres
from network.http_client import HttpClient


def test_is_search_page_url_query_params():
    assert is_search_page_url("https://example.com/search?q=subject") is True
    assert is_search_page_url("https://www.example.com/search/?text=subject") is True
    assert is_search_page_url("https://www.example.com/results?search_query=subject") is True
    assert is_search_page_url("https://example.com/search/subject/") is True
    assert is_search_page_url("https://example.com/posts/123") is False


def test_transform_to_highres_domain_config_and_wordpress(monkeypatch):
    import json
    
    mock_config = {
        "highres_transforms": {
            "booru": {
                "host_contains": ["rule34", "booru"],
                "rules": [
                    {"pattern": r"\.pic\d+\.(jpe?g|png|webp)$", "replacement": r".\1", "target": "path"}
                ]
            }
        }
    }
    
    def mock_exists(self):
        return True
        
    def mock_read_text(self, encoding=None):
        return json.dumps(mock_config)
        
    import pathlib
    monkeypatch.setattr(pathlib.Path, "exists", mock_exists)
    monkeypatch.setattr(pathlib.Path, "read_text", mock_read_text)

    # Domain-config-driven thumbnail replacement (loaded from data/domain_config.json)
    # Uses a booru-style URL since that pattern is in highres_transforms
    booru_thumb = "https://rule34.example.com/images/sample.pic256.jpg"
    upscaled_booru, _ = transform_to_highres(booru_thumb)
    assert upscaled_booru == "https://rule34.example.com/images/sample.jpg"

    # WordPress -scaled replacement
    wp_scaled = "https://example.com/wp-content/uploads/2026/07/photo-scaled.jpg"
    upscaled_wp, _ = transform_to_highres(wp_scaled)
    assert upscaled_wp == "https://example.com/wp-content/uploads/2026/07/photo.jpg"


def test_flaresolverr_endpoint_initialization():
    from config import FLARESOLVERR_URL
    assert "127.0.0.1" in FLARESOLVERR_URL
