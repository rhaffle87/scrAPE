"""Centralized Watchdog Manager for the scrAPE application."""

import os
import re
import sys
import time
import threading
import subprocess
import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

class WatchdogManager:
    def __init__(self):
        self._watchdog_process: Optional[subprocess.Popen] = None
        self._watchdog_state_lock = threading.Lock()
        self._watchdog_info: dict = {
            "status": "idle",
            "pid": None,
            "keyword": None,
            "interval": 60,
            "started_at": None,
        }

    def get_status(self) -> Dict[str, Any]:
        from src.cli.monitor_agent import get_watchdog_telemetry_snapshot
        
        with self._watchdog_state_lock:
            if self._watchdog_process is not None:
                if self._watchdog_process.poll() is not None:
                    self._watchdog_process = None
                    self._watchdog_info["status"] = "idle"
                    self._watchdog_info["pid"] = None
                else:
                    self._watchdog_info["status"] = "active"

            telemetry = get_watchdog_telemetry_snapshot()
            return {
                "status": self._watchdog_info["status"],
                "pid": self._watchdog_info["pid"],
                "keyword": self._watchdog_info.get("keyword"),
                "interval": self._watchdog_info.get("interval", 60),
                "started_at": self._watchdog_info.get("started_at"),
                "telemetry": telemetry,
            }

    def start(self, keyword: str, interval: Optional[int] = 60, seed: Optional[str] = None) -> Dict[str, Any]:
        with self._watchdog_state_lock:
            if self._watchdog_process is not None and self._watchdog_process.poll() is None:
                return {
                    "status": "error",
                    "message": f"Watchdog is already running (PID {self._watchdog_process.pid})",
                    "pid": self._watchdog_process.pid,
                }

            if not keyword or not re.match(r"^[\w\-. ]+$", keyword):
                raise ValueError("Invalid subject keyword format.")
                
            raw_clean_keyword = re.sub(r"[^\w\-. ]", "", keyword).strip()
            if not raw_clean_keyword or len(raw_clean_keyword) > 128:
                raise ValueError("Subject keyword length or format invalid.")
                
            clean_keyword = raw_clean_keyword

            interval_val = interval if interval is not None else 60
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
            
            if seed:
                seed_basename = os.path.basename(seed)
                if not seed_basename or not re.match(r"^[\w\-. ]+\.txt$", seed_basename):
                    raise ValueError("Invalid seed file name.")
                seeds_base = os.path.abspath(str(ROOT_DIR / "seeds"))
                seed_resolved = os.path.abspath(os.path.join(seeds_base, seed_basename))
                if not seed_resolved.startswith(seeds_base + os.sep):
                    raise ValueError("Seed path traverses outside allowed directory.")
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

                self._watchdog_process = proc
                self._watchdog_info = {
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

    def stop(self) -> Dict[str, Any]:
        with self._watchdog_state_lock:
            if self._watchdog_process is None or self._watchdog_process.poll() is not None:
                self._watchdog_process = None
                self._watchdog_info["status"] = "idle"
                self._watchdog_info["pid"] = None
                return {"status": "idle", "message": "Watchdog was not running"}

            try:
                self._watchdog_process.terminate()
                try:
                    self._watchdog_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self._watchdog_process.kill()
            except Exception as e:
                logger.warning(f"Error terminating watchdog process: {e}")

            self._watchdog_process = None
            self._watchdog_info["status"] = "idle"
            self._watchdog_info["pid"] = None

            return {"status": "idle", "message": "Watchdog daemon stopped successfully"}

# Global singleton instance
watchdog_manager = WatchdogManager()
