from __future__ import annotations

import logging
import queue
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional, ContextManager, TYPE_CHECKING
import contextlib

if TYPE_CHECKING:
    from DrissionPage import ChromiumPage

LOGGER = logging.getLogger(__name__)

@dataclass
class PooledBrowser:
    page: 'ChromiumPage'
    proxy: str | None
    headless: bool
    last_used: float

class BrowserPoolManager:
    """
    Manages a bounded pool of headless browser instances to prevent OOM
    and eliminate cold-boot overhead during WAF fallback storms.
    """
    
    _lock = threading.RLock()
    _max_browsers = 4
    _pool: list[PooledBrowser] = []
    _active_count = 0
    _condition = threading.Condition(_lock)

    @classmethod
    def get_drission_page(cls, proxy: str | None, headless: bool, timeout: float = 60.0) -> ContextManager['ChromiumPage']:
        """
        Acquire a DrissionPage ChromiumPage instance from the pool or block until one is available.
        Ensures proxy and headless mode match.
        """
        @contextlib.contextmanager
        def _acquire():
            browser = cls._checkout(proxy, headless, timeout)
            
            # Use the latest tab or clear cookies to ensure session isolation
            try:
                # We clear cookies to ensure clean state
                browser.page.clear_cache(cookies=True)
            except Exception as e:
                LOGGER.debug("Failed to clear cookies on pooled browser: %s", e)

            success = False
            try:
                yield browser.page
                success = True
            finally:
                cls._checkin(browser, success=success)
                
        return _acquire()

    @classmethod
    def _checkout(cls, proxy: str | None, headless: bool, timeout: float) -> PooledBrowser:
        start_time = time.time()
        with cls._condition:
            while True:
                # Try to find an exact match in the idle pool
                for i, b in enumerate(cls._pool):
                    if b.proxy == proxy and b.headless == headless:
                        browser = cls._pool.pop(i)
                        cls._active_count += 1
                        return browser
                
                # If we have capacity to create a new one, but no exact match in idle pool
                # We can evict an idle browser if we are at the limit of the pool list length
                # Wait, the limit is on _active_count + len(_pool)
                total_browsers = cls._active_count + len(cls._pool)
                
                if total_browsers < cls._max_browsers:
                    # We can safely create a new browser
                    cls._active_count += 1
                    break
                elif len(cls._pool) > 0:
                    # We are at capacity, but there are idle browsers with WRONG proxy/headless
                    # Evict the oldest idle browser to make room
                    oldest_idx = min(range(len(cls._pool)), key=lambda i: cls._pool[i].last_used)
                    evicted = cls._pool.pop(oldest_idx)
                    try:
                        evicted.page.quit()
                    except Exception:
                        pass
                    cls._active_count += 1
                    break
                else:
                    # All browsers are actively checked out. We must wait.
                    elapsed = time.time() - start_time
                    remaining = timeout - elapsed
                    if remaining <= 0:
                        raise TimeoutError("Timeout waiting for an available browser in the pool.")
                    cls._condition.wait(timeout=remaining)

        # We broke out, meaning we need to instantiate a new browser
        return cls._create_new_browser(proxy, headless)

    @classmethod
    def _create_new_browser(cls, proxy: str | None, headless: bool) -> PooledBrowser:
        from DrissionPage import ChromiumOptions, ChromiumPage
        import uuid
        from pathlib import Path
        import re

        co = ChromiumOptions()
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-gpu")
        co.set_argument("--incognito") # Enforce incognito for isolation
        co.set_argument("--disable-blink-features=AutomationControlled")
        co.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if proxy:
            co.set_proxy(proxy)
        
        co.headless(headless)
        
        profile_path = Path("data/drission_profiles") / f"pool_{uuid.uuid4().hex[:8]}"
        profile_path.mkdir(parents=True, exist_ok=True)
        co.set_user_data_path(str(profile_path.resolve()))
        
        LOGGER.info("Booting new pooled DrissionPage (proxy=%s, headless=%s)", proxy, headless)
        page = ChromiumPage(co)
        
        # Inject stealth JS globally for this page
        stealth_js = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
window.chrome = { app: { isInstalled: false }, runtime: {} };
const getParameter = WebGLRenderingContext.getParameter;
WebGLRenderingContext.prototype.getParameter = function(parameter) {
    if (parameter === 37445) { return 'Intel Inc.'; }
    if (parameter === 37446) { return 'Intel Iris OpenGL Engine'; }
    return getParameter(parameter);
};
        """
        try:
            page.run_cdp("Page.addScriptToEvaluateOnNewDocument", source=stealth_js)
        except Exception as e:
            LOGGER.debug("Failed to inject stealth.js into new pooled browser: %s", e)

        return PooledBrowser(page=page, proxy=proxy, headless=headless, last_used=time.time())

    @classmethod
    def _checkin(cls, browser: PooledBrowser, success: bool = True):
        with cls._condition:
            cls._active_count -= 1
            if success:
                browser.last_used = time.time()
                cls._pool.append(browser)
            else:
                # If checkout failed (e.g. proxy banned/timeout), destroy it
                try:
                    browser.page.quit()
                except Exception:
                    pass
            cls._condition.notify_all()

    @classmethod
    def shutdown(cls):
        with cls._condition:
            for b in cls._pool:
                try:
                    b.page.quit()
                except Exception:
                    pass
            cls._pool.clear()

import atexit
atexit.register(BrowserPoolManager.shutdown)
