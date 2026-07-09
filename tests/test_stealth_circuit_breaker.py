import pytest
from unittest.mock import MagicMock
from utils.http_client import HttpClient, ScraperBypassError


def test_stealth_circuit_breaker(monkeypatch):
    client = HttpClient()

    # Reset state to ensure clean test
    HttpClient._stealth_failed_hosts.clear()
    HttpClient._stealth_required_hosts.clear()

    # Mock _get_with_crawl4ai to fail
    def mock_get_with_crawl4ai(url):
        raise Exception("Mocked Crawl4AI browser failure")

    monkeypatch.setattr(client, "_get_with_crawl4ai", mock_get_with_crawl4ai)

    # Mock rate limiter wait to prevent delay
    client._rate_limiter_for("https://protected-site.com").wait = MagicMock()

    # Mock httpx.Client.get to return a 403 to trigger Crawl4AI fallback
    import httpx

    mock_resp = httpx.Response(
        status_code=403, request=httpx.Request("GET", "https://protected-site.com")
    )
    monkeypatch.setattr(client.client, "get", MagicMock(return_value=mock_resp))

    # First attempt: should hit WAF, fall back to Crawl4AI, fail, and raise ScraperBypassError
    with pytest.raises(ScraperBypassError) as exc_info:
        client.get("https://protected-site.com/page1")

    assert "Crawl4AI fallback failed" in str(exc_info.value)

    # The host should now be in _stealth_failed_hosts
    assert "protected-site.com" in HttpClient._stealth_failed_hosts

    # Second attempt: should immediately fail-fast with ScraperBypassError without calling Crawl4AI or httpx
    mock_get_with_crawl4ai_spy = MagicMock()
    monkeypatch.setattr(client, "_get_with_crawl4ai", mock_get_with_crawl4ai_spy)
    client.client.get = MagicMock()

    with pytest.raises(ScraperBypassError) as exc_info2:
        client.get("https://protected-site.com/page2")

    assert "previously failed all stealth fallback tiers" in str(exc_info2.value)
    mock_get_with_crawl4ai_spy.assert_not_called()
    client.client.get.assert_not_called()
