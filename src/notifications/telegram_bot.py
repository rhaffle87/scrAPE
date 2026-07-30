from __future__ import annotations

import logging
import threading
import time
from typing import Any
import requests

LOGGER = logging.getLogger(__name__)


class TelegramBotNotifier:
    """Telegram Bot Notifier for pushing alerts and stats notifications."""

    def __init__(self, token: str | None = None, chat_id: str | None = None):
        self.token = (token or "").strip()
        self.chat_id = (chat_id or "").strip()
        self.api_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""

    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send a message to the configured Telegram chat."""
        if not self.is_configured():
            LOGGER.debug("Telegram bot is not fully configured.")
            return False

        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }

        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                LOGGER.info("Telegram message sent successfully.")
                return True
            LOGGER.warning("Telegram sendMessage returned HTTP %d: %s", res.status_code, res.text)
        except Exception as exc:
            LOGGER.warning("Failed to send Telegram message: %s", exc)

        return False

    def notify_run_complete(self, keyword: str, pages: int, images: int, videos: int, duration_s: float) -> bool:
        """Send HTML-formatted notification when a scraping run completes."""
        text = (
            f"<b>scrAPE Run Completed</b>\n\n"
            f"<b>Keyword:</b> <code>{keyword}</code>\n"
            f"<b>Pages Scanned:</b> {pages}\n"
            f"<b>Images Fetched:</b> {images}\n"
            f"<b>Videos Fetched:</b> {videos}\n"
            f"<b>Duration:</b> {duration_s:.1f}s"
        )
        return self.send_message(text)

    def notify_waf_block(self, domain: str, cooldown_s: int) -> bool:
        """Send WAF block alert notification."""
        text = (
            f"<b>WAF Block Triggered</b>\n\n"
            f"<b>Domain:</b> <code>{domain}</code>\n"
            f"<b>Cooldown Active:</b> {cooldown_s}s\n"
            f"<i>Automated fallback sequence initiated.</i>"
        )
        return self.send_message(text)


class TelegramCommandHandler:
    """Daemon thread handler polling Telegram updates and executing interactive commands."""

    def __init__(self, notifier: TelegramBotNotifier, task_state_ref: dict[str, Any] | None = None):
        self.notifier = notifier
        self.task_state = task_state_ref or {}
        self._running = False
        self._thread: threading.Thread | None = None
        self._last_update_id = 0

    def start(self) -> None:
        """Start command polling thread."""
        if not self.notifier.is_configured():
            return
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop command polling thread."""
        self._running = False

    def _poll_loop(self) -> None:
        url = f"{self.notifier.api_url}/getUpdates"
        while self._running:
            try:
                params = {"offset": self._last_update_id + 1, "timeout": 5}
                res = requests.get(url, params=params, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    if data.get("ok"):
                        for update in data.get("result", []):
                            self._last_update_id = max(self._last_update_id, update.get("update_id", 0))
                            msg = update.get("message", {})
                            text = (msg.get("text") or "").strip()
                            if text.startswith("/"):
                                self._handle_command(text)
            except Exception as exc:
                LOGGER.debug("Telegram poll error: %s", exc)
            time.sleep(2)

    def _handle_command(self, cmd: str) -> None:
        cmd_name = cmd.split()[0].lower()
        if cmd_name in {"/status", "/status@bot"}:
            status = self.task_state.get("status", "idle").upper()
            kw = self.task_state.get("keyword", "N/A")
            self.notifier.send_message(f"<b>scrAPE Status:</b> <code>{status}</code>\n<b>Active Keyword:</b> <code>{kw}</code>")
        elif cmd_name in {"/stats", "/stats@bot"}:
            pages = self.task_state.get("pages_scanned", 0)
            img = self.task_state.get("images_found", 0)
            vid = self.task_state.get("videos_found", 0)
            self.notifier.send_message(f"<b>Current Stats:</b>\nPages: {pages}\nImages: {img}\nVideos: {vid}")
        elif cmd_name in {"/pause", "/pause@bot"}:
            self.task_state["status"] = "paused"
            self.notifier.send_message("<b>scrAPE Task Paused</b>")
        elif cmd_name in {"/resume", "/resume@bot"}:
            self.task_state["status"] = "running"
            self.notifier.send_message("<b>scrAPE Task Resumed</b>")
