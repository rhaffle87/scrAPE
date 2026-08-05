from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

from notifications.notification_manager import (
    BaseNotifier,
    CustomWebhookNotifier,
    DiscordNotifier,
    EventTypes,
    NotificationPipeline,
    SlackNotifier,
    SMTPNotifier,
    TelegramNotifier,
)


def test_event_types_constants():
    assert EventTypes.RUN_START == "run_start"
    assert EventTypes.RUN_COMPLETE == "run_complete"
    assert EventTypes.RUN_ERROR == "run_error"
    assert EventTypes.WAF_BLOCK == "waf_block"
    assert EventTypes.CAPTCHA_SOLVED == "captcha_solved"


def test_discord_notifier_not_configured():
    notifier = DiscordNotifier(webhook_url="")
    assert not notifier.is_configured()
    assert not notifier.notify_run_start("test", 1)


@patch("requests.post")
def test_discord_notifier_dispatch(mock_post):
    mock_post.return_value.status_code = 204
    notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/123/abc")
    assert notifier.is_configured()

    assert notifier.notify_run_start("cat", 5, ["example.com"], 100, 4, 50, 2)
    assert mock_post.called

    assert notifier.notify_run_complete("cat", 10, 50, 2, 12.5)
    assert notifier.notify_waf_block("example.com", 60, "StealthPipeline")
    assert notifier.notify_run_error("cat", "Connection failure")
    assert notifier.notify_captcha_solved("example.com", "CapSolver", 0.002)


def test_slack_notifier_not_configured():
    notifier = SlackNotifier(webhook_url="")
    assert not notifier.is_configured()


@patch("requests.post")
def test_slack_notifier_dispatch(mock_post):
    mock_post.return_value.status_code = 200
    notifier = SlackNotifier(webhook_url="https://hooks.slack.com/services/123")
    assert notifier.is_configured()

    assert notifier.notify_run_start("dog", 2)
    assert notifier.notify_run_complete("dog", 5, 20, 1, 8.0)
    assert notifier.notify_waf_block("domain.com", 30)
    assert notifier.notify_run_error("dog", "Timeout")
    assert notifier.notify_captcha_solved("domain.com", "2Captcha", 0.001)


@patch("requests.post")
def test_custom_webhook_notifier(mock_post):
    mock_post.return_value.status_code = 200
    notifier = CustomWebhookNotifier(webhook_url="https://api.myapp.com/webhook")
    assert notifier.is_configured()

    assert notifier.notify_run_start("bird", 1)
    assert notifier.notify_run_complete("bird", 1, 2, 0, 3.0)
    assert notifier.notify_waf_block("test.com", 15)
    assert notifier.notify_run_error("bird", "Error")
    assert notifier.notify_captcha_solved("test.com", "AntiCaptcha", 0.003)


def test_smtp_notifier_not_configured():
    notifier = SMTPNotifier(host="", port=587, to_email="")
    assert not notifier.is_configured()


@patch("smtplib.SMTP")
def test_smtp_notifier_dispatch(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value.__enter__.return_value = mock_server

    notifier = SMTPNotifier(
        host="smtp.gmail.com",
        port=587,
        user="test@gmail.com",
        password="secretpassword",
        to_email="alerts@domain.com",
        use_tls=True,
    )
    assert notifier.is_configured()

    assert notifier.notify_run_start("car", 2)
    assert notifier.notify_run_complete("car", 10, 30, 0, 15.0)
    assert notifier.notify_waf_block("cars.com", 60)
    assert notifier.notify_run_error("car", "Exception trace")
    assert notifier.notify_captcha_solved("cars.com", "CapSolver", 0.005)


def test_notification_pipeline_dispatch():
    class DummyNotifier(BaseNotifier):
        def is_configured(self) -> bool:
            return True
        def notify_run_complete(self, keyword, pages, images, videos, duration_s, extra_text=""):
            return True
        def notify_waf_block(self, domain, cooldown_s, strategy_name=""):
            return True
        def notify_run_start(self, keyword, seed_count, seed_domains=None, max_results=0, workers=0, page_limit=0, crawl_depth=0):
            return True
        def notify_run_error(self, keyword, error_msg):
            return True
        def notify_captcha_solved(self, domain, solver_name, cost=0.0):
            return True

    dummy = DummyNotifier()
    pipeline = NotificationPipeline(providers=[dummy])
    assert len(pipeline.providers) == 1

    res_start = pipeline.notify_run_start("query", 5)
    assert res_start["DummyNotifier"] is True

    res_complete = pipeline.notify_run_complete("query", 1, 2, 3, 4.0)
    assert res_complete["DummyNotifier"] is True

    res_waf = pipeline.notify_waf_block("target.com", 30)
    assert res_waf["DummyNotifier"] is True

    res_err = pipeline.notify_run_error("query", "Error msg")
    assert res_err["DummyNotifier"] is True

    res_cap = pipeline.notify_captcha_solved("target.com", "CapSolver", 0.01)
    assert res_cap["DummyNotifier"] is True
