"""FastAPI router for continuous Watchdog monitoring daemon controls."""

import os
import re
import sys
import time
import threading
import subprocess
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/watchdog", tags=["watchdog"])

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
_watchdog_process: Optional[subprocess.Popen] = None
_watchdog_state_lock = threading.Lock()

_watchdog_info: dict = {
    "status": "idle",
    "pid": None,
    "keyword": None,
    "interval": 60,
    "started_at": None,
}


class WatchdogStartRequest(BaseModel):
    keyword: str
    interval: Optional[int] = 60
    seed: Optional[str] = None


@router.get("/status")
def get_watchdog_status():
    """Retrieve current Watchdog background daemon status and telemetry snapshot."""
    global _watchdog_process, _watchdog_info
    from src.cli.monitor_agent import get_watchdog_telemetry_snapshot

    with _watchdog_state_lock:
        if _watchdog_process is not None:
            poll_result = _watchdog_process.poll()
            if poll_result is not None:
                _watchdog_process = None
                _watchdog_info["status"] = "idle"
                _watchdog_info["pid"] = None
            else:
                _watchdog_info["status"] = "active"

        telemetry = get_watchdog_telemetry_snapshot()
        return {
            "status": _watchdog_info["status"],
            "pid": _watchdog_info["pid"],
            "keyword": _watchdog_info.get("keyword"),
            "interval": _watchdog_info.get("interval", 60),
            "telemetry": telemetry,
        }


@router.post("/start")
def start_watchdog(req: WatchdogStartRequest):
    """Launch Watchdog background agent process."""
    global _watchdog_process, _watchdog_info

    with _watchdog_state_lock:
        if _watchdog_process is not None and _watchdog_process.poll() is None:
            return {
                "status": "error",
                "message": f"Watchdog is already running (PID {_watchdog_process.pid})",
                "pid": _watchdog_process.pid,
            }

        cmd = [
            sys.executable,
            "-m",
            "src.cli.monitor_agent",
            "--keyword",
            req.keyword,
            "--interval",
            str(req.interval or 60),
            "--use-state-cache",
        ]
        if req.seed:
            seed_basename = os.path.basename(req.seed)
            if not seed_basename or not re.match(r"^[\w\-. ]+\.txt$", seed_basename):
                raise HTTPException(status_code=400, detail="Invalid seed file name.")
            seeds_base = os.path.abspath(str(ROOT_DIR / "seeds"))
            seed_resolved = os.path.abspath(os.path.join(seeds_base, seed_basename))
            if not seed_resolved.startswith(seeds_base + os.sep):
                raise HTTPException(status_code=400, detail="Seed path traverses outside allowed directory.")
            cmd.extend(["--seed", seed_resolved])

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(ROOT_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            _watchdog_process = proc
            _watchdog_info = {
                "status": "active",
                "pid": proc.pid,
                "keyword": req.keyword,
                "interval": req.interval or 60,
                "started_at": time.time(),
            }

            return {
                "status": "started",
                "message": f"Watchdog daemon started for subject '{req.keyword}'",
                "pid": proc.pid,
            }
        except Exception as e:
            logger.error(f"Failed to launch watchdog process: {e}")
            return {"status": "error", "message": str(e)}


@router.post("/stop")
def stop_watchdog():
    """Stop Watchdog background agent process."""
    global _watchdog_process, _watchdog_info

    with _watchdog_state_lock:
        if _watchdog_process is None or _watchdog_process.poll() is not None:
            _watchdog_process = None
            _watchdog_info["status"] = "idle"
            _watchdog_info["pid"] = None
            return {"status": "idle", "message": "Watchdog was not running"}

        try:
            _watchdog_process.terminate()
            try:
                _watchdog_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                _watchdog_process.kill()
        except Exception as e:
            logger.warning(f"Error terminating watchdog process: {e}")

        _watchdog_process = None
        _watchdog_info["status"] = "idle"
        _watchdog_info["pid"] = None

        return {"status": "idle", "message": "Watchdog daemon stopped successfully"}
