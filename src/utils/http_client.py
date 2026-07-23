"""
http_client.py — Tiered HTTP request client with WAF fallback.

Request flow for HttpClient.get(url):
  1. Disk cache hit → return cached response (TTL: DEFAULT_CACHE_TTL_SECONDS).
  2. Domain cooldown active? → raise ScraperBypassError immediately (circuit-breaker).
  3. httpx.get() → success → reset 429 counter, store cache, return.
  4. 403 / 401 / 429 → _get_with_crawl4ai():
       Tier 1: Playwright stealth browser (resolves most WAF soft-blocks).
       Tier 2: UndetectedAdapter browser (bypasses Cloudflare Turnstile / deep fingerprinting).
  5. Both tiers fail → raise ScraperBypassError (non-retryable, exits tenacity immediately).

Per-domain rate limiting:
  Each hostname gets its own RateLimiter seeded from DOMAIN_REQUESTS_PER_SECOND
  (falling back to DEFAULT_REQUESTS_PER_SECOND). A configurable jitter is applied
  to all limiters to prevent thundering-herd patterns.

429 circuit-breaker:
  After DOMAIN_COOLDOWN_THRESHOLD consecutive 429 responses from the same hostname,
  the domain is placed in cooldown for DOMAIN_COOLDOWN_SECONDS[n] seconds (escalating).
  Subsequent requests to that domain raise ScraperBypassError for the cooldown duration,
  preventing browser fallback overhead accumulation.

asyncio loop reuse:
  A single background event loop (daemon thread) handles all Crawl4AI coroutines.
  This eliminates the per-call browser spawn overhead from asyncio.run().
"""

from __future__ import annotations

import hashlib
import random
import re
import threading
import time
from pathlib import Path
from urllib.parse import urlparse
import httpx

import sys
import typing


from config import (
    CACHE_DIR,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_REQUESTS_PER_SECOND,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_TIMEOUT_SECONDS,
    DOMAIN_COOLDOWN_THRESHOLD,
    DOMAIN_REQUESTS_PER_SECOND,
    RATE_LIMIT_JITTER_SECONDS,
    USER_AGENTS,
    REFERER_OVERRIDES,
    ENABLE_COOKIE_HARVESTING,
    ENABLE_DRISSIONPAGE_FALLBACK,
    ENABLE_HELIUM_FALLBACK,
    ENABLE_CAMOUFOX_FALLBACK,
    ENABLE_FLARESOLVERR_FALLBACK,
    FLARESOLVERR_URL,
    FORCE_HEADLESS,
    STEALTH_HEADFUL,
)
from utils.rate_limiter import RateLimiter
from utils.session_pool import SessionPool
from utils.blacklist import is_blacklisted
from utils.session import SessionManager

FORCE_HEADLESS: bool = False
STEALTH_HEADFUL: bool = False


# ---------------------------------------------------------------------------
# URL normalisation (canonical implementation is in core.filters.normalize_url)
# ---------------------------------------------------------------------------
# normalise_url() is kept here as a convenience re-export so existing callers
# that import it from this module continue to work.  All normalisation rules
# live in config.URL_NORMALISATION_RULES — do not add patterns here.


def normalise_url(url: str) -> str:
    """Canonicalise *url* by applying all rules from ``config.URL_NORMALISATION_RULES``.

    This is a thin delegation to ``core.filters.normalize_url``.
    Add new normalisation rules to ``config.URL_NORMALISATION_RULES``, not here.
    """
    from core.filters import normalize_url

    return normalize_url(url)


# ---------------------------------------------------------------------------
# Background asyncio loop (singleton) — eliminates per-call event loop cost
# ---------------------------------------------------------------------------

_loop_lock = threading.Lock()
_background_loop = None
_background_thread = None


def _get_or_create_event_loop():
    """Return the singleton background asyncio event loop, creating it on demand."""
    global _background_loop, _background_thread  # noqa: PLW0603
    import asyncio

    with _loop_lock:
        if _background_loop is None or not _background_loop.is_running():
            _background_loop = asyncio.new_event_loop()

            def _run_loop(loop):
                asyncio.set_event_loop(loop)
                loop.run_forever()

            _background_thread = threading.Thread(
                target=_run_loop,
                args=(_background_loop,),
                daemon=True,
                name="crawl4ai-event-loop",
            )
            _background_thread.start()
    return _background_loop


def _run_coroutine_sync(coro):
    """Submit *coro* to the background event loop and block until it completes."""
    import asyncio

    loop = _get_or_create_event_loop()
    future = asyncio.run_coroutine_threadsafe(coro, loop)
    return future.result()


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class ScraperBypassError(Exception):
    """Raised when all Crawl4AI fallback tiers fail to bypass anti-bot protection.

    This is intentionally NOT a subclass of ``httpx.HTTPError`` so that
    ``tenacity`` does not attempt to retry the request — the URL is
    considered permanently hard-blocked or in cooldown.
    """


# ---------------------------------------------------------------------------
# Per-domain 429 circuit-breaker state
# ---------------------------------------------------------------------------


class _DomainCooldownState:
    """Tracks 429 hits and cooldown schedule for a single hostname."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.consecutive_429s: int = 0
        self.consecutive_failures: int = (
            0  # consecutive timeouts or connection failures
        )
        self.cooldown_count: int = 0  # how many cooldowns have been triggered
        self.cooldown_until: float = 0.0  # monotonic timestamp
        self.is_blacklisted: bool = False

    def record_429(self) -> float | None:
        """Increment the 429 counter.  Returns cooldown duration if threshold crossed, else None."""
        with self._lock:
            self.consecutive_429s += 1
            if self.consecutive_429s >= DOMAIN_COOLDOWN_THRESHOLD:
                if self.cooldown_count >= 3:
                    self.is_blacklisted = True
                    self.cooldown_until = time.monotonic() + 36000.0  # 10 hours
                    return 36000.0

                durations = [30.0, 120.0, 600.0]
                duration = durations[self.cooldown_count]
                self.cooldown_until = time.monotonic() + duration
                self.cooldown_count += 1
                self.consecutive_429s = 0
                self.consecutive_failures = 0
                return duration
        return None

    def record_failure(self) -> float | None:
        """Increment the failure counter. Returns cooldown duration if threshold crossed, else None."""
        with self._lock:
            self.consecutive_failures += 1
            if (
                self.consecutive_failures >= 3
            ):  # Cooldown after 3 consecutive timeouts/connect errors
                if self.cooldown_count >= 3:
                    self.is_blacklisted = True
                    self.cooldown_until = time.monotonic() + 36000.0  # 10 hours
                    return 36000.0

                durations = [30.0, 120.0, 600.0]
                duration = durations[self.cooldown_count]
                self.cooldown_until = time.monotonic() + duration
                self.cooldown_count += 1
                self.consecutive_429s = 0
                self.consecutive_failures = 0
                return duration
        return None

    def record_success(self) -> None:
        """Reset consecutive counters on a clean response."""
        with self._lock:
            self.consecutive_429s = 0
            self.consecutive_failures = 0

    def is_cooling_down(self) -> bool:
        with self._lock:
            return self.is_blacklisted or time.monotonic() < self.cooldown_until

    def cooldown_remaining(self) -> float:
        with self._lock:
            if self.is_blacklisted:
                return 36000.0
            return max(0.0, self.cooldown_until - time.monotonic())


def _apply_playwright_channel_patch() -> None:
    """Patch playwright and patchright launch_persistent_context to respect BrowserConfig channel."""
    from utils.logger import get_logger

    logger = get_logger(__name__)

    try:
        import playwright.async_api

        _orig_playwright_async = playwright.async_api.async_playwright

        # Check if already patched to avoid double patching
        if not getattr(_orig_playwright_async, "_is_patched", False):

            def _patched_playwright_async(*args, **kwargs):
                cm = _orig_playwright_async(*args, **kwargs)
                orig_start = cm.start

                async def patched_start(*args, **kwargs):
                    instance = await orig_start(*args, **kwargs)
                    _patch_playwright_instance(instance, logger)
                    return instance

                cm.start = patched_start
                return cm

            setattr(_patched_playwright_async, "_is_patched", True)
            playwright.async_api.async_playwright = _patched_playwright_async
            logger.info("Successfully patched playwright.async_api.async_playwright")
    except Exception as e:
        logger.warning("Failed to patch playwright.async_api.async_playwright: %s", e)

    try:
        import patchright.async_api

        _orig_patchright_async = patchright.async_api.async_playwright

        if not getattr(_orig_patchright_async, "_is_patched", False):

            def _patched_patchright_async(*args, **kwargs):
                cm = _orig_patchright_async(*args, **kwargs)
                orig_start = cm.start

                async def patched_start(*args, **kwargs):
                    instance = await orig_start(*args, **kwargs)
                    _patch_playwright_instance(instance, logger)
                    return instance

                cm.start = patched_start
                return cm

            setattr(_patched_patchright_async, "_is_patched", True)
            patchright.async_api.async_playwright = _patched_patchright_async
            logger.info("Successfully patched patchright.async_api.async_playwright")
    except Exception as e:
        logger.warning("Failed to patch patchright.async_api.async_playwright: %s", e)


def _patch_playwright_instance(instance, logger) -> None:
    import inspect

    if hasattr(instance, "chromium"):
        orig_launch_persistent = instance.chromium.launch_persistent_context
        if not getattr(orig_launch_persistent, "_is_patched", False):

            async def patched_launch_persistent(user_data_dir, **kwargs):
                # Walk up stack to find BrowserManager
                channel = None
                for frame_info in inspect.stack():
                    frame = frame_info.frame
                    self_obj = frame.f_locals.get("self")
                    if self_obj and self_obj.__class__.__name__ == "BrowserManager":
                        if hasattr(self_obj, "config"):
                            channel = getattr(
                                self_obj.config, "chrome_channel", None
                            ) or getattr(self_obj.config, "channel", None)
                        break
                if channel and channel != "chromium":
                    logger.info(
                        "Injecting channel='%s' into launch_persistent_context", channel
                    )
                    kwargs["channel"] = channel

                is_windows = sys.platform.startswith("win")

                # Filter out anti-sandbox flags that expose automation warning banners in Chrome.
                # On Windows, we must keep --no-sandbox to prevent GPU process crashes and rendering hangs.
                if "args" in kwargs and isinstance(kwargs["args"], list):
                    if is_windows:
                        kwargs["args"] = [
                            arg
                            for arg in kwargs["args"]
                            if arg != "--disable-setuid-sandbox"
                        ]
                    else:
                        kwargs["args"] = [
                            arg
                            for arg in kwargs["args"]
                            if arg not in ("--no-sandbox", "--disable-setuid-sandbox")
                        ]

                # Exclude default flags that reveal automation or trigger Cloudflare checks.
                # On Windows, we must NOT ignore --no-sandbox to ensure Chrome launches with sandbox disabled.
                target_ignores = ["--enable-automation", "--disable-extensions"]
                if not is_windows:
                    target_ignores.append("--no-sandbox")

                if "ignore_default_args" not in kwargs:
                    kwargs["ignore_default_args"] = target_ignores
                elif isinstance(kwargs["ignore_default_args"], list):
                    for arg in target_ignores:
                        if arg not in kwargs["ignore_default_args"]:
                            kwargs["ignore_default_args"].append(arg)

                logger.info("launch_persistent_context kwargs: %s", kwargs)
                return await orig_launch_persistent(user_data_dir, **kwargs)

            setattr(patched_launch_persistent, "_is_patched", True)
            instance.chromium.launch_persistent_context = patched_launch_persistent


def _get_platform_user_agent() -> str:

    if sys.platform.startswith("win"):
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    elif sys.platform == "darwin":
        return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"


# ---------------------------------------------------------------------------
# HttpClient
# ---------------------------------------------------------------------------


class HttpClient:
    """Thread-safe HTTP client with per-domain rate limiting and WAF fallback.

    Uses ``httpx`` as the primary transport and escalates to Crawl4AI
    browser-based fetching when the server returns 403, 401, or 429.
    A 429 circuit-breaker prevents thrashing a rate-limited domain.
    All text/HTML/JSON responses are cached to disk.
    """

    _stealth_required_hosts: set[str] = set()
    _stealth_lock = threading.Lock()
    _stealth_failed_hosts: dict[str, float] = {}
    _failed_stealth_lock = threading.Lock()
    _cloudflare_blocked_hosts: set[str] = set()
    _cf_blocked_lock = threading.Lock()
    _preferred_engine_by_host: dict[str, str] = {}
    _preferred_engine_lock = threading.Lock()
    _flaresolverr_online: bool | None = None
    _flaresolverr_lock = threading.Lock()
    _waf_solve_counts: dict[str, int] = {
        "crawl4ai": 0,
        "camoufox": 0,
        "flaresolverr": 0,
        "uc": 0,
        "cheerio": 0,
        "puppeteer": 0,
        "drissionpage": 0,
        "helium": 0,
    }
    _waf_solve_lock = threading.Lock()

    @classmethod
    def register_cloudflare_blocked(cls, hostname: str) -> None:
        """Mark *hostname* as Cloudflare-blocked.

        When marked, the client will skip all Crawl4AI browser fallback tiers
        for that hostname and raise ``ScraperBypassError`` immediately on 403/429.
        This prevents wasting 25+ seconds on headful browser attempts that are
        guaranteed to fail due to Turnstile challenges.
        """
        with cls._cf_blocked_lock:
            cls._cloudflare_blocked_hosts.add(hostname.lower())

    @classmethod
    def register_stealth_required(cls, hostname: str) -> None:
        """Mark *hostname* as requiring direct browser-stealth routing.

        When marked, all ``get()`` requests for that hostname bypass the standard
        ``httpx`` transport and are routed immediately through the Crawl4AI /
        DrissionPage browser pipeline.  Use for search providers and other hosts
        that block raw HTTP clients with bot-detection before returning a 4xx.
        """
        with cls._stealth_lock:
            cls._stealth_required_hosts.add(hostname.lower())

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        domain_delays: dict[str, float] | None = None,
        proxy: str | None = None,
        proxy_list: str | None = None,
        capsolver_key: str | None = None,
        global_rate_limit_rps: float = 0.0,
    ) -> None:
        """
        Args:
            timeout: Per-request timeout in seconds.
            domain_delays: Optional ``{hostname: seconds_per_request}`` overrides
                           that take priority over ``DOMAIN_REQUESTS_PER_SECOND``.
            global_rate_limit_rps: Maximum global page request rate limit in req/s (0.0 = unlimited).
        """
        self.timeout = timeout
        self.capsolver_key = capsolver_key
        self.global_rate_limit_rps = max(0.0, global_rate_limit_rps)
        
        self.proxy_list = []
        if proxy_list and Path(proxy_list).exists():
            with open(proxy_list, "r", encoding="utf-8") as f:
                self.proxy_list = [line.strip() for line in f if line.strip()]
        if proxy:
            self.proxy_list.append(proxy)
            
        self.current_proxy_index = 0
        self._proxy_lock = threading.Lock()
        
        # Configure httpx Client with proxy if available
        client_kwargs = {"timeout": timeout, "follow_redirects": True}
        if self.proxy_list:
            client_kwargs["proxy"] = self.proxy_list[0]
            
        self.client = httpx.Client(**client_kwargs)
        self.session_manager = SessionManager()
        # Convert seconds_per_request (delays) to requests_per_second (RPS)
        converted_delays = {}
        if domain_delays:
            for host, delay in domain_delays.items():
                if delay > 0:
                    converted_delays[host] = 1.0 / delay
        # Merged overrides: CLI-supplied > config defaults
        self._domain_rps_overrides: dict[str, float] = {
            **DOMAIN_REQUESTS_PER_SECOND,
            **converted_delays,
        }
        # Per-hostname RateLimiter (lazy-created)
        self._rate_limiters: dict[str, RateLimiter] = {}
        self._rl_lock = threading.Lock()
        # Per-hostname 429 circuit-breaker state (lazy-created)
        self._cooldown_states: dict[str, _DomainCooldownState] = {}
        self._cd_lock = threading.Lock()
        self._session_pool = SessionPool()
        # Per-domain serialization locks for Crawl4AI fallback
        self._domain_fallback_locks: dict[str, threading.Lock] = {}
        self._fallback_lock = threading.Lock()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        # Thread-local storage: tracks the pure *network* latency for the most
        # recent get() call on this thread (excludes rate-limiter sleep time).
        # The engine's adaptive concurrency scaler reads this to avoid penalising
        # all domains when one slow domain is simply waiting for its rate limit.
        self._thread_local = threading.local()

    def _fallback_lock_for(self, host: str) -> threading.Lock:
        with self._fallback_lock:
            if host not in self._domain_fallback_locks:
                self._domain_fallback_locks[host] = threading.Lock()
            return self._domain_fallback_locks[host]

    # ------------------------------------------------------------------
    # Proxy Management
    # ------------------------------------------------------------------
    def get_proxy(self) -> str | None:
        with self._proxy_lock:
            if not self.proxy_list:
                return None
            return self.proxy_list[self.current_proxy_index]

    def rotate_proxy(self) -> str | None:
        with self._proxy_lock:
            if not self.proxy_list:
                return None
            self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
            new_proxy = self.proxy_list[self.current_proxy_index]
            
            # Recreate httpx client with new proxy
            self.client = httpx.Client(timeout=self.timeout, follow_redirects=True, proxy=new_proxy)
            return new_proxy

    # ------------------------------------------------------------------
    # Domain helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _hostname(url: str) -> str:
        return urlparse(url).netloc.lower()

    def _rate_limiter_for(self, url: str) -> RateLimiter:
        """Return (or lazily create) the RateLimiter for *url*'s hostname."""
        host = self._hostname(url)
        with self._rl_lock:
            if host not in self._rate_limiters:
                rps = self._domain_rps_overrides.get(host, DEFAULT_REQUESTS_PER_SECOND)
                if self.global_rate_limit_rps > 0.0:
                    rps = min(rps, self.global_rate_limit_rps)
                self._rate_limiters[host] = RateLimiter(
                    rps, jitter=RATE_LIMIT_JITTER_SECONDS
                )
            return self._rate_limiters[host]

    def _cooldown_state_for(self, url: str) -> _DomainCooldownState:
        """Return (or lazily create) the cooldown state for *url*'s hostname."""
        host = self._hostname(url)
        with self._cd_lock:
            if host not in self._cooldown_states:
                self._cooldown_states[host] = _DomainCooldownState()
            return self._cooldown_states[host]

    # ------------------------------------------------------------------
    # Headers
    # ------------------------------------------------------------------

    def _headers(self, url: str | None = None) -> dict[str, str]:
        """Return a request header dict with a sticky User-Agent for the domain."""
        if url:
            host = self._hostname(url)
            session = self._session_pool.get_session(host)
            headers = session.get_headers().copy()
            for ref_host, ref_val in REFERER_OVERRIDES.items():
                if ref_host in host:
                    headers["Referer"] = ref_val
                    break
            return headers
        return {"User-Agent": random.choice(USER_AGENTS)}

    # ------------------------------------------------------------------
    # Disk cache
    # ------------------------------------------------------------------

    def _cache_path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return CACHE_DIR / f"{digest}.cache"

    def _load_cache(self, url: str) -> httpx.Response | None:
        """Return a cached response if it exists and has not expired."""
        cache_path = self._cache_path(url)
        if not cache_path.exists():
            return None
        if time.time() - cache_path.stat().st_mtime > DEFAULT_CACHE_TTL_SECONDS:
            return None
        return httpx.Response(
            status_code=200,
            text=cache_path.read_text(encoding="utf-8"),
            request=httpx.Request("GET", url),
        )

    def _store_cache(self, url: str, response: httpx.Response) -> None:
        """Persist a text/HTML/JSON response body to disk."""
        content_type = response.headers.get("content-type", "")
        if (
            "text" not in content_type
            and "json" not in content_type
            and "xml" not in content_type
        ):
            return
        self._cache_path(url).write_text(response.text, encoding="utf-8")

    # ------------------------------------------------------------------
    # Cloudflare challenge detection
    # ------------------------------------------------------------------

    def _is_cloudflare_challenge(self, html: str) -> bool:
        """Return True if the HTML is a Cloudflare interstitial challenge page."""
        if not html:
            return False
        title_match = re.search(
            r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
        )
        if title_match:
            title = title_match.group(1).strip().lower()
            if (
                "just a moment" in title
                or "checking your browser" in title
                or "attention required" in title
            ):
                return True
        lower_html = html.lower()
        if ("challenges.cloudflare.com" in lower_html or "cf-challenge" in lower_html) and (
            "just a moment" in lower_html
            or "please enable javascript" in lower_html
        ):
            return True
        return False

    def _is_blocked_page(self, html: str, url: str) -> bool:
        """Return True if the HTML indicates a Cloudflare challenge or a soft block/redirect by DuckDuckGo."""
        if not html:
            return True
        if self._is_cloudflare_challenge(html):
            return True
        parsed = urlparse(url)
        host = parsed.netloc or parsed.hostname or ""
        if "duckduckgo.com" in host:
            lower_html = html.lower()
            if (
                "if this persists, please email us" in lower_html
                or "error-lite" in lower_html
            ):
                return True
            if "/?q=" in url or "/html/" in url:
                title_match = re.search(
                    r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL
                )
                if title_match:
                    title = title_match.group(1).strip()
                    if title == "DuckDuckGo":
                        return True
        return False

    # ------------------------------------------------------------------
    # Local Cookie Harvesting & DrissionPage deep stealth fallbacks
    # ------------------------------------------------------------------

    def _crypt_unprotect_data(self, data: bytes) -> bytes:
        import ctypes
        from ctypes import wintypes

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [("cbData", wintypes.DWORD), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]

        try:
            CryptUnprotectData = ctypes.windll.crypt32.CryptUnprotectData
        except AttributeError:
            return b""
        
        in_blob = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data), ctypes.POINTER(ctypes.c_ubyte)))
        out_blob = DATA_BLOB()
        
        if CryptUnprotectData(ctypes.byref(in_blob), None, None, None, None, 0, ctypes.byref(out_blob)):
            res = ctypes.string_at(out_blob.pbData, out_blob.cbData)
            try:
                ctypes.windll.kernel32.LocalFree(out_blob.pbData)
            except Exception:
                pass
            return res
        return b""

    def _get_chrome_key(self, local_state_path: Path) -> bytes:
        import json
        import base64
        try:
            if not local_state_path.exists():
                return b""
            with open(local_state_path, "r", encoding="utf-8") as f:
                local_state = json.load(f)
            encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
            if encrypted_key.startswith(b"DPAPI"):
                encrypted_key = encrypted_key[5:]
            return self._crypt_unprotect_data(encrypted_key)
        except Exception:
            return b""

    def _decrypt_cookie(self, encrypted_value: bytes, key: bytes) -> str:
        try:
            if encrypted_value.startswith(b"v10") or encrypted_value.startswith(b"v11"):
                iv = encrypted_value[3:15]
                payload = encrypted_value[15:-16]
                tag = encrypted_value[-16:]
                from cryptography.hazmat.primitives.ciphers.aead import AESGCM
                aesgcm = AESGCM(key)
                decrypted = aesgcm.decrypt(iv, payload + tag, None)
                return decrypted.decode("utf-8", errors="ignore")
            else:
                decrypted = self._crypt_unprotect_data(encrypted_value)
                return decrypted.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _harvest_chromium_cookies_windows(self, user_data_path: Path, host: str, logger) -> dict[str, str]:
        import sqlite3
        import shutil
        import tempfile
        import random
        
        local_state_path = user_data_path / "Local State"
        if not local_state_path.exists():
            local_state_path = user_data_path.parent / "Local State"
            if not local_state_path.exists():
                return {}
                
        key = self._get_chrome_key(local_state_path)
        if not key:
            return {}
            
        cookie_db_paths = []
        for folder in ["Default", "Profile 1", "Profile 2", "Profile 3", "System"]:
            db_path = user_data_path / folder / "Network" / "Cookies"
            if db_path.exists():
                cookie_db_paths.append(db_path)
            db_path_old = user_data_path / folder / "Cookies"
            if db_path_old.exists():
                cookie_db_paths.append(db_path_old)
                
        db_opera = user_data_path / "Network" / "Cookies"
        if db_opera.exists():
            cookie_db_paths.append(db_opera)
        db_opera_old = user_data_path / "Cookies"
        if db_opera_old.exists():
            cookie_db_paths.append(db_opera_old)

        if not cookie_db_paths:
            try:
                for p in user_data_path.glob("**/Network/Cookies"):
                    cookie_db_paths.append(p)
                for p in user_data_path.glob("**/Cookies"):
                    if p.is_file() and p.name == "Cookies":
                        cookie_db_paths.append(p)
            except Exception:
                pass

        harvested = {}
        domains_to_try = [host]
        if host.startswith("www."):
            domains_to_try.append(host[4:])
        else:
            domains_to_try.append(f".{host}")

        for db_path in cookie_db_paths:
            temp_db = Path(tempfile.gettempdir()) / f"temp_cookies_{random.randint(1000, 9999)}.sqlite"
            try:
                shutil.copy2(db_path, temp_db)
                conn = sqlite3.connect(str(temp_db))
                cursor = conn.cursor()
                
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cookies'")
                if not cursor.fetchone():
                    conn.close()
                    continue
                    
                query = "SELECT name, encrypted_value, value, host_key FROM cookies WHERE " + " OR ".join(["host_key LIKE ?" for _ in domains_to_try])
                params = [f"%{dom}%" for dom in domains_to_try]
                cursor.execute(query, params)
                
                for name, enc_val, val, host_key in cursor.fetchall():
                    match = False
                    for dom in domains_to_try:
                        if dom in host_key:
                            match = True
                            break
                    if not match:
                        continue
                        
                    decrypted = self._decrypt_cookie(enc_val, key)
                    if decrypted:
                        harvested[name] = decrypted
                    elif val:
                        harvested[name] = val
                        
                conn.close()
            except Exception as err:
                logger.debug("Failed to read from temp db %s: %s", db_path, err)
            finally:
                if temp_db.exists():
                    try:
                        temp_db.unlink()
                    except Exception:
                        pass
                        
        return harvested

    def _harvest_firefox_cookies_windows(self, firefox_profiles_dir: Path, host: str, logger) -> dict[str, str]:
        import sqlite3
        import shutil
        import tempfile
        import random
        
        if not firefox_profiles_dir.exists():
            return {}
            
        harvested = {}
        domains_to_try = [host]
        if host.startswith("www."):
            domains_to_try.append(host[4:])
        else:
            domains_to_try.append(f".{host}")

        try:
            for profile in firefox_profiles_dir.glob("*"):
                db_path = profile / "cookies.sqlite"
                if db_path.exists():
                    temp_db = Path(tempfile.gettempdir()) / f"temp_ff_cookies_{random.randint(1000, 9999)}.sqlite"
                    try:
                        shutil.copy2(db_path, temp_db)
                        conn = sqlite3.connect(str(temp_db))
                        cursor = conn.cursor()
                        
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='moz_cookies'")
                        if not cursor.fetchone():
                            conn.close()
                            continue
                            
                        query = "SELECT name, value, host FROM moz_cookies WHERE " + " OR ".join(["host LIKE ?" for _ in domains_to_try])
                        params = [f"%{dom}%" for dom in domains_to_try]
                        cursor.execute(query, params)
                        
                        for name, value, host_key in cursor.fetchall():
                            harvested[name] = value
                        conn.close()
                    except Exception as err:
                        logger.debug("Failed to read from Firefox db %s: %s", db_path, err)
                    finally:
                        if temp_db.exists():
                            try:
                                temp_db.unlink()
                            except Exception:
                                pass
        except Exception as err:
            logger.debug("Failed searching Firefox profiles: %s", err)
        return harvested

    def _harvest_local_cookies(self, host: str) -> dict[str, str]:
        """Harvest local cookies for *host* from local Chrome, Edge, Firefox, Brave, Opera."""
        if not ENABLE_COOKIE_HARVESTING:
            return {}

        from utils.logger import get_logger
        import os
        import sys

        logger = get_logger(__name__)
        harvested = {}

        if sys.platform.startswith("win"):
            local_appdata = os.environ.get("LOCALAPPDATA", "")
            appdata = os.environ.get("APPDATA", "")
            
            if local_appdata:
                chrome_user_data = Path(local_appdata) / "Google" / "Chrome" / "User Data"
                brave_user_data = Path(local_appdata) / "BraveSoftware" / "Brave-Browser" / "User Data"
                edge_user_data = Path(local_appdata) / "Microsoft" / "Edge" / "User Data"
                
                if chrome_user_data.exists():
                    logger.debug("Harvesting from Chrome...")
                    harvested.update(self._harvest_chromium_cookies_windows(chrome_user_data, host, logger))
                if brave_user_data.exists():
                    logger.debug("Harvesting from Brave...")
                    harvested.update(self._harvest_chromium_cookies_windows(brave_user_data, host, logger))
                if edge_user_data.exists():
                    logger.debug("Harvesting from Edge...")
                    harvested.update(self._harvest_chromium_cookies_windows(edge_user_data, host, logger))
            
            if appdata:
                opera_user_data = Path(appdata) / "Opera Software" / "Opera Stable"
                firefox_profiles = Path(appdata) / "Mozilla" / "Firefox" / "Profiles"
                
                if opera_user_data.exists():
                    logger.debug("Harvesting from Opera...")
                    harvested.update(self._harvest_chromium_cookies_windows(opera_user_data, host, logger))
                if firefox_profiles.exists():
                    logger.debug("Harvesting from Firefox...")
                    harvested.update(self._harvest_firefox_cookies_windows(firefox_profiles, host, logger))

            if harvested:
                logger.info(
                    "Successfully harvested %d cookies for '%s' using Windows custom pipeline",
                    len(harvested),
                    host,
                )
                return harvested

        try:
            import browser_cookie3
        except ImportError:
            logger.warning("browser-cookie3 not installed, skipping browser_cookie3 fallback")
            return harvested

        browsers_to_try = [
            ("chrome", browser_cookie3.chrome),
            ("firefox", browser_cookie3.firefox),
            ("edge", browser_cookie3.edge),
            ("brave", browser_cookie3.brave),
            ("opera", browser_cookie3.opera),
        ]

        domains_to_try = [host]
        if host.startswith("www."):
            domains_to_try.append(host[4:])
        else:
            domains_to_try.append(f".{host}")

        for b_name, b_func in browsers_to_try:
            for dom in domains_to_try:
                try:
                    cj = b_func(domain_name=dom)
                    for cookie in cj:
                        harvested[cookie.name] = cookie.value
                    if harvested:
                        logger.info(
                            "Successfully harvested %d cookies for '%s' from local %s (browser_cookie3)",
                            len(harvested),
                            dom,
                            b_name,
                        )
                        return harvested
                except Exception as exc:
                    logger.debug("Local cookie harvest fallback from %s failed: %s", b_name, exc)

        return harvested

    def _get_with_crawlee_cheerio(self, url: str) -> tuple[str, list[dict]]:
        """Fetch URL using Crawlee Cheerio (fast parser)"""
        from utils.crawlee_client import CrawleeClient
        client = CrawleeClient()
        html = client.get_with_cheerio(url, proxy=self.get_proxy())
        return html, []

    def _get_with_crawlee_puppeteer(self, url: str) -> tuple[str, list[dict]]:
        """Fetch URL using Crawlee Puppeteer (stealth browser)"""
        from utils.crawlee_client import CrawleeClient
        client = CrawleeClient()
        html, cookies = client.get_with_puppeteer(url, proxy=self.get_proxy())
        return html, cookies

    def _get_with_drissionpage(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using DrissionPage to bypass Turnstile/WAF locally."""
        from utils.logger import get_logger

        logger = get_logger(__name__)

        try:
            from DrissionPage import ChromiumOptions, ChromiumPage
        except ImportError as e:
            logger.error("DrissionPage not installed: %s", e)
            raise e

        # Initialize options
        co = ChromiumOptions()
        co.set_argument("--no-sandbox")
        co.set_argument("--disable-gpu")
        
        proxy = self.get_proxy()
        if proxy:
            co.set_proxy(proxy)

        # Determine GUI platform

        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos

        headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))
        co.headless(headless_mode)

        # Build persistent profile path to share cookies/history
        host = self._hostname(url)
        domain_slug = re.sub(r"[^\w\-]", "_", host)
        profile_path = Path("data/drission_profiles") / domain_slug
        profile_path.mkdir(parents=True, exist_ok=True)
        co.set_user_data_path(str(profile_path.resolve()))

        logger.info("Launching DrissionPage for %s (headless=%s)", url, headless_mode)

        page = None
        try:
            page = ChromiumPage(co)
            # Fetch URL and wait for redirection/challenge solving with fast-fail timeout
            page.get(url, timeout=12.0)

            # Fast-fail wait for Turnstile challenge to be solved
            solve_timeout = 8.0
            start_time = time.time()
            while time.time() - start_time < solve_timeout:
                html = page.html
                if not self._is_cloudflare_challenge(html):
                    break
                time.sleep(0.5)

            html = page.html
            if self._is_cloudflare_challenge(html):
                raise TimeoutError("DrissionPage hit Cloudflare challenge timeout.")

            # Trigger lazy-loaded images by scrolling
            logger.info("Scrolling down to trigger lazy loading for %s...", url)
            try:
                last_height = 0
                for _ in range(8):  # Max 8 scrolls
                    page.scroll.to_bottom()
                    time.sleep(1.0)
                    new_height = page.run_js("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
            except Exception as e:
                logger.debug("DrissionPage scroll failed: %s", e)

            html = page.html

            # Extract cookies
            cookies = page.cookies(all_info=True)
            cookies_list = []
            for c in cookies:
                cookies_list.append(
                    {
                        "name": c.get("name"),
                        "value": c.get("value"),
                        "domain": c.get("domain") or host,
                        "path": c.get("path") or "/",
                    }
                )

            return html, cookies_list

        except Exception as e:
            logger.error("DrissionPage request failed: %s", repr(e))
            raise e
        finally:
            if page:
                try:
                    page.quit()
                except Exception:
                    pass

    def _get_with_helium(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using Helium as a browser fallback (supports Firefox if Chrome is missing)."""
        from utils.logger import get_logger

        logger = get_logger(__name__)

        try:
            import helium
        except ImportError as e:
            logger.error("Helium not installed: %s", e)
            raise e

        # Determine GUI platform

        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos
        headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))

        logger.info("Launching Helium for %s (headless=%s)", url, headless_mode)

        # Try start_chrome first, then fall back to start_firefox if chrome isn't installed/working
        started = False
        try:
            logger.info("Helium: Trying Chrome browser...")
            
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            chrome_options = ChromeOptions()
            proxy = self.get_proxy()
            if proxy:
                chrome_options.add_argument(f"--proxy-server={proxy}")
                
            helium.start_chrome(url, headless=headless_mode, options=chrome_options)
            started = True
        except Exception as chrome_err:
            logger.warning(
                "Helium: Chrome browser launch failed: %s. Falling back to Firefox...",
                chrome_err,
            )
            try:
                from selenium.webdriver.firefox.options import Options as FirefoxOptions
                firefox_options = FirefoxOptions()
                proxy = self.get_proxy()
                if proxy:
                    firefox_options.add_argument(f"--proxy-server={proxy}")
                    
                helium.start_firefox(url, headless=headless_mode, options=firefox_options)
                started = True
            except Exception as firefox_err:
                logger.error("Helium: Firefox browser launch failed: %s", firefox_err)
                raise RuntimeError(
                    f"Helium failed to start either Chrome or Firefox: {firefox_err}"
                ) from chrome_err

        try:
            driver = helium.get_driver()
            # Wait for redirection/challenge solving
            solve_timeout = 20.0
            start_time = time.time()
            while time.time() - start_time < solve_timeout:
                html = driver.page_source
                if not self._is_cloudflare_challenge(html):
                    break
                time.sleep(1.0)

            html = driver.page_source
            if self._is_cloudflare_challenge(html):
                raise TimeoutError("Helium hit Cloudflare challenge timeout.")

            logger.info("Scrolling down to trigger lazy loading for %s...", url)
            try:
                last_height = 0
                for _ in range(8):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.0)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
            except Exception as e:
                logger.debug("Helium scroll failed: %s", e)

            html = driver.page_source

            # Extract cookies
            cookies = driver.get_cookies()
            cookies_list = []
            host = self._hostname(url)
            for c in cookies:
                cookies_list.append(
                    {
                        "name": c.get("name"),
                        "value": c.get("value"),
                        "domain": c.get("domain") or host,
                        "path": c.get("path") or "/",
                    }
                )

            return html, cookies_list

        except Exception as e:
            logger.error("Helium request failed: %s", repr(e))
            raise e
        finally:
            if started:
                try:
                    helium.kill_browser()
                except Exception:
                    pass

    def _get_with_uc(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using undetected-chromedriver as the deepest fallback tier."""
        from utils.logger import get_logger

        logger = get_logger(__name__)

        try:
            import undetected_chromedriver as uc
            
            # Patch uc.Chrome.quit to suppress WinError 6 during interpreter shutdown
            if not getattr(uc.Chrome, "_patched_quit", False):
                original_quit = uc.Chrome.quit
                def patched_quit(self):
                    try:
                        original_quit(self)
                    except OSError:
                        pass
                uc.Chrome.quit = patched_quit
                uc.Chrome._patched_quit = True

        except ImportError as e:
            logger.error("undetected-chromedriver not installed: %s", e)
            raise e


        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos
        headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))

        logger.info(
            "Launching undetected-chromedriver for %s (headless=%s)", url, headless_mode
        )
        driver = None
        for attempt in range(2):
            try:
                options = uc.ChromeOptions()
                if headless_mode:
                    options.add_argument("--headless")
                options.add_argument("--disable-gpu")
                
                proxy = self.get_proxy()
                if proxy:
                    options.add_argument(f"--proxy-server={proxy}")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")

                driver = uc.Chrome(options=options, use_subprocess=True, version_main=150)
                break
            except Exception as driver_err:
                if "session not created" in str(driver_err).lower() and attempt == 0:
                    logger.warning("uc.Chrome session creation failed. Retrying initialization...")
                    time.sleep(2)
                    continue
                raise driver_err

        if driver is None:
            raise RuntimeError("Failed to initialize undetected-chromedriver driver instance.")

        try:
            driver.set_page_load_timeout(30)
            driver.get(url)


            # Wait for redirection/challenge solving
            solve_timeout = 25.0
            start_time = time.time()
            capsolver_attempted = False
            while time.time() - start_time < solve_timeout:
                html = driver.page_source
                if not self._is_cloudflare_challenge(html):
                    break
                if self.capsolver_key and not capsolver_attempted:
                    # Attempt Capsolver bypass
                    success = self._solve_cloudflare_capsolver_uc(driver, url)
                    capsolver_attempted = True
                    if success:
                        solve_timeout += 10.0  # Give it extra time to reload
                time.sleep(1.0)

            html = driver.page_source
            if self._is_cloudflare_challenge(html):
                raise TimeoutError(
                    "undetected-chromedriver hit Cloudflare challenge timeout."
                )

            logger.info("Scrolling down to trigger lazy loading for %s...", url)
            try:
                last_height = 0
                for _ in range(8):
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1.0)
                    new_height = driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        break
                    last_height = new_height
            except Exception as e:
                logger.debug("UC scroll failed: %s", e)

            html = driver.page_source

            # Extract cookies
            cookies = driver.get_cookies()
            cookies_list = []
            host = self._hostname(url)
            for c in cookies:
                cookies_list.append(
                    {
                        "name": c.get("name"),
                        "value": c.get("value"),
                        "domain": c.get("domain") or host,
                        "path": c.get("path") or "/",
                    }
                )

            return html, cookies_list

        except Exception as e:
            logger.error("undetected-chromedriver request failed: %s", e)
            raise e
        finally:
            if driver:
                try:
                    driver.quit()
                except Exception:
                    pass

    def _solve_cloudflare_capsolver_uc(self, driver, url: str) -> bool:
        if not self.capsolver_key:
            return False
        import capsolver
        from utils.logger import get_logger
        logger = get_logger(__name__)
        capsolver.api_key = self.capsolver_key
        
        html = driver.page_source
        sitekey = None
        
        # Look for data-sitekey="xxx" or similar Turnstile identifiers
        import re
        match = re.search(r'data-sitekey=["\']([^"\']+)["\']', html)
        if match:
            sitekey = match.group(1)
        if not sitekey:
            match = re.search(r'sitekey:\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if match:
                sitekey = match.group(1)
        
        if not sitekey:
            logger.warning("CapSolver: Cloudflare Turnstile detected, but sitekey not found in HTML.")
            return False
            
        logger.info("CapSolver: Solving Turnstile for sitekey %s...", sitekey)
        try:
            solution = capsolver.solve({
                "type": "AntiCloudflareTask",
                "websiteURL": url,
                "websiteKey": sitekey,
            })
            token = solution.get("token")
            if not token:
                logger.warning("CapSolver: No token returned in solution.")
                return False
                
            logger.info("CapSolver: Got token. Injecting into page...")
            script = f"""
            let input = document.querySelector('[name="cf-turnstile-response"]');
            if (input) {{
                input.value = "{token}";
                let form = input.closest('form');
                if (form) {{
                    form.submit();
                    return true;
                }}
            }}
            
            // Try window callback injection if form not found
            if (window.___grecaptcha_cfg && window.___grecaptcha_cfg.clients) {{
                for (let c in window.___grecaptcha_cfg.clients) {{
                    let client = window.___grecaptcha_cfg.clients[c];
                    for (let k in client) {{
                        if (client[k] && client[k].callback) {{
                            client[k].callback("{token}");
                            return true;
                        }}
                    }}
                }}
            }}
            
            // Try explicit turnstile callback injection
            if (window.turnstile && typeof window.turnstile.getResponse === 'function') {{
                // Unfortunately turnstile doesn't expose a direct trigger, but we can set the input manually
                // and hope the underlying JS picks it up if a form is present.
                let t_input = document.querySelector('input[name="cf-turnstile-response"]');
                if (t_input) {{
                    t_input.value = "{token}";
                }}
            }}
            return false;
            """
            success = driver.execute_script(script)
            if success:
                logger.info("CapSolver: Token injected and form submitted.")
                return True
            else:
                logger.warning("CapSolver: Failed to locate cf-turnstile-response input or form to submit.")
                return False
        except Exception as e:
            logger.error("CapSolver API failed: %s", repr(e))
            return False

    def _get_with_camoufox(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using Camoufox stealth browser with fingerprint & headful escalation tuning."""
        from utils.logger import get_logger
        logger = get_logger(__name__)

        try:
            from camoufox.sync_api import Camoufox
        except ImportError:
            logger.warning("Camoufox library is not installed.")
            raise Exception("Camoufox library is not installed")

        is_windows = sys.platform.startswith("win")
        is_macos = sys.platform == "darwin"
        is_local_gui = is_windows or is_macos
        headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))

        camou_os = "win" if is_windows else ("mac" if is_macos else "lin")

        def _fetch_camou(is_headless: bool) -> tuple[str, list[dict]]:
            logger.info("Launching Camoufox for %s (headless=%s, os=%s)", url, is_headless, camou_os)
            kwargs = {
                "headless": is_headless,
                "os": camou_os,
                "humanize": True,
                "window_size": (1920, 1080),
            }
            with Camoufox(**kwargs) as browser:
                page = browser.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=45000)

                if is_headless and self._is_cloudflare_challenge(page.content()):
                    raise TimeoutError("Camoufox headless hit Cloudflare Turnstile challenge.")

                try:
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    page.wait_for_timeout(2000)
                except Exception:
                    pass

                html = page.content()
                cookies = page.context.cookies()

                cookie_list = []
                host = self._hostname(url)
                for c in cookies:
                    cookie_list.append(
                        {
                            "name": c.get("name"),
                            "value": c.get("value"),
                            "domain": c.get("domain") or host,
                            "path": c.get("path") or "/",
                        }
                    )
                return html, cookie_list

        try:
            return _fetch_camou(headless_mode)
        except Exception as exc:
            if headless_mode and is_local_gui and not FORCE_HEADLESS:
                logger.warning(
                    "\n"
                    "========================================================================\n"
                    "CAMOUFOX HEADLESS WAF CHALLENGE ON: %s\n"
                    "Escalating Camoufox to HEADFUL (visible) mode for 20 seconds.\n"
                    "Please solve/click the Turnstile checkbox if prompted in the window.\n"
                    "========================================================================",
                    url,
                )
                try:
                    return _fetch_camou(False)
                except Exception as headful_exc:
                    logger.error("Camoufox headful escalation failed for %s: %s", url, repr(headful_exc))
                    raise headful_exc
            logger.error("Camoufox request failed: %s", repr(exc))
            raise exc

    def _get_with_flaresolverr(self, url: str) -> tuple[str, list[dict]]:
        """Fetch *url* using FlareSolverr proxy service with session reuse & proxy forwarding."""
        from utils.logger import get_logger
        logger = get_logger(__name__)

        fs_url = FLARESOLVERR_URL or "http://127.0.0.1:8191/v1"

        # 1. Health-check ping if state is unknown
        with self.__class__._flaresolverr_lock:
            if self.__class__._flaresolverr_online is False:
                logger.warning("FlareSolverr service is offline (previous ping failed). Skipping FlareSolverr fallback.")
                raise Exception("FlareSolverr service is offline")

        host = self._hostname(url)
        domain_slug = re.sub(r"[^\w\-]", "_", host)
        session_id = f"session_{domain_slug}"

        proxy = self.get_proxy()
        payload: dict[str, typing.Any] = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
            "session": session_id,
        }
        if proxy:
            payload["proxy"] = {"url": proxy}

        logger.info("Sending request to FlareSolverr at %s for %s (session=%s)", fs_url, url, session_id)

        try:
            with httpx.Client(timeout=65.0) as client:
                # Perform initial health-check if needed
                if self.__class__._flaresolverr_online is None:
                    ping_urls = [fs_url, "http://localhost:8191/v1", "http://127.0.0.1:8191/v1"]
                    ping_success = False
                    active_url = fs_url
                    for p_url in dict.fromkeys(ping_urls):
                        try:
                            base_url = p_url.rsplit("/v1", 1)[0]
                            ping_res = client.get(base_url or p_url, timeout=3.0)
                            ping_res.raise_for_status()
                            ping_success = True
                            active_url = p_url
                            break
                        except Exception:
                            continue

                    if not ping_success:
                        # Attempt to auto-start Docker container if unreachable
                        try:
                            import subprocess
                            logger.info("FlareSolverr unreachable. Attempting background docker start flaresolverr...")
                            subprocess.Popen(
                                ["docker", "start", "flaresolverr"],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL,
                            )
                            time.sleep(3.5)
                            for p_url in dict.fromkeys(ping_urls):
                                try:
                                    base_url = p_url.rsplit("/v1", 1)[0]
                                    ping_res = client.get(base_url or p_url, timeout=3.0)
                                    ping_res.raise_for_status()
                                    ping_success = True
                                    active_url = p_url
                                    break
                                except Exception:
                                    continue
                        except Exception as docker_err:
                            logger.debug("Auto-starting FlareSolverr container failed: %s", docker_err)

                    if ping_success:
                        fs_url = active_url
                        with self.__class__._flaresolverr_lock:
                            self.__class__._flaresolverr_online = True
                    else:
                        with self.__class__._flaresolverr_lock:
                            self.__class__._flaresolverr_online = False
                        logger.warning("FlareSolverr health-check failed at %s. Disabling FlareSolverr.", fs_url)
                        raise Exception("FlareSolverr health-check failed")

                res = client.post(fs_url, json=payload)
                res.raise_for_status()
                data = res.json()

                if data.get("status") == "ok":
                    sol = data.get("solution", {})
                    html = sol.get("response", "")
                    raw_cookies = sol.get("cookies", [])
                    cookie_list = []
                    for c in raw_cookies:
                        cookie_list.append(
                            {
                                "name": c.get("name"),
                                "value": c.get("value"),
                                "domain": c.get("domain") or host,
                                "path": c.get("path") or "/",
                            }
                        )
                    return html, cookie_list
                else:
                    msg = data.get("message", "Unknown FlareSolverr error")
                    logger.warning("FlareSolverr returned status '%s': %s", data.get("status"), msg)
                    raise Exception(f"FlareSolverr error: {msg}")
        except Exception as exc:
            logger.error("FlareSolverr request failed: %s", repr(exc))
            raise exc

    # ------------------------------------------------------------------
    # Crawl4AI browser fallback (runs on the shared background event loop)
    # ------------------------------------------------------------------

    def _get_with_crawl4ai(self, url: str) -> tuple[str, list[dict]] | str:
        """Fetch *url* via headless/headful browser, escalating through two stealth tiers.

        Runs on the shared background asyncio event loop to avoid spawning a
        new event loop and browser process per call.

        Returns the raw HTML string and cookies list on success.
        Raises ``Exception`` if both tiers fail.
        """
        _apply_playwright_channel_patch()

        import crawl4ai.async_webcrawler

        # Disable crawl4ai's built-in block detector — we detect Cloudflare ourselves.
        crawl4ai.async_webcrawler.is_blocked = lambda status_code, html, error_message=None: (False, "")

        from crawl4ai import (
            AsyncWebCrawler,
            BrowserConfig,
            CrawlerRunConfig,
            CacheMode,
            UndetectedAdapter,
        )
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
        from utils.logger import get_logger

        logger = get_logger(__name__)

        async def _run_tier(strategy, run_config) -> tuple[str, list[dict]]:
            async with AsyncWebCrawler(crawler_strategy=strategy) as crawler:
                res = await crawler.arun(url=url, config=run_config)
                if res and res.success:
                    cookies = []
                    try:
                        bm = crawler.crawler_strategy.browser_manager
                        for context in bm.contexts_by_config.values():
                            try:
                                ctx_cookies = await context.cookies()
                                cookies.extend(ctx_cookies)
                            except Exception as exc:
                                logger.debug("Failed to extract cookies from Crawl4AI context: %s", exc)
                    except Exception as exc:
                        logger.debug("Failed to access Crawl4AI browser manager: %s", exc)
                    return res.html, cookies
                raise Exception(res.error_message if res else "Unknown crawler error")

        async def _run_crawler() -> tuple[str, list[dict]]:
            from utils.logger import get_logger

            logger = get_logger(__name__)

            # Determine domain and build persistent profile path
            parsed = urlparse(url)
            host = parsed.netloc or parsed.hostname or ""
            domain_slug = re.sub(r"[^\w\-]", "_", host)
            profile_path = Path("data/profiles") / domain_slug
            profile_path.parent.mkdir(parents=True, exist_ok=True)

            is_windows = sys.platform.startswith("win")
            is_macos = sys.platform == "darwin"
            is_local_gui = is_windows or is_macos
            headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))

            # Load any existing session cookies to seed the browser context
            session_cookies = self.session_manager.load_session(host) or {}
            playwright_cookies = []
            for k, v in session_cookies.items():
                playwright_cookies.append(
                    {"name": k, "value": v, "domain": host, "path": "/"}
                )

            run_config = CrawlerRunConfig(
                word_count_threshold=0,
                cache_mode=CacheMode.BYPASS,
                magic=True,
                simulate_user=True,
                override_navigator=True,
                delay_before_return_html=6.0,
                session_id=f"session_{domain_slug}",
                js_code="""
                const scrollInterval = setInterval(() => {
                    window.scrollTo(0, document.body.scrollHeight);
                }, 1000);
                setTimeout(() => clearInterval(scrollInterval), 5000);
                """
            )

            async def _run_with_chrome_fallback(
                headless: bool, enable_stealth: bool, browser_adapter=None, run_cfg=None
            ) -> tuple[str, list[dict]]:
                proxy_val = self.get_proxy()

                def _make_browser_cfg(channel_opt=None):
                    kwargs = {
                        "browser_type": "chromium",
                        "headless": headless,
                        "verbose": False,
                        "enable_stealth": enable_stealth,
                        "user_agent": _get_platform_user_agent(),
                        "extra_args": ["--disable-gpu"] if headless else [],
                        "user_data_dir": str(profile_path.resolve()),
                        "use_persistent_context": True,
                        "cookies": playwright_cookies,
                    }
                    if channel_opt:
                        kwargs["channel"] = channel_opt
                        kwargs["chrome_channel"] = channel_opt
                    if proxy_val:
                        kwargs["proxy"] = proxy_val
                    return BrowserConfig(**kwargs)

                def _make_strategy(b_cfg):
                    kwargs = {"browser_config": b_cfg}
                    if browser_adapter is not None:
                        kwargs["browser_adapter"] = browser_adapter
                    return AsyncPlaywrightCrawlerStrategy(**kwargs)

                try:
                    cfg = _make_browser_cfg("chrome")
                    strat = _make_strategy(cfg)
                    return await _run_tier(strat, run_cfg)
                except Exception as exc:
                    logger.warning(
                        "Crawl4AI fallback run with channel='chrome' failed: %s. Retrying with default Playwright Chromium...",
                        exc,
                    )
                    cfg_fallback = _make_browser_cfg()
                    strat_fallback = _make_strategy(cfg_fallback)
                    return await _run_tier(strat_fallback, run_cfg)

            # --- Tier 1: Standard stealth Playwright ---
            logger.info(
                "Crawl4AI Fallback: Trying Tier 1 (Standard Stealth) for %s...", url
            )
            try:
                html, cookies = await _run_with_chrome_fallback(
                    headless=headless_mode,
                    enable_stealth=True,
                    browser_adapter=None,
                    run_cfg=run_config,
                )
                if not self._is_blocked_page(html, url):
                    logger.info("Crawl4AI Tier 1 succeeded for %s.", url)
                    return html, cookies
                logger.warning(
                    "Crawl4AI Tier 1 hit a block or challenge for %s. Escalating to Tier 2...",
                    url,
                )
            except Exception as exc:
                logger.warning(
                    "Crawl4AI Tier 1 failed for %s: %s. Escalating to Tier 2...",
                    url,
                    exc,
                )

            # --- Tier 2: UndetectedAdapter (bypasses deep fingerprinting / Turnstile) ---

            is_windows = sys.platform.startswith("win")
            is_macos = sys.platform == "darwin"
            is_local_gui = is_windows or is_macos
            headless_mode = False if STEALTH_HEADFUL else (True if FORCE_HEADLESS else (not is_local_gui))

            if not headless_mode:
                logger.warning(
                    "\n"
                    "========================================================================\n"
                    "CLOUDFLARE TURNSTILE DETECTED ON: %s\n"
                    "Running Browser in HEADFUL (visible) mode for 20 seconds.\n"
                    "Please solve/click the Turnstile checkbox if prompted in the window.\n"
                    "========================================================================",
                    url,
                )
            else:
                logger.info(
                    "CLOUDFLARE TURNSTILE DETECTED ON: %s - Running browser in HEADLESS mode.",
                    url,
                )

            run_config_2 = CrawlerRunConfig(
                word_count_threshold=0,
                cache_mode=CacheMode.BYPASS,
                magic=True,
                simulate_user=True,
                override_navigator=True,
                delay_before_return_html=20.0,  # Give 20s for WAF solve & redirection
                session_id=f"session_{domain_slug}",
                js_code="""
                const scrollInterval = setInterval(() => {
                    window.scrollTo(0, document.body.scrollHeight);
                }, 1000);
                setTimeout(() => clearInterval(scrollInterval), 18000);
                """
            )
            try:
                html, cookies = await _run_with_chrome_fallback(
                    headless=headless_mode,
                    enable_stealth=True,
                    browser_adapter=UndetectedAdapter(),
                    run_cfg=run_config_2,
                )
                if not self._is_blocked_page(html, url):
                    logger.info("Crawl4AI Tier 2 succeeded for %s.", url)
                    return html, cookies
                raise Exception("Crawl4AI Tier 2 hit a block or challenge page.")
            except Exception as exc:
                raise Exception(
                    f"All Crawl4AI fallback tiers failed for {url}: {exc}"
                ) from exc

        # Clean hostname to make a safe path slug
        parsed_url = urlparse(url)
        host = parsed_url.netloc or parsed_url.hostname or ""
        lock = self._fallback_lock_for(host)
        with lock:
            return _run_coroutine_sync(_run_crawler())

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def _execute_fallbacks(
        self, url: str, skip_crawl4ai: bool = False, preferred_engine: str | None = None
    ) -> tuple[str | None, list[dict]]:
        from utils.logger import get_logger
        logger = get_logger(__name__)

        host = self._hostname(url)

        # Check for host engine memory cache if no seed manifest override is provided
        if not preferred_engine:
            with self.__class__._preferred_engine_lock:
                preferred_engine = self.__class__._preferred_engine_by_host.get(host)

        strategy_map = {
            "crawl4ai": ("Crawl4AI", self._get_with_crawl4ai),
            "cheerio": ("Crawlee Cheerio", self._get_with_crawlee_cheerio),
            "drissionpage": ("DrissionPage", self._get_with_drissionpage if ENABLE_DRISSIONPAGE_FALLBACK else None),
            "puppeteer": ("Crawlee Puppeteer", self._get_with_crawlee_puppeteer),
            "helium": ("Helium", self._get_with_helium if ENABLE_HELIUM_FALLBACK else None),
            "uc": ("undetected-chromedriver", self._get_with_uc),
            "camoufox": ("Camoufox", self._get_with_camoufox if ENABLE_CAMOUFOX_FALLBACK else None),
            "flaresolverr": ("FlareSolverr", self._get_with_flaresolverr if ENABLE_FLARESOLVERR_FALLBACK else None),
        }

        default_order = [
            "crawl4ai",
            "cheerio",
            "drissionpage",
            "puppeteer",
            "helium",
            "uc",
            "camoufox",
            "flaresolverr",
        ]

        ordered_keys = []
        if preferred_engine and preferred_engine.lower() in strategy_map:
            pref_key = preferred_engine.lower()
            ordered_keys.append(pref_key)
            for k in default_order:
                if k != pref_key:
                    ordered_keys.append(k)
        else:
            ordered_keys = default_order

        strategies = [strategy_map[k] for k in ordered_keys]

        html_content = None
        browser_cookies = []
        start_time = time.monotonic()
        timeout_budget = 60.0  # 60 seconds total deadline for all fallbacks

        for name, strategy_func in strategies:
            if time.monotonic() - start_time > timeout_budget:
                logger.warning("WAF fallback sequence exceeded 60s total timeout budget for %s.", url)
                break

            if strategy_func is None:
                continue

            if name == "Crawl4AI" and skip_crawl4ai:
                continue

            if name != "Crawl4AI" and "pytest" in sys.modules and not preferred_engine:
                continue

            logger.info("Escalating stealth routing to %s fallback for %s...", name, url)
            try:
                res_val = strategy_func(url)
                if isinstance(res_val, tuple):
                    html_content, browser_cookies = res_val
                else:
                    html_content, browser_cookies = res_val, []

                if html_content and not self._is_blocked_page(html_content, url):
                    # Cache successful engine choice in host memory & increment telemetry counter
                    engine_key = next((k for k, (n, f) in strategy_map.items() if n == name), None)
                    if engine_key:
                        with self.__class__._preferred_engine_lock:
                            self.__class__._preferred_engine_by_host[host] = engine_key
                        with self.__class__._waf_solve_lock:
                            self.__class__._waf_solve_counts[engine_key] = (
                                self.__class__._waf_solve_counts.get(engine_key, 0) + 1
                            )
                    return html_content, browser_cookies
                else:
                    logger.warning("%s returned a blocked or redirected page for %s.", name, url)
                    html_content = None
            except Exception as exc:
                logger.error("%s fallback failed for %s: %s", name, url, repr(exc))
        if html_content is None and ENABLE_FLARESOLVERR_FALLBACK and self.__class__._flaresolverr_online is not False and ("pytest" not in sys.modules or preferred_engine):
            try:
                logger.info("Attempting automatic FlareSolverr Turnstile escalation for %s...", url)
                res_val = self._get_with_flaresolverr(url)
                html_content, browser_cookies = res_val
                if html_content and not self._is_blocked_page(html_content, url):
                    with self.__class__._waf_solve_lock:
                        self.__class__._waf_solve_counts["flaresolverr"] = (
                            self.__class__._waf_solve_counts.get("flaresolverr", 0) + 1
                        )
                    return html_content, browser_cookies
            except Exception as fs_exc:
                logger.debug("Automatic FlareSolverr escalation failed for %s: %s", url, fs_exc)

        return None, []

    @property
    def last_net_latency(self) -> float:
        """Pure network latency (seconds) of the most recent ``get()`` call on this thread.

        Excludes rate-limiter wait time and any jitter sleep.  Returns 0.0 if
        no request has been made yet on the calling thread.
        """
        return getattr(self._thread_local, "net_latency", 0.0)

    def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        preferred_engine: str | None = None,
    ) -> httpx.Response:
        """Fetch *url*, using the disk cache and WAF fallback as needed.

        Retried up to ``DEFAULT_RETRY_ATTEMPTS`` times on transient
        ``httpx.HTTPError`` network errors.  ``ScraperBypassError`` and
        domain-cooldown errors are NOT retried.
        """
        from utils.logger import get_logger

        logger = get_logger(__name__)
        domain = urlparse(url).netloc
        if is_blacklisted(domain):
            raise ScraperBypassError(f"Domain {domain} is blacklisted")

        cookies = self.session_manager.load_session(domain)
        if cookies:
            if headers is None:
                headers = {}
            headers["Cookie"] = "; ".join([f"{k}={v}" for k, v in cookies.items()])

        # 1. Cache
        cached = self._load_cache(url)
        if cached is not None:
            return cached

        # 2. Circuit-breaker: skip cooldown domains immediately
        cd_state = self._cooldown_state_for(url)
        if cd_state.is_cooling_down():
            host = self._hostname(url)
            if cd_state.is_blacklisted:
                raise ScraperBypassError(
                    f"Domain '{host}' is blacklisted due to repeated rate limits or offline failures. Fast-failing {url}."
                )
            remaining = cd_state.cooldown_remaining()
            raise ScraperBypassError(
                f"Domain '{host}' is in 429 cooldown for {remaining:.0f}s more. Skipping {url}."
            )

        # Check if the domain is known to have failed stealth before
        host = self._hostname(url)
        parsed_url = urlparse(url)
        is_robots_txt = parsed_url.path.lower() == "/robots.txt"

        with self._failed_stealth_lock:
            if host in self._stealth_failed_hosts and not is_robots_txt:
                blocked_until = self._stealth_failed_hosts[host]
                if time.time() < blocked_until:
                    remaining = blocked_until - time.time()
                    raise ScraperBypassError(
                        f"Domain '{host}' has previously failed all stealth fallback tiers. "
                        f"Stealth cooldown active for {remaining:.0f}s. Fast-failing {url}."
                    )
                else:
                    del self._stealth_failed_hosts[host]

        # Check if the domain is known to require stealth
        with self._stealth_lock:
            requires_stealth = host in self._stealth_required_hosts

        if requires_stealth and not is_robots_txt:
            from core.filters import looks_like_media

            if not looks_like_media(url):
                logger.info(
                    "Domain '%s' is marked as requiring stealth. Routing directly to Crawl4AI fallback.",
                    host,
                )
                # Apply rate limiting before direct fallback
                self._rate_limiter_for(url).wait()
                html_content, browser_cookies = self._execute_fallbacks(
                    url, preferred_engine=preferred_engine
                )

                if html_content is None:
                    with self._failed_stealth_lock:
                        self._stealth_failed_hosts[host] = time.time() + 1800.0
                    raise ScraperBypassError(
                        f"Failed to fetch {url} via direct browser routing (all fallback browsers failed)."
                    )

                response = httpx.Response(
                    status_code=200,
                    content=html_content.encode("utf-8"),
                    request=httpx.Request("GET", url),
                )
                cd_state.record_success()
                self._store_cache(url, response)

                if browser_cookies:
                    cookies_dict = {c["name"]: c["value"] for c in browser_cookies}
                    existing = self.session_manager.load_session(host) or {}
                    existing.update(cookies_dict)
                    self.session_manager.save_session(host, existing)
                    session = self._session_pool.get_session(host)
                    session.cookies.update(cookies_dict)
                    session.save_to_disk()

                return response

        current_timeout = self.timeout
        session = self._session_pool.get_session(host)

        for attempt in range(1, DEFAULT_RETRY_ATTEMPTS + 1):
            try:
                # 3. Per-domain rate limiting (with jitter) — wait BEFORE measuring
                # network latency so the rate-limiter sleep is excluded from the
                # latency reported to the adaptive concurrency scaler.
                self._rate_limiter_for(url).wait()

                # Record the start of the actual network operation.  Written to a
                # thread-local so concurrent workers do not interfere with each other.
                _net_start = time.monotonic()

                # Merge custom headers if provided
                req_headers = self._headers(url)
                if headers:
                    req_headers.update(headers)

                # Fetch with escalating timeout
                try:
                    response = self.client.get(
                        url,
                        headers=req_headers,
                        cookies=session.cookies,
                        timeout=current_timeout,
                    )
                    response.raise_for_status()
                    self._thread_local.net_latency = time.monotonic() - _net_start
                    session.cookies.update({c.name: c.value for c in response.cookies.jar})
                    session.save_to_disk()
                    if response.cookies:
                        existing = self.session_manager.load_session(host) or {}
                        existing.update({c.name: c.value for c in response.cookies.jar})
                        self.session_manager.save_session(host, existing)
                    cd_state.record_success()
                    self._store_cache(url, response)
                    return response
                except httpx.TimeoutException as exc:
                    logger.warning(
                        "Timeout fetching %s (attempt %d/%d, timeout=%ds).",
                        url,
                        attempt,
                        DEFAULT_RETRY_ATTEMPTS,
                        current_timeout,
                    )
                    current_timeout = min(60.0, current_timeout * 2.0)
                    if attempt < DEFAULT_RETRY_ATTEMPTS:
                        time.sleep(2.0**attempt)
                        continue
                    raise exc

            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code

                if status == 404:
                    raise exc

                if status in {502, 503}:
                    logger.warning(
                        "HTTPStatusError %d fetching %s (attempt %d/%d). Applying exponential backoff...",
                        status,
                        url,
                        attempt,
                        DEFAULT_RETRY_ATTEMPTS,
                    )
                    if attempt < DEFAULT_RETRY_ATTEMPTS:
                        time.sleep(2.0 ** (attempt + 1))
                        continue
                    raise exc

                if status in {403, 401, 429, 412, 406}:
                    # Rotate the session on blocks
                    session.reset_identity()

                    # 4a. Track 429 consecutive hits for circuit-breaker
                    if status == 429:
                        # Adaptive 429 rate limit backoff:
                        # Reduce RPS of the domain by 50% down to a minimum of 0.05
                        limiter = self._rate_limiter_for(url)
                        old_rps = limiter.requests_per_second
                        new_rps = max(0.05, old_rps * 0.5)
                        if new_rps < old_rps:
                            limiter.requests_per_second = new_rps
                            logger.warning(
                                "HTTP 429 received from %s. Dynamically scaling back RPS from %.3f to %.3f.",
                                host,
                                old_rps,
                                new_rps,
                            )

                        cooldown_duration = cd_state.record_429()
                        if cooldown_duration is not None:
                            host = self._hostname(url)
                            logger.warning(
                                "Domain '%s' hit 429 circuit-breaker threshold. "
                                "Entering cooldown for %ds.",
                                host,
                                cooldown_duration,
                            )
                            if cd_state.is_blacklisted:
                                from utils.blacklist import add_to_blacklist

                                add_to_blacklist(host, reason="consecutive_429s")

                    # Skip Crawl4AI fallback for direct media assets and robots.txt
                    from core.filters import looks_like_media

                    if looks_like_media(url) or is_robots_txt:
                        raise exc

                    # --- NEW PHASE 0: curl_cffi TLS Spoofing Fallback ---
                    try:
                        from curl_cffi import requests as c_requests
                        logger.info("Attempting curl_cffi TLS spoofing for %s", url)
                        
                        proxy = self.get_proxy()
                        proxy_dict = {"http": proxy, "https": proxy} if proxy else None
                        impersonate_val: typing.Literal["chrome120"] = "chrome120"
                        c_session = c_requests.Session(
                            impersonate=impersonate_val,
                            proxies=proxy_dict,  # type: ignore[arg-type]
                        )
                        
                        c_req_headers = self._headers(url)
                        if headers:
                            c_req_headers.update(headers)
                        # Add cookies if available
                        if session.cookies:
                            cookie_str = "; ".join([f"{k}={v}" for k, v in session.cookies.items()])
                            c_req_headers["Cookie"] = cookie_str
                            
                        c_resp = c_session.get(url, headers=c_req_headers, timeout=current_timeout)
                        
                        if c_resp.status_code == 200 and not self._is_blocked_page(c_resp.text, url):
                            logger.info("curl_cffi TLS spoofing successfully bypassed WAF for %s.", url)
                            # Convert to httpx.Response
                            response = httpx.Response(
                                status_code=200,
                                content=c_resp.content,
                                request=httpx.Request("GET", url),
                            )
                            
                            cd_state.record_success()
                            self._store_cache(url, response)
                            
                            # Save cookies
                            if c_resp.cookies:
                                cookies_dict = {c.name: c.value for c in c_resp.cookies.jar}
                                session.cookies.update(cookies_dict)
                                session.save_to_disk()
                                existing = self.session_manager.load_session(host) or {}
                                existing.update(cookies_dict)
                                self.session_manager.save_session(host, existing)
                                
                            return response
                        else:
                            logger.info("curl_cffi TLS spoofing still returned block/challenge for %s", url)
                    except Exception as c_exc:
                        logger.warning("curl_cffi fallback failed: %s", c_exc)

                    # --- NEW PHASE 1: Local Cookie Harvesting ---
                    if ENABLE_COOKIE_HARVESTING:
                        logger.info(
                            "Attempting local cookie harvest for domain '%s'", host
                        )
                        harvested_cookies = self._harvest_local_cookies(host)
                        if harvested_cookies:
                            logger.info(
                                "Harvested cookies: %s. Retrying httpx request with harvested cookies.",
                                list(harvested_cookies.keys()),
                            )
                            try:
                                req_headers = self._headers(url)
                                if headers:
                                    req_headers.update(headers)
                                req_headers["Cookie"] = "; ".join(
                                    [f"{k}={v}" for k, v in harvested_cookies.items()]
                                )
                                retry_resp = self.client.get(
                                    url, headers=req_headers, timeout=current_timeout
                                )
                                retry_resp.raise_for_status()
                                # Success!
                                session.cookies.update(harvested_cookies)
                                session.save_to_disk()
                                existing = self.session_manager.load_session(host) or {}
                                existing.update(harvested_cookies)
                                self.session_manager.save_session(host, existing)
                                cd_state.record_success()
                                self._store_cache(url, retry_resp)
                                logger.info(
                                    "Harvested cookies successfully bypassed WAF for %s.",
                                    url,
                                )
                                return retry_resp
                            except Exception as retry_exc:
                                logger.warning(
                                    "Retry with harvested cookies failed: %s", retry_exc
                                )

                    # BROWSER FALLBACK
                    with self.__class__._cf_blocked_lock:
                        cf_blocked = host in self.__class__._cloudflare_blocked_hosts

                    # Try fallbacks
                    logger.warning("GET %s returned %d. Initiating fallback sequence...", url, status)
                    html_content, browser_cookies = self._execute_fallbacks(
                        url, skip_crawl4ai=cf_blocked, preferred_engine=preferred_engine
                    )

                    if html_content is None:
                        with self._failed_stealth_lock:
                            self._stealth_failed_hosts[host] = time.time() + 1800.0
                        if cf_blocked:
                            raise ScraperBypassError(
                                f"Domain '{host}' is Cloudflare-blocked (Turnstile). "
                                f"Skipping all fallback tiers for {url}."
                            )
                        else:
                            raise ScraperBypassError(
                                f"Failed to fetch {url} (status {status}) "
                                f"and Crawl4AI fallback failed: all browser fallbacks failed."
                            ) from exc

                    response = httpx.Response(
                        status_code=200,
                        content=html_content.encode("utf-8"),
                        request=httpx.Request("GET", url),
                    )
                    cd_state.record_success()
                    self._store_cache(url, response)

                    # Mark hostname as requiring stealth
                    host = self._hostname(url)
                    with self._stealth_lock:
                        self._stealth_required_hosts.add(host)

                    if browser_cookies:
                        cookies_dict = {c["name"]: c["value"] for c in browser_cookies}
                        existing = self.session_manager.load_session(host) or {}
                        existing.update(cookies_dict)
                        self.session_manager.save_session(host, existing)
                        session.cookies.update(cookies_dict)
                        session.save_to_disk()

                    return response

                logger.warning(
                    "HTTPStatusError %d fetching %s (attempt %d/%d).",
                    status,
                    url,
                    attempt,
                    DEFAULT_RETRY_ATTEMPTS,
                )
                if attempt < DEFAULT_RETRY_ATTEMPTS:
                    time.sleep(2.0**attempt)
                    continue
                raise exc

            except httpx.HTTPError as exc:
                logger.warning(
                    "HTTPError fetching %s (attempt %d/%d): %s",
                    url,
                    attempt,
                    DEFAULT_RETRY_ATTEMPTS,
                    exc,
                )
                if attempt < DEFAULT_RETRY_ATTEMPTS:
                    time.sleep(2.0**attempt)
                    continue

                cooldown_duration = cd_state.record_failure()
                if cooldown_duration is not None:
                    host = self._hostname(url)
                    logger.warning(
                        "Domain '%s' hit connection/timeout failure threshold. "
                        "Entering cooldown for %ds.",
                        host,
                        cooldown_duration,
                    )
                    if cd_state.is_blacklisted:
                        from utils.blacklist import add_to_blacklist

                        add_to_blacklist(host, reason="consecutive_failures")
                raise exc

        raise ScraperBypassError(f"Failed to fetch {url}: retry limit reached")
