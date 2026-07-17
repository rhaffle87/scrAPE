import logging
import urllib.parse
from plugins.base import ExtractorPlugin, SpecializedResult

LOGGER = logging.getLogger(__name__)

class RedditExtractor(ExtractorPlugin):
    """Extracts media from Reddit posts via their JSON API."""
    
    def can_handle(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host == "reddit.com"

    def extract(self, url: str) -> SpecializedResult:
        import requests

        json_url = url
        if "?" in json_url:
            base, qs = json_url.split("?", 1)
            if not base.endswith(".json"):
                json_url = f"{base}.json?{qs}"
        else:
            if not json_url.endswith(".json"):
                json_url = f"{json_url}.json"

        try:
            resp = requests.get(json_url, headers={"User-Agent": "Mozilla/5.0 scrAPE/1.0"})
            resp.raise_for_status()
            data = resp.json()

            images = []
            videos = []

            if isinstance(data, list) and len(data) > 0:
                post_data = data[0]["data"]["children"][0]["data"]

                if "url" in post_data:
                    url_val = post_data["url"]
                    if url_val.endswith((".jpg", ".png", ".gif", ".jpeg")):
                        images.append(url_val)
                    elif url_val.endswith((".mp4", ".gifv")):
                        videos.append(url_val)

                if (
                    "secure_media" in post_data
                    and post_data["secure_media"]
                    and "reddit_video" in post_data["secure_media"]
                ):
                    videos.append(post_data["secure_media"]["reddit_video"]["fallback_url"])

                if "media_metadata" in post_data:
                    for media_id, media_item in post_data["media_metadata"].items():
                        if (
                            media_item.get("status") == "valid"
                            and "s" in media_item
                            and "u" in media_item["s"]
                        ):
                            images.append(media_item["s"]["u"].replace("&amp;", "&"))

            return SpecializedResult(images=images, videos=videos)
        except Exception as e:
            LOGGER.warning("Reddit API extraction failed for %s: %s", url, e)
            return SpecializedResult([], [])
