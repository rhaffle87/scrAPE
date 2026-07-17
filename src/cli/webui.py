import sys
import subprocess
import threading
from collections import deque
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
import json

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
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

task_state: Dict[str, Any] = {
    "status": "idle",
    "current_keyword": None,
    "pid": None
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
    global log_buffer
    if proc.stdout:
        for line in iter(proc.stdout.readline, ""):
            if line:
                log_buffer.append(line.rstrip("\n"))
        proc.stdout.close()

@app.get("/api/logs")
def get_logs(offset: int = 0):
    global log_buffer
    logs = list(log_buffer)
    if offset > len(logs):
        offset = 0
    new_lines = logs[offset:]
    return {"lines": new_lines, "next_offset": offset + len(new_lines)}

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
        "--crawl-depth", str(req.crawl_depth)
    ]
    if req.seed:
        # Resolve seed path relative to ROOT_DIR if it's not absolute
        seed_path = Path(req.seed)
        if not seed_path.is_absolute():
            seed_path = ROOT_DIR / req.seed
        cmd.extend(["--seed-file", str(seed_path)])
        
    if req.download_media:
        cmd.append("--download-media")
    if req.ignore_robots:
        cmd.append("--ignore-robots")

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
    
    return {"message": "Scrape started", "pid": _current_process.pid}

@app.get("/api/dashboard")
def get_dashboard():
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

    return {
        "total_runs": total_runs,
        "total_images": total_images,
        "total_videos": total_videos,
        "total_scanned_pages": total_scanned,
        "images": images,
        "videos": videos
    }

@app.get("/")
def serve_index():
    template_path = ROOT_DIR / "src" / "cli" / "templates" / "index.html"
    return FileResponse(template_path)

# Mount static files at the root to serve all media assets.
# This MUST be declared last so it doesn't swallow API routes.
app.mount("/", StaticFiles(directory=str(OUTPUT_DIR), html=False), name="output")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=10001)
    args = parser.parse_args()
    
    uvicorn.run("src.cli.webui:app", host="localhost", port=args.port, reload=False)
