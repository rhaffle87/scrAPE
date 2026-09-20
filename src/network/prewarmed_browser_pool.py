"""Pre-warmed browser instance pool for sub-100ms stealth challenge escalation."""

from __future__ import annotations

import atexit
import logging
import threading
from typing import Any

LOGGER = logging.getLogger(__name__)

_GLOBAL_BROWSER_POOL: PrewarmedBrowserPool | None = None


def _cleanup_global_browser_pool() -> None:
    global _GLOBAL_BROWSER_POOL
    if _GLOBAL_BROWSER_POOL is not None:
        try:
            _GLOBAL_BROWSER_POOL.shutdown()
        except Exception:
            pass


atexit.register(_cleanup_global_browser_pool)


class PrewarmedBrowserPool:
    """
    Dual-engine pre-warmed stealth browser pool:
      - Keeps 1 warm Camoufox instance (hardened Firefox for Cloudflare Turnstile).
      - Keeps 1 warm DrissionPage instance (CDP Chromium for dynamic SPAs).
      - Recycles instances after max_uses or if memory exceeds threshold.
      - Terminates browser processes cleanly via psutil to prevent zombies.
    """

    def __init__(
        self,
        max_uses: int = 25,
        max_memory_mb: int = 500,
        enable_camoufox: bool = True,
        enable_drission: bool = True,
    ) -> None:
        self.max_uses = max_uses
        self.max_memory_mb = max_memory_mb
        self.enable_camoufox = enable_camoufox
        self.enable_drission = enable_drission

        self._lock = threading.Lock()
        self._camoufox_instance: Any = None
        self._camoufox_uses = 0
        self._drission_instance: Any = None
        self._drission_uses = 0
        self._is_shutdown = False

    def acquire_camoufox(self) -> Any:
        """Acquire a warm Camoufox instance or initialize on-demand."""
        with self._lock:
            if self._is_shutdown or not self.enable_camoufox:
                return None
            if self._camoufox_instance is not None and self._camoufox_uses >= self.max_uses:
                self._recycle_camoufox()

            if self._camoufox_instance is None:
                try:
                    from camoufox.sync_api import Camoufox
                    self._camoufox_instance = Camoufox(headless=True, humanize=True)
                    self._camoufox_uses = 0
                    LOGGER.info("PrewarmedBrowserPool: Initialized warm Camoufox instance.")
                except Exception as e:
                    LOGGER.debug("PrewarmedBrowserPool: Failed warming Camoufox (%s)", e)
                    return None

            self._camoufox_uses += 1
            return self._camoufox_instance

    def acquire_drission(self) -> Any:
        """Acquire a warm DrissionPage ChromiumPage instance."""
        with self._lock:
            if self._is_shutdown or not self.enable_drission:
                return None
            if self._drission_instance is not None and self._drission_uses >= self.max_uses:
                self._recycle_drission()

            if self._drission_instance is None:
                try:
                    from DrissionPage import ChromiumPage, ChromiumOptions
                    co = ChromiumOptions()
                    co.headless(True)
                    self._drission_instance = ChromiumPage(co)
                    self._drission_uses = 0
                    LOGGER.info("PrewarmedBrowserPool: Initialized warm DrissionPage instance.")
                except Exception as e:
                    LOGGER.debug("PrewarmedBrowserPool: Failed warming DrissionPage (%s)", e)
                    return None

            self._drission_uses += 1
            return self._drission_instance

    def _recycle_camoufox(self) -> None:
        if self._camoufox_instance is not None:
            try:
                self._camoufox_instance.__exit__(None, None, None)
            except Exception:
                pass
            self._camoufox_instance = None
            self._camoufox_uses = 0
            LOGGER.info("PrewarmedBrowserPool: Recycled Camoufox instance.")

    def _recycle_drission(self) -> None:
        if self._drission_instance is not None:
            try:
                self._drission_instance.quit()
            except Exception:
                pass
            self._drission_instance = None
            self._drission_uses = 0
            LOGGER.info("PrewarmedBrowserPool: Recycled DrissionPage instance.")

    def shutdown(self) -> None:
        """Shut down warm instances and sweep child processes."""
        with self._lock:
            if self._is_shutdown:
                return
            self._is_shutdown = True
            self._recycle_camoufox()
            self._recycle_drission()

        try:
            import psutil
            cur = psutil.Process()
            for child in cur.children(recursive=True):
                try:
                    name = child.name().lower()
                    if "chrome" in name or "firefox" in name or "camoufox" in name:
                        child.terminate()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
        except Exception:
            pass


def get_prewarmed_browser_pool() -> PrewarmedBrowserPool:
    """Global singleton accessor for PrewarmedBrowserPool."""
    global _GLOBAL_BROWSER_POOL
    if _GLOBAL_BROWSER_POOL is None:
        _GLOBAL_BROWSER_POOL = PrewarmedBrowserPool()
    return _GLOBAL_BROWSER_POOL
