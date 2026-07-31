"""
stealth_pipeline.py — Chain-of-Responsibility Strategy Pattern for WAF Fallback Pipeline.

This module encapsulates all stealth fallback engines into pluggable StealthStrategy classes
with per-strategy failure tracking, standardized StealthResponse payloads, and circuit-breaking.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import threading
import time
from typing import Any
import httpx


@dataclass
class StealthResponse:
    """Standardized result object returned by all stealth strategies."""

    status_code: int
    text: str
    cookies: dict[str, str] = field(default_factory=dict)
    headers: dict[str, str] = field(default_factory=dict)
    strategy_name: str = "unknown"
    user_agent: str | None = None

    def to_httpx_response(self, request_url: str) -> httpx.Response:
        """Convert StealthResponse to a standard httpx.Response object."""
        return httpx.Response(
            status_code=self.status_code,
            text=self.text,
            headers=self.headers,
            request=httpx.Request("GET", request_url),
        )


class _StrategyCircuitBreaker:
    """Tracks per-strategy, per-hostname consecutive failures and cooldowns."""

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 300.0) -> None:
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._lock = threading.Lock()
        self._failures: dict[tuple[str, str], int] = {}
        self._cooldown_until: dict[tuple[str, str], float] = {}

    def record_failure(self, strategy_name: str, host: str) -> None:
        key = (strategy_name.lower(), host.lower())
        with self._lock:
            count = self._failures.get(key, 0) + 1
            self._failures[key] = count
            if count >= self.failure_threshold:
                # Exponential backoff up to 1800s (30m)
                mult = 2 ** min(5, count - self.failure_threshold)
                cooldown = min(1800.0, self.cooldown_seconds * mult)
                self._cooldown_until[key] = time.monotonic() + cooldown

    def record_success(self, strategy_name: str, host: str) -> None:
        key = (strategy_name.lower(), host.lower())
        with self._lock:
            self._failures[key] = 0
            self._cooldown_until.pop(key, None)

    def is_cooling_down(self, strategy_name: str, host: str) -> bool:
        key = (strategy_name.lower(), host.lower())
        with self._lock:
            until = self._cooldown_until.get(key, 0.0)
            return time.monotonic() < until

    def auto_heal_quarantined_tiers(self) -> int:
        """Checks for expired strategy cooldowns and resets failure counters to restore active pipeline tiers."""
        healed_count = 0
        now = time.monotonic()
        with self._lock:
            expired_keys = [key for key, until in self._cooldown_until.items() if now >= until]
            for key in expired_keys:
                self._failures[key] = 0
                self._cooldown_until.pop(key, None)
                healed_count += 1
        return healed_count


class StealthStrategy(ABC):
    """Abstract base class for all stealth fallback strategies."""

    name: str = "base"

    def is_available(self) -> bool:
        return True

    def can_handle(self, url: str, host: str) -> bool:
        return True

    @abstractmethod
    def execute(self, url: str, client: Any) -> StealthResponse | None:
        """Execute the strategy and return a StealthResponse if successful, else None."""
        pass


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


class CrawleeStrategy(StealthStrategy):
    name = "crawlee"

    def is_available(self) -> bool:
        try:
            from network.crawlee_client import CrawleeClient
            client = CrawleeClient()
            return client._is_server_running()
        except Exception:
            return False

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        # Tier A: Fast cheerio
        try:
            html, _ = client._get_with_crawlee_cheerio(url)
            if html and not client._is_blocked_page(html, url):
                return StealthResponse(status_code=200, text=html, strategy_name=self.name)
        except Exception:
            pass

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
        except Exception:
            pass

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
        except Exception:
            pass
        return None


class DrissionPageStrategy(StealthStrategy):
    name = "drissionpage"

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        try:
            html, cookies = client._get_with_drissionpage(url)
            if html and not client._is_blocked_page(html, url):
                cookie_dict = {}
                if isinstance(cookies, list):
                    cookie_dict = {c["name"]: c["value"] for c in cookies if isinstance(c, dict) and "name" in c and "value" in c}
                elif isinstance(cookies, dict):
                    cookie_dict = cookies
                return StealthResponse(status_code=200, text=html, cookies=cookie_dict, strategy_name=self.name)
        except Exception:
            pass
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
        except Exception:
            pass
        return None


class FlareSolverrStrategy(StealthStrategy):
    name = "flaresolverr"
    _monitor = None

    def is_available(self) -> bool:
        from config import FLARESOLVERR_URL, ENABLE_FLARESOLVERR_FALLBACK
        if not ENABLE_FLARESOLVERR_FALLBACK or not FLARESOLVERR_URL:
            return False
            
        # Check Docker telemetry health to avoid routing to a stuck FlareSolverr instance
        try:
            from network.flaresolverr_monitor import FlareSolverrMonitor
            # Use a singleton pattern or class variable to keep the thread alive
            if self.__class__._monitor is None:
                self.__class__._monitor = FlareSolverrMonitor()
                self.__class__._monitor.start()  # type: ignore
            
            if not self.__class__._monitor.is_healthy():  # type: ignore
                return False
        except ImportError:
            pass

        try:
            base_url = FLARESOLVERR_URL.rsplit("/v1", 1)[0] or FLARESOLVERR_URL
            r = httpx.get(base_url, timeout=1.5)
            return r.status_code == 200
        except Exception:
            return False

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
        except Exception:
            pass
        return None


class CamoufoxStrategy(StealthStrategy):
    name = "camoufox"

    def is_available(self) -> bool:
        return True

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
        except Exception:
            pass
        return None


class StealthPipeline:
    """Orchestrates sequential execution of StealthStrategy instances with per-tier circuit-breaking."""

    def __init__(self, strategies: list[StealthStrategy] | None = None) -> None:
        from captcha.captcha_strategy import ThirdPartyCaptchaStrategy

        self.circuit_breaker = _StrategyCircuitBreaker()
        if strategies is not None:
            self.strategies = strategies
        else:
            self.strategies = [
                HttpxStrategy(),
                ThirdPartyCaptchaStrategy(),
                CrawleeStrategy(),
                Crawl4AIStrategy(),
                DrissionPageStrategy(),
                HeliumStrategy(),
                FlareSolverrStrategy(),
                CamoufoxStrategy(),
            ]

    def get_ordered_strategies(self, host: str, client: Any = None, preferred_engine: str | None = None) -> list[StealthStrategy]:
        """Return strategies re-ordered according to preferred_engine hint if specified or cached in client."""
        ordered = list(self.strategies)
        engine_hint = preferred_engine
        if not engine_hint and client and hasattr(client, "_preferred_engine_by_host"):
            engine_hint = client._preferred_engine_by_host.get(host)
        if engine_hint:
            preferred_name = engine_hint.lower()
            pref_matches = [s for s in ordered if s.name.lower() == preferred_name]
            other = [s for s in ordered if s.name.lower() != preferred_name]
            ordered = pref_matches + other
        return ordered

    def execute(
        self, url: str, client: Any, skip_httpx: bool = False, preferred_engine: str | None = None
    ) -> StealthResponse:
        import concurrent.futures
        from network.http_client import ScraperBypassError
        from monitoring.logger import get_logger
        from monitoring.hardware_governor import get_governor

        logger = get_logger(__name__)
        host = client._hostname(url)
        ordered_strategies = self.get_ordered_strategies(host, client=client, preferred_engine=preferred_engine)

        valid_strategies = []
        for strategy in ordered_strategies:
            if skip_httpx and strategy.name == "httpx":
                continue

            if not strategy.is_available() or not strategy.can_handle(url, host):
                continue

            if self.circuit_breaker.is_cooling_down(strategy.name, host):
                logger.debug(
                    "Skipping strategy '%s' for host '%s' due to active circuit breaker",
                    strategy.name,
                    host,
                )
                continue
                
            valid_strategies.append(strategy)

        if not valid_strategies:
            raise ScraperBypassError(f"No available stealth fallback tiers for {url}")

        def _run_strategy(strategy: StealthStrategy) -> StealthResponse | None:
            logger.info("Attempting stealth fallback tier '%s' for %s", strategy.name, url)
            try:
                res = strategy.execute(url, client)
                if res is not None and res.status_code < 400:
                    return res
            except Exception as e:
                logger.debug("Strategy '%s' execution error on %s: %s", strategy.name, url, e)
            return None

        # Sequential fallback execution
        for strategy in valid_strategies:
            res = _run_strategy(strategy)
            
            if res is not None:
                self.circuit_breaker.record_success(strategy.name, host)
                with client._waf_solve_lock:
                    client._waf_solve_counts[strategy.name] = (
                        client._waf_solve_counts.get(strategy.name, 0) + 1
                    )
                if hasattr(client, "_preferred_engine_by_host"):
                    with client._preferred_engine_lock:
                        client._preferred_engine_by_host[host] = strategy.name

                # Auto-persist harvested cookies and user-agent if present
                if (res.cookies or res.user_agent) and hasattr(client, "_session_pool"):
                    try:
                        client._session_pool.update_session(host, cookies=res.cookies, user_agent=res.user_agent)
                        if hasattr(client, "session_manager"):
                            existing = client.session_manager.load_session(host) or {}
                            if res.cookies:
                                existing.update(res.cookies)
                            client.session_manager.save_session(host, existing)
                    except Exception as c_err:
                        logger.warning(
                            "Failed to persist harvested session for %s: %s", host, c_err
                        )
                return res
            else:
                # Record failure if tier did not yield a clean response
                self.circuit_breaker.record_failure(strategy.name, host)

        raise ScraperBypassError(
            f"All stealth fallback tiers failed to bypass anti-bot protection for {url}"
        )

