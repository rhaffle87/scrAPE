from __future__ import annotations

from utils.telegram_bot import TelegramBotNotifier, TelegramCommandHandler


def test_telegram_bot_notifier_formatting():
    """Test TelegramBotNotifier formatting and payload creation."""
    notifier = TelegramBotNotifier("123456:ABC-DEF", "987654321")
    assert notifier.is_configured() is True

    empty = TelegramBotNotifier("", "")
    assert empty.is_configured() is False
    assert empty.send_message("test") is False


def test_telegram_command_handler_parsing():
    """Test TelegramCommandHandler command handling."""
    notifier = TelegramBotNotifier("123456:ABC-DEF", "987654321")
    task_state = {"status": "idle", "keyword": "test_subject"}
    handler = TelegramCommandHandler(notifier, task_state)

    handler._handle_command("/pause")
    assert task_state["status"] == "paused"

    handler._handle_command("/resume")
    assert task_state["status"] == "running"
