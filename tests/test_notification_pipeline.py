import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from frontend.app import app
from notifications.notification_manager import (
    BaseNotifier,
    NotificationPipeline,
    TelegramNotifier,
    DiscordNotifier,
    SlackNotifier,
    CustomWebhookNotifier,
)

client = TestClient(app)


class MockCustomNotifier(BaseNotifier):
    """Test implementation of BaseNotifier plugin interface."""

    def __init__(self):
        self.run_completed_calls = []
        self.waf_block_calls = []

    def is_configured(self) -> bool:
        return True

    def notify_run_complete(
        self, keyword: str, pages: int, images: int, videos: int, duration_s: float, extra_text: str = ""
    ) -> bool:
        self.run_completed_calls.append((keyword, pages, images, videos, duration_s))
        return True

    def notify_waf_block(self, domain: str, cooldown_s: int, strategy_name: str = "") -> bool:
        self.waf_block_calls.append((domain, cooldown_s, strategy_name))
        return True


def test_base_notifier_plugin_extension():
    mock_provider = MockCustomNotifier()
    pipeline = NotificationPipeline(providers=[mock_provider])

    results = pipeline.notify_run_complete("test_subject", 10, 50, 5, 12.5)
    assert results.get("MockCustomNotifier") is True
    assert len(mock_provider.run_completed_calls) == 1
    assert mock_provider.run_completed_calls[0] == ("test_subject", 10, 50, 5, 12.5)

    waf_results = pipeline.notify_waf_block("blocked-target.com", 300, "Crawlee")
    assert waf_results.get("MockCustomNotifier") is True
    assert len(mock_provider.waf_block_calls) == 1


def test_discord_notifier_formatting(monkeypatch):
    discord = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/dummy/123")
    assert discord.is_configured()

    posted = {}

    def mock_post(url, json, timeout):
        posted["url"] = url
        posted["json"] = json
        res = MagicMock()
        res.status_code = 204
        return res

    monkeypatch.setattr("requests.post", mock_post)

    success = discord.notify_run_complete("cosplay", 5, 100, 10, 45.0)
    assert success is True
    assert posted["url"] == "https://discord.com/api/webhooks/dummy/123"
    assert "embeds" in posted["json"]
    assert posted["json"]["embeds"][0]["title"] == "⚡ scrAPE Run Completed"


def test_slack_notifier_formatting(monkeypatch):
    slack = SlackNotifier(webhook_url="https://hooks.slack.com/services/dummy/456")
    assert slack.is_configured()

    posted = {}

    def mock_post(url, json, timeout):
        posted["url"] = url
        posted["json"] = json
        res = MagicMock()
        res.status_code = 200
        return res

    monkeypatch.setattr("requests.post", mock_post)

    success = slack.notify_waf_block("cloudflare-site.com", 600, "FlareSolverr")
    assert success is True
    assert posted["url"] == "https://hooks.slack.com/services/dummy/456"
    assert "blocks" in posted["json"]


def test_api_test_notifications_endpoint():
    from unittest.mock import patch
    
    with patch("notifications.notification_manager.NotificationPipeline.notify_watchdog_status") as mock_notify:
        mock_notify.return_value = {"MockNotifier": True}
        res = client.post("/api/notifications/test")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert "delivered_providers" in data
