from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any
from urllib.parse import urlparse

from utils.notification_manager import NotificationPipeline

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
        self.bytes_transferred: int = 0

    def record_success(self, latency_ms: float) -> None:
        self.successes += 1
        self.consecutive_failures = 0
        self.total_latency_ms += latency_ms
        self.avg_latency_ms = round(self.total_latency_ms / max(1, self.successes), 1)
        if latency_ms > 3000.0:
            self.cooldown_until = time.monotonic() + 300.0
            LOGGER.warning(
                "Proxy '%s' entered 5-minute cooldown (high latency %.1f ms > 3000ms).",
                self.url,
                latency_ms,
            )

    def record_failure(self) -> None:
        self.failures += 1
        self.consecutive_failures += 1
        if self.consecutive_failures >= 3:
            # 5-minute auto-eviction cooldown
            self.cooldown_until = time.monotonic() + 300.0
            LOGGER.warning(
                "Proxy '%s' entered 5-minute cooldown (3 consecutive failures).",
                self.url,
            )

    def record_bytes(self, num_bytes: int) -> None:
        if num_bytes > 0:
            self.bytes_transferred += num_bytes

    def is_healthy(self) -> bool:
        return time.monotonic() >= self.cooldown_until


class ProxyPoolManager:
    """Thread-safe Proxy Pool Manager handling health probing, latency sorting, bandwidth quota, and auto-eviction."""

    _instance: ProxyPoolManager | None = None
    _lock = threading.RLock()

    def __init__(self, max_bandwidth_mb: float | None = None) -> None:
        self._pool_lock = threading.RLock()
        self._proxies: dict[str, ProxyInfo] = {}
        self._domain_bindings: dict[str, str] = {}

        env_max_mb = float(os.getenv("PROXY_MAX_BANDWIDTH_MB", "500.0"))
        mb = max_bandwidth_mb if max_bandwidth_mb is not None else env_max_mb
        self.max_bandwidth_bytes: int = int(mb * 1024 * 1024)

        self._warning_sent: bool = False
        self._halt_sent: bool = False

    @classmethod
    def get_instance(cls) -> ProxyPoolManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def reset_bandwidth_stats(self) -> None:
        """Reset bandwidth stats and quota warning flags."""
        with self._pool_lock:
            for p in self._proxies.values():
                p.bytes_transferred = 0
            self._warning_sent = False
            self._halt_sent = False

    def get_total_bytes_transferred(self) -> int:
        with self._pool_lock:
            return sum(p.bytes_transferred for p in self._proxies.values())

    def record_bytes_transferred(self, proxy_url_or_domain: str, num_bytes: int) -> None:
        """Record bandwidth consumption for a proxy URL or bound domain."""
        if num_bytes <= 0:
            return

        with self._pool_lock:
            target_proxy = None
            if proxy_url_or_domain in self._proxies:
                target_proxy = self._proxies[proxy_url_or_domain]
            elif proxy_url_or_domain.lower() in self._domain_bindings:
                bound_url = self._domain_bindings[proxy_url_or_domain.lower()]
                target_proxy = self._proxies.get(bound_url)

            if target_proxy:
                target_proxy.record_bytes(num_bytes)

            total_bytes = self.get_total_bytes_transferred()
            quota_80 = int(0.80 * self.max_bandwidth_bytes)

            if total_bytes >= quota_80 and not self._warning_sent:
                self._warning_sent = True
                LOGGER.warning(
                    "Proxy pool bandwidth usage (%.2f MB) reached 80%% quota warning limit (%.2f MB).",
                    total_bytes / (1024 * 1024),
                    self.max_bandwidth_bytes / (1024 * 1024),
                )
                NotificationPipeline().notify_watchdog_status(
                    "Proxy pool bandwidth usage reached 80% quota warning limit."
                )

            if total_bytes >= self.max_bandwidth_bytes and not self._halt_sent:
                self._halt_sent = True
                LOGGER.warning(
                    "Proxy pool bandwidth usage (%.2f MB) reached 100%% quota limit. Auto-halting proxy routing.",
                    total_bytes / (1024 * 1024),
                )
                NotificationPipeline().notify_watchdog_status(
                    "Proxy pool bandwidth quota exhausted (500 MB). Auto-halting proxy routing."
                )

    def set_proxies(self, proxy_list: list[str]) -> None:
        """Register or update proxy URLs in the pool."""
        with self._pool_lock:
            for p in proxy_list:
                cleaned = p.strip()
                if cleaned and cleaned not in self._proxies:
                    self._proxies[cleaned] = ProxyInfo(cleaned)

    def bind_domain_proxy(self, domain: str, proxy_url: str) -> None:
        """Explicitly bind a specific proxy URL to a domain."""
        with self._pool_lock:
            domain_clean = domain.lower().strip()
            cleaned_proxy = proxy_url.strip()
            if cleaned_proxy and cleaned_proxy not in self._proxies:
                self._proxies[cleaned_proxy] = ProxyInfo(cleaned_proxy)
            self._domain_bindings[domain_clean] = cleaned_proxy

    def get_best_proxy(self) -> str | None:
        """Return the lowest-latency healthy proxy from the pool, or None if quota exhausted."""
        with self._pool_lock:
            if self.get_total_bytes_transferred() >= self.max_bandwidth_bytes:
                LOGGER.warning("Proxy pool bandwidth quota exhausted. Halting proxy routing.")
                return None

            healthy = [p for p in self._proxies.values() if p.is_healthy()]
            if not healthy:
                return None
            healthy.sort(key=lambda p: (p.consecutive_failures, p.avg_latency_ms))
            return healthy[0].url

    def get_proxy_for_domain(self, domain: str) -> str | None:
        """Return sticky assigned proxy for *domain*, or assign best available proxy."""
        with self._pool_lock:
            if self.get_total_bytes_transferred() >= self.max_bandwidth_bytes:
                LOGGER.warning("Proxy pool bandwidth quota exhausted. Halting proxy routing for %s.", domain)
                return None

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
                    "bytes_transferred": p.bytes_transferred,
                }
                for p in self._proxies.values()
            ]
