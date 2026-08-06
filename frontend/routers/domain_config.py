"""FastAPI APIRouter for WebUI Domain Config Studio managing domain rules with live hot reload."""

import json
import logging
from pathlib import Path
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

from core.managers import DomainRulesManager

router = APIRouter(prefix="/api/domain-config", tags=["domain_config"])
logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT_DIR / "data" / "domain_config.json"


class DomainConfigSaveRequest(BaseModel):
    config: Dict[str, Any]


@router.get("")
@router.get("/")
def get_domain_config():
    """Retrieve raw domain_config.json payload and structure stats."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        default_config = {
            "rate_limits": {},
            "hotlink_protected": [],
            "referer_overrides": {},
            "stealth_required": [],
            "deep_scrape": []
        }
        CONFIG_PATH.write_text(json.dumps(default_config, indent=4), encoding="utf-8")

    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return {
            "config": data,
            "raw_json": json.dumps(data, indent=4),
            "stats": {
                "hotlink_domains": len(data.get("hotlink_protected", [])),
                "rate_limits": len(data.get("rate_limits", {})),
                "stealth_required": len(data.get("stealth_required", [])),
                "deep_scrape": len(data.get("deep_scrape", [])),
                "referer_overrides": len(data.get("referer_overrides", {})),
            }
        }
    except Exception as exc:
        logger.error("Failed to read domain_config.json: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to read configuration: {exc}")


@router.post("/save")
async def save_domain_config(request: Request):
    """Validate JSON payload, write to data/domain_config.json, and clear DomainRulesManager cache."""
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

        # Invalidate in-memory DomainRulesManager cache
        try:
            DomainRulesManager().clear_cache()
            logger.info("DomainRulesManager cache cleared following WebUI config update.")
        except Exception as exc:
            logger.warning("Failed clearing DomainRulesManager cache: %s", exc)

        if "text/html" in request.headers.get("accept", "") or "hx-request" in request.headers:
            return HTMLResponse(
                '<div class="alert alert-success" style="color: #00ff66; border: 1px solid #00ff66; padding: 10px; margin-top: 10px; font-family: \'JetBrains Mono\', monospace;">'
                '✅ Domain configuration saved and hot-reloaded successfully!'
                '</div>'
            )

        return {
            "status": "ok",
            "message": "Domain configuration updated and hot-reloaded successfully.",
            "config": config_data,
        }
    except json.JSONDecodeError as err:
        msg = f"Invalid JSON syntax: {err}"
        if "text/html" in request.headers.get("accept", "") or "hx-request" in request.headers:
            return HTMLResponse(
                f'<div class="alert alert-danger" style="color: #ff3333; border: 1px solid #ff3333; padding: 10px; margin-top: 10px; font-family: \'JetBrains Mono\', monospace;">'
                f'❌ {msg}'
                f'</div>',
                status_code=400,
            )
        raise HTTPException(status_code=400, detail=msg)
    except Exception as exc:
        logger.error("Failed saving domain configuration: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
