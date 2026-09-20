import time
from network.http_client import StealthTierHealthManager


def test_stealth_tier_health_manager_recording():
    """Verify StealthTierHealthManager records successes, latency, and failure cooldowns."""
    manager = StealthTierHealthManager()

    # Initial state should be healthy
    assert manager.is_healthy("flaresolverr") is True

    # Record success with 150ms latency
    manager.record_success("flaresolverr", 150.0)
    snapshot = manager.get_health_snapshot()
    assert snapshot["flaresolverr"]["successes"] == 1
    assert snapshot["flaresolverr"]["avg_latency_ms"] == 150.0

    # Record 3 consecutive failures
    manager.record_failure("flaresolverr")
    manager.record_failure("flaresolverr")
    manager.record_failure("flaresolverr")

    # Tier should now be unhealthy (in cooldown)
    assert manager.is_healthy("flaresolverr") is False
    snapshot_after = manager.get_health_snapshot()
    assert snapshot_after["flaresolverr"]["healthy"] is False
    assert snapshot_after["flaresolverr"]["consecutive_failures"] == 3
    assert snapshot_after["flaresolverr"]["cooldown_remaining_sec"] > 0
