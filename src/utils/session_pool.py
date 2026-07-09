"""
session_pool.py — Sticky session and cookie management for resilient crawling.
"""

from __future__ import annotations

import random
import threading
import httpx
from config import USER_AGENTS


class Session:
    """Represents a virtual scraping session with sticky browser properties."""

    def __init__(self, domain: str) -> None:
        self.domain = domain
        self.user_agent = random.choice(USER_AGENTS)
        self.cookies = httpx.Cookies()
        self.consecutive_errors = 0
        self.lock = threading.Lock()

    def get_headers(self) -> dict[str, str]:
        """Return consistent headers for this session."""
        return {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

    def reset_identity(self) -> None:
        """Rotate User-Agent and clear cookies on blocks."""
        with self.lock:
            # Pick a different user agent if possible
            available_uas = [ua for ua in USER_AGENTS if ua != self.user_agent]
            self.user_agent = random.choice(available_uas) if available_uas else self.user_agent
            self.cookies.clear()
            self.consecutive_errors = 0


class SessionPool:
    """Thread-safe pool of active scraping sessions grouped by domain."""

    def __init__(self) -> None:
        self._sessions: dict[str, Session] = {}
        self._lock = threading.Lock()

    def get_session(self, domain: str) -> Session:
        """Get (or lazily create) the sticky session for a domain."""
        domain_key = domain.lower()
        with self._lock:
            if domain_key not in self._sessions:
                self._sessions[domain_key] = Session(domain_key)
            return self._sessions[domain_key]

    def rotate_session(self, domain: str) -> None:
        """Force reset identity for a domain session due to blocks or rate limiting."""
        session = self.get_session(domain)
        session.reset_identity()
