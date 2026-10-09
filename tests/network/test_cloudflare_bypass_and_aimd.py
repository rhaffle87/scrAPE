"""
test_cloudflare_bypass_and_aimd.py — Tests for TLS session vault, Bézier curves, and AIMD backoff.
"""

import time
from unittest.mock import MagicMock, patch
import pytest

from network.browser_client import generate_bezier_curve
from network.proxy_manager import ProxyInfo, ProxyPoolManager
from network.session_pool import Session, SessionPool
from network.http_client import HttpClient


def test_bezier_curve_endpoints_and_length():
    """Verify Bézier curve starts at source, ends at destination, and has expected steps."""
    start = (100.0, 100.0)
    end = (500.0, 300.0)
    steps = 30
    points = generate_bezier_curve(start, end, steps=steps)

    assert len(points) == steps + 1
    assert points[0] == (100, 100)
    assert points[-1] == (500, 300)

    # All points are integers
    for pt in points:
        assert isinstance(pt[0], int)
        assert isinstance(pt[1], int)

    # Degenerate distance returns single endpoint
    same_points = generate_bezier_curve((50.0, 50.0), (50.0, 50.0), steps=20)
    assert len(same_points) == 1
    assert same_points[0] == (50, 50)


def test_session_vault_tls_binding_and_validation(tmp_path):
    """Verify cf_clearance session vault binds TLS profile, proxy, and TTL."""
    with patch("network.session_pool.Path") as mock_path:
        cache_file = tmp_path / "test.json"
        mock_path.return_value = tmp_path
        session = Session("example.com")
        session._cookie_file = cache_file

        # Initially no clearance
        assert not session.is_clearance_valid()

        # Bind clearance with 1-hour TTL
        session.bind_tls_session(
            cookies={"cf_clearance": "token_abc123", "session_id": "sid_999"},
            tls_profile="chrome120",
            proxy="http://proxy1:8080",
            ttl_seconds=3600.0,
        )

        assert session.cookies["cf_clearance"] == "token_abc123"
        assert session.tls_profile == "chrome120"
        assert session.bound_proxy == "http://proxy1:8080"
        assert session.is_clearance_valid(proxy="http://proxy1:8080")

        # Proxy mismatch invalidates clearance
        assert not session.is_clearance_valid(proxy="http://other_proxy:8080")

        # Expired clearance is invalid
        session.clearance_expires_at = time.time() - 10.0
        assert not session.is_clearance_valid(proxy="http://proxy1:8080")

        # Reset identity clears clearance and profile
        session.reset_identity()
        assert not session.is_clearance_valid()
        assert "cf_clearance" not in session.cookies
        assert session.tls_profile == "chrome120"
        assert session.bound_proxy is None


def test_session_pool_binding_delegation():
    """Verify SessionPool delegates bind_tls_session and is_clearance_valid correctly."""
    pool = SessionPool()
    domain = "cloudflare-protected.org"
    pool.bind_tls_session(
        domain,
        cookies={"cf_clearance": "cf_valid"},
        tls_profile="firefox133",
        proxy="http://1.2.3.4:8080",
        ttl_seconds=1800.0,
    )

    assert pool.is_clearance_valid(domain, proxy="http://1.2.3.4:8080")
    assert not pool.is_clearance_valid(domain, proxy="http://wrong_proxy:8080")


def test_aimd_proxy_quarantine_backoff():
    """Verify AIMD quarantine increases backoff geometrically on successive rate limits."""
    info = ProxyInfo("http://node1.proxy.internal:8080")
    assert info.quarantine_tier == 0
    assert info.health_score == 1.0

    # Tier 1 rate limit
    d1 = info.record_rate_limit(base_duration_s=30.0)
    assert d1 == 30.0
    assert info.quarantine_tier == 1
    assert not info.is_healthy()

    # Tier 2 rate limit (2x backoff)
    d2 = info.record_rate_limit(base_duration_s=30.0)
    assert d2 == 60.0
    assert info.quarantine_tier == 2

    # Tier 3 rate limit (4x backoff)
    d3 = info.record_rate_limit(base_duration_s=30.0)
    assert d3 == 120.0
    assert info.quarantine_tier == 3

    # Recovery on success resets tier
    info.record_success(latency_ms=100.0)
    assert info.quarantine_tier == 0


def test_aimd_domain_rps_recovery():
    """Verify additive increase of RPS after rate-limiting reduction."""
    client = HttpClient()
    url = "https://aimd-test.com/data"
    host = "aimd-test.com"

    limiter = client._rate_limiter_for(url)
    base_rps = limiter.requests_per_second

    # Simulate multiplicative decrease on 429
    limiter.requests_per_second = max(0.05, base_rps * 0.5)
    reduced_rps = limiter.requests_per_second
    assert reduced_rps < base_rps

    # Record success: additive increase
    client._record_domain_success(host, url)
    recovered_rps = limiter.requests_per_second
    assert recovered_rps > reduced_rps
    assert recovered_rps <= base_rps
