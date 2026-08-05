from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from notifications.telegram_bot import TelegramBotNotifier, TelegramCommandHandler


@pytest.fixture
def mock_bot():
    bot = TelegramBotNotifier(token="123456:ABCdefGHI", chat_id="987654321")
    return bot


def test_telegram_bot_configured(mock_bot):
    assert mock_bot.is_configured()


@patch("requests.post")
def test_send_message_and_photo(mock_post, mock_bot, tmp_path):
    mock_post.return_value.status_code = 200

    assert mock_bot.send_message("Test message")
    assert mock_post.called

    test_img = tmp_path / "sample.jpg"
    test_img.write_bytes(b"\xFF\xD8\xFF\xE0\x00\x10JFIF")

    assert mock_bot.send_photo(str(test_img), caption="Test Caption")


def test_command_handler_status_and_stats(mock_bot):
    state = {"status": "running", "keyword": "cyberpunk", "pages_scanned": 15, "images_found": 42, "videos_found": 3}
    handler = TelegramCommandHandler(mock_bot, task_state_ref=state)

    with patch.object(mock_bot, "send_message") as mock_send:
        handler._handle_command("/status")
        mock_send.assert_called_once()
        assert "cyberpunk" in mock_send.call_args[0][0]

    with patch.object(mock_bot, "send_message") as mock_send:
        handler._handle_command("/stats")
        mock_send.assert_called_once()
        assert "42" in mock_send.call_args[0][0]


def test_command_handler_pause_resume(mock_bot):
    state = {"status": "running"}
    handler = TelegramCommandHandler(mock_bot, task_state_ref=state)

    with patch.object(mock_bot, "send_message"):
        handler._handle_command("/pause")
        assert state["status"] == "paused"

        handler._handle_command("/resume")
        assert state["status"] == "running"


def test_command_handler_stop_and_abort_interactive(mock_bot):
    state = {}
    handler = TelegramCommandHandler(mock_bot, task_state_ref=state)

    with patch.object(mock_bot, "send_message") as mock_send:
        handler._handle_command("/stop")
        assert "reply_markup" in mock_send.call_args[1]

    with patch.object(mock_bot, "send_message") as mock_send:
        handler._handle_command("/abort")
        assert "reply_markup" in mock_send.call_args[1]

    # Test callback query confirmation
    with patch.object(mock_bot, "answer_callback_query"), patch.object(mock_bot, "send_message"):
        handler._handle_callback_query({"id": "cb1", "data": "confirm_stop"})
        assert state.get("stop_requested") is True

        handler._handle_callback_query({"id": "cb2", "data": "confirm_abort"})
        assert state.get("abort_requested") is True


def test_command_handler_blacklist_and_setlimit(mock_bot):
    state = {}
    handler = TelegramCommandHandler(mock_bot, task_state_ref=state)

    with patch.object(mock_bot, "send_message"):
        handler._handle_command("/blacklist badsite.com")
        assert "badsite.com" in state.get("blacklisted_domains", [])

        handler._handle_command("/setlimit 300")
        assert state.get("max_results_override") == 300


def test_command_handler_report_and_watchdog(mock_bot):
    state = {"domain_report": {"example.com": {"pages": 5, "images": 12, "videos": 0}}, "watchdog_active": False}
    handler = TelegramCommandHandler(mock_bot, task_state_ref=state)

    with patch.object(mock_bot, "send_message") as mock_send:
        handler._handle_command("/report")
        assert "example.com" in mock_send.call_args[0][0]

    with patch.object(mock_bot, "send_message"):
        handler._handle_command("/watchdog")
        assert state["watchdog_active"] is True
