import logging
import urllib.parse
import re
from plugins.base import ExtractorPlugin, SpecializedResult

LOGGER = logging.getLogger(__name__)

class InstagramExtractor(ExtractorPlugin):
    """Extracts media from Instagram posts, reels, and IGTV videos."""

    def can_handle(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        if host not in ["instagram.com", "instagr.am"]:
            return False
        path = parsed.path.lower()
        return any(p in path for p in ["/p/", "/reel/", "/reels/", "/tv/"])

    def extract(self, url: str) -> SpecializedResult:
        images = []
        videos = []

        # 1. Attempt API JSON endpoints (?__a=1&__d=dis)
        try:
            import requests
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
            }
            api_url = url.split("?")[0].rstrip("/") + "/?__a=1&__d=dis"
            resp = requests.get(api_url, headers=headers, timeout=10.0)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("graphql", {}).get("shortcode_media", {}) or data.get("items", [{}])[0]
                if items:
                    # Single video / Reel
                    if items.get("is_video") and items.get("video_url"):
                        videos.append(items["video_url"])
                    elif items.get("display_url"):
                        images.append(items["display_url"])

                    # Carousel items
                    sidecar = items.get("edge_sidecar_to_children", {}).get("edges", [])
                    for edge in sidecar:
                        node = edge.get("node", {})
                        if node.get("is_video") and node.get("video_url"):
                            videos.append(node["video_url"])
                        elif node.get("display_url"):
                            images.append(node["display_url"])
        except Exception as exc:
            LOGGER.debug("Instagram API JSON extraction failed for %s: %s", url, exc)

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
                        for entry in info.get("entries", []):
                            if entry.get("url"):
                                if entry.get("ext") in ["mp4", "webm", "mkv"]:
                                    videos.append(entry["url"])
                                else:
                                    images.append(entry["url"])
            except Exception as ytdlp_exc:
                LOGGER.debug("Instagram yt-dlp fallback failed for %s: %s", url, ytdlp_exc)

        return SpecializedResult(images=list(dict.fromkeys(images)), videos=list(dict.fromkeys(videos)))
