"""
tests/test_file_downloader_instance_state.py
Unit tests for PR-1 file_downloader.py fix:
  - _fast_limiters and _host_semaphores are now instance-scoped (not module-level).
    Two MediaDownloader instances must have independent state, preventing
    watchdog-mode memory leaks where stale domain entries accumulate.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch


def _make_downloader():
    """Create a MediaDownloader with all heavy dependencies mocked."""
    mock_http = MagicMock()
    mock_http.get_proxy = MagicMock(return_value=None)

    with patch("storage.file_downloader.HttpClient", return_value=mock_http), \
         patch("network.bandwidth_limiter.BandwidthLimiter", MagicMock()), \
         patch("ml.aesthetic_scorer.AestheticScorer", MagicMock()):
        from storage.file_downloader import MediaDownloader
        return MediaDownloader(http=mock_http)


def test_limiters_are_instance_not_module_level():
    """Two MediaDownloader instances must have independent _fast_limiters dicts."""
    a = _make_downloader()
    b = _make_downloader()
    assert id(a._fast_limiters) != id(b._fast_limiters), (
        "_fast_limiters must be instance-scoped, not module-level shared"
    )


def test_semaphores_are_instance_not_module_level():
    """Two MediaDownloader instances must have independent _host_semaphores dicts."""
    a = _make_downloader()
    b = _make_downloader()
    assert id(a._host_semaphores) != id(b._host_semaphores), (
        "_host_semaphores must be instance-scoped, not module-level shared"
    )


def test_dl_lock_is_instance_not_module_level():
    """Two MediaDownloader instances must have independent _dl_lock objects."""
    a = _make_downloader()
    b = _make_downloader()
    assert id(a._dl_lock) != id(b._dl_lock), (
        "_dl_lock must be instance-scoped, not module-level shared"
    )


def test_fast_limiter_for_creates_and_caches():
    """_fast_limiter_for returns the same RateLimiter for the same host."""
    downloader = _make_downloader()
    limiter1 = downloader._fast_limiter_for("example.com")
    limiter2 = downloader._fast_limiter_for("example.com")
    assert limiter1 is limiter2, "_fast_limiter_for must cache the RateLimiter per host"


def test_host_semaphore_for_creates_and_caches():
    """_host_semaphore_for returns the same Semaphore for the same host."""
    downloader = _make_downloader()
    sem1 = downloader._host_semaphore_for("example.com")
    sem2 = downloader._host_semaphore_for("example.com")
    assert sem1 is sem2, "_host_semaphore_for must cache the Semaphore per host"


def test_instances_have_isolated_domain_state():
    """Adding a host to one downloader's limiter cache must not affect another."""
    a = _make_downloader()
    b = _make_downloader()

    a._fast_limiter_for("isolatedhost.com")
    assert a._fast_limiters.get("isolatedhost.com") is not None
    assert b._fast_limiters.get("isolatedhost.com") is None, (
        "Domain state added to instance A must not bleed into instance B"
    )
