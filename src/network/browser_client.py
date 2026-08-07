"""
browser_client.py — Browser Automation Fallback Mixin for HttpClient.

Provides browser automation fallback execution methods for WAF bypass and stealth scraping:
  - Crawlee (Cheerio & Puppeteer)
  - DrissionPage
  - Helium (Chrome & Firefox)
  - undetected-chromedriver (UC)
  - Camoufox
  - Nodriver
  - FlareSolverr
  - Crawl4AI
"""

from __future__ import annotations

import sys
import httpx
import shutil
import asyncio
from typing import Any, cast
from monitoring.logger import get_logger
import time
import re
import typing
from pathlib import Path
from urllib.parse import urlparse

import config
from config import (
    FLARESOLVERR_URL,
    BROWSER_PROFILE_MAX_AGE_DAYS,
)

import threading
from typing import ClassVar

logger = get_logger(__name__)

__all__ = ["BrowserClientMixin"]


def _get_or_create_event_loop():
    """Return the singleton background asyncio event loop, creating it on demand."""
    global _background_loop, _background_thread  # noqa: PLW0603

    with _loop_lock:
        if _background_loop is None or not _background_loop.is_running():
            _background_loop = asyncio.new_event_loop()

            def _run_loop(loop):
                asyncio.set_event_loop(loop)
                loop.run_forever()

            _background_thread = threading.Thread(
                target=_run_loop,
                args=(_background_loop,),
                daemon=True,
                name="crawl4ai-event-loop",
            )
            _background_thread.start()
    return _background_loop

def _run_coroutine_sync(coro):
    """Submit *coro* to the background event loop and block until it completes."""

    loop = _get_or_create_event_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()

def _apply_playwright_channel_patch() -> None:
    """Patch playwright and patchright launch_persistent_context to respect BrowserConfig channel."""
    from monitoring.logger import get_logger

    logger = get_logger(__name__)

    try:
        import playwright.async_api

        _orig_playwright_async = playwright.async_api.async_playwright

        # Check if already patched to avoid double patching
        if not getattr(_orig_playwright_async, "_is_patched", False):

            def _patched_playwright_async(*args, **kwargs):
                cm = _orig_playwright_async(*args, **kwargs)
                orig_start = cm.start

                async def patched_start(*args, **kwargs):
                    instance = await orig_start(*args, **kwargs)
                    _patch_playwright_instance(instance, logger)
                    return instance

                cm.start = patched_start
                return cm

            setattr(_patched_playwright_async, "_is_patched", True)
            playwright.async_api.async_playwright = _patched_playwright_async
            logger.info("Successfully patched playwright.async_api.async_playwright")
    except Exception as e:
        logger.warning("Failed to patch playwright.async_api.async_playwright: %s", e)

    try:
        import patchright.async_api

        _orig_patchright_async = patchright.async_api.async_playwright

        if not getattr(_orig_patchright_async, "_is_patched", False):

            def _patched_patchright_async(*args, **kwargs):
                cm = _orig_patchright_async(*args, **kwargs)
                orig_start = cm.start

                async def patched_start(*args, **kwargs):
                    instance = await orig_start(*args, **kwargs)
                    _patch_playwright_instance(instance, logger)
                    return instance

                cm.start = patched_start
                return cm

            setattr(_patched_patchright_async, "_is_patched", True)
            patchright.async_api.async_playwright = _patched_patchright_async
            logger.info("Successfully patched patchright.async_api.async_playwright")
    except Exception as e:
        logger.warning("Failed to patch patchright.async_api.async_playwright: %s", e)

def _patch_playwright_instance(instance, logger) -> None:
    import inspect

    if hasattr(instance, "chromium"):
        orig_launch_persistent = instance.chromium.launch_persistent_context
        if not getattr(orig_launch_persistent, "_is_patched", False):

            async def patched_launch_persistent(user_data_dir, **kwargs):
                # Walk up stack to find BrowserManager
                channel = None
                for frame_info in inspect.stack():
                    frame = frame_info.frame
                    self_obj = frame.f_locals.get("self")
                    if self_obj and self_obj.__class__.__name__ == "BrowserManager":
                        if hasattr(self_obj, "config"):
                            channel = getattr(
                                self_obj.config, "chrome_channel", None
                            ) or getattr(self_obj.config, "channel", None)
                        break
                if channel and channel != "chromium":
                    logger.info(
                        "Injecting channel='%s' into launch_persistent_context", channel
                    )
                    kwargs["channel"] = channel

                is_windows = sys.platform.startswith("win")

                # Filter out anti-sandbox flags that expose automation warning banners in Chrome.
                # On Windows, we must keep --no-sandbox to prevent GPU process crashes and rendering hangs.
                if "args" in kwargs and isinstance(kwargs["args"], list):
                    if is_windows:
                        kwargs["args"] = [
                            arg
                            for arg in kwargs["args"]
                            if arg != "--disable-setuid-sandbox"
                        ]
                    else:
                        kwargs["args"] = [
                            arg
                            for arg in kwargs["args"]
                            if arg not in ("--no-sandbox", "--disable-setuid-sandbox")
                        ]

                # Exclude default flags that reveal automation or trigger Cloudflare checks.
                # On Windows, we must NOT ignore --no-sandbox to ensure Chrome launches with sandbox disabled.
                target_ignores = ["--enable-automation", "--disable-extensions"]
                if not is_windows:
                    target_ignores.append("--no-sandbox")

                if "ignore_default_args" not in kwargs:
                    kwargs["ignore_default_args"] = target_ignores
                elif isinstance(kwargs["ignore_default_args"], list):
                    for arg in target_ignores:
                        if arg not in kwargs["ignore_default_args"]:
                            kwargs["ignore_default_args"].append(arg)

                logger.info("launch_persistent_context kwargs: %s", kwargs)
                return await orig_launch_persistent(user_data_dir, **kwargs)

            setattr(patched_launch_persistent, "_is_patched", True)
            instance.chromium.launch_persistent_context = patched_launch_persistent

def _get_platform_user_agent() -> str:
    if sys.platform.startswith("win"):
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    elif sys.platform == "darwin":
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"




_loop_lock = threading.Lock()
_background_loop = None
_background_thread = None

class BrowserClientMixin:
    """Mixin class providing browser automation fallback methods to HttpClient."""

    _flaresolverr_lock: ClassVar[threading.Lock] = threading.Lock()
    _flaresolverr_online: ClassVar[bool | None] = None

    captcha_provider: str | typing.Any = None
    captcha_key: str | None = None
    max_captcha_spend: float = 0.0
    session_manager: typing.Any = None
    proxy_list: list[str] | typing.Any = []
    timeout: float = 30.0
    _fallback_lock: threading.Lock | typing.Any = threading.Lock()
    _domain_fallback_locks: dict[str, threading.Lock] | typing.Any = {}
    _session_pool: typing.Any = None
    client: typing.Any = None
    stealth_pipeline: typing.Any = None
    _preferred_engine_by_host: dict[str, str] | typing.Any = {}

    def get_proxy(self) -> str | None:
        return None

    def get_tls_impersonate(self, domain: str) -> str:
        return "chrome"

    def _hostname(self, url: str) -> str:
        return urlparse(url).netloc.lower()





    def _get_with_curl_cffi(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using curl_cffi with domain-specific browser TLS impersonation."""
        from urllib.parse import urlparse
        import curl_cffi.requests as curl_req

        parsed = urlparse(url)
        domain = parsed.netloc or ""
        impersonate_target = self.get_tls_impersonate(domain)

        proxies: dict[str, str] | None = None
        if self.proxy_list:
            proxies = {"http": self.proxy_list[0], "https": self.proxy_list[0]}

        resp = curl_req.get(
            url,
            impersonate=cast(Any, impersonate_target),
            timeout=int(self.timeout),
            proxies=cast(Any, proxies),
            verify=False,
        )
        if resp.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"curl_cffi HTTP {resp.status_code}",
                request=httpx.Request("GET", url),
                response=httpx.Response(resp.status_code, text=resp.text),
            )

        cookies_list = []
        for name, value in resp.cookies.items():
            cookies_list.append(
                {"name": name, "value": value, "domain": domain, "path": "/"}
            )

        return resp.text, cookies_list

    def _try_curl_cffi_fallback(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        skip_httpx: bool = False,
    ) -> httpx.Response | None:
        """Attempt to bypass WAF challenges using curl_cffi TLS impersonation."""
        from monitoring.logger import get_logger

        logger = get_logger(__name__)

        try:
            from config import ENABLE_CURL_CFFI_FALLBACK
        except ImportError:
            ENABLE_CURL_CFFI_FALLBACK = True

        from unittest.mock import MagicMock

        client_get = getattr(getattr(self, "client", None), "get", None)
        is_mocked = (
            isinstance(getattr(self, "client", None), MagicMock)
            or isinstance(client_get, MagicMock)
            or getattr(client_get, "__name__", "").startswith("mock_")
        )

        if not ENABLE_CURL_CFFI_FALLBACK or skip_httpx or is_mocked:
            return None

        host = self._hostname(url)
        session = self._session_pool.get_session(host) if self._session_pool else None

        try:
            from curl_cffi import requests as c_requests

            logger.info("Attempting curl_cffi TLS spoofing for %s", url)

            proxy = self.get_proxy()
            proxy_dict = {"http": proxy, "https": proxy} if proxy else None
            impersonate_val: typing.Literal["chrome120"] = "chrome120"
            c_session = c_requests.Session(
                impersonate=impersonate_val,
                proxies=proxy_dict,  # type: ignore[arg-type]
            )

            c_req_headers = self._headers(url) if hasattr(self, "_headers") else {}
            if headers:
                c_req_headers.update(headers)

            if session and session.cookies:
                cookie_str = "; ".join([f"{k}={v}" for k, v in session.cookies.items()])
                c_req_headers["Cookie"] = cookie_str

            current_timeout = timeout if timeout is not None else self.timeout
            c_resp = c_session.get(url, headers=c_req_headers, timeout=current_timeout)

            if c_resp.status_code == 200 and not self._is_blocked_page(c_resp.text, url):
                logger.info("curl_cffi TLS spoofing successfully bypassed WAF for %s.", url)
                response = httpx.Response(
                    status_code=200,
                    content=c_resp.content,
                    request=httpx.Request("GET", url),
                )

                if c_resp.cookies and session:
                    cookies_dict = {c.name: c.value for c in c_resp.cookies.jar}
                    session.cookies.update(cookies_dict)
                    session.save_to_disk()
                    if self.session_manager:
                        cookie_list = [
                            {"name": k, "value": v, "domain": host, "path": "/"}
                            for k, v in cookies_dict.items()
                        ]
                        self.session_manager.save_session(host, cookie_list)

                return response
            else:
                logger.info(
                    "curl_cffi TLS spoofing still returned block/challenge for %s (status %d)",
                    url,
                    c_resp.status_code,
                )
                if c_resp.status_code in (403, 520, 429) and hasattr(
                    self.__class__, "register_cloudflare_blocked"
                ):
                    self.__class__.register_cloudflare_blocked(host)
        except Exception as c_exc:
            logger.warning("curl_cffi fallback failed: %s", c_exc)

        return None

    def _try_cookie_harvest_fallback(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response | None:
        """Attempt to bypass WAF challenges using locally harvested browser cookies."""
        from monitoring.logger import get_logger

        logger = get_logger(__name__)

        try:
            from config import ENABLE_COOKIE_HARVESTING
        except ImportError:
            ENABLE_COOKIE_HARVESTING = True

        if not ENABLE_COOKIE_HARVESTING or not self.session_manager:
            return None

        host = self._hostname(url)
        logger.info("Attempting local cookie harvest for domain '%s'", host)
        local_cookies = self.session_manager.get_local_cookies(host)
        if not local_cookies:
            return None

        logger.info(
            "Harvested cookies: %s. Retrying httpx request with harvested cookies.",
            list(local_cookies.keys()),
        )
        try:
            req_headers = self._headers(url) if hasattr(self, "_headers") else {}
            if headers:
                req_headers.update(headers)
            req_headers["Cookie"] = "; ".join(
                [f"{k}={v}" for k, v in local_cookies.items()]
            )
            current_timeout = timeout if timeout is not None else self.timeout
            retry_resp = self.client.get(
                url, headers=req_headers, timeout=current_timeout
            )
            retry_resp.raise_for_status()

            session = self._session_pool.get_session(host) if self._session_pool else None
            if session:
                session.cookies.update(local_cookies)
                session.save_to_disk()
            harvested_list = [
                {"name": k, "value": v, "domain": host, "path": "/"}
                for k, v in local_cookies.items()
            ]
            self.session_manager.save_session(host, harvested_list)
            logger.info("Harvested cookies successfully bypassed WAF for %s.", url)
            return retry_resp
        except Exception as retry_exc:
            logger.warning("Retry with harvested cookies failed: %s", retry_exc)

        return None


    def _fallback_lock_for(self, host: str) -> threading.Lock:
        with self._fallback_lock:
            if host not in self._domain_fallback_locks:
                self._domain_fallback_locks[host] = threading.Lock()
            return self._domain_fallback_locks[host]

    def _save_domain_cookies(self, url: str, cookies: dict | list) -> None:
        """Save solved cookies to persistent disk session and session pool."""
        from monitoring.logger import get_logger
        logger = get_logger(__name__)
        host = self._hostname(url)
        cookie_dict = {}
        if isinstance(cookies, list):
            cookie_dict = {c["name"]: c["value"] for c in cookies if isinstance(c, dict) and "name" in c and "value" in c}
        elif isinstance(cookies, dict):
            cookie_dict = cookies

        if cookie_dict:
            try:
                self.session_manager.save_session(host, cookie_dict)
                self._session_pool.update_cookies(host, cookie_dict)
                for k, v in cookie_dict.items():
                    self.client.cookies.set(k, v, domain=host)
            except Exception as e:
                logger.debug("Failed saving domain cookies for %s: %s", host, e)

    def _get_browser_profile_path(self, host: str) -> str:
        """Return the absolute path to the persistent browser profile for *host*."""
        domain_slug = re.sub(r"[^\w\-]", "_", host)
        profile_path = Path("data/profiles") / domain_slug
        profile_path.mkdir(parents=True, exist_ok=True)
        return str(profile_path.resolve())

    def _cleanup_stale_profiles(self) -> None:
        """Deletes physical browser profiles in data/profiles/ that exceed retention threshold."""
        profiles_dir = Path("data/profiles")
        if not profiles_dir.exists():
            return
            
        now = time.time()
        max_age_seconds = BROWSER_PROFILE_MAX_AGE_DAYS * 86400
        
        for profile in profiles_dir.iterdir():
            if profile.is_dir():
                try:
                    mtime = profile.stat().st_mtime
                    if now - mtime > max_age_seconds:
                        logger.info("Cleaning up stale browser profile: %s", profile.name)
                        shutil.rmtree(profile, ignore_errors=True)
                except Exception as e:
                    logger.warning("Failed to clean up profile %s: %s", profile.name, e)

    def _is_cloudflare_challenge(self, html: str) -> bool:
        """Return True if the HTML is a Cloudflare, Turnstile, or WAF interstitial challenge page."""
        if not html:
            return False
        title_match = re.search(
            r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
        )
        if title_match:
            title = title_match.group(1).strip().lower()
            if any(t in title for t in [
                "just a moment",
                "checking your browser",
                "attention required",
                "ddos-guard",
                "security check",
                "access denied",
                "shield",
                "human verification",
                "robot check",
            ]):
                return True
        lower_html = html.lower()
        waf_signatures = [
            "challenges.cloudflare.com",
            "cf-challenge",
            "cf-turnstile",
            "ray id:",
            "turnstile.render",
            "cf_clearance",
            "g-recaptcha",
            "hcaptcha",
            "datadome",
            "kasada",
            "perimeterx",
            "akamai",
            "aws-waf",
            "awswaf",
            "geetest",
        ]
        block_phrases = [
            "just a moment",
            "please enable javascript",
            "enable cookies",
            "verify you are human",
            "checking if the site connection is secure",
            "press & hold",
            "press and hold",
        ]
        if any(sig in lower_html for sig in ["cf-turnstile", "challenges.cloudflare.com/turnstile"]):
            return True
        if any(sig in lower_html for sig in waf_signatures) and any(bp in lower_html for bp in block_phrases):
            return True
        return False

    def _is_blocked_page(self, html: str, url: str = "") -> bool:
        """Return True if the HTML indicates a Cloudflare challenge or a soft block/redirect by DuckDuckGo."""
        if not html:
            return True
        if self._is_cloudflare_challenge(html):
            return True
        parsed = urlparse(url)
        host = parsed.netloc or parsed.hostname or ""
        if host == "duckduckgo.com" or host.endswith(".duckduckgo.com"):
            lower_html = html.lower()
            if (
                "if this persists, please email us" in lower_html
                or "error-lite" in lower_html
            ):
                return True
            if "/?q=" in url or "/html/" in url:
                title_match = re.search(
                    r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
                )
                if title_match:
                    title = title_match.group(1).strip()
                    if title == "DuckDuckGo":
                        return True
        return False

    def _execute_fallbacks(
        self,
        url: str,
        skip_httpx: bool = False,
        skip_crawl4ai: bool = False,
        preferred_engine: str | None = None,
    ) -> tuple[str | None, list[dict] | dict]:
        """Legacy fallback delegation to self.stealth_pipeline."""
        skip = skip_httpx or skip_crawl4ai
        try:
            res = self.stealth_pipeline.execute(url, self, skip_httpx=skip, preferred_engine=preferred_engine)
            host = self._hostname(url)
            if res and res.strategy_name and res.strategy_name != "unknown":
                self._preferred_engine_by_host[host] = res.strategy_name
            return res.text, res.cookies
        except Exception as exc:
            logger.debug("StealthPipeline legacy adapter failed for %s: %s", url, exc)
            return None, []


    def _get_with_crawlee_cheerio(self, url: str) -> tuple[str, list[dict]]:
        """Fetch URL using Crawlee Cheerio (fast parser)"""
        from network.crawlee_client import CrawleeClient
        client = CrawleeClient()
        html = client.get_with_cheerio(url, proxy=self.get_proxy())
        return html, []

    def _get_with_crawlee_puppeteer(self, url: str) -> tuple[str, list[dict]]:
        """Fetch URL using Crawlee Puppeteer (stealth browser)"""
        from network.crawlee_client import CrawleeClient
        client = CrawleeClient()
        host = self._hostname(url)
        profile_path = self._get_browser_profile_path(host)
        html, cookies = client.get_with_puppeteer(url, proxy=self.get_proxy(), user_data_dir=profile_path)
        return html, cookies

    def _get_with_drissionpage(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using DrissionPage to bypass Turnstile/WAF locally."""
        from monitoring.logger import get_logger

        logger = get_logger(__name__)

        try:
            from network.browser_pool import BrowserPoolManager
        except ImportError as e:
            logger.error("BrowserPoolManager not found: %s", e)
            raise e

        proxy = self.get_proxy()
        host = self._hostname(url)

        # Determine GUI platform
        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos
        headless_mode = False if config.STEALTH_HEADFUL else (True if config.FORCE_HEADLESS else (not is_local_gui))

        logger.info("Requesting pooled DrissionPage for %s (headless=%s)", url, headless_mode)

        try:
            with BrowserPoolManager.get_drission_page(proxy, headless_mode) as page:
                # Fetch URL and wait for redirection/challenge solving with fast-fail timeout
                page.get(url, timeout=20.0)

                # Fast-fail wait for Turnstile challenge to be solved
                solve_timeout = 30.0
                start_time = time.time()
                clicked = False
                while time.time() - start_time < solve_timeout:
                    html = page.html
                    if not self._is_cloudflare_challenge(html):
                        break

                    # Active Turnstile clicker
                    try:
                        import random
                        # Inject human-like mouse jitter
                        page.actions.move(random.randint(50, 200), random.randint(50, 200))

                        if not clicked:
                            cf_iframe = page.ele('xpath://iframe', timeout=1) or page.ele('#jvye6', timeout=1)
                            if cf_iframe:
                                logger.info("Found Cloudflare Turnstile widget/iframe, simulating human hover and click.")
                                page.actions.move_to(cf_iframe).click()
                                clicked = True
                    except Exception as e:
                        logger.debug("Turnstile auto-clicker exception: %s", repr(e))

                    time.sleep(0.5)

                html = page.html
                if self._is_cloudflare_challenge(html):
                    raise TimeoutError("DrissionPage hit Cloudflare challenge timeout.")

                # Trigger lazy-loaded images by scrolling
                logger.info("Scrolling down to trigger lazy loading for %s...", url)
                try:
                    last_height = 0
                    for _ in range(8):  # Max 8 scrolls
                        page.scroll.to_bottom()
                        time.sleep(1.0)
                        new_height = page.run_js("return document.body.scrollHeight")
                        if new_height == last_height:
                            break
                        last_height = new_height
                except Exception as e:
                    logger.debug("DrissionPage scroll failed: %s", e)

                html = page.html

                # Extract cookies
                cookies = page.cookies(all_info=True)
                cookies_list = []
                for c in cookies:
                    cookies_list.append(
                        {
                            "name": c.get("name"),
                            "value": c.get("value"),
                            "domain": c.get("domain") or host,
                            "path": c.get("path") or "/",
                        }
                    )

                return html, cookies_list

        except Exception as e:
            logger.error("DrissionPage request failed: %s", repr(e))
            raise e

        raise RuntimeError("Unreachable code path in _get_with_drissionpage")

    def _get_with_helium(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using Helium as a browser fallback (supports Firefox if Chrome is missing)."""
        from monitoring.logger import get_logger

        logger = get_logger(__name__)

        try:
            import helium
        except ImportError as e:
            logger.error("Helium not installed: %s", e)
            raise e

        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos
        headless_mode = False if config.STEALTH_HEADFUL else (True if config.FORCE_HEADLESS else (not is_local_gui))

        logger.info("Launching Helium for %s (headless=%s)", url, headless_mode)

        started = False
        try:
            logger.info("Helium: Trying Chrome browser...")

            from selenium.webdriver.chrome.options import Options as ChromeOptions
            chrome_options = ChromeOptions()

            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            proxy = self.get_proxy()
            if proxy:
                chrome_options.add_argument(f"--proxy-server={proxy}")

            helium.start_chrome(url, headless=headless_mode, options=chrome_options)
            started = True
        except Exception as chrome_err:
            logger.warning(
                "Helium: Chrome browser launch failed: %s. Falling back to Firefox...",
                chrome_err,
            )
            try:
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                firefox_options = FirefoxOptions()
                proxy = self.get_proxy()
                if proxy:
                    firefox_options.add_argument(f"--proxy-server={proxy}")

                helium.start_firefox(url, headless=headless_mode, options=firefox_options)
                started = True
            except Exception as firefox_err:
                logger.error("Helium: Firefox browser launch failed: %s", firefox_err)
                raise RuntimeError(
                    f"Helium failed to start either Chrome or Firefox: {firefox_err}"
                ) from chrome_err

        try:
            driver = helium.get_driver()
            solve_timeout = 30.0
            start_time = time.time()
            while time.time() - start_time < solve_timeout:
                html = driver.page_source
                if not self._is_cloudflare_challenge(html):
                    break
                time.sleep(1.0)

            html = driver.page_source
            if self._is_cloudflare_challenge(html):
                raise TimeoutError("Helium hit Cloudflare challenge timeout.")

            logger.info("Scrolling down to trigger lazy loading for %s...", url)
            try:
                last_height = 0
                for _ in range(8):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.0)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
            except Exception as e:
                logger.debug("Helium scroll failed: %s", e)

            html = driver.page_source

            cookies = driver.get_cookies()
            cookies_list = []
            host = self._hostname(url)
            for c in cookies:
                cookies_list.append(
                    {
                        "name": c.get("name"),
                        "value": c.get("value"),
                        "domain": c.get("domain") or host,
                        "path": c.get("path") or "/",
                    }
                )

            return html, cookies_list

        except Exception as e:
            logger.error("Helium request failed: %s", repr(e))
            raise e
        finally:
            if started:
                try:
                    helium.kill_browser()
                except Exception:
                    pass

    def _get_with_uc(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using undetected-chromedriver as the deepest fallback tier."""
        from monitoring.logger import get_logger

        logger = get_logger(__name__)

        try:
            import undetected_chromedriver as uc

            if not getattr(uc.Chrome, "_patched_quit", False):
                original_quit = uc.Chrome.quit
                def patched_quit(self):
                    try:
                        original_quit(self)
                    except OSError:
                        pass
                uc.Chrome.quit = patched_quit
                uc.Chrome._patched_quit = True

        except ImportError as e:
            logger.error("undetected-chromedriver not installed: %s", e)
            raise e

        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos
        headless_mode = False if config.STEALTH_HEADFUL else (True if config.FORCE_HEADLESS else (not is_local_gui))

        logger.info(
            "Launching undetected-chromedriver for %s (headless=%s)", url, headless_mode
        )
        driver = None
        for attempt in range(2):
            try:
                options = uc.ChromeOptions()
                if headless_mode:
                    options.add_argument("--headless")
                options.add_argument("--disable-gpu")

                proxy = self.get_proxy()
                if proxy:
                    options.add_argument(f"--proxy-server={proxy}")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

                driver = uc.Chrome(options=options, use_subprocess=True, version_main=150)
                break
            except Exception as driver_err:
                if "session not created" in str(driver_err).lower() and attempt == 0:
                    logger.warning("uc.Chrome session creation failed. Retrying initialization...")
                    time.sleep(2)
                    continue
                raise driver_err

        if driver is None:
            raise RuntimeError("Failed to initialize undetected-chromedriver driver instance.")

        try:
            driver.set_page_load_timeout(30)
            driver.get(url)

            solve_timeout = 25.0
            start_time = time.time()
            capsolver_attempted = False
            while time.time() - start_time < solve_timeout:
                html = driver.page_source
                if not self._is_cloudflare_challenge(html):
                    break
                if self.captcha_provider and self.captcha_key and not capsolver_attempted:
                    success = self._solve_cloudflare_captcha_uc(driver, url)
                    capsolver_attempted = True
                    if success:
                        solve_timeout += 10.0
                time.sleep(1.0)

            html = driver.page_source
            if self._is_cloudflare_challenge(html):
                raise TimeoutError(
                    "undetected-chromedriver hit Cloudflare challenge timeout."
                )

            logger.info("Scrolling down to trigger lazy loading for %s...", url)
            try:
                last_height = 0
                for _ in range(8):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.0)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
            except Exception as e:
                logger.debug("UC scroll failed: %s", e)

            html = driver.page_source

            cookies = driver.get_cookies()
            cookies_list = []
            host = self._hostname(url)
            for c in cookies:
                cookies_list.append(
                    {
                        "name": c.get("name"),
                        "value": c.get("value"),
                        "domain": c.get("domain") or host,
                        "path": c.get("path") or "/",
                    }
                )

            return html, cookies_list

        except Exception as e:
            logger.error("undetected-chromedriver request failed: %s", e)
            raise e
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    def _solve_cloudflare_captcha_uc(self, driver, url: str) -> bool:
        if not self.captcha_provider or not self.captcha_key:
            return False
        from monitoring.logger import get_logger
        logger = get_logger(__name__)

        provider_str = self.captcha_provider if isinstance(self.captcha_provider, str) else getattr(self.captcha_provider, "name", "")
        provider_name = (provider_str or "").lower()
        api_key_str = self.captcha_key or ""
        spend_limit = float(getattr(self, "max_captcha_spend", 0.0) or 0.0)
        provider = None
        if provider_name == "capsolver":
            from captcha.captcha_solvers.capsolver_provider import CapSolverProvider
            provider = CapSolverProvider(api_key=api_key_str, max_spend_per_run=spend_limit)
        elif provider_name == "2captcha":
            from captcha.captcha_solvers.twocaptcha_provider import TwoCaptchaProvider
            provider = TwoCaptchaProvider(api_key=api_key_str, max_spend=spend_limit)
        elif provider_name == "anticaptcha":
            from captcha.captcha_solvers.anticaptcha_provider import AntiCaptchaProvider
            provider = AntiCaptchaProvider(api_key=api_key_str, max_spend=spend_limit)
        else:
            logger.warning(f"Unknown captcha provider: {provider_name}")
            return False

        html = driver.page_source
        sitekey = None

        match = re.search(r'data-sitekey=["\']([^"\']+)["\']', html)
        if match:
            sitekey = match.group(1)
        if not sitekey:
            match = re.search(r'sitekey:\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if match:
                sitekey = match.group(1)

        if not sitekey:
            logger.warning(f"{provider_name}: Cloudflare Turnstile detected, but sitekey not found in HTML.")
            return False

        logger.info(f"{provider_name}: Solving Turnstile for sitekey {sitekey}...")
        try:
            token = provider.solve_turnstile(website_url=url, website_key=sitekey, timeout=60)
            if not token:
                logger.warning(f"{provider_name}: No token returned in solution.")
                return False

            logger.info(f"{provider_name}: Injecting token...")
            script = f"""
            let input = document.querySelector('[name="cf-turnstile-response"]');
            if (input) {{
                input.value = "{token}";
                let form = input.closest('form');
                if (form) {{
                    form.submit();
                    return true;
                }}
            }}

            if (window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients) {{
                for (let c in window.___grecaptcha_cfg.clients) {{
                    let client = window.___grecaptcha_cfg.clients[c];
                    for (let k in client) {{
                        if (client[k] && client[k].callback) {{
                            client[k].callback("{token}");
                            return true;
                        }}
                    }}
                }}
            }}

            if (window.turnstile && typeof window.turnstile.getResponse === 'function') {{
                let t_input = document.querySelector('input[name="cf-turnstile-response"]');
                if (t_input) {{
                    t_input.value = "{token}";
                }}
            }}
            return false;
            """
            success = driver.execute_script(script)
            if success:
                logger.info(f"{provider_name}: Token injected and form submitted.")
                return True
            else:
                logger.warning(f"{provider_name}: Failed to locate cf-turnstile-response input or form to submit.")
                return False
        except Exception as e:
            logger.error(f"{provider_name} API failed: {repr(e)}")
            return False

    def _get_with_camoufox(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using Camoufox stealth browser with fingerprint & headful escalation tuning."""
        from monitoring.logger import get_logger
        logger = get_logger(__name__)

        try:
            from camoufox.sync_api import Camoufox
        except ImportError:
            logger.warning("Camoufox library is not installed.")
            raise Exception("Camoufox library is not installed")

        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos
        headless_mode = False if config.STEALTH_HEADFUL else (True if config.FORCE_HEADLESS else (not is_local_gui))

        camou_os = "windows" if is_windows else ("mac" if is_macos else "linux")

        def _fetch_camou(is_headless: bool) -> tuple[str, list[dict]]:
            logger.info("Launching Camoufox for %s (headless=%s, os=%s)", url, is_headless, camou_os)
            host = self._hostname(url)
            profile_path = self._get_browser_profile_path(host)
            kwargs = {
                "headless": is_headless,
                "os": camou_os,
                "humanize": True,
                "window_size": (1920, 1080),
                "user_data_dir": profile_path,
            }
            with Camoufox(**kwargs) as browser:
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=30000)

                if is_headless and self._is_cloudflare_challenge(page.content()):
                    raise TimeoutError("Camoufox headless hit Cloudflare Turnstile challenge.")

                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                except Exception:
                    pass

                html = page.content()
                cookies = page.context.cookies()

                cookie_list = []
                host = self._hostname(url)
                for c in cookies:
                    cookie_list.append(
                        {
                            "name": c.get("name"),
                            "value": c.get("value"),
                            "domain": c.get("domain") or host,
                            "path": c.get("path") or "/",
                        }
                    )
                return html, cookie_list

        try:
            return _fetch_camou(headless_mode)
        except Exception as exc:
            if headless_mode and is_local_gui and not config.FORCE_HEADLESS:
                logger.warning(
                    "\n"
                    "========================================================================\n"
                    "CAMOUFOX HEADLESS WAF CHALLENGE ON: %s\n"
                    "Escalating Camoufox to HEADFUL (visible) mode for 20 seconds.\n"
                    "Please solve/click the Turnstile checkbox if prompted in the window.\n"
                    "========================================================================",
                    url,
                )
                try:
                    return _fetch_camou(False)
                except Exception as headful_exc:
                    logger.error("Camoufox headful escalation failed for %s: %s", url, repr(headful_exc))
                    raise headful_exc
            logger.error("Camoufox request failed: %s", repr(exc))
            raise exc

    def _get_with_nodriver(self, url: str, force_headful: bool = False) -> tuple[str, list[dict]]:
        """Fetch *url* using Nodriver stealth browser for Turnstile bypass.
        Auto-escalates to headful mode if headless challenge fails.
        """
        from monitoring.logger import get_logger
        logger = get_logger(__name__)

        try:
            import nodriver as uc  # type: ignore
        except ImportError:
            logger.warning("Nodriver library is not installed.")
            raise Exception("Nodriver library is not installed")


        async def _fetch():
            is_windows = sys.platform.startswith("win")
            is_macos = sys.platform == "darwin"
            is_local_gui = is_windows or is_macos
            headless_mode = False if (config.STEALTH_HEADFUL or force_headful) else (True if config.FORCE_HEADLESS else (not is_local_gui))

            logger.info("Launching Nodriver for %s (headless=%s, force_headful=%s)", url, headless_mode, force_headful)

            browser = await uc.start(headless=headless_mode)
            try:
                page = await browser.get(url)

                await asyncio.sleep(4.0)

                content = await page.get_content()
                if self._is_cloudflare_challenge(content):
                    logger.info("Cloudflare challenge detected in Nodriver. Attempting interaction...")

                    try:
                        await page.evaluate("window.scrollTo(0, Math.floor(Math.random() * 500));")
                        await asyncio.sleep(1.0)

                        widget = await page.select("iframe[src*='turnstile'], .cf-turnstile")
                        if widget:
                            logger.info("Found Turnstile widget. Simulating click...")
                            await widget.click()
                            await asyncio.sleep(4.0)
                    except Exception as interact_err:
                        logger.debug("Nodriver interaction failed: %s", interact_err)

                content = await page.get_content()
                if self._is_cloudflare_challenge(content):
                    if headless_mode and is_local_gui and not config.FORCE_HEADLESS:
                        logger.warning("Nodriver failed Cloudflare challenge in headless mode. Escalating to headful mode.")
                        raise TimeoutError("Nodriver hit Cloudflare challenge (headless mode).")
                    elif not headless_mode:
                        logger.warning("Nodriver failed Cloudflare challenge even in headful mode.")
                        raise TimeoutError("Nodriver hit Cloudflare challenge (headful mode).")
                    else:
                        raise TimeoutError("Nodriver hit Cloudflare challenge (non-GUI environment).")

                cookies_str = str(await page.evaluate("document.cookie"))
                cookies = []
                host = self._hostname(url)
                if cookies_str:
                    for c_pair in cookies_str.split(";"):
                        c_pair = c_pair.strip()
                        if "=" in c_pair:
                            name, val = c_pair.split("=", 1)
                            cookies.append({"name": name, "value": val, "domain": host, "path": "/"})

                return content, cookies
            finally:
                browser.stop()

        try:
            return asyncio.run(_fetch())
        except TimeoutError as exc:
            if not force_headful and "headless mode" in str(exc):
                return self._get_with_nodriver(url, force_headful=True)
            logger.error("Nodriver request failed: %s", repr(exc))
            raise exc
        except Exception as exc:
            logger.error("Nodriver request failed: %s", repr(exc))
            raise exc

    def _get_with_flaresolverr(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using FlareSolverr proxy service with session reuse & proxy forwarding."""
        import httpx
        from monitoring.logger import get_logger
        logger = get_logger(__name__)

        fs_url = FLARESOLVERR_URL or "http://127.0.0.1:8191/v1"

        with self.__class__._flaresolverr_lock:
            if self.__class__._flaresolverr_online is False:
                logger.warning("FlareSolverr service is offline (previous ping failed). Skipping FlareSolverr fallback.")
                raise Exception("FlareSolverr service is offline")

        host = self._hostname(url)
        domain_slug = re.sub(r"[^\w\-]", "_", host)
        session_id = f"session_{domain_slug}"

        proxy = self.get_proxy()
        payload: dict[str, typing.Any] = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
            "session": session_id,
        }
        if proxy:
            payload["proxy"] = {"url": proxy}

        logger.info("Sending request to FlareSolverr at %s for %s (session=%s)", fs_url, url, session_id)

        try:
            with httpx.Client(timeout=65.0) as client:
                if self.__class__._flaresolverr_online is None:
                    ping_urls = [fs_url, "http://localhost:8191/v1", "http://127.0.0.1:8191/v1"]
                    ping_success = False
                    active_url = fs_url
                    for p_url in dict.fromkeys(ping_urls):
                        try:
                            base_url = p_url.rsplit("/v1", 1)[0]
                            ping_res = client.get(base_url or p_url, timeout=3.0)
                            ping_res.raise_for_status()
                            ping_success = True
                            active_url = p_url
                            break
                        except Exception:
                            continue

                    if not ping_success:
                        try:
                            import subprocess
                            logger.info("FlareSolverr unreachable. Attempting background docker start flaresolverr...")
                            subprocess.Popen(  # nosec B603 B607
                                ["docker", "start", "flaresolverr"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                            time.sleep(3.5)
                            for p_url in dict.fromkeys(ping_urls):
                                try:
                                    base_url = p_url.rsplit("/v1", 1)[0]
                                    ping_res = client.get(base_url or p_url, timeout=3.0)
                                    ping_res.raise_for_status()
                                    ping_success = True
                                    active_url = p_url
                                    break
                                except Exception:
                                    continue
                        except Exception as docker_err:
                            logger.debug("Auto-starting FlareSolverr container failed: %s", docker_err)

                    if ping_success:
                        fs_url = active_url
                        with self.__class__._flaresolverr_lock:
                            self.__class__._flaresolverr_online = True
                    else:
                        with self.__class__._flaresolverr_lock:
                            self.__class__._flaresolverr_online = False
                        logger.warning("FlareSolverr health-check failed at %s. Disabling FlareSolverr.", fs_url)
                        raise Exception("FlareSolverr health-check failed")

                res = client.post(fs_url, json=payload)
                res.raise_for_status()
                data = res.json()

                if data.get("status") == "ok":
                    sol = data.get("solution", {})
                    html = sol.get("response", "")
                    raw_cookies = sol.get("cookies", [])
                    cookie_list = []
                    for c in raw_cookies:
                        cookie_list.append(
                            {
                                "name": c.get("name"),
                                "value": c.get("value"),
                                "domain": c.get("domain") or host,
                                "path": c.get("path") or "/",
                            }
                        )
                    return html, cookie_list
                else:
                    msg = data.get("message", "Unknown FlareSolverr error")
                    logger.warning("FlareSolverr returned status '%s': %s", data.get("status"), msg)
                    raise Exception(f"FlareSolverr error: {msg}")
        except Exception as exc:
            logger.error("FlareSolverr request failed: %s", repr(exc))
            raise exc

    def _get_with_crawl4ai(self, url: str) -> tuple[str, list[dict]] | str:
        """Fetch *url* via headless/headful browser, escalating through two stealth tiers."""

        

        import crawl4ai.async_webcrawler

        crawl4ai.async_webcrawler.is_blocked = lambda status_code, html, error_message=None: (False, "")

        from crawl4ai import (
            AsyncWebCrawler,
            BrowserConfig,
            CrawlerRunConfig,
            CacheMode,
            UndetectedAdapter,
        )
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
        from monitoring.logger import get_logger

        logger = get_logger(__name__)

        async def _run_tier(strategy, run_config) -> tuple[str, list[dict]]:
            async with AsyncWebCrawler(crawler_strategy=strategy) as crawler:
                res = await crawler.arun(url=url, config=run_config)
                if res and res.success:
                    cookies = []
                    try:
                        bm = crawler.crawler_strategy.browser_manager
                        for context in bm.contexts_by_config.values():
                            try:
                                ctx_cookies = await context.cookies()
                                cookies.extend(ctx_cookies)
                            except Exception as exc:
                                logger.debug("Failed to extract cookies from Crawl4AI context: %s", exc)
                    except Exception as exc:
                        logger.debug("Failed to access Crawl4AI browser manager: %s", exc)
                    return res.html, cookies
                raise Exception(res.error_message if res else "Unknown crawler error")

        async def _run_crawler() -> tuple[str, list[dict]]:
            from monitoring.logger import get_logger

            logger = get_logger(__name__)

            parsed = urlparse(url)
            host = parsed.netloc or parsed.hostname or ""
            domain_slug = re.sub(r"[^\w\-]", "_", host)
            raw_profile = self._get_browser_profile_path(host)
            profile_path = Path(raw_profile) if raw_profile else None

            is_windows = sys.platform.startswith("win")
            is_macos = sys.platform == "darwin"
            is_local_gui = is_windows or is_macos
            headless_mode = False if config.STEALTH_HEADFUL else (True if config.FORCE_HEADLESS else (not is_local_gui))

            session_cookies = self.session_manager.load_session(host) or {}
            playwright_cookies = []
            for k, v in session_cookies.items():
                playwright_cookies.append(
                    {"name": k, "value": v, "domain": host, "path": "/"}
                )

            run_config = CrawlerRunConfig(
                word_count_threshold=0,
                cache_mode=CacheMode.BYPASS,
                magic=True,
                simulate_user=True,
                override_navigator=True,
                delay_before_return_html=6.0,
                page_timeout=30000,
                session_id=f"session_{domain_slug}",
                js_code="""
                const scrollInterval = setInterval(() => {
                    window.scrollTo(0, document.body.scrollHeight);
                }, 1000);
                setTimeout(() => clearInterval(scrollInterval), 5000);
                """
            )

            async def _run_with_chrome_fallback(
                headless: bool, enable_stealth: bool, browser_adapter=None, run_cfg=None
            ) -> tuple[str, list[dict]]:
                proxy_val = self.get_proxy()

                def _make_browser_cfg(channel_opt=None):
                    kwargs = {
                        "browser_type": "chromium",
                        "headless": headless,
                        "verbose": False,
                        "enable_stealth": enable_stealth,
                        "user_agent": _get_platform_user_agent(),
                        "extra_args": ["--disable-gpu"] if headless else [],
                        "use_persistent_context": True,
                        "cookies": playwright_cookies,
                    }
                    if profile_path:
                        kwargs["user_data_dir"] = str(profile_path.resolve())
                    if channel_opt:
                        kwargs["channel"] = channel_opt
                        kwargs["chrome_channel"] = channel_opt
                    if proxy_val:
                        kwargs["proxy"] = proxy_val
                    return BrowserConfig(**kwargs)

                def _make_strategy(b_cfg):
                    kwargs = {"browser_config": b_cfg}
                    if browser_adapter is not None:
                        kwargs["browser_adapter"] = browser_adapter
                    return AsyncPlaywrightCrawlerStrategy(**kwargs)

                try:
                    cfg = _make_browser_cfg("chrome")
                    strat = _make_strategy(cfg)
                    return await _run_tier(strat, run_cfg)
                except Exception as exc:
                    logger.warning(
                        "Crawl4AI fallback run with channel='chrome' failed: %s. Retrying with default Playwright Chromium...",
                        exc,
                    )
                    cfg_fallback = _make_browser_cfg()
                    strat_fallback = _make_strategy(cfg_fallback)
                    return await _run_tier(strat_fallback, run_cfg)

            logger.info(
                "Crawl4AI Fallback: Trying Tier 1 (Standard Stealth) for %s...", url
            )
            try:
                html, cookies = await _run_with_chrome_fallback(
                    headless=headless_mode,
                    enable_stealth=True,
                    browser_adapter=None,
                    run_cfg=run_config,
                )
                if not self._is_blocked_page(html, url):
                    logger.info("Crawl4AI Tier 1 succeeded for %s.", url)
                    return html, cookies
                logger.warning(
                    "Crawl4AI Tier 1 hit a block or challenge for %s. Escalating to Tier 2...",
                    url,
                )
            except Exception as exc:
                logger.warning(
                    "Crawl4AI Tier 1 failed for %s: %s. Escalating to Tier 2...",
                    url,
                    exc,
                )

            is_windows = sys.platform.startswith("win")
            is_macos = sys.platform == "darwin"
            is_local_gui = is_windows or is_macos
            headless_mode = False if config.STEALTH_HEADFUL else (True if config.FORCE_HEADLESS else (not is_local_gui))

            if not headless_mode:
                logger.warning(
                    "\n"
                    "========================================================================\n"
                    "CLOUDFLARE TURNSTILE DETECTED ON: %s\n"
                    "Running Browser in HEADFUL (visible) mode for 20 seconds.\n"
                    "Please solve/click the Turnstile checkbox if prompted in the window.\n"
                    "========================================================================",
                    url,
                )
            else:
                logger.info(
                    "CLOUDFLARE TURNSTILE DETECTED ON: %s - Running browser in HEADLESS mode.",
                    url,
                )

            run_config_2 = CrawlerRunConfig(
                word_count_threshold=0,
                cache_mode=CacheMode.BYPASS,
                magic=True,
                simulate_user=True,
                override_navigator=True,
                delay_before_return_html=20.0,
                page_timeout=30000,
                session_id=f"session_{domain_slug}",
                js_code="""
                const scrollInterval = setInterval(() => {
                    window.scrollTo(0, document.body.scrollHeight);
                }, 1000);
                setTimeout(() => clearInterval(scrollInterval), 18000);
                """
            )
            try:
                html, cookies = await _run_with_chrome_fallback(
                    headless=headless_mode,
                    enable_stealth=True,
                    browser_adapter=UndetectedAdapter(),
                    run_cfg=run_config_2,
                )
                if not self._is_blocked_page(html, url):
                    logger.info("Crawl4AI Tier 2 succeeded for %s.", url)
                    return html, cookies
                raise Exception("Crawl4AI Tier 2 hit a block or challenge page.")
            except Exception as exc:
                raise Exception(
                    f"All Crawl4AI fallback tiers failed for {url}: {exc}"
                ) from exc

        parsed_url = urlparse(url)
        host = parsed_url.netloc or parsed_url.hostname or ""
        lock = self._fallback_lock_for(host)
        with lock:
            return _run_coroutine_sync(_run_crawler())
