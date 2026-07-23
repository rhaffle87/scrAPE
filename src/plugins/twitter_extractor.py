import logging
import urllib.parse
import re
from plugins.base import ExtractorPlugin, SpecializedResult

LOGGER = logging.getLogger(__name__)

class TwitterExtractor(ExtractorPlugin):
    """Extracts media from Twitter / X posts via vxtwitter API and yt-dlp."""

    def can_handle(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        if host not in ["twitter.com", "x.com", "vxtwitter.com", "fxtwitter.com"]:
            return False
        path = parsed.path.lower()
        return "/status/" in path

    def extract(self, url: str) -> SpecializedResult:
        images = []
        videos = []

        parsed = urllib.parse.urlparse(url)
        status_match = re.search(r"/status/(\d+)", parsed.path)
        status_id = status_match.group(1) if status_match else None

        # 1. Attempt vxtwitter API JSON fallback
        if status_id:
            try:
                import requests
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json",
                }
                api_url = f"https://api.vxtwitter.com/Twitter/status/{status_id}"
                resp = requests.get(api_url, headers=headers, timeout=10.0)
                if resp.status_code == 200:
                    data = resp.json()
                    media_list = data.get("media_extended", []) or data.get("mediaURLs", [])
                    for item in media_list:
                        if isinstance(item, dict):
                            kind = item.get("type")
                            if kind == "video":
                                # Select highest bitrate video variant
                                variants = item.get("variants", []) or []
                                best_variant = None
                                max_bitrate = -1
                                for var in variants:
                                    if var.get("url"):
                                        bitrate = var.get("bitrate", 0) or 0
                                        if bitrate > max_bitrate:
                                            max_bitrate = bitrate
                                            best_variant = var.get("url")
                                if best_variant:
                                    videos.append(best_variant)
                                elif item.get("url"):
                                    videos.append(item["url"])
                            else:
                                media_url = item.get("url") or item.get("thumbnail_url")
                                if media_url:
                                    images.append(media_url)
                        elif isinstance(item, str):
                            if item.endswith((".mp4", ".m3u8")):
                                videos.append(item)
                            else:
                                images.append(item)
            except Exception as exc:
                LOGGER.debug("Twitter vxtwitter API extraction failed for %s: %s", url, exc)

        # 2. Fallback to yt-dlp metadata extraction
        if not images and not videos:
            try:
                import yt_dlp
                ydl_opts = {
                    "quiet": True,
                    "no_warnings": True,
                    "extract_flat": False,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if info:
                        if info.get("url"):
                            if info.get("ext") in ["mp4", "webm", "mkv"]:
                                videos.append(info["url"])
                            else:
                                images.append(info["url"])
                        else:
                            # Pick highest quality format URL
                            formats = info.get("formats") or []
                            best_f = None
                            max_tbr = -1
                            for f in formats:
                                f_url = f.get("url")
                                tbr = f.get("tbr") or f.get("vbr") or 0
                                if f_url and (f.get("ext") == "mp4" or f_url.endswith(".mp4")):
                                    if tbr > max_tbr:
                                        max_tbr = tbr
                                        best_f = f_url
                            if best_f:
                                videos.append(best_f)
            except Exception as ytdlp_exc:
                LOGGER.debug("Twitter yt-dlp fallback failed for %s: %s", url, ytdlp_exc)

        # Ensure high-res Twitter image transformation (name=orig / name=large)
        transformed_images = []
        for img in images:
            if "name=small" in img or "name=medium" in img:
                img = img.replace("name=small", "name=large").replace("name=medium", "name=large")
            elif "format=" in img and "name=" not in img:
                img = f"{img}&name=large"
            transformed_images.append(img)

        return SpecializedResult(
            images=list(dict.fromkeys(transformed_images)),
            videos=list(dict.fromkeys(videos)),
        )
