"""FastAPI router for gallery browsing, pagination, and media item management."""

from __future__ import annotations

import html
import logging
import os
from pathlib import Path
import re
import sys
from subprocess import Popen
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from frontend.state import OUTPUT_DIR
from common.security import validate_safe_path

logger = logging.getLogger(__name__)

router = APIRouter(tags=["gallery"])


@router.get("/api/gallery/{keyword}")
def get_gallery_items(keyword: str, page: int = 1, limit: int = 50, domain: str = ""):
    images = []
    videos = []

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
        [f for f in img_files if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]]
        + [f for f in vid_files if f.suffix.lower() in [".mp4", ".webm", ".mkv", ".ogv"]],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
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
        "limit": limit,
    }


@router.get("/htmx/gallery")
def htmx_gallery(keyword: str = "apple", domain: str = "", page: int = 1, limit: int = 20, media_kind: str = "all"):
    safe_keyword = os.path.basename(keyword)
    if not safe_keyword or not re.match(r"^[\w\-. ]+$", safe_keyword):
        return HTMLResponse(
            "<div style='grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;'>No media found for this keyword.</div>"
        )

    base_dir = os.path.abspath(str(OUTPUT_DIR))
    keyword_dir_str = os.path.abspath(os.path.join(base_dir, safe_keyword, "runs"))
    if not keyword_dir_str.startswith(base_dir + os.sep):
        return HTMLResponse(
            "<div style='grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;'>No media found for this keyword.</div>"
        )
    keyword_dir = Path(keyword_dir_str)
    if not keyword_dir.exists():
        return HTMLResponse(
            "<div style='grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;'>No media found for this keyword.</div>"
        )

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
        [f for f in img_files if f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".gif"]]
        + [f for f in vid_files if f.suffix.lower() in [".mp4", ".webm", ".mkv", ".ogv"]],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
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
            safe_kw = quote(keyword)
            safe_dom = quote(domain) if domain else ""
            safe_kind = quote(media_kind)
            next_url = f"/htmx/gallery?keyword={safe_kw}&domain={safe_dom}&page={page+1}&limit={limit}&media_kind={safe_kind}"
            safe_next_url = html.escape(next_url)
            htmx_attrs = f' hx-get="{safe_next_url}" hx-trigger="revealed" hx-swap="afterend"'

        card_html = []
        card_html.append(f'<div class="media-card"{htmx_attrs}>')
        if f.suffix.lower() in [".mp4", ".webm", ".mkv", ".ogv"]:
            card_html.append(
                f'<video src="/{safe_rel_path}" controls preload="metadata" controlsList="nodownload" disablePictureInPicture></video>'
            )
        else:
            card_html.append(f'<img src="/{safe_rel_path}" loading="lazy" />')

        safe_folder_path = html.escape(rel_path)
        card_html.append(f"""
        <div class="overlay">
            <div class="overlay-buttons">
                <button hx-post="/htmx/open-folder" hx-vals='{{"path": "{safe_folder_path}"}}' hx-swap="none" class="btn-overlay">FOLDER</button>
                <button hx-delete="/htmx/media?path={safe_rel_path}" hx-target="closest .media-card" hx-swap="outerHTML swap:0.2s" class="btn-overlay delete">DELETE</button>
            </div>
            <div class="media-filename">{safe_name}</div>
        </div>
        </div>
        """)
        html_chunks.append("".join(card_html))

    if not html_chunks and page == 1:
        return HTMLResponse(
            "<div style='grid-column: 1 / -1; text-align: center; color: var(--text-muted); padding: 2rem;'>No media found.</div>"
        )

    return HTMLResponse("\n".join(html_chunks))


@router.delete("/htmx/media")
def delete_media(path: str):
    base_dir = os.path.abspath(str(OUTPUT_DIR))
    target_path = os.path.abspath(os.path.join(base_dir, path))
    if not target_path.startswith(base_dir + os.sep):
        raise HTTPException(status_code=400)
    target = Path(target_path)
    try:
        if target.is_file():
            target.unlink()
            return HTMLResponse("")
    except Exception:
        pass
    raise HTTPException(status_code=404)


def _get_form_str(form: Any, key: str, default: str | None = None) -> str | None:
    val = form.get(key)
    if isinstance(val, str):
        return val
    return default


@router.post("/htmx/open-folder")
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
        safe_path = validate_safe_path(base_dir, Path(base_dir) / clean_name)

        if safe_path.exists():
            target_path = str(safe_path)
            if os.name == "nt":
                Popen(["explorer", "/select,", target_path])  # nosec B603 B607
            elif sys.platform == "darwin":
                Popen(["open", "-R", target_path])  # nosec B603 B607
            else:
                Popen(["xdg-open", target_path])  # nosec B603 B607
            return HTMLResponse("Opened")
    except Exception as e:
        logger.warning("Failed to open folder: %s", e)
    return HTMLResponse("Failed to open")
