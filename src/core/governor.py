import logging
import time
import threading
from typing import Dict, Set

LOGGER = logging.getLogger(__name__)

class CrawlGovernor:
    """
    Manages rate limits, dynamic host scaling, and error backoffs
    to ensure the crawl remains healthy without bottlenecking global performance.
    """
    def __init__(self, initial_concurrency: int):
        self.max_concurrency = initial_concurrency
        
        # Internal state
        self.lock = threading.Lock()
        
        # Host tracking
        self.failed_hosts: Set[str] = set()
        self.host_cooldowns: Dict[str, float] = {}  # host -> unpause time
        self.consecutive_host_failures: Dict[str, int] = {}
        
        # Dynamic concurrency tracking
        self.active_workers: Dict[str, int] = {}
        self.host_yield: Dict[str, int] = {}
        
    def is_host_available(self, host: str) -> bool:
        """Checks if a host is currently allowed to be fetched."""
        with self.lock:
            if host in self.failed_hosts:
                return False
            
            if host in self.host_cooldowns:
                if time.monotonic() < self.host_cooldowns[host]:
                    return False
                else:
                    del self.host_cooldowns[host]
            
            return True

    def report_success(self, host: str):
        """Report a successful fetch for a host."""
        with self.lock:
            self.consecutive_host_failures[host] = 0

    def report_429(self, host: str):
        """Report a rate limit hit for a host."""
        with self.lock:
            # Backoff for 5 seconds
            self.host_cooldowns[host] = time.monotonic() + 5.0
            LOGGER.warning(f"Governor: Rate limit (429) hit for {host}. Pausing host for 5s.")

    def report_error(self, host: str, is_login_wall: bool = False):
        """Report a fetch error for a host."""
        with self.lock:
            if is_login_wall:
                self.failed_hosts.add(host)
                LOGGER.warning(f"Governor: Flagging {host} as failed (login wall).")
            else:
                self.consecutive_host_failures[host] = self.consecutive_host_failures.get(host, 0) + 1
                if self.consecutive_host_failures[host] >= 3:
                    self.failed_hosts.add(host)
                    LOGGER.warning(f"Governor: Flagging {host} as failed (3 consecutive errors).")
                else:
                    # Small backoff for normal errors
                    self.host_cooldowns[host] = time.monotonic() + 2.0

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
        Dynamic allocation: Start with 1 worker per domain (Broad Discovery).
        If the domain yields >= 5 media items, scale up to max_concurrency (Deep Scrape).
        """
        with self.lock:
            if self.host_yield.get(host, 0) >= 5:
                return self.max_concurrency
            return 1

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
