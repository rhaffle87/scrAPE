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
import threading
import time
from pathlib import Path
from urllib.parse import urlparse
import httpx
from typing import Any, ClassVar

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
    PREFERRED_ENGINES,
)
from network.browser_client import BrowserClientMixin
from network.rate_limiter import RateLimiter
from network.session_pool import SessionPool
from common.blacklist import is_blacklisted
from network.session import SessionManager
from network.stealth_pipeline import StealthTierHealthManager
from monitoring.logger import get_logger

logger = get_logger(__name__)


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
        self.total_429s: int = 0  # cumulative 429s for adaptive jitter scaling

    def adaptive_jitter(self) -> float:
        """Return a scaled jitter ceiling based on cumulative 429 pressure.

        Formula: ``min(RATE_LIMIT_JITTER_SECONDS + (total_429s * 0.1), 2.0)``
        - Baseline: 0.4 s (zero 429s observed).
        - Grows +0.1 s per 429 hit.
        - Hard-capped at 2.0 s to prevent crawl stalls.
        """
        return min(RATE_LIMIT_JITTER_SECONDS + self.total_429s * 0.1, 2.0)

    def record_429(self) -> float | None:
        """Increment the 429 counter.  Returns cooldown duration if threshold crossed, else None."""
        with self._lock:
            self.total_429s += 1
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






__all__ = [
    "HttpClient",
    "ScraperBypassError",
    "StealthTierHealthManager",
    "normalise_url",
]


# ---------------------------------------------------------------------------
# HttpClient
# ---------------------------------------------------------------------------


class HttpClient(BrowserClientMixin):
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
    _login_locked_hosts: set[str] = set()
    _login_locked_lock = threading.Lock()
    _preferred_engine_by_host: dict[str, str] = PREFERRED_ENGINES.copy()
    _preferred_engine_lock = threading.Lock()
    _flaresolverr_online: ClassVar[bool | None] = None
    _flaresolverr_lock: ClassVar[threading.Lock] = threading.Lock()
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

    _tls_impersonate_map: dict[str, str] = {}
    _tls_impersonate_loaded: bool = False
    _tls_impersonate_lock = threading.Lock()

    @classmethod
    def get_tls_impersonate(cls, domain: str) -> str:
        """Return the configured curl_cffi TLS impersonate browser profile for *domain*.

        Defaults to 'chrome120' if no explicit profile is configured in data/domain_config.json.
        """
        import json

        with cls._tls_impersonate_lock:
            if not cls._tls_impersonate_loaded:
                config_path = Path("data/domain_config.json")
                if config_path.exists():
                    try:
                        cfg = json.loads(config_path.read_text(encoding="utf-8"))
                        cls._tls_impersonate_map = {
                            k.lower(): str(v)
                            for k, v in cfg.get("tls_impersonate", {}).items()
                        }
                    except Exception as exc:
                        logger.warning("Failed to load tls_impersonate from domain_config.json: %s", exc)
                cls._tls_impersonate_loaded = True

        domain_clean = domain.lower().strip()
        for d_key, profile in cls._tls_impersonate_map.items():
            if d_key in domain_clean:
                return profile
        return "chrome120"


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

    @classmethod
    def register_login_locked(cls, hostname: str) -> None:
        """Mark *hostname* as login-locked (requires authentication).

        When marked, the client will immediately fast-fail requests to this hostname
        to avoid infinite redirect loops or captcha loops on a login wall.
        """
        with cls._login_locked_lock:
            cls._login_locked_hosts.add(hostname.lower())

    @classmethod
    def is_login_locked(cls, hostname: str) -> bool:
        with cls._login_locked_lock:
            return hostname.lower() in cls._login_locked_hosts

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        domain_delays: dict[str, float] | None = None,
        proxy: str | None = None,
        proxy_list: str | None = None,
        captcha_provider: str | None = None,
        captcha_key: str | None = None,
        max_captcha_spend: float | None = None,
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
        self.captcha_provider = captcha_provider
        self.captcha_key = captcha_key
        self.max_captcha_spend: float = 0.0 if max_captcha_spend is None else max_captcha_spend
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
        client_kwargs: dict[str, Any] = {"timeout": timeout, "follow_redirects": True}
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
        from network.stealth_pipeline import StealthPipeline
        self.stealth_pipeline = StealthPipeline()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        # Thread-local storage: tracks the pure *network* latency for the most
        # recent get() call on this thread (excludes rate-limiter sleep time).
        # The engine's adaptive concurrency scaler reads this to avoid penalising
        # all domains when one slow domain is simply waiting for its rate limit.
        # thread-local storage tracking
        self._thread_local = threading.local()

        # Run automated cleanup for old persistent browser profiles
        self._cleanup_stale_profiles()



    # ------------------------------------------------------------------
    # Proxy Management
    # ------------------------------------------------------------------
    def get_proxy(self) -> str | None:
        with self._proxy_lock:
            if not self.proxy_list:
                return None
            from network.proxy_manager import ProxyPoolManager

            pool = ProxyPoolManager.get_instance()
            pool.set_proxies(self.proxy_list)
            best = pool.get_best_proxy()
            return best or self.proxy_list[self.current_proxy_index]

    def rotate_proxy(self) -> str | None:
        with self._proxy_lock:
            if not self.proxy_list:
                return None
            from network.proxy_manager import ProxyPoolManager

            pool = ProxyPoolManager.get_instance()
            pool.set_proxies(self.proxy_list)
            current = self.proxy_list[self.current_proxy_index]
            pool.record_proxy_failure(current)
            pool.quarantine_proxy(current, duration_s=60.0)

            self.current_proxy_index = (self.current_proxy_index + 1) % len(
                self.proxy_list
            )
            new_proxy = (
                pool.get_best_proxy() or self.proxy_list[self.current_proxy_index]
            )

            # Recreate httpx client with new proxy
            self.client = httpx.Client(
                timeout=self.timeout, follow_redirects=True, proxy=new_proxy
            )
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
            # Update live jitter from adaptive 429-pressure scaling
            with self._cd_lock:
                cd_state = self._cooldown_states.get(host)
            if cd_state is not None:
                self._rate_limiters[host].jitter = cd_state.adaptive_jitter()
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



        # Note: All _get_with_* browser fallback methods (Crawlee, DrissionPage, Helium,
    # UC, Camoufox, Nodriver, FlareSolverr, Crawl4AI) are inherited from BrowserClientMixin
    # in src/network/browser_client.py.

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------


    @property
    def last_net_latency(self) -> float:
        """Pure network latency (seconds) of the most recent ``get()`` call on this thread.

        Excludes rate-limiter wait time and any jitter sleep.  Returns 0.0 if
        no request has been made yet on the calling thread.
        """
        return getattr(self._thread_local, "net_latency", 0.0)

    def _is_domain_cloudflare_marked(self, host: str) -> bool:
        """Return True if host is configured with cloudflare: true in domain_config.json."""
        try:
            from core.managers import DomainRulesManager
            dm = DomainRulesManager()
            cfg = dm._get_config()
            domain_cfg = cfg.get("domain_handlers", {}).get(host, {})
            return bool(domain_cfg.get("cloudflare", False))
        except Exception:
            return False

    def get(
        self,
        url: str,
        headers: dict[str, str] | None = None,
        preferred_engine: str | None = None,
        timeout: float | None = None,
        skip_httpx: bool = False,
    ) -> httpx.Response:
        """Fetch *url*, using the disk cache and WAF fallback as needed.

        Retried up to ``DEFAULT_RETRY_ATTEMPTS`` times on transient
        ``httpx.HTTPError`` network errors.  ``ScraperBypassError`` and
        domain-cooldown errors are NOT retried.
        """
        from monitoring.logger import get_logger

        logger = get_logger(__name__)
        domain = urlparse(url).netloc
        if is_blacklisted(domain):
            raise ScraperBypassError(f"Domain {domain} is blacklisted")
            
        if self.is_login_locked(domain):
            raise ScraperBypassError(f"Domain {domain} is locked behind a login wall")

        cookies = self.session_manager.load_session(domain)
        if cookies:
            if headers is None:
                headers = {}
            if isinstance(cookies, list):
                cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies if isinstance(c, dict) and "name" in c and "value" in c])
            elif isinstance(cookies, dict):
                cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            else:
                cookie_str = ""
            if cookie_str:
                headers["Cookie"] = cookie_str

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
        from config import STEALTH_REQUIRED_DOMAINS

        with self._stealth_lock:
            requires_stealth = (
                skip_httpx
                or (host in self._stealth_required_hosts)
                or (host in STEALTH_REQUIRED_DOMAINS)
                or self._is_domain_cloudflare_marked(host)
            )

        if requires_stealth and not is_robots_txt:
            from core.filters import looks_like_media

            if not looks_like_media(url):
                logger.info(
                    "Domain '%s' requires direct stealth routing. Directing to WAF pipeline.",
                    host,
                )
                # Apply rate limiting before direct fallback
                self._rate_limiter_for(url).wait()
                html_content, browser_cookies = self._execute_fallbacks(
                    url, skip_httpx=skip_httpx, preferred_engine=preferred_engine
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
                    cookies_dict = {c["name"]: c["value"] for c in browser_cookies if isinstance(c, dict) and "name" in c and "value" in c}
                    existing = self.session_manager.load_session(host) or {}
                    existing.update(cookies_dict)
                    self.session_manager.save_session(host, existing)
                    session = self._session_pool.get_session(host)
                    session.cookies.update(cookies_dict)
                    session.save_to_disk()

                return response

        current_timeout = timeout if timeout is not None else self.timeout
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

                if session.cookies:
                    self.client.cookies.update(session.cookies)
                try:
                    response = self.client.get(
                        url,
                        headers=req_headers,
                        timeout=current_timeout,
                        follow_redirects=True,
                    )
                    from config import EMPTY_SEARCH_REDIRECTS
                    if host in EMPTY_SEARCH_REDIRECTS:
                        for redirect_pattern in EMPTY_SEARCH_REDIRECTS[host]:
                            if redirect_pattern in str(response.url):
                                raise ScraperBypassError(f"Redirected to empty search pattern '{redirect_pattern}'")
                    
                    _parsed_redirect = urlparse(str(response.url))
                    _redirect_netloc = _parsed_redirect.netloc.lower()
                    _redirect_path = _parsed_redirect.path.lower()
                    _is_login_wall = (
                        _redirect_path.startswith("/login")
                        or _redirect_path.startswith("/auth")
                        or _redirect_path.startswith("/signin")
                        or _redirect_path.startswith("/signup")
                        or _redirect_netloc == "accounts.google.com"
                        or _redirect_netloc.endswith(".accounts.google.com")
                    )
                    if _is_login_wall:
                        HttpClient.register_login_locked(host)
                        raise ScraperBypassError(f"Redirected to login wall: {response.url}")
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
                    # Rotate the session and evict disk session cache on auth blocks
                    session.reset_identity()
                    if status in {401, 403}:
                        self.session_manager.evict_session(host)
                    
                    if status in {403, 429}:
                        logger.warning("HTTP %d received from %s. Immediately rotating proxy and retrying...", status, host)
                        from network.proxy_manager import ProxyPoolManager
                        pool = ProxyPoolManager.get_instance()
                        pool.clear_domain_binding(host)
                        self.rotate_proxy()
                        if attempt < DEFAULT_RETRY_ATTEMPTS:
                            continue

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
                                from common.blacklist import add_to_blacklist

                                add_to_blacklist(host, reason="consecutive_429s")

                    # Skip Crawl4AI fallback for direct media assets and robots.txt
                    from core.filters import looks_like_media

                    if looks_like_media(url) or is_robots_txt:
                        raise exc

                    # Phase 0: curl_cffi TLS spoofing fallback
                    cffi_resp = self._try_curl_cffi_fallback(
                        url, headers=headers, timeout=current_timeout, skip_httpx=skip_httpx
                    )
                    if cffi_resp is not None:
                        cd_state.record_success()
                        self._store_cache(url, cffi_resp)
                        return cffi_resp

                    # Phase 1: Local cookie harvesting fallback
                    harvest_resp = self._try_cookie_harvest_fallback(
                        url, headers=headers, timeout=current_timeout
                    )
                    if harvest_resp is not None:
                        cd_state.record_success()
                        self._store_cache(url, harvest_resp)
                        return harvest_resp


                    # BROWSER FALLBACK
                    with self.__class__._cf_blocked_lock:
                        cf_blocked = host in self.__class__._cloudflare_blocked_hosts

                    # Try fallbacks
                    logger.warning("GET %s returned %d. Initiating fallback sequence...", url, status)
                    html_content, browser_cookies = self._execute_fallbacks(
                        url, skip_httpx=True, preferred_engine=preferred_engine
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
                        try:
                            self.session_manager.save_session(host, browser_cookies)
                            cookies_dict = {}
                            if isinstance(browser_cookies, list):
                                cookies_dict = {c["name"]: c["value"] for c in browser_cookies if isinstance(c, dict) and "name" in c and "value" in c}
                            elif isinstance(browser_cookies, dict):
                                cookies_dict = browser_cookies
                            if cookies_dict:
                                session.cookies.update(cookies_dict)
                                session.save_to_disk()
                                for ck, cv in cookies_dict.items():
                                    self.client.cookies.set(ck, cv, domain=host)
                        except Exception as cookie_err:
                            logger.warning("Failed updating session cookies for %s: %s", host, cookie_err)

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
                if "CERTIFICATE_VERIFY_FAILED" in str(exc) or "certificate verify failed" in str(exc):
                    logger.warning("SSL certificate verification failed for %s. Retrying with verify=False fallback...", url)
                    try:
                        import urllib3
                        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                        ssl_headers = self._headers(url)
                        if headers:
                            ssl_headers.update(headers)
                        with httpx.Client(verify=False, follow_redirects=True, timeout=current_timeout) as unverified_client:  # nosec B501
                            resp = unverified_client.get(url, headers=ssl_headers)
                            if resp.status_code == 200:
                                logger.info("Unverified SSL fallback succeeded for %s.", url)
                                cd_state.record_success()
                                self._store_cache(url, resp)
                                return resp
                    except Exception as unverify_err:
                        logger.warning("Unverified SSL fallback failed for %s: %s", url, unverify_err)

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
                        from common.blacklist import add_to_blacklist

                        add_to_blacklist(host, reason="consecutive_failures")
                raise exc

        raise ScraperBypassError(f"Failed to fetch {url}: retry limit reached")
