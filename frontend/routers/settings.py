"""FastAPI router for application configuration and solver credentials."""

from __future__ import annotations

import logging
import os

from fastapi import APIRouter, HTTPException, Form, Request

from frontend.state import ROOT_DIR

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["settings"])
ENV_PATH = ROOT_DIR / ".env"


def update_env(key: str, value: str):
    lines = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    new_lines = []
    found = False
    for line in lines:
        if line.startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)

    if not found:
        new_lines.append(f"{key}={value}")

    ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


@router.post("/solver")
def api_update_solver(
    provider: str = Form("capsolver"),
    api_key: str = Form(""),
):
    """Update captcha solver settings in .env"""
    if provider == "capsolver":
        update_env("CAPSOLVER_API_KEY", api_key)
    elif provider == "2captcha":
        update_env("TWOCAPTCHA_API_KEY", api_key)
    elif provider == "anticaptcha":
        update_env("ANTICAPTCHA_API_KEY", api_key)
    else:
        raise HTTPException(status_code=400, detail="Invalid provider")

    return {"status": "ok", "message": f"{provider} configuration saved."}


@router.get("")
@router.get("/")
def api_get_settings():
    """Get all settings combining SettingsManager and .env, with secrets masked."""
    try:
        from src.config.settings_manager import SettingsManager
        manager = SettingsManager()
        settings = manager.get_all()
    except Exception:
        settings = {}

    if ENV_PATH.exists():
        try:
            lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    if key not in settings:
                        settings[key] = val
        except Exception:
            pass

    sensitive_keys = [
        "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "DISCORD_WEBHOOK_URL",
        "SLACK_WEBHOOK_URL", "CAPSOLVER_API_KEY", "2CAPTCHA_API_KEY", "ANTICAPTCHA_API_KEY"
    ]

    for key in sensitive_keys:
        val = settings.get(key) or os.getenv(key)
        if val:
            settings[key] = "********"

    return settings


@router.post("")
@router.post("/")
async def api_save_settings(request: Request):
    """Save settings via SettingsManager and update .env."""
    body = await request.json()
    settings_dict = body.get("settings", body) if isinstance(body, dict) else {}

    try:
        from src.config.settings_manager import SettingsManager
        manager = SettingsManager()
        for key, value in settings_dict.items():
            manager.set(key, value)
    except Exception as e:
        logger.warning("Could not persist to SettingsManager: %s", e)

    for key, value in settings_dict.items():
        if isinstance(value, bool):
            value = str(value).lower()
        update_env(key, str(value))

    return {"status": "success", "message": "Settings saved successfully"}
