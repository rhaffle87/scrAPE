from __future__ import annotations

from pathlib import Path

DEFAULT_MAX_RESULTS = 0
DEFAULT_OUTPUT_FORMAT = "json"
DEFAULT_REQUESTS_PER_SECOND = 1.0
DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_CACHE_TTL_SECONDS = 3600
MAX_PAGE_FETCHES = 0
MAX_CRAWL_DEPTH = 0

# Per-request jitter added on top of the rate-limit interval (seconds).
# Spreads concurrent requests across domains to reduce 429 clustering.
RATE_LIMIT_JITTER_SECONDS = 0.4

# Per-domain rate-limit overrides (requests/second).
# Domains not listed here fall back to DEFAULT_REQUESTS_PER_SECOND.
# e.g. {"example.com": 0.5}
DOMAIN_REQUESTS_PER_SECOND: dict[str, float] = {
    "example-rate-limited.com": 0.2,
    "example-throttled.com": 0.1,
}

# 429 circuit-breaker: how many consecutive 429 responses before cooldown triggers.
DOMAIN_COOLDOWN_THRESHOLD = 3
# Escalating cooldown durations in seconds (applied on 1st, 2nd, 3rd+ activations).
DOMAIN_COOLDOWN_SECONDS = [30, 60, 120]

# Concurrency controls
# Max pages fetched concurrently across different domains.
CONCURRENT_PAGES_PER_BATCH = 12
# Max simultaneous media file downloads.
CONCURRENT_DOWNLOADS = 16

OUTPUT_DIR = Path("output")
CACHE_DIR = Path(".cache")
DEFAULT_RUNS_SUBDIR = "runs"
DEFAULT_DOWNLOAD_IMAGES_SUBDIR = "images"
DEFAULT_DOWNLOAD_VIDEOS_SUBDIR = "videos"
MIN_IMAGE_DOWNLOAD_BYTES = 10240
MIN_VIDEO_DOWNLOAD_BYTES = 16384
MIN_IMAGE_WIDTH = 400
MIN_IMAGE_HEIGHT = 300
GENERIC_ASSET_TERMS = {
    "logo",
    "icon",
    "banner",
    "badge",
    "avatar",
    "placeholder",
    "sprite",
    "thumbnail",
    "app-store",
    "play-store",
}
PREVIEW_MARKERS = {
    "thumb_vid",
    "thumb-vid",
    "_thumb",
    "-thumb",
    "thumb.",
    "thumbnail",
    "preview",
    "avatar",
    "icon",
    "sprite",
    "small",
    "tiny",
    "blur",
    "lowres",
    "low-res",
    "collage",
    "storyboard",
    "previewsheet",
    "sample",
    "trailer",
    "short",
    "promo",
}
DISCOVERY_PATH_HINTS = [
    "/gallery",
    "/galleries",
    "/album",
    "/albums",
    "/photo",
    "/photos",
    "/image",
    "/images",
    "/video",
    "/videos",
    "/media",
    "/post",
    "/posts",
    "/upload",
    "/uploads",
]
HLS_EXTENSIONS = {".m3u8"}
DASH_EXTENSIONS = {".mpd"}

ALWAYS_BLOCK_DOMAINS = {
    "unsplash.com",
    "pexels.com",
    "pixabay.com",
    "commons.wikimedia.org",
    "openverse.org",
    "api.openverse.org",
    "gravatar.com",
    "google-analytics.com",
    "googletagmanager.com",
    "doubleclick.net",
    "facebook.net",
    "pixel.wp.com",
    "adsystem.com",
    "adservice.google.com",
}
# CDN parent domains are now derived dynamically from the seed manifest's [CDN]
# annotations (SeedManifest.all_allowed_hosts) instead of a hardcoded dict here.
# See src/core/seed_manifest.py and the _normalise_cdn_host() function.

USER_AGENTS = [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.5 Safari/605.1.15"
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
]

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".avif",
    ".apng",
    ".bmp",
    ".heic",
    ".heif",
}
VIDEO_EXTENSIONS = {".mp4", ".webm", ".ogv", ".mov", ".avi", ".mkv", ".m4v"}
SUPPORTED_OUTPUT_FORMATS = {"json", "csv", "both"}