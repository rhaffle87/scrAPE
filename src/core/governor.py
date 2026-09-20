import json
import logging
import time
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Set

LOGGER = logging.getLogger(__name__)


class CrawlGovernor:
    """
    Manages rate limits, dynamic host scaling, AIMD concurrency auto-tuning,
    and error backoffs, integrated with the HardwareLoadGovernor to ensure
    the crawl remains healthy without bottlenecking global performance or
    exhausting host / system resources.
    """

    def __init__(
        self,
        initial_concurrency: int,
        hardware_governor: Optional[Any] = None,
        aimd_increase_step: float = 1.0,
        aimd_decrease_factor: float = 0.5,
        min_concurrency: int = 1,
    ):
        self.max_concurrency = initial_concurrency
        self.min_concurrency = min_concurrency
        self.aimd_increase_step = aimd_increase_step
        self.aimd_decrease_factor = aimd_decrease_factor

        # Internal state
        self.lock = threading.RLock()

        # Host tracking
        self.failed_hosts: Set[str] = set()
        self.host_cooldowns: Dict[str, float] = {}  # host -> unpause time
        self.consecutive_host_failures: Dict[str, int] = {}

        self.config_path = "data/domain_config.json"
        self._last_config_load = 0.0
        self._quarantined_domains: Set[str] = set()

        # Dynamic concurrency tracking
        self.active_workers: Dict[str, int] = {}
        self.host_yield: Dict[str, int] = {}
        self.host_concurrency: Dict[str, float] = {}  # host -> AIMD window
        self.host_latencies: Dict[str, list[float]] = {}  # host -> recent latencies
        self.host_outcomes: Dict[str, list[bool]] = {}  # host -> rolling outcomes (True/False)

        # Hardware Governor integration
        if hardware_governor is not None:
            self.hardware_governor = hardware_governor
        else:
            try:
                from monitoring.hardware_governor import get_governor

                self.hardware_governor = get_governor()
            except Exception:
                self.hardware_governor = None

    def _refresh_quarantine_config(self):
        now = time.monotonic()
        if now - self._last_config_load > 10.0:
            self._last_config_load = now
            p = Path(self.config_path)
            if not p.is_absolute():
                _project_root = Path(__file__).resolve().parent.parent.parent
                p = _project_root / self.config_path
            if p.exists():
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                    quarantined = data.get("quarantined_domains", [])
                    self._quarantined_domains = set(quarantined)
                except Exception:
                    pass

    def is_host_available(self, host: str) -> bool:
        """Checks if a host is currently allowed to be fetched."""
        with self.lock:
            self._refresh_quarantine_config()
            if host in self._quarantined_domains:
                return False

            if host in self.failed_hosts:
                return False

            if self.get_host_health_state(host) == "PARKED":
                if host not in self.host_cooldowns:
                    self.host_cooldowns[host] = time.monotonic() + 15.0
                    LOGGER.warning("Governor: Host %s is PARKED (SR < 25%%). Quiet backoff 15s applied.", host)
                if time.monotonic() < self.host_cooldowns[host]:
                    return False
                else:
                    del self.host_cooldowns[host]

            if host in self.host_cooldowns:
                if time.monotonic() < self.host_cooldowns[host]:
                    return False
                else:
                    del self.host_cooldowns[host]

            return True

    def _record_host_outcome(self, host: str, success: bool):
        outcomes = self.host_outcomes.setdefault(host, [])
        outcomes.append(success)
        if len(outcomes) > 20:
            outcomes.pop(0)

    def _record_host_latency(self, host: str, latency_s: float):
        lats = self.host_latencies.setdefault(host, [])
        lats.append(latency_s)
        if len(lats) > 20:
            lats.pop(0)

    def report_success(self, host: str, latency_s: Optional[float] = None):
        """Report a successful fetch for a host with AIMD additive increase."""
        with self.lock:
            self.consecutive_host_failures[host] = 0
            self._record_host_outcome(host, True)
            current_window = self.host_concurrency.get(host, 1.0)
            if latency_s is not None:
                self._record_host_latency(host, latency_s)
                # Healthy latency threshold (<= 1.5s): Additive Increase
                if latency_s <= 1.5:
                    self.host_concurrency[host] = min(
                        float(self.max_concurrency),
                        current_window + self.aimd_increase_step,
                    )
                elif latency_s >= 3.0:
                    # High latency spike: Multiplicative Decrease
                    self.host_concurrency[host] = max(
                        float(self.min_concurrency),
                        current_window * self.aimd_decrease_factor,
                    )
            else:
                self.host_concurrency[host] = min(
                    float(self.max_concurrency),
                    current_window + self.aimd_increase_step,
                )

    def report_429(self, host: str):
        """Report a rate limit hit for a host with AIMD multiplicative decrease."""
        with self.lock:
            self._record_host_outcome(host, False)
            self.host_cooldowns[host] = time.monotonic() + 5.0
            current_window = self.host_concurrency.get(host, float(self.max_concurrency))
            self.host_concurrency[host] = max(
                float(self.min_concurrency),
                current_window * self.aimd_decrease_factor,
            )
            LOGGER.warning(
                f"Governor: Rate limit (429) hit for {host}. AIMD window reduced to {self.host_concurrency[host]:.1f}. Pausing host for 5s."
            )

    def report_error(self, host: str, is_login_wall: bool = False):
        """Report a fetch error for a host with AIMD multiplicative decrease."""
        with self.lock:
            self._record_host_outcome(host, False)
            current_window = self.host_concurrency.get(host, float(self.max_concurrency))
            self.host_concurrency[host] = max(
                float(self.min_concurrency),
                current_window * self.aimd_decrease_factor,
            )
            if is_login_wall:
                self.failed_hosts.add(host)
                LOGGER.warning(f"Governor: Flagging {host} as failed (login wall).")
            else:
                self.consecutive_host_failures[host] = (
                    self.consecutive_host_failures.get(host, 0) + 1
                )
                if self.consecutive_host_failures[host] >= 3:
                    self.failed_hosts.add(host)
                    LOGGER.warning(
                        f"Governor: Flagging {host} as failed (3 consecutive errors)."
                    )
                else:
                    self.host_cooldowns[host] = time.monotonic() + 2.0

    def get_host_success_rate(self, host: str) -> float:
        """Return rolling success rate for *host* in [0.0, 1.0]."""
        with self.lock:
            outcomes = self.host_outcomes.get(host)
            if not outcomes:
                return 1.0
            return sum(1 for ok in outcomes if ok) / len(outcomes)

    def get_host_health_state(self, host: str) -> str:
        """
        Evaluate real-time host health state based on rolling success rate:
        - PARKED: success rate < 0.25 after at least 5 attempts
        - CRITICAL: success rate < 0.70
        - DEGRADED: 0.70 <= success rate < 0.85
        - HEALTHY: success rate >= 0.85 (or no history yet)
        """
        with self.lock:
            outcomes = self.host_outcomes.get(host)
            if not outcomes:
                return "HEALTHY"
            sr = sum(1 for ok in outcomes if ok) / len(outcomes)
            if len(outcomes) >= 5 and sr < 0.25:
                return "PARKED"
            if sr < 0.70:
                return "CRITICAL"
            if sr < 0.85:
                return "DEGRADED"
            return "HEALTHY"

    def report_latency(self, host: str, latency_s: float):
        """Record request latency for a host and adapt AIMD concurrency window."""
        with self.lock:
            self._record_host_latency(host, latency_s)
            current_window = self.host_concurrency.get(host, float(self.max_concurrency))
            if latency_s > 3.0:
                self.host_concurrency[host] = max(
                    float(self.min_concurrency),
                    current_window * self.aimd_decrease_factor,
                )

    def increment_worker(self, host: str):
        """Increment the active worker count for a host."""
        with self.lock:
            self.active_workers[host] = self.active_workers.get(host, 0) + 1

    def decrement_worker(self, host: str):
        """Decrement the active worker count for a host."""
        with self.lock:
            if host in self.active_workers:
                self.active_workers[host] = max(0, self.active_workers[host] - 1)

    def report_yield(self, host: str, items_found: int):
        """Report successful extraction yield to scale up concurrency."""
        with self.lock:
            self.host_yield[host] = self.host_yield.get(host, 0) + items_found

    def get_allowed_concurrency(self, host: str) -> int:
        """
        Dual Governor dynamic concurrency:
        1. Host allocation: 1 worker for broad discovery (<5 items), scaled AIMD window
           for deep scrape (>=5 items).
        2. System modulation: Modulated by HardwareLoadGovernor scale factor (0.25 to 1.0)
           to prevent system freezes under high memory or CPU stress.
        """
        with self.lock:
            if self.host_yield.get(host, 0) >= 5:
                base = int(round(self.host_concurrency.get(host, float(self.max_concurrency))))
                base = max(self.min_concurrency, min(base, self.max_concurrency))
            else:
                base = 1

            hw_scale = 1.0
            if self.hardware_governor is not None:
                try:
                    hw_scale = self.hardware_governor.get_concurrency_scale_factor()
                except Exception:
                    hw_scale = 1.0

            allowed = max(self.min_concurrency, int(round(base * hw_scale)))
            return allowed

    def get_global_concurrency_limit(self) -> int:
        """Return the overall system concurrency ceiling based on hardware load."""
        with self.lock:
            hw_scale = 1.0
            if self.hardware_governor is not None:
                try:
                    hw_scale = self.hardware_governor.get_concurrency_scale_factor()
                except Exception:
                    hw_scale = 1.0
            return max(1, int(round(self.max_concurrency * hw_scale)))

    def can_acquire_worker(self, host: str) -> bool:
        """Check if a host can take another worker based on its allowed concurrency."""
        with self.lock:
            allowed = self.get_allowed_concurrency(host)
            current = self.active_workers.get(host, 0)
            return current < allowed

    def flag_host_failed(self, host: str, reason: str):
        """Manually flag a host as completely failed."""
        with self.lock:
            self.failed_hosts.add(host)
            LOGGER.info(f"Governor: Host {host} marked failed. Reason: {reason}")

    def cooldown_remaining(self, host: str) -> float:
        """Return seconds remaining in the host's current cooldown (0.0 if none)."""
        with self.lock:
            t = self.host_cooldowns.get(host, 0.0)
            return max(0.0, t - time.monotonic())
