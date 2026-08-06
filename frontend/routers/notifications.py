"""FastAPI router for Telegram Bot & Multi-Channel Webhook Notifications."""

from fastapi import APIRouter, Form
import config

router = APIRouter(prefix="/api", tags=["notifications"])

telegram_config = {
    "token": getattr(config, "TELEGRAM_BOT_TOKEN", ""),
    "chat_id": getattr(config, "TELEGRAM_CHAT_ID", ""),
    "enabled": True,
}


@router.get("/telegram/config")
def get_telegram_config():
    """Return current Telegram Bot configuration."""
    return {"status": "ok", **telegram_config}


@router.post("/telegram/config")
def update_telegram_config(token: str = Form(""), chat_id: str = Form(""), enabled: bool = Form(True)):
    """Update Telegram Bot configuration."""
    telegram_config["token"] = token.strip()
    telegram_config["chat_id"] = chat_id.strip()
    telegram_config["enabled"] = enabled
    return {"status": "ok", **telegram_config}


@router.post("/telegram/test")
def test_telegram_notification(token: str = Form(""), chat_id: str = Form("")):
    """Send a test notification message via Telegram Bot API."""
    from notifications.telegram_bot import TelegramBotNotifier

    tok = token.strip() or telegram_config.get("token", "")
    cid = chat_id.strip() or telegram_config.get("chat_id", "")
    notifier = TelegramBotNotifier(tok, cid)
    success = notifier.send_message("<b>scrAPE Telegram Bot Connected!</b>\nTest alert message received successfully.")
    return {"status": "ok" if success else "failed", "sent": success}
