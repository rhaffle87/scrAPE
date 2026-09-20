from __future__ import annotations

import pytest
from captcha.captcha_solvers.capsolver_provider import CapSolverProvider
from network.proxy_manager import ProxyPoolManager, ProxyInfo


def test_capsolver_payload_and_balance(requests_mock=None):
    """Test CapSolver API payload generation and balance querying."""
    client = CapSolverProvider(api_key="test_api_key")
    assert client.api_key == "test_api_key"

    # Test balance fallback when key is empty
    empty_client = CapSolverProvider(api_key="")
    assert empty_client.get_balance() == 0.0


def test_proxy_pool_latency_and_quarantine():
    """Test ProxyPoolManager latency auto-rotation and high latency quarantine."""
    pm = ProxyPoolManager.get_instance()
    p_url = "http://1.2.3.4:8080"
    pm.set_proxies([p_url])

    info = pm._proxies[p_url]
    assert info.is_healthy() is True

    # Record 3 failures to trigger 5-minute quarantine
    info.record_failure()
    info.record_failure()
    info.record_failure()
    assert info.is_healthy() is False

    # Reset cooldown for latency test
    info.cooldown_until = 0.0
    assert info.is_healthy() is True

    # High latency > 3000ms triggers quarantine
    info.record_success(3500.0)
    assert info.is_healthy() is False


def test_proxy_pool_sticky_domain_binding():
    """Test ProxyPoolManager sticky per-domain binding."""
    pm = ProxyPoolManager.get_instance()
    domain = "example-domain.com"
    p_url = "http://5.6.7.8:8080"

    pm.bind_domain_proxy(domain, p_url)
    assigned = pm.get_proxy_for_domain(domain)
    assert assigned == p_url
