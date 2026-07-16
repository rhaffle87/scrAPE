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


def test_fallback_cookie_sync_and_locking(monkeypatch):
    client = HttpClient()
    host = "test-sync-site.com"
    url = f"https://{host}/page"

    # Reset state to ensure clean test
    HttpClient._stealth_failed_hosts.clear()
    HttpClient._stealth_required_hosts.clear()

    # Pre-populate session with a cookie
    client.session_manager.save_session(host, {"pre_existing": "value"})

    # Mock _run_coroutine_sync to mock crawler execution
    def mock_run_coroutine_sync(coro):
        # We simulate the inner _run_crawler function behavior
        # Close the coroutine to avoid RuntimeWarning
        coro.close()
        # Return a mock HTML and mock browser cookies list
        return "<html>Clean Page</html>", [
            {"name": "cf_clearance", "value": "solved_token", "domain": host},
            {"name": "new_session", "value": "active_val", "domain": host},
        ]

    monkeypatch.setattr(
        "utils.http_client._run_coroutine_sync", mock_run_coroutine_sync
    )

    # Trigger directly
    html, cookies = client._get_with_crawl4ai(url)
    assert "Clean Page" in html
    assert len(cookies) == 2

    # Check that domain locks are created dynamically
    assert host in client._domain_fallback_locks
    lock = client._fallback_lock_for(host)
    assert lock is not None

    # Check cookies syncing back to SessionManager and SessionPool
    import httpx

    # Trigger through standard get fallback (on 403)
    mock_resp = httpx.Response(status_code=403, request=httpx.Request("GET", url))
    monkeypatch.setattr(client.client, "get", MagicMock(return_value=mock_resp))
    client._rate_limiter_for(url).wait = MagicMock()

    resp = client.get(url)
    assert resp.status_code == 200
    assert resp.text == "<html>Clean Page</html>"

    # Verify cookies in SessionManager
    saved = client.session_manager.load_session(host)
    assert saved.get("cf_clearance") == "solved_token"
    assert saved.get("new_session") == "active_val"

    # Verify cookies in SessionPool (active session)
    session = client._session_pool.get_session(host)
    assert session.cookies.get("cf_clearance") == "solved_token"
    assert session.cookies.get("new_session") == "active_val"
