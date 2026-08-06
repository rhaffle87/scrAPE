"""FastAPI router for AI dataset curation, WD14 tagging, and Kohya LoRA exports."""

import os
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import Response

router = APIRouter(prefix="/api/dataset", tags=["dataset"])

# Lazy output directory derivation
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
OUTPUT_DIR = ROOT_DIR / "output"


@router.post("/tag")
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


@router.get("/sidecar")
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


@router.post("/sidecar")
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


@router.post("/score")
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


@router.post("/crop")
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


@router.get("/export")
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
