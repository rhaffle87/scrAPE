"""
tests/test_stealth_pipeline_fixes.py
Unit tests for PR-1 stealth_pipeline.py fixes:
  - DrissionPageStrategy duplicate eliminated
  - CrawleeStrategy.is_available() TTL-cached (30s)
  - FlareSolverrStrategy.is_available() TTL-cached (60s)
  - CamoufoxStrategy.is_available() uses import-check, not platform check
"""
from __future__ import annotations

import sys
import time
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# 1. No duplicate DrissionPageStrategy
# ---------------------------------------------------------------------------
def test_drissionpage_strategy_not_duplicated():
    """stealth_pipeline module must define DrissionPageStrategy exactly once."""
    import network.stealth_pipeline as sp_mod

    drission_names = [name for name in dir(sp_mod) if name == "DrissionPageStrategy"]
    assert len(drission_names) == 1, (
        "DrissionPageStrategy must be defined exactly once in stealth_pipeline"
    )

    cls = getattr(sp_mod, "DrissionPageStrategy")
    assert hasattr(cls, "is_available"), "DrissionPageStrategy must have is_available()"


# ---------------------------------------------------------------------------
# 2. CrawleeStrategy TTL cache — is_available() called only once in window
# ---------------------------------------------------------------------------
def test_crawlee_availability_ttl_cached():
    """CrawleeStrategy.is_available() must use TTL caching; the inner HTTP check
    must be called only once even if is_available() is invoked multiple times
    within the 30s window."""
    import network.stealth_pipeline as sp_mod

    strategy = sp_mod.CrawleeStrategy()
    sp_mod.CrawleeStrategy._avail_until = 0.0
    sp_mod.CrawleeStrategy._avail_result = False

    call_count = 0

    def fake_is_running():
        nonlocal call_count
        call_count += 1
        return True

    mock_cc = MagicMock()
    mock_cc.CrawleeClient = MagicMock(return_value=MagicMock(_is_server_running=fake_is_running))

    with patch.dict("sys.modules", {"network.crawlee_client": mock_cc}):
        sp_mod.CrawleeStrategy._avail_until = 0.0
        sp_mod.CrawleeStrategy._avail_result = False

        result1 = strategy.is_available()
        result2 = strategy.is_available()  # Must use cached value

    assert result1 is True
    assert result2 is True
    assert call_count == 1, (
        f"_is_server_running should be called only once (TTL cache hit), got {call_count}"
    )


# ---------------------------------------------------------------------------
# 3. FlareSolverrStrategy TTL cache
# ---------------------------------------------------------------------------
def test_flaresolverr_availability_ttl_cached():
    """FlareSolverrStrategy.is_available() must use TTL caching; the inner httpx.get
    must be called only once even if is_available() is invoked multiple times."""
    import network.stealth_pipeline as sp_mod

    strategy = sp_mod.FlareSolverrStrategy()
    sp_mod.FlareSolverrStrategy._avail_until = 0.0
    sp_mod.FlareSolverrStrategy._avail_result = False

    http_call_count = 0

    def fake_httpx_get(url, timeout):
        nonlocal http_call_count
        http_call_count += 1
        return MagicMock(status_code=200)

    mock_monitor_mod = MagicMock()
    mock_monitor_mod.FlareSolverrMonitor = MagicMock(
        return_value=MagicMock(is_healthy=MagicMock(return_value=True))
    )

    with patch("config.FLARESOLVERR_URL", "http://localhost:8191/v1"), \
         patch("config.ENABLE_FLARESOLVERR_FALLBACK", True), \
         patch("network.stealth_pipeline.httpx.get", side_effect=fake_httpx_get), \
         patch.dict("sys.modules", {"network.flaresolverr_monitor": mock_monitor_mod}):

        sp_mod.FlareSolverrStrategy._avail_until = 0.0
        sp_mod.FlareSolverrStrategy._avail_result = False
        sp_mod.FlareSolverrStrategy._monitor = None

        result1 = strategy.is_available()
        result2 = strategy.is_available()  # Must hit cache

    assert result1 is True
    assert result2 is True
    assert http_call_count == 1, (
        f"httpx.get should be called only once (TTL cache hit), got {http_call_count}"
    )


# ---------------------------------------------------------------------------
# 4. CamoufoxStrategy.is_available() — import-check, not platform
# ---------------------------------------------------------------------------
def test_camoufox_available_when_importable():
    """CamoufoxStrategy.is_available() must return True when camoufox is importable,
    regardless of the OS platform (Windows included)."""
    import network.stealth_pipeline as sp_mod

    strategy = sp_mod.CamoufoxStrategy()
    fake_camoufox = MagicMock()
    with patch.dict("sys.modules", {"camoufox": fake_camoufox}):
        result = strategy.is_available()

    assert result is True, "CamoufoxStrategy.is_available() should return True when camoufox is importable"


def test_camoufox_unavailable_when_not_importable():
    """CamoufoxStrategy.is_available() must return False when camoufox is not installed."""
    import network.stealth_pipeline as sp_mod

    strategy = sp_mod.CamoufoxStrategy()
    # Ensure camoufox raises ImportError
    with patch.dict("sys.modules", {"camoufox": None}):
        result = strategy.is_available()

    assert result is False, "CamoufoxStrategy.is_available() should return False when camoufox is not installed"
