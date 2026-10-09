"""
session_pool.py — Sticky session and cookie management for resilient crawling.
"""

from __future__ import annotations

import random
import threading
from config import USER_AGENTS
import json
from pathlib import Path
from monitoring.logger import get_logger

logger = get_logger(__name__)


class FlatCookies(dict):
    """A flat dictionary representing cookies that implements a subset of httpx.Cookies.
    
    Prevents CookieConflictError by only maintaining a single value per cookie name.
    """
    def set(self, name: str, value: str, domain: str = "", path: str = "") -> None:
        self[name] = value


class Session:
    """Represents a virtual scraping session with sticky browser properties."""

    def __init__(self, domain: str) -> None:
        self.domain = domain
        self.user_agent = random.choice(USER_AGENTS)
        self.cookies = FlatCookies()
        self.consecutive_errors = 0
        self.tls_profile: str = "chrome120"
        self.bound_proxy: str | None = None
        self.clearance_expires_at: float = 0.0
        self.lock = threading.Lock()
        self._cookie_file = Path(".cache") / "cookies" / f"{self.domain}.json"
        self._load_from_disk()

    def _load_from_disk(self) -> None:
        try:
            if self._cookie_file.exists():
                data = json.loads(self._cookie_file.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    if "user_agent" in data:
                        self.user_agent = data["user_agent"]
                    if "cookies" in data and isinstance(data["cookies"], dict):
                        self.cookies.update(data["cookies"])
                    if "tls_profile" in data:
                        self.tls_profile = str(data["tls_profile"])
                    if "bound_proxy" in data:
                        self.bound_proxy = data["bound_proxy"]
                    if "clearance_expires_at" in data:
                        self.clearance_expires_at = float(data["clearance_expires_at"])
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load session from disk: %s", exc)

    def save_to_disk(self) -> None:
        """Persist current cookies and user agent to disk."""
        with self.lock:
            try:
                self._cookie_file.parent.mkdir(parents=True, exist_ok=True)
                data = {
                    "user_agent": self.user_agent,
                    "cookies": dict(self.cookies),
                    "tls_profile": self.tls_profile,
                    "bound_proxy": self.bound_proxy,
                    "clearance_expires_at": self.clearance_expires_at,
                }
                self._cookie_file.write_text(json.dumps(data), encoding="utf-8")
            except (OSError, TypeError) as exc:
                logger.warning("Failed to save session to disk: %s", exc)

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
            self.user_agent = (
                random.choice(available_uas) if available_uas else self.user_agent
            )
            self.cookies.clear()
            self.consecutive_errors = 0
            self.tls_profile = "chrome120"
            self.bound_proxy = None
            self.clearance_expires_at = 0.0
            try:
                if self._cookie_file.exists():
                    self._cookie_file.unlink()
            except OSError as exc:
                logger.warning("Failed to delete session file: %s", exc)

    def bind_tls_session(
        self,
        cookies: list[dict] | dict,
        tls_profile: str = "chrome120",
        user_agent: str | None = None,
        proxy: str | None = None,
        ttl_seconds: float = 3600.0,
    ) -> None:
        """Bind solved cf_clearance cookies to a matching TLS profile, IP proxy, and TTL."""
        import time

        with self.lock:
            if user_agent:
                self.user_agent = user_agent
            if isinstance(cookies, list):
                for c in cookies:
                    if isinstance(c, dict) and "name" in c and "value" in c:
                        self.cookies[c["name"]] = c["value"]
            elif isinstance(cookies, dict):
                self.cookies.update(cookies)
            self.tls_profile = tls_profile
            self.bound_proxy = proxy
            self.clearance_expires_at = time.time() + ttl_seconds
        self.save_to_disk()

    def is_clearance_valid(self, proxy: str | None = None) -> bool:
        """Return True if cf_clearance exists, is unexpired, and matches proxy IP binding."""
        import time

        with self.lock:
            if "cf_clearance" not in self.cookies:
                return False
            if time.time() >= self.clearance_expires_at:
                return False
            if self.bound_proxy is not None and proxy is not None and self.bound_proxy != proxy:
                return False
            return True

    def update_cookies(self, cookies: list[dict] | dict, user_agent: str | None = None) -> None:
        """Update session cookies and optional user_agent, then persist to disk."""
        with self.lock:
            if user_agent:
                self.user_agent = user_agent
            if isinstance(cookies, list):
                for c in cookies:
                    if isinstance(c, dict) and "name" in c and "value" in c:
                        self.cookies[c["name"]] = c["value"]
            elif isinstance(cookies, dict):
                self.cookies.update(cookies)
        self.save_to_disk()

    def update_session(self, cookies: list[dict] | dict | None = None, user_agent: str | None = None) -> None:
        """Update session cookies and/or User-Agent."""
        if cookies is not None:
            self.update_cookies(cookies, user_agent=user_agent)
        elif user_agent:
            with self.lock:
                self.user_agent = user_agent
            self.save_to_disk()


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

    def update_cookies(self, domain: str, cookies: list[dict] | dict, user_agent: str | None = None) -> None:
        """Update session cookies and optional user_agent for *domain*."""
        session = self.get_session(domain)
        session.update_cookies(cookies, user_agent=user_agent)

    set_cookies = update_cookies

    def update_session(self, domain: str, cookies: list[dict] | dict | None = None, user_agent: str | None = None) -> None:
        """Update session cookies and/or User-Agent for *domain*."""
        session = self.get_session(domain)
        session.update_session(cookies=cookies, user_agent=user_agent)

    def bind_tls_session(
        self,
        domain: str,
        cookies: list[dict] | dict,
        tls_profile: str = "chrome120",
        user_agent: str | None = None,
        proxy: str | None = None,
        ttl_seconds: float = 3600.0,
    ) -> None:
        """Bind solved cf_clearance cookies for *domain* to TLS profile, proxy IP, and TTL."""
        session = self.get_session(domain)
        session.bind_tls_session(
            cookies,
            tls_profile=tls_profile,
            user_agent=user_agent,
            proxy=proxy,
            ttl_seconds=ttl_seconds,
        )

    def is_clearance_valid(self, domain: str, proxy: str | None = None) -> bool:
        """Check if *domain* has a valid, unexpired cf_clearance matching proxy IP binding."""
        session = self.get_session(domain)
        return session.is_clearance_valid(proxy=proxy)

