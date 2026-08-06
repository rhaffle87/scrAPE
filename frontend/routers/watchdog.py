"""FastAPI router for continuous Watchdog monitoring daemon controls."""

import shlex
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
            if _watchdog_process.poll() is not None:
                _watchdog_process = None
                _watchdog_info["status"] = "idle"
                _watchdog_info["pid"] = None

        telemetry = get_watchdog_telemetry_snapshot()
        return {
            "status": _watchdog_info["status"],
            "pid": _watchdog_info["pid"],
            "keyword": _watchdog_info["keyword"],
            "interval": _watchdog_info["interval"],
            "started_at": _watchdog_info["started_at"],
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

        # Sanitize and validate inputs to prevent uncontrolled command execution (CodeQL remediation)
        if not req.keyword or not re.match(r"^[\w\-. ]+$", req.keyword):
            raise HTTPException(status_code=400, detail="Invalid subject keyword format.")
        raw_clean_keyword = re.sub(r"[^\w\-. ]", "", req.keyword).strip()
        if not raw_clean_keyword or len(raw_clean_keyword) > 128:
            raise HTTPException(status_code=400, detail="Subject keyword length or format invalid.")

        clean_keyword = shlex.quote(raw_clean_keyword)

        interval_val = req.interval if req.interval is not None else 60
        clean_interval = max(10, min(interval_val, 86400))




        cmd = [
            sys.executable,
            "-m",
            "src.cli.monitor_agent",
            "--keyword",
            clean_keyword,
            "--interval",
            str(clean_interval),
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
            cmd.extend(["--seed", shlex.quote(seed_resolved)])

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
                "keyword": clean_keyword,
                "interval": clean_interval,
                "started_at": time.time(),
            }

            return {
                "status": "started",
                "message": f"Watchdog daemon started for subject '{clean_keyword}'",
                "pid": proc.pid,
            }
        except Exception as e:
            logger.error("Failed to launch watchdog process: %s", e)
            return {"status": "error", "message": "Failed to launch watchdog daemon process."}



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
