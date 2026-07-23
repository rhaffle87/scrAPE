import logging
import urllib.parse
from plugins.base import ExtractorPlugin, SpecializedResult

LOGGER = logging.getLogger(__name__)


class ArtStationExtractor(ExtractorPlugin):
    """Extracts original resolution artwork assets from ArtStation artwork pages."""

    def can_handle(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host == "artstation.com"

    def extract(self, url: str) -> SpecializedResult:
        import httpx

        images = []
        videos = []
        parsed = urllib.parse.urlparse(url)
        path_parts = [p for p in parsed.path.split("/") if p]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

        try:
            # ArtStation artwork URL: artstation.com/artwork/<hash_id>
            if len(path_parts) >= 2 and path_parts[0] == "artwork":
                hash_id = path_parts[1]
                api_url = f"https://www.artstation.com/projects/{hash_id}.json"

                with httpx.Client(timeout=15.0, headers=headers) as client:
                    res = client.get(api_url)
                    if res.status_code == 200:
                        data = res.json()
                        assets = data.get("assets", [])
                        for asset in assets:
                            asset_type = asset.get("asset_type")
                            image_url = asset.get("image_url")
                            if image_url:
                                if asset_type == "video" or image_url.endswith(".mp4"):
                                    videos.append(image_url)
                                else:
                                    images.append(image_url)

        except Exception as exc:
            LOGGER.warning("ArtStation API extraction failed for %s: %s", url, exc)

        return SpecializedResult(images=images, videos=videos)
