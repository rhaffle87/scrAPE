from __future__ import annotations

import threading
import time
from typing import Any
import httpx
from monitoring.logger import get_logger
from .base import StealthStrategy, StealthResponse

logger = get_logger(__name__)


class HttpxStrategy(StealthStrategy):
    name = "httpx"

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        headers = client._headers(url)
        resp = client.client.get(url, headers=headers)
        if resp.status_code < 400:
            return StealthResponse(
                status_code=resp.status_code,
                text=resp.text,
                headers=dict(resp.headers),
                strategy_name=self.name,
            )
        return None



class DrissionPageStrategy(StealthStrategy):
    name = "drissionpage"

    def is_available(self) -> bool:
        try:
            from network.browser_client import BrowserClient  # type: ignore
            return BrowserClient._get_browser_type("drissionpage") is not None
        except ImportError:
            return False

    def can_handle(self, url: str, host: str) -> bool:
        # Only use if we couldn't get the page with httpx
        return True

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        try:
            from network.browser_client import BrowserClient  # type: ignore
            html, cookies, user_agent = BrowserClient._get_with_drissionpage(url)
            if html and not client._is_blocked_page(html, url):
                cookie_dict = {}
                if isinstance(cookies, list):
                    for cookie in cookies:
                        if isinstance(cookie, dict) and "name" in cookie and "value" in cookie:
                            cookie_dict[cookie["name"]] = cookie["value"]
                elif isinstance(cookies, dict):
                    cookie_dict = cookies
                return StealthResponse(
                    status_code=200,
                    text=html,
                    cookies=cookie_dict,
                    headers={"User-Agent": user_agent or ""},
                    strategy_name=self.name,
                    user_agent=user_agent
                )
        except Exception as exc:
            logger.debug("Strategy 'drissionpage' execution failed for %s: %s", url, exc)

        return None



class CurlCffiStrategy(StealthStrategy):
    name = "curl_cffi"

    def is_available(self) -> bool:
        try:
            import curl_cffi.requests  # noqa: F401
            return True
        except ImportError:
            return False

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        try:
            if hasattr(client, "_get_with_curl_cffi"):
                html, cookies = client._get_with_curl_cffi(url)
                if html and not (hasattr(client, "_is_blocked_page") and client._is_blocked_page(html, url)):
                    cookie_dict = {}
                    if isinstance(cookies, list):
                        cookie_dict = {c["name"]: c["value"] for c in cookies if isinstance(c, dict) and "name" in c and "value" in c}
                    elif isinstance(cookies, dict):
                        cookie_dict = cookies
                    return StealthResponse(status_code=200, text=html, cookies=cookie_dict, strategy_name=self.name)
        except Exception as exc:
            logger.debug("Strategy 'curl_cffi' execution failed for %s: %s", url, exc)

        return None



class CrawleeStrategy(StealthStrategy):
    name = "crawlee"

    # TTL-cached availability: avoids an HTTP ping to the Node.js bridge per URL.
    _avail_result: bool = False
    _avail_until: float = 0.0
    _avail_lock: threading.Lock = threading.Lock()
    _AVAIL_TTL_S: float = 30.0

    def is_available(self) -> bool:
        now = time.monotonic()
        with self.__class__._avail_lock:
            if now < self.__class__._avail_until:
                return self.__class__._avail_result
        try:
            from network.crawlee_client import CrawleeClient
            result = CrawleeClient()._is_server_running()
        except Exception:
            result = False
        with self.__class__._avail_lock:
            self.__class__._avail_result = result
            self.__class__._avail_until = time.monotonic() + self.__class__._AVAIL_TTL_S
        return result

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        # Tier A: Fast cheerio
        try:
            html, _ = client._get_with_crawlee_cheerio(url)
            if html and not client._is_blocked_page(html, url):
                return StealthResponse(status_code=200, text=html, strategy_name=self.name)
        except Exception as exc:
            logger.debug("Strategy 'crawlee_cheerio' execution failed for %s: %s", url, exc)


        # Tier B: Puppeteer stealth
        try:
            html, cookies = client._get_with_crawlee_puppeteer(url)
            if html and not client._is_blocked_page(html, url):
                cookie_dict = {}
                if isinstance(cookies, list):
                    cookie_dict = {c["name"]: c["value"] for c in cookies if isinstance(c, dict) and "name" in c and "value" in c}
                elif isinstance(cookies, dict):
                    cookie_dict = cookies
                return StealthResponse(status_code=200, text=html, cookies=cookie_dict, strategy_name=self.name)
        except Exception as exc:
            logger.debug("Strategy 'crawlee_puppeteer' execution failed for %s: %s", url, exc)


        return None



class Crawl4AIStrategy(StealthStrategy):
    name = "crawl4ai"

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        try:
            res = client._get_with_crawl4ai(url)
            if isinstance(res, tuple):
                html, cookies = res
            else:
                html, cookies = res, []
            if html and not client._is_blocked_page(html, url):
                cookie_dict = {}
                if isinstance(cookies, list):
                    cookie_dict = {c["name"]: c["value"] for c in cookies if isinstance(c, dict) and "name" in c and "value" in c}
                elif isinstance(cookies, dict):
                    cookie_dict = cookies
                return StealthResponse(status_code=200, text=html, cookies=cookie_dict, strategy_name=self.name)
        except Exception as exc:
            logger.debug("Strategy 'crawl4ai' execution failed for %s: %s", url, exc)

        return None




class HeliumStrategy(StealthStrategy):
    name = "helium"

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        try:
            html, cookies = client._get_with_helium(url)
            if html and not client._is_blocked_page(html, url):
                cookie_dict = {}
                if isinstance(cookies, list):
                    cookie_dict = {c["name"]: c["value"] for c in cookies if isinstance(c, dict) and "name" in c and "value" in c}
                elif isinstance(cookies, dict):
                    cookie_dict = cookies
                return StealthResponse(status_code=200, text=html, cookies=cookie_dict, strategy_name=self.name)
        except Exception as exc:
            logger.debug("Strategy 'helium' execution failed for %s: %s", url, exc)

        return None



class FlareSolverrStrategy(StealthStrategy):
    name = "flaresolverr"
    _monitor = None

    # TTL-cached availability: avoids an HTTP GET to the FlareSolverr container per URL.
    _avail_result: bool = False
    _avail_until: float = 0.0
    _avail_lock: threading.Lock = threading.Lock()
    _AVAIL_TTL_S: float = 60.0

    def is_available(self) -> bool:
        from config import FLARESOLVERR_URL, ENABLE_FLARESOLVERR_FALLBACK
        if not ENABLE_FLARESOLVERR_FALLBACK or not FLARESOLVERR_URL:
            return False

        now = time.monotonic()
        with self.__class__._avail_lock:
            if now < self.__class__._avail_until:
                return self.__class__._avail_result

        result = False
        # Check Docker telemetry health to avoid routing to a stuck FlareSolverr instance
        try:
            from network.flaresolverr_monitor import FlareSolverrMonitor
            # Use a singleton pattern or class variable to keep the thread alive
            if self.__class__._monitor is None:
                self.__class__._monitor = FlareSolverrMonitor()
                self.__class__._monitor.start()  # type: ignore
            if not self.__class__._monitor.is_healthy():  # type: ignore
                with self.__class__._avail_lock:
                    self.__class__._avail_result = False
                    self.__class__._avail_until = time.monotonic() + self.__class__._AVAIL_TTL_S
                return False
        except ImportError:
            pass

        try:
            base_url = FLARESOLVERR_URL.rsplit("/v1", 1)[0] or FLARESOLVERR_URL
            r = httpx.get(base_url, timeout=1.5)
            result = r.status_code == 200
        except Exception:
            result = False

        with self.__class__._avail_lock:
            self.__class__._avail_result = result
            self.__class__._avail_until = time.monotonic() + self.__class__._AVAIL_TTL_S
        return result

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        try:
            html, cookies = client._get_with_flaresolverr(url)
            if html and not client._is_blocked_page(html, url):
                cookie_dict = {}
                if isinstance(cookies, list):
                    cookie_dict = {c["name"]: c["value"] for c in cookies if isinstance(c, dict) and "name" in c and "value" in c}
                elif isinstance(cookies, dict):
                    cookie_dict = cookies
                return StealthResponse(status_code=200, text=html, cookies=cookie_dict, strategy_name=self.name)
        except Exception as exc:
            logger.debug("Strategy 'flaresolverr' execution failed for %s: %s", url, exc)

        return None



class CamoufoxStrategy(StealthStrategy):
    name = "camoufox"

    def is_available(self) -> bool:
        # Camoufox has supported Windows since v0.4.0 — use import-check, not platform check.
        try:
            import camoufox  # type: ignore  # noqa: F401
            return True
        except ImportError:
            return False

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        try:
            html, cookies = client._get_with_camoufox(url)
            if html and not client._is_blocked_page(html, url):
                cookie_dict = {}
                if isinstance(cookies, list):
                    cookie_dict = {c["name"]: c["value"] for c in cookies if isinstance(c, dict) and "name" in c and "value" in c}
                elif isinstance(cookies, dict):
                    cookie_dict = cookies
                return StealthResponse(status_code=200, text=html, cookies=cookie_dict, strategy_name=self.name)
        except Exception as exc:
            logger.debug("Strategy 'camoufox' execution failed for %s: %s", url, exc)

        return None



class NodriverStrategy(StealthStrategy):
    name = "nodriver"

    def is_available(self) -> bool:
        try:
            import nodriver  # noqa: F401 # type: ignore
            return True
        except ImportError:
            return False

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        try:
            if hasattr(client, "_get_with_nodriver"):
                html, cookies = client._get_with_nodriver(url)
                if html and not (hasattr(client, "_is_blocked_page") and client._is_blocked_page(html, url)):
                    cookie_dict = {}
                    if isinstance(cookies, list):
                        cookie_dict = {c["name"]: c["value"] for c in cookies if isinstance(c, dict) and "name" in c and "value" in c}
                    elif isinstance(cookies, dict):
                        cookie_dict = cookies
                    return StealthResponse(status_code=200, text=html, cookies=cookie_dict, strategy_name=self.name)
        except Exception as exc:
            logger.debug("Strategy 'nodriver' execution failed for %s: %s", url, exc)

        return None



