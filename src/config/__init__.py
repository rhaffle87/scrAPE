from __future__ import annotations

from pathlib import Path
import json
import os
import re as _re
import logging

from .version import VERSION, VERSION_TAG

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Attempt to load .env file if available
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# Environment Variables & Credentials
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "").strip()
CAPSOLVER_API_KEY: str = os.getenv("CAPSOLVER_API_KEY", "").strip()
TWOCAPTCHA_API_KEY: str = os.getenv("TWOCAPTCHA_API_KEY", "").strip()
ANTICAPTCHA_API_KEY: str = os.getenv("ANTICAPTCHA_API_KEY", "").strip()

ENABLE_COOKIE_HARVESTING = True
ENABLE_DRISSIONPAGE_FALLBACK = True
ENABLE_HELIUM_FALLBACK = True
ENABLE_CAMOUFOX_FALLBACK = True
ENABLE_FLARESOLVERR_FALLBACK = True
FLARESOLVERR_URL = "http://127.0.0.1:8191/v1"
SEARXNG_HOSTS: list[str] = ["https://searx.be", "https://searx.space"]
DEFAULT_VIDEO_QUALITY = "best"
FORCE_HEADLESS: bool = False
STEALTH_HEADFUL: bool = False

DEFAULT_MAX_RESULTS = 0
DEFAULT_OUTPUT_FORMAT = "json"
DEFAULT_REQUESTS_PER_SECOND = 0.5  # Very safe baseline for single IP
DEFAULT_TIMEOUT_SECONDS = 15.0
DEFAULT_RETRY_ATTEMPTS = 3
DEFAULT_CACHE_TTL_SECONDS = 3600
MAX_PAGE_FETCHES = 0
MAX_CRAWL_DEPTH = 0
DEFAULT_DOWNLOAD_SPEED_LIMIT_KBPS = 0
DEFAULT_GLOBAL_CRAWL_RATE_RPS = 0.0

# Per-request jitter added on top of the rate-limit interval (seconds).
# Spreads concurrent requests across domains to reduce 429 clustering.
RATE_LIMIT_JITTER_SECONDS = 1.5  # High jitter to simulate human variance

# Per-domain rate-limit overrides (requests/second).
# Domains not listed here fall back to DEFAULT_REQUESTS_PER_SECOND.
# e.g. {"example.com": 0.5}
# Note: Custom rate limits are dynamically loaded from seed manifest headers or --domain-delay.
DOMAIN_REQUESTS_PER_SECOND: dict[str, float] = {}

ENABLE_COOKIE_HARVESTING = True
ENABLE_DRISSIONPAGE_FALLBACK = True
ENABLE_HELIUM_FALLBACK = True
ENABLE_CAMOUFOX_FALLBACK = True
ENABLE_FLARESOLVERR_FALLBACK = True
ENABLE_CURL_CFFI_FALLBACK = True
FLARESOLVERR_URL = "http://127.0.0.1:8191/v1"

# 429 circuit-breaker: how many consecutive 429 responses before cooldown triggers.
DOMAIN_COOLDOWN_THRESHOLD = 3
# Escalating cooldown durations in seconds (applied on 1st, 2nd, 3rd+ activations).
DOMAIN_COOLDOWN_SECONDS = [30, 60, 120]

# Concurrency controls
# Max pages fetched concurrently across different domains.
CONCURRENT_PAGES_PER_BATCH = 6  # Low batch size to prevent IP blocks on deep crawls
# Max simultaneous media file downloads.
CONCURRENT_DOWNLOADS = 16  # CDNs can handle more, but keeping it safe for local bandwidth

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
    "color_indicator",
    "color-indicator",
    "color_dot",
    "color-dot",
    "favicon",
    "service",
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
    "en.wikipedia.org",
    "www.wikipedia.org",
    "www.imdb.com",
    "www.youtube.com",
    "www.tiktok.com",
    "onlyfans.com",
    "linktr.ee",
    "socialveins.com",
}

HOTLINK_PROTECTED_DOMAINS: set[str] = set()
REFERER_OVERRIDES: dict[str, str] = {}
STEALTH_REQUIRED_DOMAINS: set[str] = set()
AUTH_GATED_DOMAINS: set[str] = set()

# ---------------------------------------------------------------------------
# URL Normalisation Rules
# ---------------------------------------------------------------------------
# Populated at startup from data/url_normalisation_rules.json.
# Each entry is a (compiled_re.Pattern, replacement_str) tuple applied in order
# by normalize_url() in core/filters.py.  Edit the JSON file to add or change
# rules — do NOT hardcode domain patterns here or in any logic file.

# Map domains to paths that indicate an empty search fallback
EMPTY_SEARCH_REDIRECTS: dict[str, list[str]] = {}
PREFERRED_ENGINES: dict[str, str] = {}

URL_NORMALISATION_RULES: list[tuple] = []

def _load_dynamic_config() -> None:
    global DOMAIN_REQUESTS_PER_SECOND, HOTLINK_PROTECTED_DOMAINS, REFERER_OVERRIDES, STEALTH_REQUIRED_DOMAINS, AUTH_GATED_DOMAINS, EMPTY_SEARCH_REDIRECTS, PREFERRED_ENGINES
    # ── domain_config.json ────────────────────────────────────────────────
    try:
        with open(PROJECT_ROOT / "data" / "domain_config.json", "r") as f:
            cfg = json.load(f)
            DOMAIN_REQUESTS_PER_SECOND.update(cfg.get("rate_limits", {}))
            HOTLINK_PROTECTED_DOMAINS.update(cfg.get("hotlink_protected", []))
            REFERER_OVERRIDES.update(cfg.get("referer_overrides", {}))
            STEALTH_REQUIRED_DOMAINS.update(cfg.get("stealth_required", []))
            AUTH_GATED_DOMAINS.update(cfg.get("auth_gated", []))
            EMPTY_SEARCH_REDIRECTS.update(cfg.get("empty_search_redirects", {}))
            PREFERRED_ENGINES.update(cfg.get("preferred_engines", {}))
    except FileNotFoundError:
        pass
    except Exception as e:
        logging.getLogger(__name__).warning("Failed to parse data/domain_config.json: %s", e)

    # ── url_normalisation_rules.json ──────────────────────────────────────
    try:
        with open(PROJECT_ROOT / "data" / "url_normalisation_rules.json", "r") as f:
            data = json.load(f)
        for rule in data.get("rules", []):
            pattern_str = rule.get("pattern", "")
            replacement = rule.get("replacement", "")
            if pattern_str:
                URL_NORMALISATION_RULES.append(
                    (_re.compile(pattern_str, _re.IGNORECASE), replacement)
                )
    except FileNotFoundError:
        pass
    except Exception as e:
        logging.getLogger(__name__).warning("Failed to parse data/url_normalisation_rules.json: %s", e)


_load_dynamic_config()


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
