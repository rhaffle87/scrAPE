from __future__ import annotations

from pathlib import Path
import config


def test_env_credentials_loading():
    """Test that config loads TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from .env."""
    token = getattr(config, "TELEGRAM_BOT_TOKEN", "")
    chat_id = getattr(config, "TELEGRAM_CHAT_ID", "")

    assert token == "6070297118:AAFedBmN0-U9UOpBQEtofv5HKKJWne6_6r4"
    assert chat_id == "1269573823"


def test_gitignore_contains_env():
    """Test that .gitignore includes .env."""
    gitignore = Path(".gitignore")
    assert gitignore.exists()
    content = gitignore.read_text(encoding="utf-8")
    assert ".env" in content
