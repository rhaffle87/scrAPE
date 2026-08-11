import logging
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from network.session import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/plugins/auth", tags=["auth"])

class AuthCookieRequest(BaseModel):
    domain: str
    cookies: dict[str, str]

@router.post("")
def save_auth_cookies(req: AuthCookieRequest):
    """Save authentication cookies for a specific domain via SessionManager."""
    if not req.domain or not req.cookies:
        raise HTTPException(status_code=400, detail="Domain and cookies are required.")
    
    try:
        manager = SessionManager()
        existing = manager.load_session(req.domain) or {}
        if isinstance(existing, list):
            existing_dict = {c["name"]: c["value"] for c in existing if isinstance(c, dict)}
        else:
            existing_dict = existing
            
        existing_dict.update(req.cookies)
        manager.save_session(req.domain, existing_dict)
        
        return {"status": "ok", "message": f"Saved {len(req.cookies)} cookies for {req.domain}"}
    except Exception as e:
        logger.error("Failed to save cookies for %s: %s", req.domain, e)
        raise HTTPException(status_code=500, detail="Failed to save cookies.")
