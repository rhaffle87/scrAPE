from __future__ import annotations

import logging
import threading
import time
from typing import Any
from urllib.parse import urlparse
import requests

LOGGER = logging.getLogger(__name__)


class ProxyInfo:
    """Dataclass holding health metrics and metadata for a single proxy."""

    def __init__(self, proxy_url: str):
        self.url = proxy_url.strip()
        self.parsed = urlparse(self.url)
        self.scheme = self.parsed.scheme.lower() or "http"
        self.host = self.parsed.hostname or ""
        self.port = self.parsed.port or (443 if self.scheme == "https" else 80)
        self.username = self.parsed.username
        self.password = self.parsed.password

        self.successes: int = 0
        self.failures: int = 0
        self.consecutive_failures: int = 0
        self.total_latency_ms: float = 0.0
        self.avg_latency_ms: float = 0.0
        self.cooldown_until: float = 0.0

    def record_success(self, latency_ms: float) -> None:
        self.successes += 1
        self.consecutive_failures = 0
        self.total_latency_ms += latency_ms
        self.avg_latency_ms = round(self.total_latency_ms / max(1, self.successes), 1)

    def record_failure(self) -> None:
        self.failures += 1
        self.consecutive_failures += 1
        if self.consecutive_failures >= 3:
            # 10-minute auto-eviction cooldown
            self.cooldown_until = time.monotonic() + 600.0
            LOGGER.warning(
                "Proxy '%s' entered 10-minute cooldown (3 consecutive failures).",
                self.url,
            )

    def is_healthy(self) -> bool:
        return time.monotonic() >= self.cooldown_until


class ProxyPoolManager:
    """Thread-safe Proxy Pool Manager handling health probing, latency sorting, sticky domain binding, and auto-eviction."""

    _instance: ProxyPoolManager | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._pool_lock = threading.Lock()
        self._proxies: dict[str, ProxyInfo] = {}
        self._domain_bindings: dict[str, str] = {}

    @classmethod
    def get_instance(cls) -> ProxyPoolManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def set_proxies(self, proxy_list: list[str]) -> None:
        """Register or update proxy URLs in the pool."""
        with self._pool_lock:
            for p in proxy_list:
                cleaned = p.strip()
                if cleaned and cleaned not in self._proxies:
                    self._proxies[cleaned] = ProxyInfo(cleaned)

    def get_best_proxy(self) -> str | None:
        """Return the lowest-latency healthy proxy from the pool."""
        with self._pool_lock:
            healthy = [p for p in self._proxies.values() if p.is_healthy()]
            if not healthy:
                return None
            healthy.sort(key=lambda p: (p.consecutive_failures, p.avg_latency_ms))
            return healthy[0].url

    def get_proxy_for_domain(self, domain: str) -> str | None:
        """Return sticky assigned proxy for *domain*, or assign best available proxy."""
        with self._pool_lock:
            domain_clean = domain.lower().strip()
            bound_url = self._domain_bindings.get(domain_clean)
            if bound_url and bound_url in self._proxies and self._proxies[bound_url].is_healthy():
                return bound_url

            best_proxy = self.get_best_proxy()
            if best_proxy:
                self._domain_bindings[domain_clean] = best_proxy
            return best_proxy

    def record_proxy_success(self, proxy_url: str, latency_ms: float) -> None:
        with self._pool_lock:
            info = self._proxies.get(proxy_url)
            if info:
                info.record_success(latency_ms)

    def record_proxy_failure(self, proxy_url: str) -> None:
        with self._pool_lock:
            info = self._proxies.get(proxy_url)
            if info:
                info.record_failure()

    def get_pool_status(self) -> list[dict[str, Any]]:
        with self._pool_lock:
            return [
                {
                    "url": p.url,
                    "healthy": p.is_healthy(),
                    "successes": p.successes,
                    "failures": p.failures,
                    "consecutive_failures": p.consecutive_failures,
                    "avg_latency_ms": p.avg_latency_ms,
                }
                for p in self._proxies.values()
            ]
