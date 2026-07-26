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
                
        if path.endswith(".m3u8") or path.endswith(".mpd"):
            return True

        return host in ["youtube.com", "youtu.be", "tiktok.com", "vimeo.com", "twitter.com", "x.com"]

    def extract(self, url: str) -> SpecializedResult:
        try:
            import yt_dlp
        except ImportError:
            LOGGER.warning("yt-dlp is not installed. Skipping specialized extraction for %s", url)
            return SpecializedResult([], [])

        import config
        quality = getattr(config, "DEFAULT_VIDEO_QUALITY", "best")
        format_spec = "bv*+ba/b"
        if quality == "1080p":
            format_spec = "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best"
        elif quality == "720p":
            format_spec = "bestvideo[height<=720]+bestaudio/best[height<=720]/best"
        elif quality == "480p":
            format_spec = "bestvideo[height<=480]+bestaudio/best[height<=480]/best"

        parsed_host = urllib.parse.urlparse(url).netloc.lower()
        if parsed_host.startswith("www."):
            parsed_host = parsed_host[4:]

        import typing
        ydl_opts: dict[str, typing.Any] = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": "in_playlist",
            "skip_download": True,
            "dumpjson": True,
            "format": format_spec,
        }

        cookies = self.get_domain_cookies(parsed_host)
        if cookies:
            cookie_header = "; ".join(f"{k}={v}" for k, v in cookies.items())
            ydl_opts["http_headers"] = {"Cookie": cookie_header}

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
