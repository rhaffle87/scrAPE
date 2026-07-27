from utils.proxy_manager import ProxyPoolManager, ProxyInfo


def test_proxy_info_recording_and_cooldown():
    """Verify ProxyInfo records latency and triggers 10-min cooldown after 3 failures."""
    info = ProxyInfo("http://user:pass@127.0.0.1:8080")
    assert info.scheme == "http"
    assert info.host == "127.0.0.1"
    assert info.port == 8080
    assert info.username == "user"
    assert info.password == "pass"
    assert info.is_healthy() is True

    # Record success
    info.record_success(120.0)
    assert info.successes == 1
    assert info.avg_latency_ms == 120.0

    # Record 3 failures to trigger cooldown
    info.record_failure()
    info.record_failure()
    info.record_failure()

    assert info.is_healthy() is False
    assert info.consecutive_failures == 3


def test_proxy_pool_manager_latency_sorting():
    """Verify ProxyPoolManager sorts healthy proxies by lowest latency."""
    pool = ProxyPoolManager()
    proxies = ["http://proxy1.local:8080", "http://proxy2.local:8080"]
    pool.set_proxies(proxies)

    # Record lower latency for proxy2
    pool.record_proxy_success("http://proxy1.local:8080", 450.0)
    pool.record_proxy_success("http://proxy2.local:8080", 85.0)

    best = pool.get_best_proxy()
    assert best == "http://proxy2.local:8080"


def test_proxy_pool_manager_sticky_domain_binding():
    """Verify ProxyPoolManager maintains sticky domain assignments."""
    pool = ProxyPoolManager()
    proxies = ["http://proxyA.local:8080", "http://proxyB.local:8080"]
    pool.set_proxies(proxies)

    assigned1 = pool.get_proxy_for_domain("example.com")
    assigned2 = pool.get_proxy_for_domain("example.com")

    assert assigned1 == assigned2
    assert assigned1 in proxies
