import logging
import os
import random
import threading
import time
from typing import Any
import requests

from common.blacklist import add_to_blacklist

LOGGER = logging.getLogger(__name__)


class TelegramBotNotifier:
    """Telegram Bot Notifier for pushing alerts, stats, and media previews."""

    def __init__(self, token: str | None = None, chat_id: str | None = None):
        self.token = (token or "").strip()
        self.chat_id = (chat_id or "").strip()
        self.api_url = f"https://api.telegram.org/bot{self.token}" if self.token else ""

    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send_message(self, text: str, parse_mode: str = "HTML", reply_markup: dict[str, Any] | None = None) -> bool:
        """Send a message to the configured Telegram chat, optionally with an inline keyboard."""
        if not self.is_configured():
            LOGGER.debug("Telegram bot is not fully configured.")
            return False

        url = f"{self.api_url}/sendMessage"
        payload: dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                LOGGER.info("Telegram message sent successfully.")
                return True
            LOGGER.warning("Telegram sendMessage returned HTTP %d: %s", res.status_code, res.text)
        except Exception as exc:
            LOGGER.warning("Failed to send Telegram message: %s", exc)

        return False

    def send_photo(self, photo_path: str, caption: str = "") -> bool:
        """Send a local photo file to the configured Telegram chat."""
        if not self.is_configured() or not os.path.isfile(photo_path):
            return False

        url = f"{self.api_url}/sendPhoto"
        try:
            with open(photo_path, "rb") as img_file:
                files = {"photo": img_file}
                data = {"chat_id": self.chat_id, "caption": caption[:1024], "parse_mode": "HTML"}
                res = requests.post(url, data=data, files=files, timeout=20)
                return res.status_code == 200
        except Exception as exc:
            LOGGER.warning("Failed to send Telegram photo: %s", exc)
            return False

    def answer_callback_query(self, callback_query_id: str, text: str = "") -> bool:
        """Answer an inline button callback query."""
        if not self.is_configured():
            return False
        url = f"{self.api_url}/answerCallbackQuery"
        try:
            requests.post(url, json={"callback_query_id": callback_query_id, "text": text}, timeout=5)
            return True
        except Exception:
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
        self.task_state = task_state_ref if task_state_ref is not None else {}
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
                            
                            # Handle Callback Queries (Inline Keyboards)
                            if "callback_query" in update:
                                self._handle_callback_query(update["callback_query"])
                                continue
                            
                            # Handle Text Commands
                            msg = update.get("message", {})
                            text = (msg.get("text") or "").strip()
                            if text.startswith("/"):
                                self._handle_command(text)
            except Exception as exc:
                LOGGER.debug("Telegram poll error: %s", exc)
                time.sleep(2)

    def _handle_callback_query(self, cb: dict[str, Any]) -> None:
        cb_id = cb.get("id", "")
        data = cb.get("data", "")
        if data == "confirm_stop":
            self.task_state["stop_requested"] = True
            self.notifier.answer_callback_query(cb_id, "Stop request confirmed")
            self.notifier.send_message("<b>🛑 Graceful Stop Triggered</b>\nEngine will finish active downloads and halt.")
        elif data == "confirm_abort":
            self.task_state["abort_requested"] = True
            self.notifier.answer_callback_query(cb_id, "Abort request confirmed")
            self.notifier.send_message("<b>💥 Hard Abort Triggered</b>\nExecution terminating immediately.")
        elif data == "cancel_action":
            self.notifier.answer_callback_query(cb_id, "Action cancelled")
            self.notifier.send_message("<i>Action cancelled.</i>")

    def _handle_command(self, cmd: str) -> None:
        parts = cmd.split(maxsplit=1)
        cmd_name = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""

        if cmd_name in {"/status", "/status@bot"}:
            status = self.task_state.get("status", "idle").upper()
            kw = self.task_state.get("keyword", "N/A")
            wd = "ACTIVE" if self.task_state.get("watchdog_active") else "INACTIVE"
            self.notifier.send_message(
                f"<b>scrAPE Status:</b> <code>{status}</code>\n"
                f"<b>Active Keyword:</b> <code>{kw}</code>\n"
                f"<b>Watchdog Agent:</b> <code>{wd}</code>"
            )

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

        elif cmd_name in {"/stop", "/stop@bot"}:
            keyboard = {
                "inline_keyboard": [[
                    {"text": "✅ Confirm Stop", "callback_data": "confirm_stop"},
                    {"text": "❌ Cancel", "callback_data": "cancel_action"},
                ]]
            }
            self.notifier.send_message(
                "<b>⚠️ Confirm Graceful Stop?</b>\nThis will finish active downloads and save results.",
                reply_markup=keyboard,
            )

        elif cmd_name in {"/abort", "/abort@bot"}:
            keyboard = {
                "inline_keyboard": [[
                    {"text": "✅ Confirm Hard Abort", "callback_data": "confirm_abort"},
                    {"text": "❌ Cancel", "callback_data": "cancel_action"},
                ]]
            }
            self.notifier.send_message(
                "<b>💥 Confirm Hard Abort?</b>\nThis will terminate the scraper immediately without saving state.",
                reply_markup=keyboard,
            )

        elif cmd_name in {"/blacklist", "/blacklist@bot"}:
            if not args:
                self.notifier.send_message("<b>Usage:</b> <code>/blacklist domain.com</code>")
                return
            domain = args.lower().strip()
            add_to_blacklist(domain, reason="telegram_bot")
            self.task_state.setdefault("blacklisted_domains", []).append(domain)
            self.notifier.send_message(f"<b>🚫 Blacklisted Domain:</b> <code>{domain}</code>")

        elif cmd_name in {"/setlimit", "/setlimit@bot"}:
            if not args.isdigit():
                self.notifier.send_message("<b>Usage:</b> <code>/setlimit 500</code>")
                return
            new_limit = int(args)
            self.task_state["max_results_override"] = new_limit
            self.notifier.send_message(f"<b>🎯 Max Results Updated:</b> <code>{new_limit}</code>")

        elif cmd_name in {"/report", "/report@bot"}:
            report = self.task_state.get("domain_report", {})
            if not report:
                self.notifier.send_message("<i>No domain report available yet.</i>")
                return
            lines = ["<b>📊 Domain Yield Report:</b>\n"]
            for dom, stats in report.items():
                p = stats.get("pages", 0)
                i = stats.get("images", 0)
                v = stats.get("videos", 0)
                lines.append(f"• <code>{dom}</code>: {p} pages | {i} img | {v} vid")
            self.notifier.send_message("\n".join(lines))

        elif cmd_name in {"/preview", "/preview@bot"}:
            recent = self.task_state.get("latest_media", [])
            output_dir = self.task_state.get("output_dir", "output")
            sample_file = None

            if recent and os.path.exists(recent[-1]):
                sample_file = recent[-1]
            elif os.path.exists(output_dir):
                for root, _, files in os.walk(output_dir):
                    imgs = [os.path.join(root, f) for f in files if f.lower().endswith((".jpg", ".png", ".webp"))]
                    if imgs:
                        sample_file = random.choice(imgs)
                        break

            if sample_file:
                filename = os.path.basename(sample_file)
                self.notifier.send_photo(sample_file, caption=f"📸 <b>Preview:</b> <code>{filename}</code>")
            else:
                self.notifier.send_message("<i>No local preview images found.</i>")

        elif cmd_name in {"/watchdog", "/watchdog@bot"}:
            current = self.task_state.get("watchdog_active", False)
            new_state = not current
            self.task_state["watchdog_active"] = new_state
            state_str = "ENABLED" if new_state else "DISABLED"
            self.notifier.send_message(f"<b>🐕 Watchdog Continuous Agent:</b> <code>{state_str}</code>")

        elif cmd_name in {"/help", "/help@bot"}:
            help_text = (
                "<b>🤖 scrAPE Bot Commands:</b>\n\n"
                "/status - View current run status\n"
                "/stats - View current pages & media counts\n"
                "/report - Detailed per-domain yield breakdown\n"
                "/preview - View a sample harvested image\n"
                "/pause - Pause crawl execution\n"
                "/resume - Resume crawl execution\n"
                "/stop - Graceful stop with confirmation\n"
                "/abort - Hard kill scraper process\n"
                "/blacklist domain.com - Add domain to blacklist mid-run\n"
                "/setlimit N - Update target max results on-the-fly\n"
                "/watchdog - Toggle continuous watchdog monitoring\n"
                "/help - Show this message"
            )
            self.notifier.send_message(help_text)

