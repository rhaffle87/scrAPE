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

    def notify_run_complete(
        self, keyword: str, pages: int, images: int, videos: int, duration_s: float,
        extra_text: str = "",
    ) -> bool:
        """Send HTML-formatted notification when a scraping run completes."""
        mins, secs = divmod(int(duration_s), 60)
        dur_str = f"{mins}m {secs}s" if mins else f"{secs}s"
        text = (
            f"\u2705 <b>scrAPE Run Complete</b>\n\n"
            f"<b>Keyword:</b> <code>{keyword}</code>\n"
            f"<b>Duration:</b> {dur_str}\n"
            f"<b>Pages:</b> {pages} | \U0001f5bc Images: {images} | \U0001f3ac Videos: {videos}"
        )
        if extra_text:
            text += f"\n\n{extra_text}"
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
        """Send run-start notification with configuration summary."""
        domain_line = ""
        if seed_domains:
            shown = seed_domains[:6]
            extra = len(seed_domains) - len(shown)
            names = ", ".join(f"<code>{d}</code>" for d in shown)
            domain_line = f"\n<b>Seeds:</b> {names}" + (f" +{extra} more" if extra else "")
        text = (
            f"\U0001f680 <b>scrAPE Run Started</b>\n\n"
            f"<b>Keyword:</b> <code>{keyword}</code>\n"
            f"<b>Seed URLs:</b> {seed_count}{domain_line}\n"
            f"<b>Max Results:</b> {max_results} | <b>Workers:</b> {workers}\n"
            f"<b>Depth:</b> {crawl_depth} | <b>Page Limit:</b> {page_limit}"
        )
        return self.send_message(text)

    def notify_run_error(self, keyword: str, error_msg: str) -> bool:
        """Send error alert when a run crashes with an unhandled exception."""
        # Trim very long tracebacks
        trimmed = error_msg[:400] + "\u2026" if len(error_msg) > 400 else error_msg
        text = (
            f"\u274c <b>scrAPE Run Error</b>\n\n"
            f"<b>Keyword:</b> <code>{keyword}</code>\n"
            f"<b>Error:</b> <pre>{trimmed}</pre>"
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
