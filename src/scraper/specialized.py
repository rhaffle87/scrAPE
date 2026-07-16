import logging
import urllib.parse
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)


@dataclass
class SpecializedResult:
    images: list[str]
    videos: list[str]


class SpecializedExtractor:
    """Handles deep extraction for platforms that block or complicate traditional DOM scraping."""

    @staticmethod
    def is_supported(url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]

        return host in ["youtube.com", "youtu.be", "tiktok.com", "reddit.com"]

    @staticmethod
    def extract(url: str) -> SpecializedResult:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]

        if host in ["youtube.com", "youtu.be", "tiktok.com"]:
            return SpecializedExtractor._extract_via_ytdlp(url)
        elif host == "reddit.com":
            return SpecializedExtractor._extract_reddit(url)

        return SpecializedResult([], [])

    @staticmethod
    def _extract_via_ytdlp(url: str) -> SpecializedResult:
        """Use yt-dlp to extract the raw video URL without downloading."""
        try:
            import yt_dlp
        except ImportError:
            LOGGER.warning(
                "yt-dlp is not installed. Skipping specialized extraction for %s", url
            )
            return SpecializedResult([], [])

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
            "dumpjson": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return SpecializedResult([], [])

                # yt-dlp usually populates 'url' for the direct stream link
                # Sometimes it returns a playlist, we only handle single videos for now.
                videos = []
                if "entries" in info:
                    for entry in info["entries"]:
                        if entry and "url" in entry:
                            videos.append(entry["url"])
                elif "url" in info:
                    videos.append(info["url"])

                return SpecializedResult(images=[], videos=videos)
        except Exception as e:
            LOGGER.error("yt-dlp failed to extract info for %s: %s", url, e)
            return SpecializedResult([], [])

    @staticmethod
    def _extract_reddit(url: str) -> SpecializedResult:
        """Extract media from Reddit posts via their JSON representation."""
        import requests

        # Append .json to the URL if it's a reddit post
        json_url = url
        if "?" in json_url:
            base, qs = json_url.split("?", 1)
            if not base.endswith(".json"):
                json_url = f"{base}.json?{qs}"
        else:
            if not json_url.endswith(".json"):
                json_url = f"{json_url}.json"

        try:
            resp = requests.get(
                json_url, headers={"User-Agent": "Mozilla/5.0 scrAPE/1.0"}
            )
            resp.raise_for_status()
            data = resp.json()

            images = []
            videos = []

            if isinstance(data, list) and len(data) > 0:
                post_data = data[0]["data"]["children"][0]["data"]

                # Check for direct URL
                if "url" in post_data:
                    url_val = post_data["url"]
                    if url_val.endswith((".jpg", ".png", ".gif", ".jpeg")):
                        images.append(url_val)
                    elif url_val.endswith((".mp4", ".gifv")):
                        videos.append(url_val)

                # Check for Reddit hosted video
                if (
                    "secure_media" in post_data
                    and post_data["secure_media"]
                    and "reddit_video" in post_data["secure_media"]
                ):
                    videos.append(
                        post_data["secure_media"]["reddit_video"]["fallback_url"]
                    )

                # Check for gallery
                if "media_metadata" in post_data:
                    for media_id, media_item in post_data["media_metadata"].items():
                        if (
                            media_item.get("status") == "valid"
                            and "s" in media_item
                            and "u" in media_item["s"]
                        ):
                            # u has &amp; which needs to be replaced
                            images.append(media_item["s"]["u"].replace("&amp;", "&"))

            return SpecializedResult(images=images, videos=videos)
        except Exception as e:
            LOGGER.warning("Reddit API extraction failed for %s: %s", url, e)
            return SpecializedResult([], [])
