"""
session_pool.py — Sticky session and cookie management for resilient crawling.
"""

from __future__ import annotations

import random
import threading
import httpx
from config import USER_AGENTS
import json
from pathlib import Path
from utils.logger import get_logger

logger = get_logger(__name__)


class FlatCookies(dict):
    """A flat dictionary representing cookies that implements a subset of httpx.Cookies.
    
    Prevents CookieConflictError by only maintaining a single value per cookie name.
    """
    def set(self, name: str, value: str, domain: str = "", path: str = "") -> None:
        self[name] = value

    def get(self, name: str, default: str | None = None) -> str | None:
        return super().get(name, default)


class Session:
    """Represents a virtual scraping session with sticky browser properties."""

    def __init__(self, domain: str) -> None:
        self.domain = domain
        self.user_agent = random.choice(USER_AGENTS)
        self.cookies = FlatCookies()
        self.consecutive_errors = 0
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
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load session from disk: %s", exc)

    def save_to_disk(self) -> None:
        """Persist current cookies and user agent to disk."""
        with self.lock:
            try:
                self._cookie_file.parent.mkdir(parents=True, exist_ok=True)
                data = {"user_agent": self.user_agent, "cookies": self.cookies}
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
            try:
                if self._cookie_file.exists():
                    self._cookie_file.unlink()
            except OSError as exc:
                logger.warning("Failed to delete session file: %s", exc)


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
