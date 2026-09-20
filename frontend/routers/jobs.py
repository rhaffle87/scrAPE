"""FastAPI router for scraping job execution, subprocess tracking, pause/resume, and termination."""

from __future__ import annotations

import json
import logging
import os
import re
from subprocess import Popen, PIPE, STDOUT
import sys
import threading
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from frontend.state import (
    ROOT_DIR,
    SEEDS_DIR,
    task_state,
    _state_lock,
    get_current_process,
    set_current_process,
    log_buffer,
    broadcaster,
    _is_safe_target_url,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["jobs"])


class ScrapeRequest(BaseModel):
    keyword: str
    max_results: Optional[int] = 50
    workers: Optional[int] = 8
    dl_workers: Optional[int] = 6
    page_limit: Optional[int] = 100
    crawl_depth: Optional[int] = 2
    output: Optional[str] = "both"
    seed: Optional[str] = None
    seed_urls: Optional[str] = None
    allow_domains: Optional[str] = None
    block_domains: Optional[str] = None
    entity_tokens: Optional[str] = None
    domain_delays: Optional[str] = None
    proxy: Optional[str] = None
    capsolver_key: Optional[str] = None
    download_media: Optional[bool] = False
    ignore_robots: Optional[bool] = False
    skip_search: Optional[bool] = False
    strict_domain: Optional[bool] = False
    site_tree_only: Optional[bool] = False
    force_search: Optional[bool] = False
    clear_cache: Optional[bool] = False
    use_state_cache: Optional[bool] = False
    headless: Optional[bool] = False
    stealth_headful: Optional[bool] = False
    dl_speed_limit: Optional[int] = 0
    save_rejected: Optional[str] = ""
    rate_limit: Optional[float] = 0.0
    aesthetic_score: Optional[float] = 0.0
    auto_crop: Optional[bool] = False
    tag_dataset: Optional[bool] = False
    export_rag: Optional[bool] = False
    auto_export_db: Optional[bool] = False
    storage_backend: Optional[str] = "local"
    s3_bucket: Optional[str] = ""
    s3_prefix: Optional[str] = ""
    enable_self_healing: Optional[bool] = False
    worker_processes: Optional[int] = 0


def read_subprocess_logs(proc: Popen):
    with _state_lock:
        task_state["active_metrics"] = {
            "pages_scanned": 0,
            "images_saved": 0,
            "videos_saved": 0,
            "errors": 0,
        }
        task_state["progress"] = {
            "percent": 0,
            "current": 0,
            "total": 0,
            "time_info": "",
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
                "time_info": time_info,
            }
        broadcaster.broadcast("progress", task_state["progress"])

    def process_log_line(log_line: str):
        if "[TELEMETRY:" in log_line:
            telemetry_match = re.search(r"\[TELEMETRY:([^\]]+)\]\s*(.*)", log_line)
            if telemetry_match:
                event_type = telemetry_match.group(1)
                try:
                    data = json.loads(telemetry_match.group(2))
                    broadcaster.broadcast(event_type, data)
                except Exception:
                    pass

        log_buffer.append(log_line)
        lower_line = log_line.lower()
        with _state_lock:
            if "http request: get" in lower_line or "fetching page" in lower_line or "routing " in lower_line:
                if not any(
                    ext in lower_line
                    for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".mp4", ".webm", ".mkv"]
                ):
                    task_state["active_metrics"]["pages_scanned"] += 1
            elif "downloaded " in lower_line:
                if "images" in lower_line or any(
                    ext in lower_line for ext in [".jpg", ".jpeg", ".png", ".webp", ".gif"]
                ):
                    task_state["active_metrics"]["images_saved"] += 1
                elif "videos" in lower_line or any(
                    ext in lower_line for ext in [".mp4", ".webm", ".mkv", ".ogv"]
                ):
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
    set_current_process(None)
    broadcaster.broadcast("status", {"status": "idle"})


@router.post("/api/run")
def run_scrape(req: ScrapeRequest):
    curr_proc = get_current_process()
    if task_state["status"] == "running" and curr_proc:
        if curr_proc.poll() is None:
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
        "--output", req.output or "both",
    ]
    if req.seed:
        seed_basename = os.path.basename(req.seed)
        if not seed_basename or not re.match(r"^[\w\-. ]+\.txt$", seed_basename):
            raise HTTPException(status_code=400, detail="Invalid seed file name.")

        seeds_base = os.path.abspath(str(SEEDS_DIR))
        seed_resolved = os.path.abspath(os.path.join(seeds_base, seed_basename))
        if not seed_resolved.startswith(seeds_base + os.sep):
            raise HTTPException(status_code=400, detail="Seed path traverses outside allowed directory.")

        cmd.extend(["--seed-file", seed_resolved])

    if req.seed_urls:
        for url in req.seed_urls.split(","):
            url_clean = url.strip()
            if url_clean:
                if not _is_safe_target_url(url_clean):
                    raise HTTPException(
                        status_code=400,
                        detail=f"Target URL not permitted (SSRF protection): {url_clean}",
                    )
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
    if req.save_rejected:
        cmd.extend(["--save-rejected", req.save_rejected])
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

    if req.aesthetic_score and req.aesthetic_score > 0.0:
        cmd.extend(["--aesthetic-score", str(req.aesthetic_score)])
    if req.auto_crop:
        cmd.append("--auto-crop")
    if req.tag_dataset:
        cmd.append("--tag-dataset")
    if req.export_rag:
        cmd.append("--export-rag")
    if req.auto_export_db:
        cmd.append("--auto-export-db")
    if req.storage_backend and req.storage_backend != "local":
        cmd.extend(["--storage-backend", req.storage_backend])
    if req.s3_bucket:
        cmd.extend(["--s3-bucket", req.s3_bucket])
    if req.s3_prefix:
        cmd.extend(["--s3-prefix", req.s3_prefix])
    if req.enable_self_healing:
        cmd.append("--enable-self-healing")
    if req.worker_processes and req.worker_processes > 0:
        cmd.extend(["--worker-processes", str(req.worker_processes)])

    log_buffer.clear()

    popen_cls = getattr(sys.modules.get("frontend.app"), "Popen", Popen)
    proc = popen_cls(  # nosec B603
        cmd,
        executable=sys.executable,
        cwd=str(ROOT_DIR),
        stdout=PIPE,
        stderr=STDOUT,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace",
    )
    set_current_process(proc)

    threading.Thread(target=read_subprocess_logs, args=(proc,), daemon=True).start()

    task_state["status"] = "running"
    task_state["current_keyword"] = req.keyword
    task_state["pid"] = proc.pid
    task_state["progress"] = {
        "percent": 0,
        "current": 0,
        "total": 0,
        "time_info": "",
    }

    return {"message": "Scrape started", "pid": proc.pid}


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


@router.post("/htmx/run")
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
    save_rejected_val = _get_form_str(form, "save_rejected")
    if save_rejected_val:
        req.save_rejected = save_rejected_val
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
    if form.get("auto_crop") == "on":
        req.auto_crop = True
    if form.get("tag_dataset") == "on":
        req.tag_dataset = True
    if form.get("export_rag") == "on":
        req.export_rag = True
    if form.get("auto_export_db") == "on":
        req.auto_export_db = True
    if form.get("enable_self_healing") == "on":
        req.enable_self_healing = True

    aesthetic_str = _get_form_str(form, "aesthetic_score")
    if aesthetic_str:
        try:
            req.aesthetic_score = float(aesthetic_str)
        except ValueError:
            pass

    storage_val = _get_form_str(form, "storage_backend")
    if storage_val:
        req.storage_backend = storage_val
    s3_b = _get_form_str(form, "s3_bucket")
    if s3_b:
        req.s3_bucket = s3_b
    s3_p = _get_form_str(form, "s3_prefix")
    if s3_p:
        req.s3_prefix = s3_p
    w_proc = _get_form_int(form, "worker_processes", 0)
    if w_proc > 0:
        req.worker_processes = w_proc

    try:
        run_scrape(req)
        broadcaster.broadcast("status", {"status": "running"})
        return render_control_buttons()
    except Exception:
        return HTMLResponse(
            "<div style='color: red; margin-top: 1rem;'>ERR: An internal error occurred. Please check logs.</div>"
        )


@router.post("/htmx/kill")
def kill_scrape():
    with _state_lock:
        curr_proc = get_current_process()
        if curr_proc and curr_proc.poll() is None:
            try:
                import psutil
                parent = psutil.Process(curr_proc.pid)
                for child in parent.children(recursive=True):
                    try:
                        child.kill()
                    except Exception:
                        pass
                parent.kill()
            except Exception:
                curr_proc.kill()

            task_state["status"] = "idle"
            task_state["pid"] = None
            set_current_process(None)
            log_buffer.append(">>> PROCESS & CHILD WORKERS TERMINATED BY USER <<<")
            broadcaster.broadcast("status", {"status": "idle"})
            return render_control_buttons()
    return HTMLResponse("<div style='color: var(--text-muted); margin-top: 1rem;'>NO ACTIVE PROCESS</div>")


@router.post("/htmx/pause")
def htmx_pause_scrape():
    with _state_lock:
        curr_proc = get_current_process()
        if task_state["status"] == "running" and curr_proc and curr_proc.poll() is None:
            try:
                import psutil
                parent = psutil.Process(curr_proc.pid)
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


@router.post("/htmx/resume")
def htmx_resume_scrape():
    with _state_lock:
        curr_proc = get_current_process()
        if task_state["status"] == "paused" and curr_proc and curr_proc.poll() is None:
            try:
                import psutil
                parent = psutil.Process(curr_proc.pid)
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


@router.post("/htmx/stop")
def htmx_stop_scrape():
    return kill_scrape()


@router.post("/api/pause")
def api_pause():
    htmx_pause_scrape()
    return {"status": task_state["status"]}


@router.post("/api/resume")
def api_resume():
    htmx_resume_scrape()
    return {"status": task_state["status"]}


@router.post("/api/stop")
def api_stop():
    kill_scrape()
    return {"status": task_state["status"]}


@router.get("/htmx/controls")
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


@router.get("/htmx/status-badge")
def render_status_badge():
    status = task_state.get("status", "idle").upper()
    badge_class = "status-badge"
    if status == "RUNNING":
        badge_class += " running"
    elif status == "PAUSED":
        badge_class += " paused"

    color_style = (
        "color: var(--accent); border-color: var(--accent);"
        if status in {"RUNNING", "PAUSED"}
        else "color: var(--text-muted);"
    )
    return HTMLResponse(f'<span class="{badge_class}" style="{color_style}">{status}</span>')
