from fastapi import APIRouter, HTTPException, Form
from pathlib import Path

router = APIRouter(prefix="/api/settings", tags=["settings"])
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
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


from fastapi import Request

@router.get("/")
def api_get_settings():
    """Get all settings from .env"""
    settings = {}
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                settings[key] = val
    return settings

@router.post("/")
async def api_save_settings(request: Request):
    """Save settings to .env"""
    settings = await request.json()
    for key, value in settings.items():
        if isinstance(value, bool):
            value = str(value).lower()
        update_env(key, str(value))
    return {"status": "ok", "message": "Settings saved."}
