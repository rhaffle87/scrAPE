import logging
import urllib.parse
import re
try:
    from plugins.base import ExtractorPlugin, SpecializedResult
except ImportError:
    from src.plugins.base import ExtractorPlugin, SpecializedResult

LOGGER = logging.getLogger(__name__)

class TelegramExtractor(ExtractorPlugin):
    """Extracts media from public Telegram channel posts (t.me/s/channel/id)."""

    def can_handle(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host in ["t.me", "telegram.me"]

    def extract(self, url: str) -> SpecializedResult:
        images = []
        videos = []

        # Convert t.me/channel/id to web preview t.me/s/channel/id
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        if not path.startswith("/s/"):
            web_url = f"https://t.me/s{path}"
        else:
            web_url = url

        try:
            import requests
            from bs4 import BeautifulSoup

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }
            resp = requests.get(web_url, headers=headers, timeout=10.0)
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "lxml")

            # Extract photo wraps
            for wrap in soup.select(".tgme_widget_message_photo_wrap"):
                style = wrap.get("style", "")
                bg_match = re.search(r"background-image:url\(['\"]?(.*?)['\"]?\)", style)
                if bg_match:
                    images.append(bg_match.group(1))

            # Extract video wraps
            for vid in soup.select("video.tgme_widget_message_video, video"):
                src = vid.get("src")
                if src:
                    videos.append(src)

        except Exception as exc:
            LOGGER.debug("Telegram extraction failed for %s: %s", url, exc)

        return SpecializedResult(
            images=list(dict.fromkeys(images)),
            videos=list(dict.fromkeys(videos)),
        )
