"""
bandwidth_limiter.py — Thread-safe token bucket bandwidth throttler for media downloads.
"""

from __future__ import annotations

import threading
import time


class BandwidthLimiter:
    """Limits data transfer rate across concurrent download workers.

    Args:
        max_kbps: Maximum transfer rate in Kilobytes per second (KB/s).
                   0 or negative means unlimited.
    """

    def __init__(self, max_kbps: int = 0) -> None:
        self.max_kbps = max(0, max_kbps)
        self._lock = threading.Lock()
        self._last_time = time.monotonic()
        # Token capacity in bytes (allow burst of up to 0.5s worth of data)
        self._max_bytes_per_sec = self.max_kbps * 1024.0
        self._tokens = self._max_bytes_per_sec * 0.5
        self._capacity = max(65536.0, self._max_bytes_per_sec * 0.5)

    def update_rate(self, max_kbps: int) -> None:
        """Dynamically update maximum transfer speed in KB/s."""
        with self._lock:
            self.max_kbps = max(0, max_kbps)
            self._max_bytes_per_sec = self.max_kbps * 1024.0
            self._capacity = max(65536.0, self._max_bytes_per_sec * 0.5)

    def throttle(self, byte_count: int) -> None:
        """Throttle execution to maintain target bandwidth ceiling.

        Args:
            byte_count: Number of bytes processed in the current chunk.
        """
        if self.max_kbps <= 0 or byte_count <= 0:
            return

        with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_time
            self._last_time = now

            # Replenish tokens based on elapsed time
            self._tokens = min(
                self._capacity,
                self._tokens + elapsed * self._max_bytes_per_sec,
            )

            # Consume tokens for this byte chunk
            self._tokens -= byte_count

            # If tokens drop below 0, calculate sleep delay needed to refill tokens to 0
            if self._tokens < 0:
                needed_seconds = (-self._tokens) / self._max_bytes_per_sec
                # Cap maximum single sleep pause at 5 seconds
                sleep_time = min(5.0, max(0.001, needed_seconds))
                time.sleep(sleep_time)
                self._last_time = time.monotonic()
                self._tokens = 0.0
