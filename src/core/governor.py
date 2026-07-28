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
                    
    def flag_host_failed(self, host: str, reason: str):
        """Manually flag a host as completely failed."""
        with self.lock:
            self.failed_hosts.add(host)
            LOGGER.info(f"Governor: Host {host} marked failed. Reason: {reason}")
