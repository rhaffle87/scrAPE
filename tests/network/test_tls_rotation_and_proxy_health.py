from __future__ import annotations

import time
from unittest.mock import patch

from network.http_client import HttpClient, _DomainCooldownState
from network.proxy_manager import ProxyInfo, ProxyPoolManager
from network.proxy_pool import ProxyPoolManager as AliasedProxyPoolManager, ProxyInfo as AliasedProxyInfo


def test_proxy_pool_module_reexport():
    """Verify network.proxy_pool successfully re-exports ProxyPoolManager and ProxyInfo."""
    assert AliasedProxyPoolManager is ProxyPoolManager
    assert AliasedProxyInfo is ProxyInfo


def test_proxy_info_ema_latency_and_health_scoring():
    """Verify EMA latency updating and composite health score calculations."""
    proxy = ProxyInfo("http://user:pass@192.168.1.1:8080")
    assert proxy.ema_latency_ms == 0.0
    assert proxy.health_score == 1.0

    # First success
    proxy.record_success(100.0)
    assert proxy.ema_latency_ms == 100.0
    assert proxy.avg_latency_ms == 100.0
    assert proxy.health_score > 0.5

    # Second success with higher latency: EMA = 0.2*200 + 0.8*100 = 120.0
    proxy.record_success(200.0)
    assert proxy.ema_latency_ms == 120.0
    assert proxy.avg_latency_ms == 150.0

    # Record failure: health score should drop
    score_before = proxy.health_score
    proxy.record_failure()
    assert proxy.failures == 1
    assert proxy.consecutive_failures == 1
    assert proxy.health_score < score_before


def test_proxy_info_tiered_quarantine_backoff_and_probing():
    """Verify tiered quarantine backoff progression and recovery probing."""
    proxy = ProxyInfo("http://10.0.0.1:3128")
    assert proxy.is_healthy() is True

    # 1st and 2nd failure: healthy remains True
    proxy.record_failure()
    proxy.record_failure()
    assert proxy.is_healthy() is True
    assert proxy.quarantine_tier == 0

    # 3rd failure: Tier 1 quarantine (300s)
    proxy.record_failure()
    assert proxy.consecutive_failures == 3
    assert proxy.quarantine_tier == 1
    assert proxy.is_healthy() is False

    # 4th failure: Tier 2 quarantine (600s)
    proxy.record_failure()
    assert proxy.consecutive_failures == 4
    assert proxy.quarantine_tier == 2
    assert proxy.is_healthy() is False

    # Simulate quarantine expiry
    proxy.cooldown_until = time.monotonic() - 1.0
    assert proxy.is_healthy() is True
    assert proxy.is_probing is True

    # Success while probing resets quarantine and consecutive failures
    proxy.record_success(150.0)
    assert proxy.quarantine_tier == 0
    assert proxy.is_probing is False
    assert proxy.consecutive_failures == 0
    assert proxy.is_healthy() is True


def test_proxy_pool_manager_health_weighted_selection():
    """Verify get_healthy_proxy prioritises higher health scores and lower latencies."""
    pool = ProxyPoolManager()
    proxies = [
        "http://proxy-good.local:8080",
        "http://proxy-laggy.local:8080",
        "http://proxy-dead.local:8080",
    ]
    pool.set_proxies(proxies)

    # proxy-good: 5 successes, 80ms latency
    for _ in range(5):
        pool.record_proxy_success("http://proxy-good.local:8080", 80.0)

    # proxy-laggy: 5 successes, 1500ms latency
    for _ in range(5):
        pool.record_proxy_success("http://proxy-laggy.local:8080", 1500.0)

    # proxy-dead: 3 failures (quarantined)
    for _ in range(3):
        pool.record_proxy_failure("http://proxy-dead.local:8080")

    best_healthy = pool.get_healthy_proxy()
    assert best_healthy == "http://proxy-good.local:8080"

    status = pool.get_pool_status()
    good_status = next(s for s in status if s["url"] == "http://proxy-good.local:8080")
    assert "health_score" in good_status
    assert "ema_latency_ms" in good_status
    assert good_status["healthy"] is True


def test_http_client_sticky_tls_rotation():
    """Verify sticky TLS profiles and rotation across supported modern profiles."""
    test_domain = "tls-test-domain.example"

    # Default fallback is chrome120
    assert HttpClient.get_tls_impersonate(test_domain) == "chrome120"

    # Explicit sticky assignment
    HttpClient.set_domain_tls_profile(test_domain, "safari17_0")
    assert HttpClient.get_tls_impersonate(test_domain) == "safari17_0"

    # Rotate profile
    next_profile = HttpClient.rotate_tls_profile(test_domain)
    assert next_profile == "safari18_0"
    assert HttpClient.get_tls_impersonate(test_domain) == "safari18_0"

    # Next rotation
    after_profile = HttpClient.rotate_tls_profile(test_domain)
    assert after_profile == "firefox133"
    assert HttpClient.get_tls_impersonate(test_domain) == "firefox133"


def test_domain_reputation_and_adaptive_delays():
    """Verify _DomainCooldownState reputation tracking and adaptive delay scaling."""
    state = _DomainCooldownState()
    assert state.reputation_score == 1.0

    # Base delay with perfect reputation should be unchanged
    assert state.adaptive_delay(1.0) == 1.0

    # Recording 429 lowers reputation and scales delay
    state.record_429()
    assert state.reputation_score < 0.8
    scaled_delay = state.adaptive_delay(1.0)
    assert scaled_delay > 1.0

    # Adaptive jitter scales with reduced reputation
    jitter = state.adaptive_jitter()
    assert jitter > 0.4

    # Multiple successes restore reputation
    for _ in range(10):
        state.record_success()
    assert state.reputation_score == 1.0
    assert state.adaptive_delay(1.0) == 1.0


def test_http_client_get_domain_delay():
    """Verify HttpClient.get_domain_delay combines overrides with adaptive scaling."""
    client = HttpClient(domain_delays={"slow-domain.org": 2.0})
    # Initial delay should match base (2.0s)
    delay = client.get_domain_delay("slow-domain.org")
    assert delay == 2.0

    # Degrade reputation on that domain
    cd_state = client._cooldown_state_for("https://slow-domain.org/items")
    cd_state.record_429()

    # Effective delay should scale up
    adaptive_delay = client.get_domain_delay("slow-domain.org")
    assert adaptive_delay > 2.0
