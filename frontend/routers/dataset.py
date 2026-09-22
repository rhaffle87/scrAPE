"""FastAPI router for AI dataset curation, WD14 tagging, Kohya LoRA, and RAG exports."""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
import re
import shutil
import threading
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import Response
from pydantic import BaseModel

from frontend.state import ROOT_DIR, OUTPUT_DIR, _is_safe_path_component
from common.security import validate_safe_path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["dataset"])


class ExportDatasetPayload(BaseModel):
    subject: str
    run_id: str
    layout: str = "1"  # "1" = flat, "2" = domain, "3" = media_type


class ExportRAGPayload(BaseModel):
    subject: str
    run_id: str


class DatasetExportRequest(BaseModel):
    min_aesthetic_score: float = 5.5
    enable_wd14_tagging: bool = True
    smart_crop: bool = False


class DatabaseExportRequest(BaseModel):
    format: str = "csv"


# ---------------------------------------------------------------------------
# Dataset Curation & Tagging Endpoints
# ---------------------------------------------------------------------------

@router.post("/dataset/tag")
def api_dataset_tag(subject: str = Form(""), trigger_tag: str = Form("")):
    """Batch auto-tag downloaded images in a subject run folder."""
    from ml.dataset_tagger import DatasetTagger

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
        output_dir = Path(fallback_path)

    tagger = DatasetTagger(trigger_tag=trigger_tag)
    res = tagger.tag_directory(output_dir)
    return {"status": "ok", "subject": safe_subject, **res}


@router.get("/dataset/sidecar")
def get_dataset_sidecar(path: str):
    """Retrieve sidecar text file for a given image path."""
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


@router.post("/dataset/sidecar")
def save_dataset_sidecar(path: str = Form(...), tags: str = Form(...)):
    """Update sidecar text file for a given image path."""
    base_dir = os.path.abspath(str(OUTPUT_DIR))
    resolved = os.path.abspath(os.path.join(base_dir, path))
    if not resolved.startswith(base_dir + os.sep):
        raise HTTPException(status_code=400, detail="Invalid path")
    img_path = Path(resolved)
    sidecar_path = img_path.with_suffix(".txt")
    sidecar_path.write_text(tags, encoding="utf-8")
    return {"status": "ok", "path": str(sidecar_path), "saved_tags": tags}


@router.post("/dataset/score")
def api_dataset_score(subject: str = Form(""), min_score: float = Form(6.0)):
    """Evaluate aesthetic quality scores for images in a subject folder."""
    from ml.aesthetic_scorer import AestheticScorer

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


@router.post("/dataset/crop")
def api_dataset_crop(subject: str = Form(""), width: int = Form(1024), height: int = Form(1024)):
    """Batch smart-crop images in a subject folder to specified aspect ratio/resolution."""
    from ml.dataset_cropper import DatasetCropper

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


@router.get("/dataset/export")
def export_dataset_zip(subject: str, repeats: int = 10, concept: str = "concept"):
    """Export Kohya_ss formatted LoRA dataset ZIP archive."""
    from ml.dataset_exporter import KohyaDatasetExporter

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


@router.post("/dataset/export/{subject}")
def export_dataset_post(subject: str, req: DatasetExportRequest):
    """Trigger background dataset export with full ML processing."""
    from ml.dataset_exporter import create_dataset_task

    safe_subject = os.path.basename(subject)
    if not safe_subject or not re.match(r"^[\w\-. ]+$", safe_subject):
        raise HTTPException(status_code=400, detail="Invalid subject name")

    thread = threading.Thread(
        target=create_dataset_task,
        args=(safe_subject, req.min_aesthetic_score, req.enable_wd14_tagging, req.smart_crop, OUTPUT_DIR),
        daemon=True,
    )
    thread.start()

    return {"status": "ok", "message": f"Dataset export started for {safe_subject}"}


@router.post("/dataset/export-db/{subject}")
@router.post("/export-db/{subject}")
def api_export_database(subject: str, req: DatabaseExportRequest):
    """Export the local database to CSV, JSON, or Parquet format."""
    safe_subject = os.path.basename(subject)
    if not safe_subject or not re.match(r"^[\w\-. ]+$", safe_subject):
        raise HTTPException(status_code=400, detail="Invalid subject name")

    base_dir = os.path.abspath(str(OUTPUT_DIR))
    try:
        subject_path = validate_safe_path(base_dir, Path(base_dir) / safe_subject)
    except ValueError:
        raise HTTPException(status_code=400, detail="Path traversal detected")

    if not subject_path.exists():
        raise HTTPException(status_code=404, detail="Subject directory not found")

    try:
        from storage.analytics_exporter import export_analytics
        export_analytics(subject_path, req.format)
        return {"status": "ok", "message": f"Successfully exported database to {req.format.upper()} format."}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database export failed: {e}")


# ---------------------------------------------------------------------------
# AI LoRA & RAG Run Export Endpoints
# ---------------------------------------------------------------------------

@router.get("/runs/{subject}/{run_id}/summary")
def get_run_summary(subject: str, run_id: str):
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


@router.post("/export/dataset")
def export_ai_dataset(payload: ExportDatasetPayload):
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
        raise HTTPException(status_code=404, detail="Run directory not found")

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


@router.get("/export/dataset/download/{subject}/{run_id}")
def download_kohya_dataset_zip(
    subject: str, run_id: str, repeats: int = 10, min_resolution: int = 512, min_aesthetic_score: float = 0.0
):
    """Generate and stream Kohya_ss LoRA dataset ZIP file directly to browser."""
    from ml.dataset_exporter import KohyaDatasetExporter

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


@router.post("/export/rag")
def export_rag_markdown(payload: ExportRAGPayload):
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
    except Exception:
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
