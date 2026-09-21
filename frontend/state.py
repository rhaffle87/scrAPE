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


from common.security import is_safe_target_url as _is_safe_target_url



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
