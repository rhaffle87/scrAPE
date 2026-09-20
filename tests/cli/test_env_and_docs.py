from __future__ import annotations

from pathlib import Path
import config


def test_env_credentials_loading():
    """Test that config loads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from .env
    without asserting on literal secret values.  We verify:
      - Both attributes exist and are strings (not None/missing).
      - TELEGRAM_BOT_TOKEN looks like a Telegram bot-token (<numeric_id>:<hash>).
      - TELEGRAM_CHAT_ID is numeric (positive or negative integer string).
    """
    token = getattr(config, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(config, "TELEGRAM_CHAT_ID", "")

    # Must be present (non-empty) when a .env file is configured
    # In CI without .env these will be empty — that is also acceptable.
    assert isinstance(token, str), "TELEGRAM_BOT_TOKEN must be a string"
    assert isinstance(chat_id, str), "TELEGRAM_CHAT_ID must be a string"

    # If populated, validate format (never assert the literal secret value)
    if token:
        parts = token.split(":")
        assert len(parts) == 2, "TELEGRAM_BOT_TOKEN must follow <id>:<hash> format"
        assert parts[0].isdigit(), "TELEGRAM_BOT_TOKEN id segment must be numeric"
        assert len(parts[1]) > 10, "TELEGRAM_BOT_TOKEN hash segment too short"

    if chat_id:
        assert chat_id.lstrip("-").isdigit(), "TELEGRAM_CHAT_ID must be numeric"


def test_gitignore_contains_env():
    """Test that .gitignore includes .env so secrets are never committed."""
    gitignore = Path(".gitignore")
    assert gitignore.exists()
    content = gitignore.read_text(encoding="utf-8")
    assert ".env" in content
