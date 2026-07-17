import logging
import urllib.parse
from plugins.base import ExtractorPlugin, SpecializedResult

LOGGER = logging.getLogger(__name__)

class YtDlpExtractor(ExtractorPlugin):
    """Uses yt-dlp to extract raw video URLs from video platforms."""
    
    def can_handle(self, url: str) -> bool:
        parsed = urllib.parse.urlparse(url)
        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]
            
        path = parsed.path.lower()
        
        if host == "youtube.com":
            # Ignore generic non-video paths
            ignored_paths = ["", "/", "/ads/", "/about/", "/creators/", "/t/terms", "/t/privacy", "/t/contact_us/", "/ads", "/about", "/creators", "/t/contact_us"]
            if path in ignored_paths:
                return False
                
        if host == "tiktok.com":
            # Ignore tag/search pages
            if path.startswith("/tag/"):
                return False
                
        return host in ["youtube.com", "youtu.be", "tiktok.com"]

    def extract(self, url: str) -> SpecializedResult:
        try:
            import yt_dlp
        except ImportError:
            LOGGER.warning("yt-dlp is not installed. Skipping specialized extraction for %s", url)
            return SpecializedResult([], [])

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
            "dumpjson": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
                info = ydl.extract_info(url, download=False)
                if not info:
                    return SpecializedResult([], [])

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
