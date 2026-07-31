import logging
import urllib.parse
from typing import Any
from typing import TYPE_CHECKING, Optional
from plugins.base import ExtractorPlugin, SpecializedResult

if TYPE_CHECKING:
    from network.http_client import HttpClient

LOGGER = logging.getLogger(__name__)


class CivitaiExtractor(ExtractorPlugin):
    """Extracts high-resolution images and prompt/model metadata from Civitai."""

    def can_handle(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host == "civitai.com"

    def extract(self, url: str, http_client: Optional['HttpClient'] = None) -> SpecializedResult:
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
            def _fetch(api_url: str):
                if http_client:
                    return http_client.get(api_url, headers=headers, timeout=15.0)
                else:
                    with httpx.Client(timeout=15.0, headers=headers) as client:
                        return client.get(api_url)

            # 1. Direct Image Page: civitai.com/images/<id>
            if len(path_parts) >= 2 and path_parts[0] == "images":
                image_id = path_parts[1]
                api_url = f"https://civitai.com/api/v1/images?imageId={image_id}"
                res = _fetch(api_url)
                if res.status_code == 200:
                    data = res.json()
                    items = data.get("items", [])
                    for item in items:
                        img_url = item.get("url")
                        if img_url:
                            images.append(img_url)

            # 2. Model Page: civitai.com/models/<id>
            elif len(path_parts) >= 2 and path_parts[0] == "models":
                model_id = path_parts[1]
                api_url = f"https://civitai.com/api/v1/models/{model_id}"
                res = _fetch(api_url)
                if res.status_code == 200:
                    data = res.json()
                    for version in data.get("modelVersions", []):
                        for img in version.get("images", []):
                            img_url = img.get("url")
                            if img_url:
                                images.append(img_url)

            # Fallback: civitai images search API
            if not images:
                api_url = f"https://civitai.com/api/v1/images?limit=20"
                res = _fetch(api_url)
                if res.status_code == 200:
                    data = res.json()
                    for item in data.get("items", []):
                        img_url = item.get("url")
                        if img_url:
                            images.append(img_url)

        except Exception as exc:
            LOGGER.warning("Civitai API extraction failed for %s: %s", url, exc)

        return SpecializedResult(images=images, videos=videos)
