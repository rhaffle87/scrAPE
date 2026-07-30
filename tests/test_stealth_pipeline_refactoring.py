from __future__ import annotations

import httpx
import pytest
from network.stealth_pipeline import (
    _StrategyCircuitBreaker,
    StealthPipeline,
    StealthResponse,
    StealthStrategy,
)
from network.http_client import HttpClient


class MockSuccessStrategy(StealthStrategy):
    name = "mock_success"

    def execute(self, url: str, client) -> StealthResponse | None:
        return StealthResponse(
            status_code=200,
            text="<html>Success</html>",
            cookies={"session_token": "abc123xyz"},
            strategy_name=self.name,
        )


class MockFailingStrategy(StealthStrategy):
    name = "mock_fail"

    def execute(self, url: str, client) -> StealthResponse | None:
        return None


def test_stealth_response_to_httpx_response():
    s_resp = StealthResponse(
        status_code=200,
        text="Hello World",
        cookies={"c1": "v1"},
        headers={"Content-Type": "text/html"},
        strategy_name="test_strat",
    )
    h_resp = s_resp.to_httpx_response("https://example.com/page")
    assert isinstance(h_resp, httpx.Response)
    assert h_resp.status_code == 200
    assert h_resp.text == "Hello World"
    assert h_resp.headers.get("Content-Type") == "text/html"


def test_strategy_circuit_breaker_isolation_and_cooldown():
    cb = _StrategyCircuitBreaker(failure_threshold=3, cooldown_seconds=3600.0)
    host = "testdomain.com"

    assert cb.is_cooling_down("strategy_a", host) is False
    assert cb.is_cooling_down("strategy_b", host) is False

    cb.record_failure("strategy_a", host)
    cb.record_failure("strategy_a", host)
    assert cb.is_cooling_down("strategy_a", host) is False

    cb.record_failure("strategy_a", host)
    assert cb.is_cooling_down("strategy_a", host) is True
    assert cb.is_cooling_down("strategy_b", host) is False

    cb.record_success("strategy_a", host)
    assert cb.is_cooling_down("strategy_a", host) is False


def test_stealth_pipeline_execution_flow_and_cookie_persistence():
    fail_strat = MockFailingStrategy()
    succ_strat = MockSuccessStrategy()

    pipeline = StealthPipeline(strategies=[fail_strat, succ_strat])
    client = HttpClient()

    url = "https://example.com/test"
    resp = pipeline.execute(url, client)

    assert isinstance(resp, StealthResponse)
    assert resp.status_code == 200
    assert "Success" in resp.text
    assert resp.cookies == {"session_token": "abc123xyz"}

    # Verify circuit breaker tracked failure for fail_strat
    key = ("mock_fail", "example.com")
    assert pipeline.circuit_breaker._failures.get(key, 0) == 1


def test_stealth_pipeline_priority_reordering():
    s1 = MockFailingStrategy()
    s1.name = "crawlee"
    s2 = MockSuccessStrategy()
    s2.name = "flaresolverr"

    pipeline = StealthPipeline(strategies=[s1, s2])
    ordered = pipeline.get_ordered_strategies("example.com", preferred_engine="flaresolverr")

    assert len(ordered) == 2
    assert ordered[0].name == "flaresolverr"
    assert ordered[1].name == "crawlee"


def test_http_client_stealth_pipeline_integration():
    client = HttpClient()
    assert hasattr(client, "stealth_pipeline")
    assert isinstance(client.stealth_pipeline, StealthPipeline)

    host = "samplehost.org"
    cb = client.stealth_pipeline.circuit_breaker

    assert cb.is_cooling_down("crawlee", host) is False

    for _ in range(3):
        cb.record_failure("crawlee", host)

    assert cb.is_cooling_down("crawlee", host) is True
    assert cb.is_cooling_down("flaresolverr", host) is False
