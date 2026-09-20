"""FastAPI application entrypoint for the scrAPE Brutalist Dashboard and Web Cockpit."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import WEBUI_HOST, WEBUI_PORT
from monitoring.telemetry import register_telemetry_listener
from src.config.version import VERSION

# Shared frontend state, broadcasters, and sanitizers
from frontend.state import (
    ROOT_DIR,
    OUTPUT_DIR,
    SEEDS_DIR,
    log_buffer,
    task_state,
    _state_lock,
    _current_process,
    get_current_process,
    set_current_process,
    LogBroadcaster,
    broadcaster,
    _is_safe_path_component,
    _is_safe_target_url,
)

# Modular Routers
from frontend.routers.dataset import router as dataset_router
from frontend.routers.seeds import (
    router as seeds_router,
    SaveSeedPayload,
    ValidateSeedPayload,
    DiscoverSeedPayload,
    discover_search_urls,
    get_subjects,
)
from frontend.routers.watchdog import router as watchdog_router
from frontend.routers.notifications import router as notifications_router
from frontend.routers.domain_config import router as domain_config_router
from frontend.routers.url_rules import router as url_rules_router
from frontend.routers.subject_profiles import router as subject_profiles_router
from frontend.routers.auth import router as auth_router
from frontend.routers.settings import router as settings_router
from frontend.routers.gallery import router as gallery_router
from frontend.routers.jobs import (
    router as jobs_router,
    ScrapeRequest,
    run_scrape,
    read_subprocess_logs,
    kill_scrape,
    Popen,
    PIPE,
)
from frontend.routers.telemetry import (
    router as telemetry_router,
    get_status,
    get_logs,
    stream_logs,
    get_telemetry_stats,
    stream_telemetry,
    get_stealth_telemetry,
)

logger = logging.getLogger(__name__)

# Wire telemetry listener to SSE broadcaster
register_telemetry_listener(broadcaster.broadcast)

# Initialize FastAPI application
app = FastAPI(title="scrAPE Web GUI", version=VERSION)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Mount modular routers
app.include_router(dataset_router)
app.include_router(seeds_router)
app.include_router(watchdog_router)
app.include_router(notifications_router)
app.include_router(domain_config_router)
app.include_router(url_rules_router)
app.include_router(subject_profiles_router)
app.include_router(auth_router)
app.include_router(settings_router)
app.include_router(gallery_router)
app.include_router(jobs_router)
app.include_router(telemetry_router)

# Mount static asset directories
STATIC_DIR = ROOT_DIR / "frontend" / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/gallery")
def serve_gallery():
    template_path = ROOT_DIR / "frontend" / "templates" / "gallery.html"
    if template_path.exists():
        return FileResponse(template_path)
    return {"error": "gallery.html not found"}


@app.get("/")
def serve_index():
    template_path = ROOT_DIR / "frontend" / "templates" / "index.html"
    return FileResponse(template_path)


# Mount static output files at root for downloaded media previews
# MUST remain declared last so it does not intercept API routes
app.mount("/", StaticFiles(directory=str(OUTPUT_DIR), html=False), name="output")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default=WEBUI_HOST)
    parser.add_argument("--port", type=int, default=WEBUI_PORT)
    args = parser.parse_args()

    uvicorn.run("frontend.app:app", host=args.host, port=args.port, reload=False)
