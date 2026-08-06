"""FastAPI router for continuous Watchdog monitoring daemon controls."""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.core.watchdog_manager import watchdog_manager

router = APIRouter(prefix="/api/watchdog", tags=["watchdog"])
logger = logging.getLogger(__name__)


class WatchdogStartRequest(BaseModel):
    keyword: str
    interval: Optional[int] = 60
    seed: Optional[str] = None


@router.get("/status")
def get_watchdog_status():
    """Retrieve current Watchdog background daemon status and telemetry snapshot."""
    return watchdog_manager.get_status()


@router.post("/start")
def start_watchdog(req: WatchdogStartRequest):
    """Launch Watchdog background agent process."""
    try:
        return watchdog_manager.start(req.keyword, req.interval, req.seed)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stop")
def stop_watchdog():
    """Stop Watchdog background agent process."""
    return watchdog_manager.stop()
