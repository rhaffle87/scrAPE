"""
test_monitor_agent_enhanced.py — Unit tests for enhanced Continuous Watchdog Agent.
"""

from unittest.mock import MagicMock
from src.cli.monitor_agent import discover_rotation_targets, notify_telegram


def test_discover_rotation_targets(tmp_path):
    seeds_dir = tmp_path / "seeds"
    seeds_dir.mkdir(parents=True, exist_ok=True)

    (seeds_dir / "subject_alpha.txt").write_text("https://example.com/alpha", encoding="utf-8")
    (seeds_dir / "subject_beta.txt").write_text("https://example.com/beta", encoding="utf-8")

    targets = discover_rotation_targets(str(seeds_dir))
    assert len(targets) == 2
    assert targets[0] == ("subject alpha", str(seeds_dir / "subject_alpha.txt"))
    assert targets[1] == ("subject beta", str(seeds_dir / "subject_beta.txt"))


def test_notify_telegram(monkeypatch):
    mock_notifier = MagicMock()
    mock_notifier.is_configured.return_value = True

    monkeypatch.setattr("utils.telegram_bot.TelegramBotNotifier", lambda token, chat_id: mock_notifier)

    notify_telegram("Test Watchdog Alert")
    mock_notifier.send_message.assert_called_once_with("Test Watchdog Alert")
