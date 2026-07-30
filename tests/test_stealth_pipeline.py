import pytest
from unittest.mock import MagicMock, patch
import httpx

from network.http_client import HttpClient, ScraperBypassError
from network.stealth_pipeline import (
    StealthPipeline,
    StealthResponse,
    FlareSolverrStrategy,
    _StrategyCircuitBreaker,
)


def test_stealth_response_to_httpx_response():
    s_resp = StealthResponse(
        status_code=200,
        text="<html>Success</html>",
        cookies={"cf_clearance": "123"},
        headers={"content-type": "text/html; charset=utf-8"},
        user_agent="Mozilla/5.0 TestBrowser",
        strategy_name="camoufox",
    )
    h_resp = s_resp.to_httpx_response("https://example.com")
    assert h_resp.status_code == 200
    assert h_resp.text == "<html>Success</html>"
    assert h_resp.headers["content-type"] == "text/html; charset=utf-8"


def test_strategy_circuit_breaker_isolation_and_cooldown():
    cb = _StrategyCircuitBreaker(failure_threshold=3, cooldown_seconds=300.0)

    host = "breaker-test.com"
    strategy = "crawl4ai"

    # Initially not cooling down
    assert cb.is_cooling_down(strategy, host) is False

    # 3 consecutive failures trigger cooldown
    cb.record_failure(strategy, host)
    cb.record_failure(strategy, host)
    cb.record_failure(strategy, host)

    assert cb.is_cooling_down(strategy, host) is True

    # Success resets breaker
    cb.record_success(strategy, host)
    assert cb.is_cooling_down(strategy, host) is False


def test_stealth_pipeline_priority_reordering():
    pipeline = StealthPipeline()
    client = HttpClient()
    host = "preferred-engine-test.com"

    HttpClient._preferred_engine_by_host[host] = "camoufox"
    ordered = pipeline.get_ordered_strategies(host, client=client)
    assert ordered[0].name == "camoufox"

    # Explicit hint override
    ordered_override = pipeline.get_ordered_strategies(host, client=client, preferred_engine="flaresolverr")
    assert ordered_override[0].name == "flaresolverr"


def test_stealth_circuit_breaker(monkeypatch):
    client = HttpClient()

    HttpClient._stealth_failed_hosts.clear()
    HttpClient._stealth_required_hosts.clear()

    def mock_fail(url):
        raise Exception("Mocked browser failure")

    monkeypatch.setattr(client, "_get_with_crawlee_cheerio", mock_fail)
    monkeypatch.setattr(client, "_get_with_crawlee_puppeteer", mock_fail)
    monkeypatch.setattr(client, "_get_with_crawl4ai", mock_fail)
    monkeypatch.setattr(client, "_get_with_drissionpage", mock_fail)
    monkeypatch.setattr(client, "_get_with_helium", mock_fail)
    monkeypatch.setattr(client, "_get_with_camoufox", mock_fail)
    monkeypatch.setattr(client, "_get_with_flaresolverr", mock_fail)

    client._rate_limiter_for("https://protected-site.com").wait = MagicMock()

    mock_resp = httpx.Response(
        status_code=403, request=httpx.Request("GET", "https://protected-site.com")
    )
    monkeypatch.setattr(client.client, "get", MagicMock(return_value=mock_resp))

    with pytest.raises(ScraperBypassError) as exc_info:
        client.get("https://protected-site.com/page1")

    assert "failed to bypass anti-bot protection" in str(exc_info.value) or "all browser fallbacks failed" in str(exc_info.value)
    assert any(h == "protected-site.com" for h in HttpClient._stealth_failed_hosts)


def test_flaresolverr_fallback_success(monkeypatch):
    client = HttpClient()
    url = "https://flaresolverr-site.com/page"

    def mock_flaresolverr(u):
        return "<html>FlareSolverr Solved</html>", [
            {"name": "cf_clearance", "value": "fl_token", "domain": "flaresolverr-site.com"}
        ]

    monkeypatch.setattr(client, "_get_with_flaresolverr", mock_flaresolverr)
    strategy = FlareSolverrStrategy()

    with patch.object(strategy, "is_available", return_value=True):
        resp = strategy.execute(url, client)
        assert resp is not None
        assert resp.status_code == 200
        assert "FlareSolverr Solved" in resp.text
        assert resp.cookies.get("cf_clearance") == "fl_token"
