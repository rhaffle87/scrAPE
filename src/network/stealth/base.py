from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import threading
import time
from typing import Any
import httpx
from config import STEALTH_TIER_COOLDOWN_SECONDS
from monitoring.logger import get_logger

logger = get_logger(__name__)

class StealthTierHealthManager:
    """Monitors real-time health, latency, and auto-cooldown circuit breaking for WAF stealth tiers."""

    _instance: StealthTierHealthManager | None = None
    _lock = threading.Lock()

    def __init__(self) -> None:
        self._tier_lock = threading.Lock()
        self._health: dict[str, dict[str, Any]] = {}
        for tier in ["flaresolverr", "crawlee", "drissionpage", "camoufox", "nodriver"]:
            self._health[tier] = {
                "successes": 0,
                "failures": 0,
                "consecutive_failures": 0,
                "total_latency_ms": 0.0,
                "avg_latency_ms": 0.0,
                "cooldown_until": 0.0,
            }

    @classmethod
    def get_instance(cls) -> StealthTierHealthManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def is_healthy(self, tier: str) -> bool:
        tier_name = tier.lower()
        with self._tier_lock:
            info = self._health.get(tier_name)
            if not info:
                return True
            if time.monotonic() < info["cooldown_until"]:
                return False
            return True

    def record_success(self, tier: str, latency_ms: float) -> None:
        tier_name = tier.lower()
        with self._tier_lock:
            info = self._health.setdefault(
                tier_name,
                {
                    "successes": 0,
                    "failures": 0,
                    "consecutive_failures": 0,
                    "total_latency_ms": 0.0,
                    "avg_latency_ms": 0.0,
                    "cooldown_until": 0.0,
                },
            )
            info["successes"] += 1
            info["consecutive_failures"] = 0
            info["total_latency_ms"] += latency_ms
            info["avg_latency_ms"] = round(
                info["total_latency_ms"] / max(1, info["successes"]), 1
            )

    def record_failure(self, tier: str) -> None:
        tier_name = tier.lower()
        with self._tier_lock:
            info = self._health.setdefault(
                tier_name,
                {
                    "successes": 0,
                    "failures": 0,
                    "consecutive_failures": 0,
                    "total_latency_ms": 0.0,
                    "avg_latency_ms": 0.0,
                    "cooldown_until": 0.0,
                },
            )
            info["failures"] += 1
            info["consecutive_failures"] += 1
            if info["consecutive_failures"] >= 3:
                info["cooldown_until"] = time.monotonic() + STEALTH_TIER_COOLDOWN_SECONDS
                logger.warning(
                    "WAF stealth tier '%s' entered circuit-breaker cooldown (3 consecutive failures).",
                    tier_name,
                )

    def get_health_snapshot(self) -> dict[str, Any]:
        with self._tier_lock:
            now = time.monotonic()
            snapshot = {}
            for t, info in self._health.items():
                snapshot[t] = {
                    "healthy": now >= info["cooldown_until"],
                    "successes": info["successes"],
                    "failures": info["failures"],
                    "consecutive_failures": info["consecutive_failures"],
                    "avg_latency_ms": info["avg_latency_ms"],
                    "cooldown_remaining_sec": max(
                        0, int(info["cooldown_until"] - now)
                    ),
                }
            return snapshot




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


