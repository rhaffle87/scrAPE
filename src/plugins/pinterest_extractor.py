import json
import logging
import re
import urllib.parse
from plugins.base import ExtractorPlugin, SpecializedResult

LOGGER = logging.getLogger(__name__)


class PinterestExtractor(ExtractorPlugin):
    """Extracts original resolution images from Pinterest pins and boards."""

    def can_handle(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host in ["pinterest.com", "pinterest.co.uk", "pinimg.com", "i.pinimg.com"]

    def extract(self, url: str) -> SpecializedResult:
        import httpx

        images = []
        videos = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

        try:
            with httpx.Client(timeout=15.0, headers=headers, follow_redirects=True) as client:
                res = client.get(url)
                if res.status_code == 200:
                    html = res.text

                    # 1. Look for original resolution pinimg URLs in script tags or HTML
                    matches = re.findall(
                        r"https://i\.pinimg\.com/(?:originals|\d+x)/[a-f0-9/]+\.(?:jpg|png|gif|jpeg|webp)",
                        html,
                        re.IGNORECASE,
                    )
                    for m in matches:
                        # Convert to original full-resolution URL
                        orig_url = re.sub(r"https://i\.pinimg\.com/\d+x/", "https://i.pinimg.com/originals/", m)
                        if orig_url not in images:
                            images.append(orig_url)

                    # 2. Extract video URLs (.mp4)
                    vid_matches = re.findall(
                        r"https://v1\.pinimg\.com/videos/[^\s\"'<>]+\.mp4",
                        html,
                        re.IGNORECASE,
                    )
                    for vm in vid_matches:
                        if vm not in videos:
                            videos.append(vm)

        except Exception as exc:
            LOGGER.warning("Pinterest extraction failed for %s: %s", url, exc)

        return SpecializedResult(images=images, videos=videos)
