from __future__ import annotations

from abc import ABC, abstractmethod
import concurrent.futures
import logging
import os
from typing import Any
import requests

from config.settings_manager import settings
from notifications.telegram_bot import TelegramBotNotifier

LOGGER = logging.getLogger(__name__)


class BaseNotifier(ABC):
    """Abstract base class for pluggable notification providers."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider credentials/urls are configured."""
        ...

    @abstractmethod
    def notify_run_complete(
        self, keyword: str, pages: int, images: int, videos: int, duration_s: float,
        extra_text: str = "",
    ) -> bool:
        """Send notification when a scraping run completes."""
        ...

    @abstractmethod
    def notify_waf_block(self, domain: str, cooldown_s: int, strategy_name: str = "") -> bool:
        """Send notification when WAF challenge / block occurs."""
        ...

    def notify_run_start(
        self,
        keyword: str,
        seed_count: int,
        seed_domains: list[str] | None = None,
        max_results: int = 0,
        workers: int = 0,
        page_limit: int = 0,
        crawl_depth: int = 0,
    ) -> bool:
        """Send notification when a scraping run is about to start."""
        return True

    def notify_run_error(self, keyword: str, error_msg: str) -> bool:
        """Send notification when a run crashes with an unhandled exception."""
        return True

    def notify_media_harvest(self, keyword: str, count: int, sample_urls: list[str] | None = None) -> bool:
        """Send notification when new media items are harvested."""
        return True

    def notify_watchdog_status(self, message: str, status_level: str = "INFO") -> bool:
        """Send watchdog health status update."""
        return True


class TelegramNotifier(BaseNotifier):
    """Telegram provider adapter wrapping TelegramBotNotifier."""

    def __init__(self, bot_instance: TelegramBotNotifier | None = None, token: str | None = None, chat_id: str | None = None):
        if bot_instance:
            self.bot = bot_instance
        else:
            token = token or settings.get("TELEGRAM_BOT_TOKEN")
            chat_id = chat_id or settings.get("TELEGRAM_CHAT_ID")
            self.bot = TelegramBotNotifier(token=token, chat_id=chat_id)

    def is_configured(self) -> bool:
        return self.bot.is_configured()

    def notify_run_complete(
        self, keyword: str, pages: int, images: int, videos: int, duration_s: float,
        extra_text: str = "",
    ) -> bool:
        return self.bot.notify_run_complete(keyword, pages, images, videos, duration_s, extra_text)

    def notify_waf_block(self, domain: str, cooldown_s: int, strategy_name: str = "") -> bool:
        return self.bot.notify_waf_block(domain, cooldown_s)

    def notify_media_harvest(self, keyword: str, count: int, sample_urls: list[str] | None = None) -> bool:
        text = f"<b>scrAPE Harvest Update</b>\nSubject: <code>{keyword}</code>\nNew Items: {count}"
        return self.bot.send_message(text)

    def notify_watchdog_status(self, message: str, status_level: str = "INFO") -> bool:
        text = f"<b>Watchdog [{status_level}]:</b> {message}"
        return self.bot.send_message(text)

    def notify_run_start(
        self,
        keyword: str,
        seed_count: int,
        seed_domains: list[str] | None = None,
        max_results: int = 0,
        workers: int = 0,
        page_limit: int = 0,
        crawl_depth: int = 0,
    ) -> bool:
        return self.bot.notify_run_start(
            keyword, seed_count, seed_domains, max_results, workers, page_limit, crawl_depth
        )

    def notify_run_error(self, keyword: str, error_msg: str) -> bool:
        return self.bot.notify_run_error(keyword, error_msg)


class DiscordNotifier(BaseNotifier):
    """Discord Webhook notification provider with rich embeds."""

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = (webhook_url or settings.get("DISCORD_WEBHOOK_URL", "")).strip()

    def is_configured(self) -> bool:
        return bool(self.webhook_url and self.webhook_url.startswith("http"))

    def _post_payload(self, payload: dict[str, Any]) -> bool:
        if not self.is_configured():
            return False
        try:
            res = requests.post(self.webhook_url, json=payload, timeout=10)
            return res.status_code in (200, 204)
        except Exception as exc:
            LOGGER.warning("Discord webhook request failed: %s", exc)
            return False

    def notify_run_complete(
        self, keyword: str, pages: int, images: int, videos: int, duration_s: float,
        extra_text: str = "",
    ) -> bool:
        fields = [
            {"name": "Keyword", "value": f"`{keyword}`", "inline": True},
            {"name": "Pages Scanned", "value": str(pages), "inline": True},
            {"name": "Images", "value": str(images), "inline": True},
            {"name": "Videos", "value": str(videos), "inline": True},
            {"name": "Duration", "value": f"{duration_s:.1f}s", "inline": True},
        ]
        if extra_text:
            fields.append({"name": "Details", "value": extra_text[:1024], "inline": False})
        payload = {
            "embeds": [
                {
                    "title": "SCRAPE Run Completed",
                    "color": 65280,  # Green
                    "fields": fields,
                    "footer": {"text": "SCRAPE AI Scraper Platform"},
                }
            ]
        }
        return self._post_payload(payload)

    def notify_waf_block(self, domain: str, cooldown_s: int, strategy_name: str = "") -> bool:
        payload = {
            "embeds": [
                {
                    "title": "[*] WAF Challenge Blocked Target",
                    "color": 16733696,  # Orange
                    "fields": [
                        {"name": "Domain", "value": f"`{domain}`", "inline": True},
                        {"name": "Cooldown", "value": f"{cooldown_s}s", "inline": True},
                        {"name": "Strategy", "value": strategy_name or "Stealth Pipeline", "inline": True},
                    ],
                }
            ]
        }
        return self._post_payload(payload)

    def notify_run_start(
        self,
        keyword: str,
        seed_count: int,
        seed_domains: list[str] | None = None,
        max_results: int = 0,
        workers: int = 0,
        page_limit: int = 0,
        crawl_depth: int = 0,
    ) -> bool:
        domains_str = ", ".join((seed_domains or [])[:6])
        payload = {
            "embeds": [{
                "title": "\U0001f680 scrAPE Run Started",
                "color": 3447003,  # Blue
                "fields": [
                    {"name": "Keyword", "value": f"`{keyword}`", "inline": True},
                    {"name": "Seeds", "value": str(seed_count), "inline": True},
                    {"name": "Max Results", "value": str(max_results), "inline": True},
                    {"name": "Workers", "value": str(workers), "inline": True},
                    {"name": "Depth", "value": str(crawl_depth), "inline": True},
                    {"name": "Seed Domains", "value": domains_str or "N/A", "inline": False},
                ],
            }]
        }
        return self._post_payload(payload)

    def notify_run_error(self, keyword: str, error_msg: str) -> bool:
        trimmed = error_msg[:500]
        payload = {
            "embeds": [{
                "title": "\u274c scrAPE Run Error",
                "color": 15158332,  # Red
                "fields": [
                    {"name": "Keyword", "value": f"`{keyword}`", "inline": True},
                    {"name": "Error", "value": f"```{trimmed}```", "inline": False},
                ],
            }]
        }
        return self._post_payload(payload)


class SlackNotifier(BaseNotifier):
    """Slack Webhook notification provider using Block Kit layout."""

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = (webhook_url or settings.get("SLACK_WEBHOOK_URL", "")).strip()

    def is_configured(self) -> bool:
        return bool(self.webhook_url and self.webhook_url.startswith("http"))

    def _post_payload(self, payload: dict[str, Any]) -> bool:
        if not self.is_configured():
            return False
        try:
            res = requests.post(self.webhook_url, json=payload, timeout=10)
            return res.status_code == 200
        except Exception as exc:
            LOGGER.warning("Slack webhook request failed: %s", exc)
            return False

    def notify_run_complete(
        self, keyword: str, pages: int, images: int, videos: int, duration_s: float,
        extra_text: str = "",
    ) -> bool:
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "[*] scrAPE Run Completed", "emoji": True},
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Keyword:* `{keyword}`"},
                        {"type": "mrkdwn", "text": f"*Pages:* {pages}"},
                        {"type": "mrkdwn", "text": f"*Images:* {images}"},
                        {"type": "mrkdwn", "text": f"*Videos:* {videos}"},
                        {"type": "mrkdwn", "text": f"*Duration:* {duration_s:.1f}s"},
                    ],
                },
            ]
        }
        if extra_text:
            payload["blocks"].append({"type": "section", "text": {"type": "mrkdwn", "text": extra_text[:3000]}})
        return self._post_payload(payload)

    def notify_waf_block(self, domain: str, cooldown_s: int, strategy_name: str = "") -> bool:
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {"type": "plain_text", "text": "[!] WAF Challenge Blocked Domain", "emoji": True},
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Domain:* `{domain}`"},
                        {"type": "mrkdwn", "text": f"*Cooldown:* {cooldown_s}s"},
                    ],
                },
            ]
        }
        return self._post_payload(payload)

    def notify_run_start(
        self,
        keyword: str,
        seed_count: int,
        seed_domains: list[str] | None = None,
        max_results: int = 0,
        workers: int = 0,
        page_limit: int = 0,
        crawl_depth: int = 0,
    ) -> bool:
        domains_str = ", ".join((seed_domains or [])[:6])
        payload = {
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": "\U0001f680 scrAPE Run Started", "emoji": True}},
                {"type": "section", "fields": [
                    {"type": "mrkdwn", "text": f"*Keyword:* `{keyword}`"},
                    {"type": "mrkdwn", "text": f"*Seeds:* {seed_count}"},
                    {"type": "mrkdwn", "text": f"*Max:* {max_results} | *Workers:* {workers}"},
                    {"type": "mrkdwn", "text": f"*Depth:* {crawl_depth} | *Pages:* {page_limit}"},
                ]},
            ]
        }
        return self._post_payload(payload)

    def notify_run_error(self, keyword: str, error_msg: str) -> bool:
        payload = {
            "blocks": [
                {"type": "header", "text": {"type": "plain_text", "text": "\u274c scrAPE Run Error", "emoji": True}},
                {"type": "section", "fields": [
                    {"type": "mrkdwn", "text": f"*Keyword:* `{keyword}`"},
                    {"type": "mrkdwn", "text": f"*Error:* ```{error_msg[:300]}```"},
                ]},
            ]
        }
        return self._post_payload(payload)


class CustomWebhookNotifier(BaseNotifier):
    """Generic custom webhook notification provider for Apprise, N8N, Zapier, etc."""

    def __init__(self, webhook_url: str | None = None):
        self.webhook_url = (webhook_url or settings.get("CUSTOM_WEBHOOK_URL", "")).strip()

    def is_configured(self) -> bool:
        return bool(self.webhook_url and self.webhook_url.startswith("http"))

    def _post_payload(self, event_type: str, data: dict[str, Any]) -> bool:
        if not self.is_configured():
            return False
        payload = {"event": event_type, "data": data, "app": "scrAPE"}
        try:
            res = requests.post(self.webhook_url, json=payload, timeout=10)
            return res.status_code in (200, 201, 202, 204)
        except Exception as exc:
            LOGGER.warning("Custom webhook POST failed: %s", exc)
            return False

    def notify_run_complete(
        self, keyword: str, pages: int, images: int, videos: int, duration_s: float,
        extra_text: str = "",
    ) -> bool:
        return self._post_payload(
            "run_complete",
            {"keyword": keyword, "pages": pages, "images": images, "videos": videos,
             "duration_s": duration_s, "extra_text": extra_text},
        )

    def notify_waf_block(self, domain: str, cooldown_s: int, strategy_name: str = "") -> bool:
        return self._post_payload(
            "waf_block", {"domain": domain, "cooldown_s": cooldown_s, "strategy_name": strategy_name}
        )

    def notify_run_start(
        self,
        keyword: str,
        seed_count: int,
        seed_domains: list[str] | None = None,
        max_results: int = 0,
        workers: int = 0,
        page_limit: int = 0,
        crawl_depth: int = 0,
    ) -> bool:
        return self._post_payload(
            "run_start",
            {"keyword": keyword, "seed_count": seed_count, "seed_domains": seed_domains or [],
             "max_results": max_results, "workers": workers, "page_limit": page_limit, "crawl_depth": crawl_depth},
        )

    def notify_run_error(self, keyword: str, error_msg: str) -> bool:
        return self._post_payload("run_error", {"keyword": keyword, "error": error_msg[:500]})


class NotificationPipeline:
    """Central registry and parallel dispatcher for all configured notification providers."""

    def __init__(self, providers: list[BaseNotifier] | None = None):
        self.providers: list[BaseNotifier] = providers if providers is not None else []
        if not self.providers:
            self._auto_discover_providers()

    def _auto_discover_providers(self) -> None:
        """Instantiate default providers from environment / configuration."""
        tg = TelegramNotifier()
        if tg.is_configured():
            self.providers.append(tg)

        dc = DiscordNotifier()
        if dc.is_configured():
            self.providers.append(dc)

        sl = SlackNotifier()
        if sl.is_configured():
            self.providers.append(sl)

        cw = CustomWebhookNotifier()
        if cw.is_configured():
            self.providers.append(cw)

    def register_provider(self, provider: BaseNotifier) -> None:
        """Dynamically register any custom notification provider instance."""
        if provider not in self.providers:
            self.providers.append(provider)

    def _dispatch_parallel(self, fn_name: str, *args: Any, **kwargs: Any) -> dict[str, bool]:
        """Dispatch notification function across all active providers concurrently."""
        active = [p for p in self.providers if p.is_configured()]
        if not active:
            return {}

        results: dict[str, bool] = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(active), 8)) as executor:
            future_to_provider = {
                executor.submit(getattr(p, fn_name), *args, **kwargs): p.__class__.__name__
                for p in active
            }
            for future in concurrent.futures.as_completed(future_to_provider):
                p_name = future_to_provider[future]
                try:
                    results[p_name] = bool(future.result())
                except Exception as exc:
                    LOGGER.warning("Provider %s failed dispatch: %s", p_name, exc)
                    results[p_name] = False

        return results

    def notify_run_complete(
        self, keyword: str, pages: int, images: int, videos: int, duration_s: float,
        extra_text: str = "",
    ) -> dict[str, bool]:
        return self._dispatch_parallel(
            "notify_run_complete", keyword, pages, images, videos, duration_s, extra_text
        )

    def notify_waf_block(self, domain: str, cooldown_s: int, strategy_name: str = "") -> dict[str, bool]:
        return self._dispatch_parallel("notify_waf_block", domain, cooldown_s, strategy_name)

    def notify_media_harvest(
        self, keyword: str, count: int, sample_urls: list[str] | None = None
    ) -> dict[str, bool]:
        return self._dispatch_parallel("notify_media_harvest", keyword, count, sample_urls)

    def notify_watchdog_status(self, message: str, status_level: str = "INFO") -> dict[str, bool]:
        return self._dispatch_parallel("notify_watchdog_status", message, status_level)

    def notify_run_start(
        self,
        keyword: str,
        seed_count: int,
        seed_domains: list[str] | None = None,
        max_results: int = 0,
        workers: int = 0,
        page_limit: int = 0,
        crawl_depth: int = 0,
    ) -> dict[str, bool]:
        return self._dispatch_parallel(
            "notify_run_start", keyword, seed_count, seed_domains, max_results, workers, page_limit, crawl_depth
        )

    def notify_run_error(self, keyword: str, error_msg: str) -> dict[str, bool]:
        return self._dispatch_parallel("notify_run_error", keyword, error_msg)
