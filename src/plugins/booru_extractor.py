import logging
import urllib.parse
from plugins.base import ExtractorPlugin, SpecializedResult

LOGGER = logging.getLogger(__name__)


class BooruExtractor(ExtractorPlugin):
    """Extracts original image URLs and tags from Danbooru and Gelbooru image boards."""

    def can_handle(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
        return host in ["danbooru.donmai.us", "gelbooru.com", "safebooru.org"]

    def extract(self, url: str) -> SpecializedResult:
        import httpx

        images = []
        videos = []
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower().replace("www.", "")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/json",
        }

        try:
            with httpx.Client(timeout=15.0, headers=headers) as client:
                # Danbooru: https://danbooru.donmai.us/posts/<id> or /posts.json
                if host == "danbooru.donmai.us":
                    path_parts = [p for p in parsed.path.split("/") if p]
                    if len(path_parts) >= 2 and path_parts[0] == "posts" and path_parts[1].isdigit():
                        post_id = path_parts[1]
                        api_url = f"https://danbooru.donmai.us/posts/{post_id}.json"
                    else:
                        api_url = f"https://danbooru.donmai.us/posts.json?limit=20"

                    res = client.get(api_url)
                    if res.status_code == 200:
                        data = res.json()
                        items = [data] if isinstance(data, dict) else data
                        for item in items:
                            file_url = item.get("file_url") or item.get("large_file_url")
                            if file_url:
                                if file_url.endswith((".mp4", ".webm")):
                                    videos.append(file_url)
                                else:
                                    images.append(file_url)

                # Gelbooru / Safebooru JSON API
                elif host in ["gelbooru.com", "safebooru.org"]:
                    qs = urllib.parse.parse_qs(parsed.query)
                    post_id = qs.get("id", [None])[0]
                    if post_id:
                        api_url = f"https://{host}/index.php?page=dapi&s=post&q=index&id={post_id}&json=1"
                    else:
                        api_url = f"https://{host}/index.php?page=dapi&s=post&q=index&json=1&limit=20"

                    res = client.get(api_url)
                    if res.status_code == 200:
                        data = res.json()
                        posts = data.get("post", []) if isinstance(data, dict) else data
                        for p in posts:
                            file_url = p.get("file_url")
                            if file_url:
                                if file_url.endswith((".mp4", ".webm")):
                                    videos.append(file_url)
                                else:
                                    images.append(file_url)

        except Exception as exc:
            LOGGER.warning("Booru API extraction failed for %s: %s", url, exc)

        return SpecializedResult(images=images, videos=videos)
