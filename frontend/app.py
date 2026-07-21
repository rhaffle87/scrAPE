import sys
import subprocess
import threading
from collections import deque
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import json
import psutil
import os
from fastapi import Request, Form

ROOT_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Global log buffer for streaming to the web UI
log_buffer = deque(maxlen=2000)

app = FastAPI(title="scrAPE Web GUI", version="1.0.0")

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
_current_process: Optional[subprocess.Popen] = None

@app.get("/api/status")
def get_status():
    global task_state, _current_process
    if task_state["status"] == "running" and _current_process:
        if _current_process.poll() is None:
            pass # still running
        else:
            task_state["status"] = "idle"
            task_state["pid"] = None
    return task_state

def read_subprocess_logs(proc: subprocess.Popen):
    global log_buffer, task_state
    
    import re
    
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
        
        task_state["progress"] = {
            "percent": pct,
            "current": current,
            "total": total,
            "time_info": time_info
        }

    def process_log_line(log_line: str):
        log_buffer.append(log_line)
        lower_line = log_line.lower()
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

@app.get("/api/logs")
def get_logs(offset: int = 0):
    global log_buffer, task_state
    logs = list(log_buffer)
    if offset > len(logs):
        offset = 0
    new_lines = logs[offset:]
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
        import os
        
        # Sanitize path: do not allow directory traversal or absolute paths
        if ".." in req.seed or os.path.isabs(req.seed):
            raise HTTPException(status_code=400, detail="Invalid seed file path. Must be a safe relative path.")
            
        seed_path = ROOT_DIR / "seeds" / req.seed
        
        # Ensure it resolves securely inside the seeds directory
        try:
            resolved_seed = seed_path.resolve()
            seeds_dir = (ROOT_DIR / "seeds").resolve()
            if not str(resolved_seed).startswith(str(seeds_dir)):
                raise HTTPException(status_code=400, detail="Seed path traverses outside allowed directory.")
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid seed path resolution.")
            
        cmd.extend(["--seed-file", str(resolved_seed)])
        
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

    _current_process = subprocess.Popen(
        cmd, 
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
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

_dashboard_cache = {
    "data": None,
    "last_updated": 0
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

    for json_file in OUTPUT_DIR.glob("*/runs/*/results.json"):
        total_runs += 1
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                total_images += data.get("download_stats", {}).get("images_saved", 0)
                total_videos += data.get("download_stats", {}).get("videos_saved", 0)
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
    
    keyword_dir = OUTPUT_DIR / keyword / "runs"
    if not keyword_dir.exists():
        return {"images": [], "videos": [], "total": 0}
        
    img_files = list(keyword_dir.glob("*/images/*.*"))
    vid_files = list(keyword_dir.glob("*/videos/*.*"))
    
    if domain:
        img_files = [f for f in img_files if domain.lower() in str(f.parent.parent)]
        vid_files = [f for f in vid_files if domain.lower() in str(f.parent.parent)]
        
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
    keyword_dir = OUTPUT_DIR / keyword / "runs"
    if not keyword_dir.exists():
        return HTMLResponse("<div style='grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;'>No media found for this keyword.</div>")
        
    img_files = []
    vid_files = []
    
    if media_kind in ["all", "images"]:
        img_files = [f for f in keyword_dir.glob("*/images/**/*.*") if f.is_file()]
    if media_kind in ["all", "videos"]:
        vid_files = [f for f in keyword_dir.glob("*/videos/**/*.*") if f.is_file()]
    
    if domain:
        img_files = [f for f in img_files if domain.lower() in str(f.parent.parent)]
        vid_files = [f for f in vid_files if domain.lower() in str(f.parent.parent)]
        
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
        is_last = (i == len(paginated_files) - 1) and (end_idx < len(all_files))
        
        htmx_attrs = ""
        if is_last:
            next_url = f"/htmx/gallery?keyword={keyword}&domain={domain}&page={page+1}&limit={limit}&media_kind={media_kind}"
            htmx_attrs = f' hx-get="{next_url}" hx-trigger="revealed" hx-swap="afterend"'
            
        card_html = []
        card_html.append(f'<div class="media-card"{htmx_attrs}>')
        if f.suffix.lower() in [".mp4", ".webm", ".mkv", ".ogv"]:
            card_html.append(f'<video src="/{rel_path}" controls preload="metadata"></video>')
        else:
            card_html.append(f'<img src="/{rel_path}" loading="lazy" />')
            
        card_html.append(f'''
        <div class="overlay">
            <div class="overlay-buttons">
                <button hx-post="/htmx/open-folder" hx-vals=\'{{"path": "{rel_path}"}}\' hx-swap="none" class="btn-overlay">FOLDER</button>
                <button hx-delete="/htmx/media?path={rel_path}" hx-target="closest .media-card" hx-swap="outerHTML swap:0.2s" class="btn-overlay delete">DELETE</button>
            </div>
            <div class="media-filename">{f.name}</div>
        </div>
        </div>
        ''')
        html_chunks.append("".join(card_html))
            
    if not html_chunks and page == 1:
        return HTMLResponse("<div style='grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;'>No media found.</div>")
        
    return HTMLResponse("\n".join(html_chunks))

@app.delete("/htmx/media")
def delete_media(path: str):
    target = OUTPUT_DIR / path
    if target.exists() and target.is_file():
        # Security check
        if str(OUTPUT_DIR.resolve()) in str(target.resolve()):
            target.unlink()
            return HTMLResponse("") # Empty response removes it from DOM
    raise HTTPException(status_code=404)

@app.post("/htmx/open-folder")
async def open_folder(request: Request):
    form = await request.form()
    path = form.get("path", "")
    target = OUTPUT_DIR / path
    if target.exists():
        # Windows only
        subprocess.Popen(f'explorer /select,"{target.resolve()}"')
    return HTMLResponse("")

@app.get("/htmx/stats")
def get_stats():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage(str(OUTPUT_DIR)).percent
    return HTMLResponse(f"""
        <div style="display: flex; gap: 2rem; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; color: var(--text-primary);">
            <div>SYS.CPU <span style="color: {'var(--accent)' if cpu > 80 else 'var(--text-muted)'}">{cpu}%</span></div>
            <div>SYS.RAM <span style="color: {'var(--accent)' if ram > 80 else 'var(--text-muted)'}">{ram}%</span></div>
            <div>SYS.DSK <span style="color: {'var(--accent)' if disk > 90 else 'var(--text-muted)'}">{disk}%</span></div>
        </div>
    """)

@app.post("/htmx/run")
async def htmx_run(request: Request):
    form = await request.form()
    req = ScrapeRequest(
        keyword=form.get("keyword"),
        max_results=int(form.get("max_results", 50)),
        workers=int(form.get("workers", 8)),
        dl_workers=int(form.get("dl_workers", 6)),
        page_limit=int(form.get("page_limit", 100)),
        crawl_depth=int(form.get("crawl_depth", 2)),
        output=form.get("output", "both"),
        seed_urls=form.get("seed_urls"),
        allow_domains=form.get("allow_domains"),
        block_domains=form.get("block_domains"),
        entity_tokens=form.get("entity_tokens"),
        domain_delays=form.get("domain_delays"),
        proxy=form.get("proxy"),
        capsolver_key=form.get("capsolver_key")
    )
    if form.get("seed"):
        req.seed = form.get("seed")
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
        return HTMLResponse("<div style='color: var(--accent); margin-top: 1rem;'>SCRAPE INITIATED // LOG STREAM ACTIVE</div>")
    except Exception as e:
        return HTMLResponse(f"<div style='color: red; margin-top: 1rem;'>ERR: {str(e)}</div>")

@app.post("/htmx/kill")
def kill_scrape():
    global _current_process, task_state
    if _current_process and _current_process.poll() is None:
        _current_process.kill()
        task_state["status"] = "idle"
        task_state["pid"] = None
        log_buffer.append(">>> PROCESS KILLED BY USER <<<")
        return HTMLResponse("<div style='color: red; margin-top: 1rem;'>PROCESS ABORTED</div>")
    return HTMLResponse("<div style='color: var(--text-muted); margin-top: 1rem;'>NO ACTIVE PROCESS</div>")

@app.get("/api/seeds")
def get_seeds():
    seeds_dir = ROOT_DIR / "seeds"
    if not seeds_dir.exists():
        return []
    return sorted([f.name for f in seeds_dir.glob("*.txt")])

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

def get_historical_stats():
    total_runs = 0
    total_images = 0
    total_videos = 0
    total_scanned = 0

    if OUTPUT_DIR.exists():
        for json_file in OUTPUT_DIR.glob("*/runs/*/results.json"):
            total_runs += 1
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    total_images += data.get("download_stats", {}).get("images_saved", 0)
                    total_videos += data.get("download_stats", {}).get("videos_saved", 0)
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

# Mount static files at the root to serve all media assets.
# This MUST be declared last so it doesn't swallow API routes.
app.mount("/", StaticFiles(directory=str(OUTPUT_DIR), html=False), name="output")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=10001)
    args = parser.parse_args()
    
    uvicorn.run("frontend.app:app", host="localhost", port=args.port, reload=False)
