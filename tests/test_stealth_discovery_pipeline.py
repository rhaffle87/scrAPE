"""
test_stealth_discovery_pipeline.py — Integration test suite for multi-engine discovery & session persistence.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

import pytest
from utils.session import SessionManager
from frontend.app import app, DiscoverSeedPayload, discover_search_urls


def test_session_manager_persistence_and_eviction():
    """Test saving, loading, and evicting sticky domain session cookies."""
    sm = SessionManager()
    test_domain = "test_stealth_domain.com"
    dummy_cookies = {"cf_clearance": "dummy_token_123", "session_id": "xyz456"}

    # 1. Save session
    sm.save_session(test_domain, dummy_cookies)
    loaded = sm.load_session(test_domain)
    assert loaded == dummy_cookies

    # 2. Evict session
    sm.evict_session(test_domain)
    loaded_after = sm.load_session(test_domain)
    assert loaded_after is None


def test_multi_engine_discovery_probe_live_graceful():
    """Test /api/seeds/discover endpoint with multi-engine probe matrix and graceful network fallback."""
    import asyncio
    from unittest.mock import patch
    import httpx
    
    payload = DiscoverSeedPayload(
        query="test_subject",
        domains=["wallhaven.cc", "deviantart.com"]
    )
    
    with patch("src.utils.http_client.HttpClient.get") as mock_get:
         
        mock_resp = httpx.Response(200, request=httpx.Request("GET", "https://example.com"))
        mock_get.return_value = mock_resp
        
        result = asyncio.run(discover_search_urls(payload))
        
        assert "discovered_urls" in result
        assert "tested_count" in result
        assert "valid_count" in result
        tested_cnt = result["tested_count"]
        assert isinstance(tested_cnt, int) and tested_cnt > 0
        assert isinstance(result["discovered_urls"], list)
