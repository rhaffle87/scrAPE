"""
stealth_pipeline.py — Chain-of-Responsibility Strategy Pattern for WAF Fallback Pipeline.

This module encapsulates all stealth fallback engines into pluggable StealthStrategy classes
with per-strategy failure tracking and circuit-breaking.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
import threading
import time
from typing import Any
import httpx


class _StrategyCircuitBreaker:
    """Tracks per-strategy, per-hostname consecutive failures and cooldowns."""

    def __init__(self, failure_threshold: int = 3, cooldown_seconds: float = 3600.0) -> None:
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
                self._cooldown_until[key] = time.monotonic() + self.cooldown_seconds

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


class StealthStrategy(ABC):
    """Abstract base class for all stealth fallback strategies."""

    name: str = "base"

    def is_available(self) -> bool:
        return True

    def can_handle(self, url: str, host: str) -> bool:
        return True

    @abstractmethod
    def execute(self, url: str, client: Any) -> httpx.Response | None:
        """Execute the strategy and return an httpx.Response if successful, else None."""
        pass


class HttpxStrategy(StealthStrategy):
    name = "httpx"

    def execute(self, url: str, client: Any) -> httpx.Response | None:
        headers = client._headers(url)
        resp = client.client.get(url, headers=headers)
        if resp.status_code < 400:
            return resp
        return None


class CrawleeStrategy(StealthStrategy):
    name = "crawlee"

    def execute(self, url: str, client: Any) -> httpx.Response | None:
        # Tier A: Fast cheerio
        try:
            html, _ = client._get_with_crawlee_cheerio(url)
            if html and not client._is_blocked_page(html, url):
                return httpx.Response(200, text=html, request=httpx.Request("GET", url))
        except Exception:
            pass

        # Tier B: Puppeteer stealth
        try:
            html, cookies = client._get_with_crawlee_puppeteer(url)
            if html and not client._is_blocked_page(html, url):
                if cookies:
                    client._session_pool.update_cookies(client._hostname(url), cookies)
                return httpx.Response(200, text=html, request=httpx.Request("GET", url))
        except Exception:
            pass

        return None


class Crawl4AIStrategy(StealthStrategy):
    name = "crawl4ai"

    def execute(self, url: str, client: Any) -> httpx.Response | None:
        try:
            html = client._get_with_crawl4ai(url)
            if html and not client._is_blocked_page(html, url):
                return httpx.Response(200, text=html, request=httpx.Request("GET", url))
        except Exception:
            pass
        return None


class DrissionPageStrategy(StealthStrategy):
    name = "drissionpage"

    def execute(self, url: str, client: Any) -> httpx.Response | None:
        try:
            html, cookies = client._get_with_drissionpage(url)
            if html and not client._is_blocked_page(html, url):
                if cookies:
                    client._session_pool.update_cookies(client._hostname(url), cookies)
                return httpx.Response(200, text=html, request=httpx.Request("GET", url))
        except Exception:
            pass
        return None


class FlareSolverrStrategy(StealthStrategy):
    name = "flaresolverr"

    def execute(self, url: str, client: Any) -> httpx.Response | None:
        try:
            html, cookies = client._get_with_flaresolverr(url)
            if html and not client._is_blocked_page(html, url):
                if cookies:
                    client._session_pool.update_cookies(client._hostname(url), cookies)
                return httpx.Response(200, text=html, request=httpx.Request("GET", url))
        except Exception:
            pass
        return None


class CamoufoxStrategy(StealthStrategy):
    name = "camoufox"

    def execute(self, url: str, client: Any) -> httpx.Response | None:
        try:
            html, cookies = client._get_with_camoufox(url)
            if html and not client._is_blocked_page(html, url):
                if cookies:
                    client._session_pool.update_cookies(client._hostname(url), cookies)
                return httpx.Response(200, text=html, request=httpx.Request("GET", url))
        except Exception:
            pass
        return None


class StealthPipeline:
    """Orchestrates sequential execution of StealthStrategy instances with per-tier circuit-breaking."""

    def __init__(self, strategies: list[StealthStrategy] | None = None) -> None:
        self.circuit_breaker = _StrategyCircuitBreaker()
        if strategies is not None:
            self.strategies = strategies
        else:
            self.strategies = [
                HttpxStrategy(),
                CrawleeStrategy(),
                Crawl4AIStrategy(),
                DrissionPageStrategy(),
                FlareSolverrStrategy(),
                CamoufoxStrategy(),
            ]

    def execute(self, url: str, client: Any, skip_httpx: bool = False) -> httpx.Response:
        from utils.http_client import ScraperBypassError
        from utils.logger import get_logger
        logger = get_logger(__name__)

        host = client._hostname(url)

        for strategy in self.strategies:
            if skip_httpx and strategy.name == "httpx":
                continue

            if not strategy.is_available() or not strategy.can_handle(url, host):
                continue

            if self.circuit_breaker.is_cooling_down(strategy.name, host):
                logger.debug("Skipping strategy '%s' for host '%s' due to active circuit breaker", strategy.name, host)
                continue

            try:
                logger.info("Attempting stealth fallback tier '%s' for %s", strategy.name, url)
                resp = strategy.execute(url, client)
                if resp is not None and resp.status_code < 400:
                    self.circuit_breaker.record_success(strategy.name, host)
                    with client._waf_solve_lock:
                        client._waf_solve_counts[strategy.name] = client._waf_solve_counts.get(strategy.name, 0) + 1
                    return resp
            except Exception as e:
                logger.debug("Strategy '%s' execution error on %s: %s", strategy.name, url, e)

            # Record failure if tier did not yield a clean response
            self.circuit_breaker.record_failure(strategy.name, host)

        raise ScraperBypassError(f"All stealth fallback tiers failed to bypass anti-bot protection for {url}")
