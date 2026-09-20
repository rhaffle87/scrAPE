"""Frontend shared state, broadcaster, process tracking, and security sanitizers."""

from __future__ import annotations

import asyncio
from collections import deque
import ipaddress
import json
import logging
import os
from pathlib import Path
import re
import socket
from subprocess import Popen
import threading
from typing import Any, Dict, Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
SEEDS_DIR = ROOT_DIR / "seeds"
SEEDS_DIR.mkdir(parents=True, exist_ok=True)

# Global log buffer for streaming to the web UI (capped to 1,000 lines to prevent DOM bloat)
log_buffer: deque[str] = deque(maxlen=1000)
_state_lock = threading.Lock()

task_state: Dict[str, Any] = {
    "status": "idle",
    "current_keyword": None,
    "pid": None,
    "active_metrics": {
        "pages_scanned": 0,
        "images_saved": 0,
        "videos_saved": 0,
        "errors": 0,
    },
}

_current_process: Optional[Popen] = None


def get_current_process() -> Optional[Popen]:
    global _current_process
    return _current_process


def set_current_process(proc: Optional[Popen]) -> None:
    global _current_process
    _current_process = proc


def _is_safe_path_component(name: str) -> bool:
    """Strictly validate path component to prevent path traversal and ensure safety."""
    if not name or not isinstance(name, str):
        return False
    # Use os.path.basename to satisfy CodeQL's requirement for path component
    if os.path.basename(name) != name:
        return False
    # Use a strict regex that CodeQL recognizes as a sanitizer
    if not re.match(r"^[\w\-. ]+$", name):
        return False
    if ".." in name:
        return False
    return True


def _is_safe_target_url(url: str) -> bool:
    """Validate target URL to prevent SSRF against loopback, link-local, or private networks."""
    if os.environ.get("SCRAPE_ALLOW_LOCAL_TARGETS", "").lower() in ("true", "1"):
        return True

    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False

        # Block literal localhost / cloud metadata strings
        if hostname.lower() in ("localhost", "metadata.google.internal", "instance-data"):
            return False

        # Check if hostname is an IP literal
        try:
            ip = ipaddress.ip_address(hostname)
            if (
                ip.is_private
                or ip.is_loopback
                or ip.is_link_local
                or ip.is_reserved
                or ip.is_multicast
            ):
                return False
        except ValueError:
            # Hostname is a domain name; resolve DNS to inspect target IP
            try:
                addr_info = socket.getaddrinfo(hostname, None)
                for item in addr_info:
                    resolved_ip_str = item[4][0]
                    resolved_ip = ipaddress.ip_address(resolved_ip_str)
                    if (
                        resolved_ip.is_private
                        or resolved_ip.is_loopback
                        or resolved_ip.is_link_local
                        or resolved_ip.is_reserved
                        or resolved_ip.is_multicast
                    ):
                        return False
            except socket.gaierror:
                pass

        return True
    except Exception:
        return False


class LogBroadcaster:
    """Manages active SSE client subscriber queues and broadcasts log/progress events."""

    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()
        self._lock = threading.Lock()

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        with self._lock:
            self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        with self._lock:
            self._subscribers.discard(q)

    def broadcast(self, event_type: str, data: dict | str) -> None:
        payload = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
        with self._lock:
            for q in list(self._subscribers):
                try:
                    q.put_nowait(payload)
                except Exception:
                    pass


broadcaster = LogBroadcaster()
