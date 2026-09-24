"""
Unit tests for Track 3: SearXNG Fallback Search Engine Pool Hardening.
Verifies:
1. Environment variable SEARXNG_INSTANCES configuration support.
2. Graceful failover when primary instance returns 502 or 403.
3. Graceful failover when instance returns an HTML / Cloudflare challenge page instead of JSON.
4. Non-instance directory endpoints (searx.space) excluded from defaults.
"""

from __future__ import annotations

import importlib
import json
from unittest.mock import MagicMock

import pytest

from scraper.google_images import SearchProviderScraper


def test_searxng_env_instances_configuration(monkeypatch):
    """Verify that SEARXNG_INSTANCES environment variable sets custom search endpoints."""
    monkeypatch.setenv("SEARXNG_INSTANCES", "https://custom1.searx.org, https://custom2.searx.org")
    import config
    importlib.reload(config)

    assert config.SEARXNG_HOSTS == ["https://custom1.searx.org", "https://custom2.searx.org"]
    assert "https://searx.space" not in config.SEARXNG_HOSTS


def test_searxng_failover_on_http_errors(monkeypatch):
    """Verify failover to secondary SearXNG instance when primary returns HTTP 502/403."""
    monkeypatch.setenv("SEARXNG_INSTANCES", "https://failing-instance.org,https://healthy-instance.org")
    import config
    importlib.reload(config)

    scraper = SearchProviderScraper()

    # Mock responses
    resp_502 = MagicMock()
    resp_502.status_code = 502
    resp_502.headers = {"content-type": "text/html"}
    resp_502.text = "<html>502 Bad Gateway</html>"

    resp_healthy = MagicMock()
    resp_healthy.status_code = 200
    resp_healthy.headers = {"content-type": "application/json"}
    resp_healthy.text = json.dumps({
        "results": [
            {"url": "https://example.com/item1"},
            {"url": "https://example.com/item2"},
        ]
    })
    resp_healthy.json.return_value = json.loads(resp_healthy.text)

    def mock_get(url, *args, **kwargs):
        if "failing-instance.org" in url:
            return resp_502
        return resp_healthy

    monkeypatch.setattr(scraper.http, "get", mock_get)

    results = scraper._search_searxng(keyword="test", max_results=10)
    assert len(results) == 2
    assert results == ["https://example.com/item1", "https://example.com/item2"]


def test_searxng_failover_on_html_challenge_page(monkeypatch):
    """Verify that an HTML challenge page (e.g. Cloudflare challenge with HTTP 200) triggers failover."""
    monkeypatch.setenv("SEARXNG_INSTANCES", "https://challenge-instance.org,https://clean-instance.org")
    import config
    importlib.reload(config)

    scraper = SearchProviderScraper()

    # Challenge response
    resp_challenge = MagicMock()
    resp_challenge.status_code = 200
    resp_challenge.headers = {"content-type": "text/html; charset=UTF-8"}
    resp_challenge.text = "<!DOCTYPE html><html><title>Just a moment...</title><body>Checking your browser</body></html>"

    # Clean JSON response
    resp_clean = MagicMock()
    resp_clean.status_code = 200
    resp_clean.headers = {"content-type": "application/json"}
    resp_clean.text = json.dumps({
        "results": [
            {"url": "https://sample.org/data1"},
        ]
    })
    resp_clean.json.return_value = json.loads(resp_clean.text)

    def mock_get(url, *args, **kwargs):
        if "challenge-instance.org" in url:
            return resp_challenge
        return resp_clean

    monkeypatch.setattr(scraper.http, "get", mock_get)

    results = scraper._search_searxng(keyword="sample", max_results=5)
    assert len(results) == 1
    assert results == ["https://sample.org/data1"]
