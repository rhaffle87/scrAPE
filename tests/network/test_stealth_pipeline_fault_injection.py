"""Fault injection tests for StealthPipeline: corrupted browser binary and mid-run network abort."""

from unittest.mock import MagicMock
import httpx
from network.stealth.base import StealthResponse, StealthStrategy
from network.stealth.pipeline import StealthPipeline


class BrokenBrowserStrategy(StealthStrategy):
    name = "broken_browser"

    def is_available(self) -> bool:
        return True

    def execute(self, url: str, client) -> StealthResponse | None:
        raise OSError("Corrupted browser binary / executable missing")


class HealthyFallbackStrategy(StealthStrategy):
    name = "healthy_fallback"

    def is_available(self) -> bool:
        return True

    def execute(self, url: str, client) -> StealthResponse | None:
        return StealthResponse(
            status_code=200,
            text="<html><body>Recovered content</body></html>",
            cookies={},
            strategy_name=self.name,
        )


def test_fault_injection_corrupted_browser_graceful_tier_degradation():
    pipeline = StealthPipeline(
        strategies=[
            BrokenBrowserStrategy(),
            HealthyFallbackStrategy(),
        ]
    )

    mock_client = MagicMock()
    mock_client._hostname.return_value = "target.site"
    mock_client.__class__._cloudflare_blocked_hosts = set()

    # Pipeline should not crash when BrokenBrowserStrategy fails; it should gracefully degrade
    resp = pipeline.execute("https://target.site/gallery", client=mock_client)
    assert resp is not None
    assert resp.status_code == 200
    assert resp.strategy_name == "healthy_fallback"
    assert "Recovered content" in resp.text


class AbortingNetworkStrategy(StealthStrategy):
    name = "aborting_network"

    def is_available(self) -> bool:
        return True

    def execute(self, url: str, client) -> StealthResponse | None:
        raise httpx.ConnectTimeout("Connection timed out mid-handshake")


def test_fault_injection_mid_run_network_abort():
    pipeline = StealthPipeline(
        strategies=[
            AbortingNetworkStrategy(),
            HealthyFallbackStrategy(),
        ]
    )

    mock_client = MagicMock()
    mock_client._hostname.return_value = "flaky.network.org"
    mock_client.__class__._cloudflare_blocked_hosts = set()

    # Ensure circuit breaker or tier escalation handles mid-stream socket abort
    resp = pipeline.execute("https://flaky.network.org/index", client=mock_client)
    assert resp is not None
    assert resp.status_code == 200
    assert resp.strategy_name == "healthy_fallback"
