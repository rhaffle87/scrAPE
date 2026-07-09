"""
rate_limiter.py — Thread-safe token-bucket rate limiter with optional jitter.
"""

from __future__ import annotations

import random
import threading
import time


class RateLimiter:
    """Token-bucket rate limiter that enforces a minimum interval between calls.

    Args:
        requests_per_second: Maximum sustained request rate.
        jitter: Maximum random extra delay (seconds) added on top of the
                minimum interval to avoid thundering-herd patterns.
                Defaults to 0 (no jitter).
    """

    def __init__(self, requests_per_second: float, jitter: float = 0.0) -> None:
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be > 0")
        self.minimum_interval: float = 1.0 / requests_per_second
        self.jitter: float = max(0.0, jitter)
        self._lock = threading.Lock()
        self._last_request_time: float = 0.0

    @property
    def requests_per_second(self) -> float:
        return 1.0 / self.minimum_interval

    @requests_per_second.setter
    def requests_per_second(self, val: float) -> None:
        if val <= 0:
            raise ValueError("requests_per_second must be > 0")
        with self._lock:
            self.minimum_interval = 1.0 / val

    def wait(self) -> None:
        """Block until the minimum inter-request interval (plus jitter) has elapsed."""
        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request_time
            sleep_time = self.minimum_interval - elapsed
            if self.jitter > 0:
                sleep_time += random.uniform(0, self.jitter)
            if sleep_time > 0:
                time.sleep(sleep_time)
            self._last_request_time = time.monotonic()
