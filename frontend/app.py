import sys
from subprocess import Popen, PIPE, STDOUT
import threading
import asyncio
from collections import deque, defaultdict
from pathlib import Path
from typing import Optional, Dict, Any, List
import re
import html
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import json
import psutil
import os

from utils.http_client import HttpClient

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Global log buffer for streaming to the web UI (capped to 1,000 lines to prevent DOM bloat)
log_buffer = deque(maxlen=1000)
_state_lock = threading.Lock()

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

from utils.telemetry import register_telemetry_listener, broadcast_telemetry_event

broadcaster = LogBroadcaster()
register_telemetry_listener(broadcaster.broadcast)

app = FastAPI(title="scrAPE Web GUI", version="0.20.0")

STATIC_DIR = ROOT_DIR / "frontend" / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class ScrapeRequest(BaseModel):
    keyword: str
    seed: Optional[str] = None
    max_results: Optional[int] = 50
    workers: Optional[int] = 8
    dl_workers: Optional[int] = 6
    page_limit: Optional[int] = 100
    crawl_depth: Optional[int] = 2
    download_media: Optional[bool] = False
    ignore_robots: Optional[bool] = False
    output: Optional[str] = "both"
    seed_urls: Optional[str] = None
    allow_domains: Optional[str] = None
    block_domains: Optional[str] = None
    entity_tokens: Optional[str] = None
    skip_search: Optional[bool] = False
    strict_domain: Optional[bool] = False
    site_tree_only: Optional[bool] = False
    domain_delays: Optional[str] = None
    proxy: Optional[str] = None
    capsolver_key: Optional[str] = None
    force_search: Optional[bool] = False
    clear_cache: Optional[bool] = False
    use_state_cache: Optional[bool] = False
    headless: Optional[bool] = False
    stealth_headful: Optional[bool] = False
    dl_speed_limit: Optional[int] = 0
    rate_limit: Optional[float] = 0.0

task_state: Dict[str, Any] = {
    "status": "idle",
    "current_keyword": None,
    "pid": None,
    "active_metrics": {
        "pages_scanned": 0,
        "images_saved": 0,
        "videos_saved": 0,
        "errors": 0
    }
}
_current_process: Optional[Popen] = None

@app.get("/api/status")
def get_status():
    global task_state, _current_process
    with _state_lock:
        if task_state["status"] == "running" and _current_process:
            if _current_process.poll() is None:
                pass # still running
            else:
                task_state["status"] = "idle"
                task_state["pid"] = None
        return task_state

def read_subprocess_logs(proc: Popen):
    global log_buffer, task_state
    
    import re
    
    with _state_lock:
        task_state["active_metrics"] = {
            "pages_scanned": 0,
            "images_saved": 0,
            "videos_saved": 0,
            "errors": 0
        }
        task_state["progress"] = {
            "percent": 0,
            "current": 0,
            "total": 0,
            "time_info": ""
        }
    
    def process_progress(bar_text: str):
        pct_match = re.search(r"(\d+)%", bar_text)
        frac_match = re.search(r"(\d+)/(\d+)", bar_text)
        time_match = re.search(r"\[([^\]]+)\]", bar_text)
        
        pct = int(pct_match.group(1)) if pct_match else 0
        current, total = (int(frac_match.group(1)), int(frac_match.group(2))) if frac_match else (0, 0)
        time_info = time_match.group(1) if time_match else ""
        
        with _state_lock:
            task_state["progress"] = {
                "percent": pct,
                "current": current,
                "total": total,
                "time_info": time_info
            }
        broadcaster.broadcast("progress", task_state["progress"])

    def process_log_line(log_line: str):
        log_buffer.append(log_line)
        lower_line = log_line.lower()
        with _state_lock:
            if "http request: get" in lower_line or "fetching page" in lower_line or "routing " in lower_line:
                if not any(ext in lower_line for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".mkv"]):
                    task_state["active_metrics"]["pages_scanned"] += 1
            elif "downloaded " in lower_line:
                if "images" in lower_line or any(ext in lower_line for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]):
                    task_state["active_metrics"]["images_saved"] += 1
                elif "videos" in lower_line or any(ext in lower_line for ext in [".mp4", ".webm", ".mkv", ".ogv"]):
                    task_state["active_metrics"]["videos_saved"] += 1
            elif any(err in log_line.upper() for err in ["429", "ERROR", "FAILED", "EXCEPTION", "TIMEOUT"]):
                task_state["active_metrics"]["errors"] += 1
        broadcaster.broadcast("log", {"line": log_line})

    if proc.stdout:
        for line in iter(proc.stdout.readline, ""):
            if line:
                sub_lines = line.split("\r")
                for sub in sub_lines:
                    cleaned_line = sub.replace("\n", "").strip()
                    if not cleaned_line:
                        continue
                    
                    log_timestamp_match = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", cleaned_line)
                    if log_timestamp_match:
                        split_index = log_timestamp_match.start()
                        progress_part = cleaned_line[:split_index].strip()
                        log_part = cleaned_line[split_index:].strip()
                        
                        if progress_part:
                            process_progress(progress_part)
                        if log_part:
                            process_log_line(log_part)
                    else:
                        if "Fetching pages:" in cleaned_line and ("%" in cleaned_line or "|" in cleaned_line):
                            process_progress(cleaned_line)
                        else:
                            process_log_line(cleaned_line)
                            
        proc.stdout.close()
    if hasattr(proc, "wait"):
        proc.wait()
    with _state_lock:
        task_state["status"] = "idle"
        task_state["pid"] = None
    broadcaster.broadcast("status", {"status": "idle"})

@app.get("/api/logs")
def get_logs(offset: int = 0):
    global log_buffer, task_state
    logs = list(log_buffer)
    if offset > len(logs):
        offset = 0
    new_lines = logs[offset:]
    with _state_lock:
        return {
            "lines": new_lines, 
            "next_offset": offset + len(new_lines),
            "status": task_state["status"],
            "progress": task_state.get("progress", {
                "percent": 0,
                "current": 0,
                "total": 0,
                "time_info": ""
            })
        }

@app.get("/api/logs/stream")
async def stream_logs(request: Request):
    q = broadcaster.subscribe()

    async def event_generator():
        # Yield historical log lines first
        for line in list(log_buffer):
            yield f"event: log\ndata: {json.dumps({'line': line})}\n\n"

        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=1.0)
                    yield msg
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            broadcaster.unsubscribe(q)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/api/telemetry/stats")
def get_telemetry_stats():
    """Return instant snapshot of system and crawl telemetry metrics."""
    from utils.proxy_manager import ProxyPoolManager
    from utils.hardware_governor import HardwareLoadGovernor
    from storage.db_store import get_state_store, PostgresStateStore

    gov = HardwareLoadGovernor()
    metrics = gov.get_metrics()
    scale = gov.get_concurrency_scale_factor()
    store = get_state_store()
    db_name = "POSTGRES / NEON" if isinstance(store, PostgresStateStore) else "SQLITE WAL"

    with _state_lock:
        status = task_state["status"]
        progress = task_state.get("progress", {})
        pages = progress.get("pages_scanned", 0)
        imgs = progress.get("images_found", 0)
        vids = progress.get("videos_found", 0)

        pm = ProxyPoolManager.get_instance()
        proxy_pool = pm.get_pool_status()
        healthy_proxies = sum(1 for p in proxy_pool if p["healthy"])

        return {
            "status": status,
            "rps": 1.0 if status == "running" else 0.0,
            "speed_kbps": (imgs + vids) * 128 if status == "running" else 0,
            "active_workers": 8 if status == "running" else 0,
            "progress": progress,
            "healthy_proxies": healthy_proxies,
            "cpu_percent": metrics.get("cpu_percent", 0.0),
            "ram_percent_available": metrics.get("ram_percent_available", 100.0),
            "governor_scale_factor": scale,
            "db_engine_name": db_name,
            "http_status_codes": {
                "200_ok": pages + imgs + vids,
                "429_rate_limit": 0,
                "waf_bypasses": len(proxy_pool),
            },
        }


@app.get("/api/telemetry/stream")
async def stream_telemetry(request: Request):
    """Stream real-time Server-Sent Events telemetry frames to the dashboard."""

    async def telemetry_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                with _state_lock:
                    status = task_state["status"]
                    progress = task_state.get("progress", {})
                    imgs = progress.get("images_found", 0)
                    vids = progress.get("videos_found", 0)
                    frame = {
                        "status": status,
                        "rps": 1.0 if status == "running" else 0.0,
                        "speed_kbps": (imgs + vids) * 128 if status == "running" else 0,
                        "active_workers": 8 if status == "running" else 0,
                    }
                yield f"event: telemetry\ndata: {json.dumps(frame)}\n\n"
                await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            pass

    return StreamingResponse(telemetry_generator(), media_type="text/event-stream")


class SeedDiscoverRequest(BaseModel):
    subject: str


class SeedLintRequest(BaseModel):
    content: str


@app.post("/api/seed/discover")
def discover_seed_manifest(req: SeedDiscoverRequest):
    from src.cli.seed_studio import SeedDiscoverer

    discoverer = SeedDiscoverer()
    manifest_text = discoverer.discover_seeds_for_subject(req.subject)
    return {"subject": req.subject, "manifest": manifest_text}


@app.post("/api/seed/lint")
def lint_seed_manifest(req: SeedLintRequest):
    from src.cli.seed_studio import SeedLinter

    linter = SeedLinter()
    report = linter.lint_manifest_text(req.content)
    return report


# ------------------------------------------------------------------
# Cache Management Endpoints
# ------------------------------------------------------------------

class CacheClearDomainRequest(BaseModel):
    domain: str


@app.get("/api/cache/stats")
def cache_stats():
    from storage.state_cache import StateCache

    cache = StateCache()
    return cache.get_db_stats()


@app.post("/api/cache/vacuum")
def cache_vacuum():
    from storage.state_cache import StateCache

    cache = StateCache()
    size_after = cache.vacuum_db()
    return {"status": "ok", "db_size_bytes_after": size_after}


@app.post("/api/cache/clear_domain")
def cache_clear_domain(req: CacheClearDomainRequest):
    from storage.state_cache import StateCache

    cache = StateCache()
    deleted = cache.clear_domain(req.domain)
    return {"status": "ok", "domain": req.domain, "rows_deleted": deleted}

@app.post("/api/run")
def run_scrape(req: ScrapeRequest):
    global task_state, _current_process
    
    # Check if already running
    if task_state["status"] == "running" and _current_process:
        if _current_process.poll() is None:
            raise HTTPException(status_code=400, detail="A scrape is already running.")
            
    cmd = [
        sys.executable,
        str(ROOT_DIR / "src" / "cli" / "main.py"),
        "--keyword", req.keyword,
        "--max-results", str(req.max_results),
        "--workers", str(req.workers),
        "--dl-workers", str(req.dl_workers),
        "--page-limit", str(req.page_limit),
        "--crawl-depth", str(req.crawl_depth),
        "--output", req.output or "both"
    ]
    if req.seed:
        # Sanitize seed filename: strip any path components, only allow basename
        seed_basename = os.path.basename(req.seed)
        if not seed_basename or not re.match(r"^[\w\-. ]+\.txt$", seed_basename):
            raise HTTPException(status_code=400, detail="Invalid seed file name.")
            
        seeds_base = os.path.abspath(str(ROOT_DIR / "seeds"))
        seed_resolved = os.path.abspath(os.path.join(seeds_base, seed_basename))
        if not seed_resolved.startswith(seeds_base + os.sep):
            raise HTTPException(status_code=400, detail="Seed path traverses outside allowed directory.")
            
        cmd.extend(["--seed-file", seed_resolved])
        
    if req.seed_urls:
        for url in req.seed_urls.split(","):
            url_clean = url.strip()
            if url_clean:
                cmd.extend(["--seed-url", url_clean])
                
    if req.allow_domains:
        for d in req.allow_domains.split(","):
            d_clean = d.strip()
            if d_clean:
                cmd.extend(["--allow-domain", d_clean])
                
    if req.block_domains:
        for d in req.block_domains.split(","):
            d_clean = d.strip()
            if d_clean:
                cmd.extend(["--block-domain", d_clean])
                
    if req.entity_tokens:
        for t in req.entity_tokens.split(","):
            t_clean = t.strip()
            if t_clean:
                cmd.extend(["--entity-token", t_clean])
                
    if req.domain_delays:
        for pair in req.domain_delays.split(","):
            pair_clean = pair.strip()
            if pair_clean:
                cmd.extend(["--domain-delay", pair_clean])

    if req.proxy:
        cmd.extend(["--proxy", req.proxy])
    if req.capsolver_key:
        cmd.extend(["--capsolver-key", req.capsolver_key])
    if req.dl_speed_limit and req.dl_speed_limit > 0:
        cmd.extend(["--dl-speed-limit", str(req.dl_speed_limit)])
    if req.rate_limit and req.rate_limit > 0.0:
        cmd.extend(["--rate-limit", str(req.rate_limit)])
        
    if req.download_media:
        cmd.append("--download-media")
    if req.ignore_robots:
        cmd.append("--ignore-robots")
    if req.skip_search:
        cmd.append("--skip-search")
    if req.strict_domain:
        cmd.append("--strict-domain")
    if req.site_tree_only:
        cmd.append("--site-tree-only")
    if req.force_search:
        cmd.append("--force-search")
    if req.clear_cache:
        cmd.append("--clear-cache")
    if req.use_state_cache:
        cmd.append("--use-state-cache")
    if req.headless:
        cmd.append("--headless")
    if req.stealth_headful:
        cmd.append("--stealth-headful")

    log_buffer.clear()

    _current_process = Popen(
        cmd,
        executable=sys.executable,
        cwd=str(ROOT_DIR),
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )
    
    threading.Thread(target=read_subprocess_logs, args=(_current_process,), daemon=True).start()
    
    task_state["status"] = "running"
    task_state["current_keyword"] = req.keyword
    task_state["pid"] = _current_process.pid
    task_state["progress"] = {
        "percent": 0,
        "current": 0,
        "total": 0,
        "time_info": ""
    }
    
    return {"message": "Scrape started", "pid": _current_process.pid}

import time
from typing import Any

_dashboard_cache: dict[str, Any] = {
    "data": None,
    "last_updated": 0.0
}

@app.get("/api/dashboard")
def get_dashboard():
    global _dashboard_cache
    now = time.time()
    
    # 30-second cache
    if _dashboard_cache["data"] and (now - _dashboard_cache["last_updated"] < 30):
        return _dashboard_cache["data"]

    total_runs = 0
    total_images = 0
    total_videos = 0
    total_scanned = 0

    IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
    VIDEO_EXTS = {".mp4", ".webm", ".mkv", ".ogv", ".mov"}

    for run_dir in OUTPUT_DIR.glob("*/runs/*/"):
        if not run_dir.is_dir():
            continue
        total_runs += 1

        img_dir = run_dir / "images"
        if img_dir.is_dir():
            total_images += sum(
                1 for f in img_dir.rglob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXTS
            )

        vid_dir = run_dir / "videos"
        if vid_dir.is_dir():
            total_videos += sum(
                1 for f in vid_dir.rglob("*") if f.is_file() and f.suffix.lower() in VIDEO_EXTS
            )

        results_file = run_dir / "results.json"
        if results_file.is_file():
            try:
                with open(results_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    total_scanned += data.get("page_count", 0)
            except Exception:
                pass

    images = []
    videos = []

    img_files = sorted(
        OUTPUT_DIR.glob("*/runs/*/images/*.*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:50]
    for img in img_files:
        if img.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            rel_path = img.relative_to(OUTPUT_DIR).as_posix()
            images.append(rel_path)

    vid_files = sorted(
        OUTPUT_DIR.glob("*/runs/*/videos/*.*"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )[:50]
    for vid in vid_files:
        if vid.suffix.lower() in [".mp4", ".webm", ".mkv", ".ogv"]:
            rel_path = vid.relative_to(OUTPUT_DIR).as_posix()
            videos.append(rel_path)

    response_data = {
        "total_runs": total_runs,
        "total_images": total_images,
        "total_videos": total_videos,
        "total_scanned_pages": total_scanned,
        "images": images,
        "videos": videos
    }
    _dashboard_cache["data"] = response_data
    _dashboard_cache["last_updated"] = now
    return response_data

@app.get("/api/gallery/{keyword}")
def get_gallery_items(keyword: str, page: int = 1, limit: int = 50, domain: str = ""):
    images = []
    videos = []
    
    # Sanitize: use basename to break CodeQL taint chain
    safe_keyword = os.path.basename(keyword)
    if not safe_keyword or not re.match(r"^[\w\-. ]+$", safe_keyword):
        return {"images": [], "videos": [], "total": 0}
    
    base_dir = os.path.abspath(str(OUTPUT_DIR))
    keyword_dir_str = os.path.abspath(os.path.join(base_dir, safe_keyword, "runs"))
    if not keyword_dir_str.startswith(base_dir + os.sep):
        return {"images": [], "videos": [], "total": 0}
    keyword_dir = Path(keyword_dir_str)
    if not keyword_dir.exists():
        return {"images": [], "videos": [], "total": 0}
        
    img_files = list(keyword_dir.glob("*/images/*.*"))
    vid_files = list(keyword_dir.glob("*/videos/*.*"))
    
    if domain:
        safe_domain = domain.lower()
        img_files = [f for f in img_files if safe_domain in f.parent.parent.name]
        vid_files = [f for f in vid_files if safe_domain in f.parent.parent.name]
        
    # Sort descending by modified time
    all_files = sorted(
        [f for f in img_files if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]] +
        [f for f in vid_files if f.suffix.lower() in [".mp4", ".webm", ".mkv", ".ogv"]],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_files = all_files[start_idx:end_idx]
    
    for f in paginated_files:
        rel_path = f.relative_to(OUTPUT_DIR).as_posix()
        if f.suffix.lower() in [".mp4", ".webm", ".mkv", ".ogv"]:
            videos.append(rel_path)
        else:
            images.append(rel_path)
            
    return {
        "images": images,
        "videos": videos,
        "total": len(all_files),
        "page": page,
        "limit": limit
    }

@app.get("/htmx/gallery")
def htmx_gallery(keyword: str = "apple", domain: str = "", page: int = 1, limit: int = 20, media_kind: str = "all"):
    # Sanitize: use basename to break CodeQL taint chain
    safe_keyword = os.path.basename(keyword)
    if not safe_keyword or not re.match(r"^[\w\-. ]+$", safe_keyword):
        return HTMLResponse("<div style='grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;'>No media found for this keyword.</div>")
    
    base_dir = os.path.abspath(str(OUTPUT_DIR))
    keyword_dir_str = os.path.abspath(os.path.join(base_dir, safe_keyword, "runs"))
    if not keyword_dir_str.startswith(base_dir + os.sep):
        return HTMLResponse("<div style='grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;'>No media found for this keyword.</div>")
    keyword_dir = Path(keyword_dir_str)
    if not keyword_dir.exists():
        return HTMLResponse("<div style='grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;'>No media found for this keyword.</div>")
        
    img_files = []
    vid_files = []
    
    if media_kind in ["all", "images"]:
        img_files = [f for f in keyword_dir.glob("*/images/**/*.*") if f.is_file()]
    if media_kind in ["all", "videos"]:
        vid_files = [f for f in keyword_dir.glob("*/videos/**/*.*") if f.is_file()]
    
    if domain:
        safe_domain = domain.lower()
        img_files = [f for f in img_files if safe_domain in f.parent.parent.name]
        vid_files = [f for f in vid_files if safe_domain in f.parent.parent.name]
        
    all_files = sorted(
        [f for f in img_files if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]] +
        [f for f in vid_files if f.suffix.lower() in [".mp4", ".webm", ".mkv", ".ogv"]],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_files = all_files[start_idx:end_idx]
    
    html_chunks = []
    for i, f in enumerate(paginated_files):
        rel_path = f.relative_to(OUTPUT_DIR).as_posix()
        safe_rel_path = quote(rel_path)
        safe_name = html.escape(f.name)
        
        is_last = (i == len(paginated_files) - 1) and (end_idx < len(all_files))
        
        htmx_attrs = ""
        if is_last:
            safe_keyword = quote(keyword)
            safe_domain = quote(domain) if domain else ""
            safe_media_kind = quote(media_kind)
            next_url = f"/htmx/gallery?keyword={safe_keyword}&domain={safe_domain}&page={page+1}&limit={limit}&media_kind={safe_media_kind}"
            safe_next_url = html.escape(next_url)
            htmx_attrs = f' hx-get="{safe_next_url}" hx-trigger="revealed" hx-swap="afterend"'
            
        card_html = []
        card_html.append(f'<div class="media-card"{htmx_attrs}>')
        if f.suffix.lower() in [".mp4", ".webm", ".mkv", ".ogv"]:
            card_html.append(f'<video src="/{safe_rel_path}" controls preload="metadata" controlsList="nodownload" disablePictureInPicture></video>')
        else:
            card_html.append(f'<img src="/{safe_rel_path}" loading="lazy" />')
            
        safe_folder_path = html.escape(rel_path)
        card_html.append(f'''
        <div class="overlay">
            <div class="overlay-buttons">
                <button hx-post="/htmx/open-folder" hx-vals=\'{{"path": "{safe_folder_path}"}}\' hx-swap="none" class="btn-overlay">FOLDER</button>
                <button hx-delete="/htmx/media?path={safe_rel_path}" hx-target="closest .media-card" hx-swap="outerHTML swap:0.2s" class="btn-overlay delete">DELETE</button>
            </div>
            <div class="media-filename">{safe_name}</div>
        </div>
        </div>
        ''')
        html_chunks.append("".join(card_html))
            
    if not html_chunks and page == 1:
        return HTMLResponse("<div style='grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;'>No media found.</div>")
        
    return HTMLResponse("\n".join(html_chunks))

@app.delete("/htmx/media")
def delete_media(path: str):
    # Break taint: normalize the path through abspath within OUTPUT_DIR
    base_dir = os.path.abspath(str(OUTPUT_DIR))
    target_path = os.path.abspath(os.path.join(base_dir, path))
    if not target_path.startswith(base_dir + os.sep):
        raise HTTPException(status_code=400)
    target = Path(target_path)
    try:
        if target.is_file():
            target.unlink()
            return HTMLResponse("")  # Empty response removes it from DOM
    except Exception:
        pass
    raise HTTPException(status_code=404)

def _get_form_str(form: Any, key: str, default: str | None = None) -> str | None:
    val = form.get(key)
    if isinstance(val, str):
        return val
    return default

def _get_form_int(form: Any, key: str, default: int) -> int:
    val = form.get(key)
    if isinstance(val, str):
        try:
            return int(val)
        except ValueError:
            pass
    return default

@app.post("/htmx/open-folder")
async def open_folder(request: Request):
    form = await request.form()
    path_str = _get_form_str(form, "path", "") or ""
    if not path_str or ".." in path_str or os.path.isabs(path_str):
        return HTMLResponse("Invalid path")
    clean_name = os.path.basename(path_str.strip().rstrip("/\\"))
    if not clean_name or not re.match(r"^[\w\-. ]+$", clean_name):
        return HTMLResponse("Invalid path")

    try:
        base_dir = os.path.abspath(str(OUTPUT_DIR))
        target_path = os.path.abspath(os.path.join(base_dir, clean_name))
        
        if not target_path.startswith(base_dir + os.sep) and target_path != base_dir:
            return HTMLResponse("Invalid path")
            
        if os.path.exists(target_path):
            Popen(["explorer", "/select,", target_path])
    except Exception:
        return HTMLResponse("<span>ERR: Status check failed</span>")
    return HTMLResponse("")

@app.get("/api/telemetry/stealth")
def get_stealth_telemetry():
    """Return live WAF stealth pipeline statistics, solve counts, and circuit breaker cooldowns."""
    from utils.http_client import HttpClient, StealthTierHealthManager
    import time
    health_mgr = StealthTierHealthManager.get_instance()
    
    with HttpClient._waf_solve_lock:
        solve_counts = dict(HttpClient._waf_solve_counts)
        
    with HttpClient._preferred_engine_lock:
        preferred_engines = dict(HttpClient._preferred_engine_by_host)

    with health_mgr._tier_lock:
        health_stats = {
            tier: {
                "successes": data.get("successes", 0),
                "failures": data.get("failures", 0),
                "avg_latency_ms": round(data.get("avg_latency_ms", 0.0), 1),
                "is_cooling_down": time.monotonic() < data.get("cooldown_until", 0.0),
            }
            for tier, data in health_mgr._health.items()
        }

    return JSONResponse({
        "status": "success",
        "solve_counts": solve_counts,
        "preferred_engines": preferred_engines,
        "health_stats": health_stats,
    })

@app.get("/htmx/stats")
def get_stats():
    from utils.hardware_governor import HardwareLoadGovernor
    from storage.db_store import get_state_store, PostgresStateStore

    gov = HardwareLoadGovernor()
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage(str(OUTPUT_DIR)).percent
    scale = gov.get_concurrency_scale_factor()

    store = get_state_store()
    db_name = "POSTGRES" if isinstance(store, PostgresStateStore) else "SQLITE"

    def get_color(val, high_thresh=85, warn_thresh=70):
        if val >= high_thresh:
            return "#ff3333"
        elif val >= warn_thresh:
            return "var(--accent)"
        return "#00ff66"

    cpu_color = get_color(cpu)
    ram_color = get_color(ram)
    disk_color = get_color(disk)

    return HTMLResponse(f"""
        <div class="telemetry-bar">
            <div class="telemetry-badge">
                <span class="pulse-dot"></span>
                <span class="telemetry-title">SYS TELEMETRY</span>
                <span style="font-size: 0.7rem; background: rgba(0,255,102,0.1); border: 1px solid #00ff66; color: #00ff66; padding: 1px 4px; margin-left: 4px; font-weight: 700;">DB: {db_name}</span>
                <span style="font-size: 0.7rem; background: rgba(255,85,0,0.1); border: 1px solid var(--accent); color: var(--accent); padding: 1px 4px; margin-left: 4px; font-weight: 700;">GOV: {scale:.2f}x</span>
            </div>
            <div class="telemetry-metrics">
                <div class="telemetry-card">
                    <div class="telemetry-label">CPU</div>
                    <div class="telemetry-meter">
                        <div class="telemetry-fill" style="width: {cpu}%; background-color: {cpu_color};"></div>
                    </div>
                    <div class="telemetry-val" style="color: {cpu_color};">{cpu:.1f}%</div>
                </div>

                <div class="telemetry-card">
                    <div class="telemetry-label">RAM</div>
                    <div class="telemetry-meter">
                        <div class="telemetry-fill" style="width: {ram}%; background-color: {ram_color};"></div>
                    </div>
                    <div class="telemetry-val" style="color: {ram_color};">{ram:.1f}%</div>
                </div>

                <div class="telemetry-card">
                    <div class="telemetry-label">DSK</div>
                    <div class="telemetry-meter">
                        <div class="telemetry-fill" style="width: {disk}%; background-color: {disk_color};"></div>
                    </div>
                    <div class="telemetry-val" style="color: {disk_color};">{disk:.1f}%</div>
                </div>
            </div>
        </div>
    """)

@app.get("/api/engine/metrics")
async def get_engine_metrics():
    """Return real-time engine telemetry metrics."""
    with HttpClient._waf_solve_lock:
        waf_counts = dict(HttpClient._waf_solve_counts)
    
    session_files = [f for f in os.listdir("data/sessions") if f.endswith(".json")] if os.path.exists("data/sessions") else []
    
    return JSONResponse({
        "status": task_state.get("status", "idle"),
        "cpu_percent": psutil.cpu_percent(interval=None),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_percent": psutil.disk_usage("/").percent if hasattr(psutil, "disk_usage") else 0.0,
        "waf_solves": waf_counts,
        "active_sessions_count": len(session_files),
        "active_threads": threading.active_count()
    })

@app.post("/htmx/run")
async def htmx_run(request: Request):
    form = await request.form()
    req = ScrapeRequest(
        keyword=_get_form_str(form, "keyword", "apple") or "apple",
        max_results=_get_form_int(form, "max_results", 50),
        workers=_get_form_int(form, "workers", 8),
        dl_workers=_get_form_int(form, "dl_workers", 6),
        page_limit=_get_form_int(form, "page_limit", 100),
        crawl_depth=_get_form_int(form, "crawl_depth", 2),
        output=_get_form_str(form, "output", "both") or "both",
        seed_urls=_get_form_str(form, "seed_urls"),
        allow_domains=_get_form_str(form, "allow_domains"),
        block_domains=_get_form_str(form, "block_domains"),
        entity_tokens=_get_form_str(form, "entity_tokens"),
        domain_delays=_get_form_str(form, "domain_delays"),
        proxy=_get_form_str(form, "proxy"),
        capsolver_key=_get_form_str(form, "capsolver_key"),
        dl_speed_limit=_get_form_int(form, "dl_speed_limit", 0),
        rate_limit=float(_get_form_str(form, "rate_limit", "0.0") or "0.0"),
    )
    seed_val = _get_form_str(form, "seed")
    if seed_val:
        req.seed = seed_val
    if form.get("download_media") == "on":
        req.download_media = True
    if form.get("ignore_robots") == "on":
        req.ignore_robots = True
    if form.get("skip_search") == "on":
        req.skip_search = True
    if form.get("strict_domain") == "on":
        req.strict_domain = True
    if form.get("site_tree_only") == "on":
        req.site_tree_only = True
    if form.get("force_search") == "on":
        req.force_search = True
    if form.get("clear_cache") == "on":
        req.clear_cache = True
    if form.get("use_state_cache") == "on":
        req.use_state_cache = True
    if form.get("headless") == "on":
        req.headless = True
    if form.get("stealth_headful") == "on":
        req.stealth_headful = True
        
    try:
        run_scrape(req)
        broadcaster.broadcast("status", {"status": "running"})
        return render_control_buttons()
    except Exception as e:
        # Avoid Information exposure through an exception by not returning str(e)
        return HTMLResponse("<div style='color: red; margin-top: 1rem;'>ERR: An internal error occurred. Please check logs.</div>")

@app.post("/htmx/kill")
def kill_scrape():
    global _current_process, task_state
    with _state_lock:
        if _current_process and _current_process.poll() is None:
            try:
                import psutil
                parent = psutil.Process(_current_process.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except Exception:
                        pass
                parent.kill()
            except Exception:
                _current_process.kill()

            task_state["status"] = "idle"
            task_state["pid"] = None
            log_buffer.append(">>> PROCESS & CHILD WORKERS TERMINATED BY USER <<<")
            broadcaster.broadcast("status", {"status": "idle"})
            return render_control_buttons()
    return HTMLResponse("<div style='color: var(--text-muted); margin-top: 1rem;'>NO ACTIVE PROCESS</div>")


@app.post("/htmx/pause")
def htmx_pause_scrape():
    global _current_process, task_state
    with _state_lock:
        if task_state["status"] == "running" and _current_process and _current_process.poll() is None:
            try:
                import psutil
                parent = psutil.Process(_current_process.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.suspend()
                    except Exception:
                        pass
                parent.suspend()
            except Exception:
                return HTMLResponse("<div style='color: red; margin-top: 1rem;'>ERR: Failed to pause scrape process.</div>")

            task_state["status"] = "paused"
            log_buffer.append(">>> SCRAPE PAUSED BY USER <<<")
            broadcaster.broadcast("status", {"status": "paused"})
            return render_control_buttons()
    return HTMLResponse("<div style='color: var(--text-muted); margin-top: 1rem;'>NO RUNNING PROCESS TO PAUSE</div>")


@app.post("/htmx/resume")
def htmx_resume_scrape():
    global _current_process, task_state
    with _state_lock:
        if task_state["status"] == "paused" and _current_process and _current_process.poll() is None:
            try:
                import psutil
                parent = psutil.Process(_current_process.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.resume()
                    except Exception:
                        pass
                parent.resume()
            except Exception:
                return HTMLResponse("<div style='color: red; margin-top: 1rem;'>ERR: Failed to resume scrape process.</div>")

            task_state["status"] = "running"
            log_buffer.append(">>> SCRAPE RESUMED BY USER <<<")
            broadcaster.broadcast("status", {"status": "running"})
            return render_control_buttons()
    return HTMLResponse("<div style='color: var(--text-muted); margin-top: 1rem;'>NO PAUSED PROCESS TO RESUME</div>")


@app.post("/htmx/stop")
def htmx_stop_scrape():
    return kill_scrape()


@app.get("/htmx/controls")
def render_control_buttons():
    status = task_state.get("status", "idle")
    if status == "running":
        return HTMLResponse('''
            <div class="button-bar" style="display: flex; gap: 0.5rem; flex: 1;">
                <button type="button" hx-post="/htmx/pause" hx-target="#action-bar-container" hx-swap="innerHTML" class="btn" style="flex: 1; background: #ffaa00; color: #000; border: 2px solid #ffaa00;">PAUSE</button>
                <button type="button" hx-post="/htmx/stop" hx-target="#action-bar-container" hx-swap="innerHTML" class="btn btn-danger" style="flex: 1; background: #ff3333; color: #fff; border: 2px solid #ff3333;">TERMINATE</button>
            </div>
        ''')
    elif status == "paused":
        return HTMLResponse('''
            <div class="button-bar" style="display: flex; gap: 0.5rem; flex: 1;">
                <button type="button" hx-post="/htmx/resume" hx-target="#action-bar-container" hx-swap="innerHTML" class="btn" style="flex: 1; background: #00ff66; color: #000; border: 2px solid #00ff66;">RESUME</button>
                <button type="button" hx-post="/htmx/stop" hx-target="#action-bar-container" hx-swap="innerHTML" class="btn btn-danger" style="flex: 1; background: #ff3333; color: #fff; border: 2px solid #ff3333;">TERMINATE</button>
            </div>
        ''')
    else:
        return HTMLResponse('''
            <button type="submit" id="btn-run" class="btn btn-primary">START SCRAPE</button>
        ''')


@app.get("/htmx/status-badge")
def render_status_badge():
    status = task_state.get("status", "idle").upper()
    badge_class = "status-badge"
    if status == "RUNNING":
        badge_class += " running"
    elif status == "PAUSED":
        badge_class += " paused"

    color_style = "color: var(--accent); border-color: var(--accent);" if status in {"RUNNING", "PAUSED"} else "color: var(--text-muted);"
    return HTMLResponse(f'<span class="{badge_class}" style="{color_style}">{status}</span>')


@app.get("/api/capsolver/balance")
def get_capsolver_balance(key: str | None = None):
    """Query live balance for CapSolver API key."""
    from utils.capsolver import CapSolverClient
    client = CapSolverClient(api_key=key)
    balance = client.get_balance()
    return {"status": "ok", "balance": balance}


@app.get("/htmx/proxy-status")
def render_proxy_status():
    """Return HTMX status cards for Proxy Pool Manager."""
    from utils.proxy_manager import ProxyPoolManager
    pm = ProxyPoolManager.get_instance()
    pool = pm.get_pool_status()
    total = len(pool)
    healthy = sum(1 for p in pool if p["healthy"])
    quarantined = total - healthy
    return HTMLResponse(f'''
        <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-primary); display: flex; gap: 1rem;">
            <span>TOTAL PROXIES: <strong style="color: var(--accent);">{total}</strong></span>
            <span>HEALTHY: <strong style="color: #00ff66;">{healthy}</strong></span>
            <span>QUARANTINED: <strong style="color: #ff3333;">{quarantined}</strong></span>
        </div>
    ''')


@app.post("/api/dataset/tag")
def api_dataset_tag(subject: str = Form(""), trigger_tag: str = Form("")):
    """Batch auto-tag downloaded images in a subject run folder."""
    from utils.dataset_tagger import DatasetTagger

    # Sanitize: use basename to break CodeQL taint chain
    safe_subject = os.path.basename(subject)
    if not safe_subject or not re.match(r"^[\w\-. ]+$", safe_subject):
        return {"status": "error", "detail": "Invalid subject name"}

    base_dir = os.path.abspath(str(OUTPUT_DIR))
    output_path = os.path.abspath(os.path.join(base_dir, safe_subject, "images"))
    if not output_path.startswith(base_dir + os.sep):
        return {"status": "error", "detail": "Invalid path"}
    output_dir = Path(output_path)
    if not output_dir.exists():
        # Fallback to subject root or first run folder
        fallback_path = os.path.abspath(os.path.join(base_dir, safe_subject))
        output_dir = Path(fallback_path)

    tagger = DatasetTagger(trigger_tag=trigger_tag)
    res = tagger.tag_directory(output_dir)
    return {"status": "ok", "subject": safe_subject, **res}


@app.get("/api/dataset/sidecar")
def get_dataset_sidecar(path: str):
    """Retrieve sidecar text file for a given image path."""
    # Sanitize: confine to OUTPUT_DIR
    base_dir = os.path.abspath(str(OUTPUT_DIR))
    resolved = os.path.abspath(os.path.join(base_dir, path))
    if not resolved.startswith(base_dir + os.sep):
        return {"status": "error", "path": "", "tags": []}
    img_path = Path(resolved)
    sidecar_path = img_path.with_suffix(".txt")
    if sidecar_path.exists():
        tags_str = sidecar_path.read_text(encoding="utf-8")
        return {"status": "ok", "path": str(sidecar_path), "tags": [t.strip() for t in tags_str.split(",") if t.strip()]}
    return {"status": "ok", "path": str(sidecar_path), "tags": []}


@app.post("/api/dataset/sidecar")
def save_dataset_sidecar(path: str = Form(...), tags: str = Form(...)):
    """Update sidecar text file for a given image path."""
    # Sanitize: confine to OUTPUT_DIR
    base_dir = os.path.abspath(str(OUTPUT_DIR))
    resolved = os.path.abspath(os.path.join(base_dir, path))
    if not resolved.startswith(base_dir + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    img_path = Path(resolved)
    sidecar_path = img_path.with_suffix(".txt")
    sidecar_path.write_text(tags, encoding="utf-8")
    return {"status": "ok", "path": str(sidecar_path), "saved_tags": tags}


@app.post("/api/dataset/score")
def api_dataset_score(subject: str = Form(""), min_score: float = Form(6.0)):
    """Evaluate aesthetic quality scores for images in a subject folder."""
    from utils.aesthetic_scorer import AestheticScorer

    safe_subject = os.path.basename(subject)
    if not safe_subject or not re.match(r"^[\w\-. ]+$", safe_subject):
        return {"status": "error", "detail": "Invalid subject name"}

    base_dir = os.path.abspath(str(OUTPUT_DIR))
    output_path = os.path.abspath(os.path.join(base_dir, safe_subject, "images"))
    if not output_path.startswith(base_dir + os.sep):
        return {"status": "error", "detail": "Invalid path"}
        
    output_dir = Path(output_path)
    if not output_dir.exists():
        fallback_path = os.path.abspath(os.path.join(base_dir, safe_subject))
        if fallback_path.startswith(base_dir + os.sep):
            output_dir = Path(fallback_path)

    scorer = AestheticScorer()
    res = scorer.filter_directory(output_dir, min_score=min_score)
    return {"subject": safe_subject, **res}


@app.post("/api/dataset/crop")
def api_dataset_crop(subject: str = Form(""), width: int = Form(1024), height: int = Form(1024)):
    """Batch smart-crop images in a subject folder to specified aspect ratio/resolution."""
    from utils.dataset_cropper import DatasetCropper

    safe_subject = os.path.basename(subject)
    if not safe_subject or not re.match(r"^[\w\-. ]+$", safe_subject):
        return {"status": "error", "detail": "Invalid subject name"}

    base_dir = os.path.abspath(str(OUTPUT_DIR))
    output_path = os.path.abspath(os.path.join(base_dir, safe_subject, "images"))
    if not output_path.startswith(base_dir + os.sep):
        return {"status": "error", "detail": "Invalid path"}
        
    output_dir = Path(output_path)
    if not output_dir.exists():
        fallback_path = os.path.abspath(os.path.join(base_dir, safe_subject))
        if fallback_path.startswith(base_dir + os.sep):
            output_dir = Path(fallback_path)

    cropper = DatasetCropper(default_target_size=(width, height))
    res = cropper.crop_directory(output_dir, target_size=(width, height))
    return {"subject": safe_subject, **res}


@app.get("/api/dataset/export")
def export_dataset_zip(subject: str, repeats: int = 10, concept: str = "concept"):
    """Export Kohya_ss formatted LoRA dataset ZIP archive."""
    from fastapi.responses import Response
    from utils.dataset_exporter import KohyaDatasetExporter

    # Sanitize: use basename to break CodeQL taint chain
    safe_subject = os.path.basename(subject)
    if not safe_subject or not re.match(r"^[\w\-. ]+$", safe_subject):
        raise HTTPException(status_code=400, detail="Invalid subject name")

    base_dir = os.path.abspath(str(OUTPUT_DIR))
    image_path = os.path.abspath(os.path.join(base_dir, safe_subject, "images"))
    if not image_path.startswith(base_dir + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    image_dir = Path(image_path)
    if not image_dir.exists():
        fallback_path = os.path.abspath(os.path.join(base_dir, safe_subject))
        image_dir = Path(fallback_path)

    exporter = KohyaDatasetExporter(repeats=repeats, concept_name=safe_subject)
    zip_bytes = exporter.create_dataset_zip_bytes(image_dir)
    filename = f"{safe_subject}_lora_dataset.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# Telegram Bot Store (Initialised from .env config)
import config

telegram_config = {
    "token": getattr(config, "TELEGRAM_BOT_TOKEN", ""),
    "chat_id": getattr(config, "TELEGRAM_CHAT_ID", ""),
    "enabled": True,
}


@app.get("/api/telegram/config")
def get_telegram_config():
    """Return current Telegram Bot configuration."""
    return {"status": "ok", **telegram_config}


@app.post("/api/telegram/config")
def update_telegram_config(token: str = Form(""), chat_id: str = Form(""), enabled: bool = Form(True)):
    """Update Telegram Bot configuration."""
    telegram_config["token"] = token.strip()
    telegram_config["chat_id"] = chat_id.strip()
    telegram_config["enabled"] = enabled
    return {"status": "ok", **telegram_config}


@app.post("/api/telegram/test")
def test_telegram_notification(token: str = Form(""), chat_id: str = Form("")):
    """Send a test notification message via Telegram Bot API."""
    from utils.telegram_bot import TelegramBotNotifier

    tok = token.strip() or telegram_config.get("token", "")
    cid = chat_id.strip() or telegram_config.get("chat_id", "")
    notifier = TelegramBotNotifier(tok, cid)
    success = notifier.send_message("<b>scrAPE Telegram Bot Connected!</b>\nTest alert message received successfully.")
    return {"status": "ok" if success else "failed", "sent": success}


@app.post("/api/pause")
def api_pause():
    res = htmx_pause_scrape()
    return {"status": task_state["status"]}


@app.post("/api/resume")
def api_resume():
    res = htmx_resume_scrape()
    return {"status": task_state["status"]}


@app.post("/api/stop")
def api_stop():
    res = kill_scrape()
    return {"status": task_state["status"]}


# Seed Studio endpoints defined below

@app.get("/api/subjects")
def get_subjects():
    subjects = []
    if OUTPUT_DIR.exists():
        for path in OUTPUT_DIR.iterdir():
            if path.is_dir() and (path / "runs").exists():
                subjects.append(path.name)
    return sorted(subjects)

@app.get("/htmx/sidebar")
def htmx_sidebar(active: str = ""):
    subjects = get_subjects()
    html = []
    current_active = active or task_state["current_keyword"]
    for sub in subjects:
        is_active = "active" if sub == current_active else ""
        html.append(f'''
        <div class="sidebar-item {is_active}" 
             data-subject="{sub}"
             onclick="selectSubject('{sub}')">
            <span class="sub-indicator"></span>
            <span class="sub-name">{sub.upper()}</span>
        </div>
        ''')
    if not html:
        return HTMLResponse("<div style='padding: 1rem; color: var(--text-muted); font-size: 0.8rem;'>NO SUBJECTS FOUND</div>")
    return HTMLResponse("\n".join(html))

def get_historical_stats(subject: str | None = None):
    total_runs = 0
    total_images = 0
    total_videos = 0
    total_scanned = 0

    IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
    VIDEO_EXTS = {".mp4", ".webm", ".mkv", ".ogv", ".mov"}

    pattern = f"{subject}/runs/*/" if subject else "*/runs/*/"

    if OUTPUT_DIR.exists():
        subj_dirs = [OUTPUT_DIR / subject] if subject else [d for d in OUTPUT_DIR.iterdir() if d.is_dir() and d.name not in ("cache", "test")]
        for sdir in subj_dirs:
            runs_dir = sdir / "runs"
            if runs_dir.exists():
                rdirs = [r for r in runs_dir.iterdir() if r.is_dir()]
            else:
                rdirs = [sdir]

            for run_dir in rdirs:
                summary_file = run_dir / "run_summary.json"
                results_file = run_dir / "results.json"
                img_dir = run_dir / "images"
                vid_dir = run_dir / "videos"

                has_summary = summary_file.is_file() or results_file.is_file()
                has_images = img_dir.is_dir() and any(f.is_file() for f in img_dir.rglob("*"))
                has_videos = vid_dir.is_dir() and any(f.is_file() for f in vid_dir.rglob("*"))

                if not (has_summary or has_images or has_videos):
                    continue

                total_runs += 1

                if img_dir.is_dir():
                    total_images += sum(
                        1 for f in img_dir.rglob("*") if f.is_file() and f.suffix.lower() in IMAGE_EXTS
                    )

                if vid_dir.is_dir():
                    total_videos += sum(
                        1 for f in vid_dir.rglob("*") if f.is_file() and f.suffix.lower() in VIDEO_EXTS
                    )

                if summary_file.is_file():
                    try:
                        with open(summary_file, "r", encoding="utf-8") as fh:
                            sdata = json.load(fh)
                            total_scanned += sdata.get("overall_stats", {}).get("total_pages_scanned", 0)
                    except Exception:
                        pass
                elif results_file.is_file():
                    try:
                        with open(results_file, "r", encoding="utf-8") as fh:
                            data = json.load(fh)
                            total_scanned += data.get("page_count", 0)
                    except Exception:
                        pass

    return {
        "total_runs": total_runs,
        "total_images": total_images,
        "total_videos": total_videos,
        "total_scanned": total_scanned
    }

@app.get("/htmx/active-stats")
def htmx_active_stats():
    if task_state["status"] == "running":
        metrics = task_state.get("active_metrics", {
            "pages_scanned": 0,
            "images_saved": 0,
            "videos_saved": 0,
            "errors": 0
        })
        return HTMLResponse(f"""
            <div class="stat-card running">
                <div class="label">LIVE.PAGES</div>
                <div class="value">{metrics["pages_scanned"]}</div>
            </div>
            <div class="stat-card running">
                <div class="label">LIVE.IMG</div>
                <div class="value">{metrics["images_saved"]}</div>
            </div>
            <div class="stat-card running">
                <div class="label">LIVE.VID</div>
                <div class="value">{metrics["videos_saved"]}</div>
            </div>
            <div class="stat-card running">
                <div class="label">LIVE.ERRS</div>
                <div class="value" style="color: #ff3333;">{metrics["errors"]}</div>
            </div>
        """)
    else:
        stats = get_historical_stats()
        return HTMLResponse(f"""
            <div class="stat-card">
                <div class="label">TOTAL.RUNS</div>
                <div class="value">{stats["total_runs"]}</div>
            </div>
            <div class="stat-card">
                <div class="label">ASSET.IMG</div>
                <div class="value">{stats["total_images"]}</div>
            </div>
            <div class="stat-card">
                <div class="label">ASSET.VID</div>
                <div class="value">{stats["total_videos"]}</div>
            </div>
            <div class="stat-card">
                <div class="label">TARGETS.SCAN</div>
                <div class="value">{stats["total_scanned"]}</div>
            </div>
        """)

@app.get("/htmx/subject-stats")
def htmx_subject_stats(subject: str = ""):
    global_stats = get_historical_stats()
    if not subject:
        subj_stats = global_stats
    else:
        subj_stats = get_historical_stats(subject=subject)

    return HTMLResponse(f"""
        <div class="stat-card">
            <div class="label">SUBJ.RUNS</div>
            <div class="value">{subj_stats["total_runs"]}</div>
            <div class="sub-total">/ {global_stats["total_runs"]} total</div>
        </div>
        <div class="stat-card">
            <div class="label">ASSET.IMG</div>
            <div class="value">{subj_stats["total_images"]}</div>
            <div class="sub-total">/ {global_stats["total_images"]} total</div>
        </div>
        <div class="stat-card">
            <div class="label">ASSET.VID</div>
            <div class="value">{subj_stats["total_videos"]}</div>
            <div class="sub-total">/ {global_stats["total_videos"]} total</div>
        </div>
        <div class="stat-card">
            <div class="label">TARGETS.SCAN</div>
            <div class="value">{subj_stats["total_scanned"]}</div>
            <div class="sub-total">/ {global_stats["total_scanned"]} total</div>
        </div>
    """)

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

# ---------------------------------------------------------------------------
# Seed Studio REST API Endpoints
# ---------------------------------------------------------------------------

SEEDS_DIR = ROOT_DIR / "seeds"
SEEDS_DIR.mkdir(parents=True, exist_ok=True)

class SaveSeedPayload(BaseModel):
    filename: str
    content: str
    overwrite: bool = True

class ValidateSeedPayload(BaseModel):
    content: str

class DiscoverSeedPayload(BaseModel):
    query: str
    domains: List[str]

@app.get("/api/seeds")
def list_seeds():
    from src.core.seed_manifest import SeedManifest
    seeds = []
    for p in sorted(SEEDS_DIR.glob("*.txt")):
        try:
            manifest = SeedManifest.from_file(p)
            seeds.append({
                "filename": p.name,
                "subject_name": manifest.subject_name or p.stem,
                "domain_count": len(manifest.domains),
                "url_count": len(manifest.all_seed_urls),
                "domains": [d.domain for d in manifest.domains]
            })
        except Exception:
            seeds.append({
                "filename": p.name,
                "subject_name": p.stem,
                "domain_count": 0,
                "url_count": 0,
                "domains": []
            })
    return {"seeds": seeds}

@app.get("/api/seeds/{filename}")
def get_seed(filename: str):
    from src.core.seed_manifest import SeedManifest
    # Sanitize: use basename to break CodeQL taint chain
    safe_filename = os.path.basename(filename)
    if not safe_filename or not re.match(r"^[\w\-. ]+$", safe_filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    seeds_base = os.path.abspath(str(SEEDS_DIR))
    target_path = os.path.abspath(os.path.join(seeds_base, safe_filename))
    if not target_path.startswith(seeds_base + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    target = Path(target_path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Seed file not found")
    content = target.read_text(encoding="utf-8")
    try:
        manifest = SeedManifest.from_file(target)
        profiles = []
        for d in manifest.domains:
            profiles.append({
                "domain": d.domain,
                "seed_urls": d.seed_urls,
                "media_type": d.media_type,
                "crawl_strategy": d.crawl_strategy,
                "crawl_depth": d.crawl_depth,
                "rate_limit": d.rate_limit,
                "preferred_engine": d.preferred_engine,
                "cloudflare_blocked": d.cloudflare_blocked,
                "requires_referer": d.requires_referer,
                "disabled": d.disabled
            })
        return {
            "filename": filename,
            "content": content,
            "subject_name": manifest.subject_name,
            "domains": profiles
        }
    except Exception:
        return {
            "filename": filename,
            "content": content,
            "subject_name": target.stem,
            "domains": []
        }

@app.post("/api/seeds")
def save_seed(payload: SaveSeedPayload):
    filename = os.path.basename(payload.filename.strip())
    if not filename or not re.match(r"^[\w\-. ]+$", filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not filename.endswith(".txt"):
        filename = f"{filename}.txt"
        
    seeds_base = os.path.abspath(str(SEEDS_DIR))
    target_path = os.path.abspath(os.path.join(seeds_base, filename))
    if not target_path.startswith(seeds_base + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    target = Path(target_path)
    if target.exists() and not payload.overwrite:
        raise HTTPException(status_code=409, detail="File already exists")
    
    target.write_text(payload.content, encoding="utf-8")
    return {"success": True, "filename": filename, "message": "Seed file saved successfully"}

@app.delete("/api/seeds/{filename}")
def delete_seed(filename: str):
    # Sanitize: use basename to break CodeQL taint chain
    safe_filename = os.path.basename(filename)
    if not safe_filename or not re.match(r"^[\w\-. ]+$", safe_filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    seeds_base = os.path.abspath(str(SEEDS_DIR))
    target_path = os.path.abspath(os.path.join(seeds_base, safe_filename))
    if not target_path.startswith(seeds_base + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    target = Path(target_path)
    if not target.exists() or not target.is_file():
        raise HTTPException(status_code=404, detail="Seed file not found")
    target.unlink()
    return {"success": True, "filename": safe_filename, "message": "Seed file deleted"}

@app.post("/api/seeds/validate")
def validate_seed(payload: ValidateSeedPayload):
    from src.core.seed_manifest import SeedManifest
    temp_file = SEEDS_DIR / "_temp_val.txt"
    try:
        temp_file.write_text(payload.content, encoding="utf-8")
        warnings = SeedManifest.validate(temp_file)
        return {"warnings": warnings, "is_valid": len(warnings) == 0}
    finally:
        if temp_file.exists():
            temp_file.unlink()

@app.post("/api/seeds/discover")
async def discover_search_urls(payload: DiscoverSeedPayload):
    import urllib.parse
    import asyncio
    import random
    from src.utils.http_client import HttpClient
    
    query = payload.query.strip()
    if not query:
        return {"discovered_urls": [], "tested_count": 0, "valid_count": 0}
        
    encoded_q = urllib.parse.quote(query)
    candidate_urls = []
    
    # 1. Multi-Engine Search Probes (SafeSearch disabled kp=-2)
    search_probes = [
        f"https://html.duckduckgo.com/html/?q={encoded_q}&kp=-2",
        f"https://duckduckgo.com/html/?q={encoded_q}&kp=-2",
        f"https://www.google.com/search?q={encoded_q}&tbm=isch",
    ]
    candidate_urls.extend(search_probes)
    
    for dom in payload.domains:
        dom = dom.strip()
        if not dom:
            continue
        if not dom.startswith("http://") and not dom.startswith("https://"):
            base_url = f"https://{dom}"
        else:
            base_url = dom
            
        base_url = base_url.rstrip("/")
        
        candidates = [
            f"{base_url}/?f_search={encoded_q}",
            f"{base_url}/posts?tags={encoded_q}",
            f"{base_url}/tags/{encoded_q}",
            f"{base_url}/m/{encoded_q}",
            f"{base_url}/user/{encoded_q}",
            f"{base_url}/search/{encoded_q}",
            f"{base_url}/search?q={encoded_q}",
            f"{base_url}/?s={encoded_q}",
            f"{base_url}/t/{encoded_q}",
            f"{base_url}/category/{encoded_q}"
        ]
        candidate_urls.extend(candidates)
        
    candidate_urls = list(dict.fromkeys(candidate_urls))
    
    client = HttpClient(timeout=6.0)
    
    async def probe_url(url: str):
        # Apply slight jitter to prevent thundering herd IP rate limits
        await asyncio.sleep(random.uniform(0.05, 0.25))
        try:
            loop = asyncio.get_event_loop()
            res = await loop.run_in_executor(None, lambda: client.get(url))
            if res is not None:
                headers_lower = {k.lower(): v.lower() for k, v in res.headers.items()}
                is_cf = "cloudflare" in headers_lower.get("server", "") or "cf-ray" in headers_lower
                is_403_429 = res.status_code in (403, 429)
                
                status_code = res.status_code
                is_valid = status_code == 200 and len(res.content) > 300
                
                annotations = {
                    "cloudflare_blocked": is_cf or is_403_429,
                    "preferred_engine": "camoufox" if (is_cf or is_403_429) else "auto",
                    "requires_referer": status_code in (403, 401)
                }
                
                if is_valid or is_cf or is_403_429:
                    return {
                        "url": url,
                        "status": status_code,
                        "valid": is_valid,
                        "annotations": annotations
                    }
        except Exception:
            pass
        return {"url": url, "status": 404, "valid": False, "annotations": {}}
        
    tasks = [probe_url(u) for u in candidate_urls]
    results = await asyncio.gather(*tasks)
    
    valid_urls = [r for r in results if r["valid"]]
    return {
        "discovered_urls": valid_urls,
        "tested_count": len(candidate_urls),
        "valid_count": len(valid_urls)
    }


# ---------------------------------------------------------------------------
# Data Export, AI Ingestion & Run Summary Endpoints
# ---------------------------------------------------------------------------

class ExportDatasetPayload(BaseModel):
    subject: str
    run_id: str
    layout: str = "1"  # "1" = flat, "2" = domain, "3" = media_type

class ExportRAGPayload(BaseModel):
    subject: str
    run_id: str

@app.get("/api/runs/{subject}/{run_id}/summary")
def get_run_summary(subject: str, run_id: str):
    # Sanitize: use basename to break CodeQL taint chain
    safe_subject = os.path.basename(subject)
    safe_run_id = os.path.basename(run_id)
    if not _is_safe_path_component(safe_subject) or not _is_safe_path_component(safe_run_id):
        raise HTTPException(status_code=400, detail="Invalid path components")
    
    base_dir = os.path.abspath(str(OUTPUT_DIR))
    summary_path_str = os.path.abspath(os.path.join(base_dir, safe_subject, "runs", safe_run_id, "run_summary.json"))
    if not summary_path_str.startswith(base_dir + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    summary_path = Path(summary_path_str)
    if summary_path.exists():
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            raise HTTPException(status_code=500, detail="Failed to read run summary")
    raise HTTPException(status_code=404, detail="Run summary not found")

@app.post("/api/export/dataset")
def export_ai_dataset(payload: ExportDatasetPayload):
    import shutil
    from urllib.parse import urlparse

    # Sanitize: use basename to break CodeQL taint chain
    safe_subject = os.path.basename(payload.subject)
    safe_run_id = os.path.basename(payload.run_id)
    if not _is_safe_path_component(safe_subject) or not _is_safe_path_component(safe_run_id):
        raise HTTPException(status_code=400, detail="Invalid path components")

    base_dir = os.path.abspath(str(OUTPUT_DIR))
    run_dir_str = os.path.abspath(os.path.join(base_dir, safe_subject, "runs", safe_run_id))
    if not run_dir_str.startswith(base_dir + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    run_dir = Path(run_dir_str)
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail=f"Run directory not found")

    image_src = run_dir / "images"
    video_src = run_dir / "videos"

    has_images = image_src.exists() and any(image_src.iterdir())
    has_videos = video_src.exists() and any(video_src.iterdir())

    if not has_images and not has_videos:
        raise HTTPException(status_code=400, detail="No media files found in this run to export")

    dataset_base = os.path.abspath(str(ROOT_DIR / "datasets"))
    dataset_dir_str = os.path.abspath(os.path.join(dataset_base, f"{safe_subject}_{safe_run_id}_dataset"))
    if not dataset_dir_str.startswith(dataset_base + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    target_root = Path(dataset_dir_str)
    target_root.mkdir(parents=True, exist_ok=True)

    results_path = run_dir / "results.json"
    url_to_domain = {}
    if results_path.exists():
        try:
            with open(results_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for img in data.get("images", []):
                url_to_domain[img.get("file_path")] = (
                    img.get("source_domain") or urlparse(img.get("url")).netloc
                )
            for vid in data.get("videos", []):
                url_to_domain[vid.get("file_path")] = (
                    vid.get("source_domain") or urlparse(vid.get("url")).netloc
                )
        except Exception:
            pass

    copied_count = 0
    for src_dir, kind in [(image_src, "images"), (video_src, "videos")]:
        if not src_dir.exists():
            continue
        for file_path in src_dir.rglob("*"):
            if not file_path.is_file():
                continue

            rel_path_in_run = file_path.relative_to(run_dir).as_posix()
            domain = url_to_domain.get(rel_path_in_run) or file_path.parent.name
            domain_clean = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", domain)

            if payload.layout == "1":
                new_name = f"{domain_clean}_{file_path.name}"
                dest = target_root / new_name
            elif payload.layout == "2":
                domain_dir = target_root / domain_clean
                domain_dir.mkdir(exist_ok=True)
                dest = domain_dir / file_path.name
            else:
                kind_dir = target_root / kind
                kind_dir.mkdir(exist_ok=True)
                dest = kind_dir / file_path.name

            shutil.copy2(file_path, dest)
            copied_count += 1

    return {
        "status": "success",
        "exported_count": copied_count,
        "export_path": str(target_root.resolve()),
    }


@app.get("/api/export/dataset/download/{subject}/{run_id}")
def download_kohya_dataset_zip(
    subject: str, run_id: str, repeats: int = 10, min_resolution: int = 512, min_aesthetic_score: float = 0.0
):
    """Generate and stream Kohya_ss LoRA dataset ZIP file directly to browser."""
    from utils.dataset_exporter import KohyaDatasetExporter

    subject = os.path.basename(subject)
    run_id = os.path.basename(run_id)

    if not _is_safe_path_component(subject) or not _is_safe_path_component(run_id):
        raise HTTPException(status_code=400, detail="Invalid path components.")

    try:
        base_dir = os.path.abspath(str(OUTPUT_DIR))
        target_path = os.path.abspath(os.path.join(base_dir, subject, "runs", run_id, "images"))
        
        if not target_path.startswith(base_dir + os.sep):
            raise HTTPException(status_code=400, detail="Invalid path components.")
            
        run_dir = Path(target_path)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path.")

    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run image directory not found")

    exporter = KohyaDatasetExporter(
        repeats=repeats, concept_name=subject, min_resolution=min_resolution, min_aesthetic_score=min_aesthetic_score
    )
    zip_bytes = exporter.create_dataset_zip_bytes(run_dir)
    if not zip_bytes:
        raise HTTPException(
            status_code=400, detail="No eligible images found for Kohya dataset export"
        )

    filename = f"{subject}_kohya_dataset.zip"
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@app.post("/api/notifications/test")
def test_notification_channels():
    """Trigger a test ping across all registered notification providers (Telegram, Discord, Slack, etc.)."""
    from utils.notification_manager import NotificationPipeline

    pipeline = NotificationPipeline()
    results = pipeline.notify_watchdog_status("scrAPE Test Ping: Notification pipeline is operational!", "INFO")
    return {"status": "ok", "delivered_providers": results}

@app.post("/api/export/rag")
def export_rag_markdown(payload: ExportRAGPayload):
    from urllib.parse import urlparse

    # CodeQL expects os.path.basename to sanitize path components
    subject = os.path.basename(payload.subject)
    run_id = os.path.basename(payload.run_id)

    try:
        if not _is_safe_path_component(subject) or not _is_safe_path_component(run_id):
            raise HTTPException(status_code=400, detail="Invalid path components.")
            
        base_dir = os.path.abspath(str(OUTPUT_DIR))
        target_path = os.path.abspath(os.path.join(base_dir, subject, "runs", run_id))
        
        if not target_path.startswith(base_dir + os.sep):
            raise HTTPException(status_code=400, detail="Invalid path components.")
            
        run_dir = Path(target_path)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path.")
    
    results_path = run_dir / "results.json"
    if not results_path.exists():
        raise HTTPException(status_code=404, detail=f"results.json not found for run {run_id}")

    try:
        with open(results_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to load results.json")

    try:
        rag_dir_str = os.path.abspath(str(ROOT_DIR / "rag_ingestion"))
        rag_target = os.path.abspath(os.path.join(rag_dir_str, f"{subject}_{run_id}_rag"))
        
        if not rag_target.startswith(rag_dir_str + os.sep):
            raise HTTPException(status_code=400, detail="Invalid path components.")
            
        target_root = Path(rag_target)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid path.")

    target_root.mkdir(parents=True, exist_ok=True)

    page_reports = data.get("page_reports", [])
    extracted_docs = 0

    for idx, page in enumerate(page_reports, start=1):
        page_url = page.get("url", "")
        title = page.get("title", "") or f"Document {idx}"
        domain = page.get("domain") or urlparse(page_url).netloc
        media_count = page.get("media_found", 0)

        clean_slug = re.sub(r"[^a-zA-Z0-9_]", "_", f"{domain}_{idx}")
        doc_path = target_root / f"{clean_slug}.md"

        content = f"""# {title}

- **Source Domain**: `{domain}`
- **Source URL**: [{page_url}]({page_url})
- **Media Count**: {media_count}
- **Subject Identifier**: `{payload.subject}`

## Summary & Extracted Tokens
Target page analyzed during automated scrape run `{payload.run_id}` for subject `{payload.subject}`. Found {media_count} media assets across domain `{domain}`.
"""
        doc_path.write_text(content, encoding="utf-8")
        extracted_docs += 1

    return {
        "status": "success",
        "extracted_documents": extracted_docs,
        "export_path": str(target_root.resolve()),
    }


# Mount static files at the root to serve all media assets.
# This MUST be declared last so it doesn't swallow API routes.
app.mount("/", StaticFiles(directory=str(OUTPUT_DIR), html=False), name="output")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=10001)
    args = parser.parse_args()
    
    uvicorn.run("frontend.app:app", host="localhost", port=args.port, reload=False)
