"""Unit tests for PrewarmedBrowserPool verifying lifecycle, recycling, and shutdown."""

from unittest.mock import MagicMock, patch
from network.prewarmed_browser_pool import PrewarmedBrowserPool, get_prewarmed_browser_pool


def test_prewarmed_browser_pool_recycling():
    pool = PrewarmedBrowserPool(max_uses=3, enable_camoufox=True, enable_drission=True)

    mock_camou = MagicMock()
    mock_driss = MagicMock()

    with patch.dict("sys.modules", {"camoufox.sync_api": MagicMock(Camoufox=MagicMock(return_value=mock_camou))}):
        with patch.dict("sys.modules", {"DrissionPage": MagicMock(ChromiumPage=MagicMock(return_value=mock_driss))}):
            # Acquire 1
            c1 = pool.acquire_camoufox()
            assert c1 is mock_camou
            assert pool._camoufox_uses == 1

            # Acquire 2
            c2 = pool.acquire_camoufox()
            assert c2 is mock_camou
            assert pool._camoufox_uses == 2

            # Acquire 3
            c3 = pool.acquire_camoufox()
            assert c3 is mock_camou
            assert pool._camoufox_uses == 3

            # Acquire 4 - should trigger recycling
            c4 = pool.acquire_camoufox()
            assert pool._camoufox_uses == 1

            # Drission acquire
            d1 = pool.acquire_drission()
            assert d1 is mock_driss
            assert pool._drission_uses == 1

    pool.shutdown()
    assert pool._is_shutdown is True


def test_get_prewarmed_browser_pool_singleton():
    p1 = get_prewarmed_browser_pool()
    p2 = get_prewarmed_browser_pool()
    assert p1 is p2
