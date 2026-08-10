"""FastAPI APIRouter for WebUI managing Subject Profiles."""

import json
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/api/subject-profiles", tags=["subject_profiles"])
logger = logging.getLogger(__name__)

import html

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT_DIR / "data" / "subject_profiles.json"

@router.get("")
@router.get("/")
def get_subject_profiles():
    """Retrieve raw subject_profiles.json payload."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        default_config = {}
        CONFIG_PATH.write_text(json.dumps(default_config, indent=4), encoding="utf-8")

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {
            "config": data,
            "raw_json": json.dumps(data, indent=4),
            "stats": {
                "profile_count": len(data),
            }
        }
    except Exception as exc:
        logger.error("Failed to read subject_profiles.json: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to read subject profiles.")


@router.post("/save")
async def save_subject_profiles(request: Request):
    """Validate JSON payload and write to data/subject_profiles.json."""
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            body = await request.json()
            config_data = body.get("config", body)
        else:
            form = await request.form()
            raw_json = form.get("raw_json", "{}")
            config_data = json.loads(str(raw_json))

        if not isinstance(config_data, dict):
            raise ValueError("Root configuration must be a JSON object.")

        # Pretty format JSON before saving
        formatted_json = json.dumps(config_data, indent=4)
        CONFIG_PATH.write_text(formatted_json, encoding="utf-8")

        if "text/html" in request.headers.get("accept", "") or "hx-request" in request.headers:
            return HTMLResponse(
                '<div class="alert alert-success" style="color: #00ff66; border: 1px solid #00ff66; padding: 10px; margin-top: 10px; font-family: \'JetBrains Mono\', monospace;">'
                '[DONE] Subject Profiles saved successfully!'
                '</div>'
            )

        return {
            "status": "ok",
            "message": "Subject Profiles updated successfully.",
            "config": config_data,
        }
    except json.JSONDecodeError as err:
        lineno = getattr(err, "lineno", None)
        colno = getattr(err, "colno", None)
        if lineno is not None and colno is not None:
            msg = f"Invalid JSON syntax at line {lineno}, column {colno}."
        else:
            msg = "Invalid JSON syntax in payload."
        safe_msg = html.escape(msg)

        if "text/html" in request.headers.get("accept", "") or "hx-request" in request.headers:
            return HTMLResponse(
                f'<div class="alert alert-danger" style="color: #ff3333; border: 1px solid #ff3333; padding: 10px; margin-top: 10px; font-family: \'JetBrains Mono\', monospace;">'
                f'[ERROR] {safe_msg}'
                f'</div>',
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=msg)
    except Exception as exc:
        logger.error("Failed saving Subject Profiles: %s", exc)
        raise HTTPException(status_code=500, detail="Failed saving subject profiles.")
