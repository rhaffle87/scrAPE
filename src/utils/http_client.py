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

# Tenacity imports removed in favor of internal escalative retries

from config import (
    CACHE_DIR,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_REQUESTS_PER_SECOND,
    DEFAULT_RETRY_ATTEMPTS,
    DEFAULT_TIMEOUT_SECONDS,
    DOMAIN_COOLDOWN_SECONDS,
    DOMAIN_COOLDOWN_THRESHOLD,
    DOMAIN_REQUESTS_PER_SECOND,
    RATE_LIMIT_JITTER_SECONDS,
    USER_AGENTS,
    REFERER_OVERRIDES,
)
from utils.rate_limiter import RateLimiter
from utils.session_pool import SessionPool
from utils.blacklist import is_blacklisted
from utils.session import SessionManager



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

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        domain_delays: dict[str, float] | None = None,
    ) -> None:
        """
        Args:
            timeout: Per-request timeout in seconds.
            domain_delays: Optional ``{hostname: seconds_per_request}`` overrides
                           that take priority over ``DOMAIN_REQUESTS_PER_SECOND``.
        """
        self.timeout = timeout
        self.client = httpx.Client(timeout=timeout, follow_redirects=True)
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
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

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
            status_code=200, text=cache_path.read_text(encoding="utf-8")
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
        if "challenges.cloudflare.com" in lower_html or "cf-challenge" in lower_html:
            if (
                "just a moment" in lower_html
                or "please enable javascript" in lower_html
            ):
                return True
        return False

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
        import crawl4ai.async_webcrawler

        # Disable crawl4ai's built-in block detector — we detect Cloudflare ourselves.
        crawl4ai.async_webcrawler.is_blocked = lambda status_code, html: (False, "")

        from crawl4ai import (
            AsyncWebCrawler,
            BrowserConfig,
            CrawlerRunConfig,
            CacheMode,
            UndetectedAdapter,
        )
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

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
                            except Exception:
                                pass
                    except Exception:
                        pass
                    return res.html, cookies
                raise Exception(res.error_message if res else "Unknown crawler error")

        async def _run_crawler() -> tuple[str, list[dict]]:
            from utils.logger import get_logger

            logger = get_logger(__name__)

            run_config = CrawlerRunConfig(
                word_count_threshold=0,
                cache_mode=CacheMode.BYPASS,
                magic=True,
                simulate_user=True,
                override_navigator=True,
                delay_before_return_html=5.0,
            )

            # --- Tier 1: Standard stealth Playwright ---
            logger.info(
                "Crawl4AI Fallback: Trying Tier 1 (Standard Stealth) for %s...", url
            )
            browser_cfg_1 = BrowserConfig(
                headless=True,
                verbose=False,
                enable_stealth=True,
                extra_args=["--disable-gpu"],
            )
            strategy_1 = AsyncPlaywrightCrawlerStrategy(browser_config=browser_cfg_1)
            try:
                html, cookies = await _run_tier(strategy_1, run_config)
                if not self._is_cloudflare_challenge(html):
                    logger.info("Crawl4AI Tier 1 succeeded for %s.", url)
                    return html, cookies
                logger.warning(
                    "Crawl4AI Tier 1 hit Cloudflare challenge for %s. Escalating to Tier 2...",
                    url,
                )
            except Exception as exc:
                logger.warning(
                    "Crawl4AI Tier 1 failed for %s: %s. Escalating to Tier 2...",
                    url,
                    exc,
                )

            # --- Tier 2: UndetectedAdapter (bypasses deep fingerprinting / Turnstile) ---
            import sys
            is_windows = sys.platform.startswith("win")
            is_macos = sys.platform == "darwin"
            is_local_gui = is_windows or is_macos

            if is_local_gui:
                logger.warning(
                    "\n"
                    "========================================================================\n"
                    "CLOUDFLARE TURNSTILE DETECTED ON: %s\n"
                    "Running Browser in HEADFUL (visible) mode for 20 seconds.\n"
                    "Please solve/click the Turnstile checkbox if prompted in the window.\n"
                    "========================================================================",
                    url
                )

            browser_cfg_2 = BrowserConfig(
                headless=not is_local_gui,
                verbose=False,
                enable_stealth=False,
                extra_args=["--disable-gpu"],
            )
            strategy_2 = AsyncPlaywrightCrawlerStrategy(
                browser_config=browser_cfg_2,
                browser_adapter=UndetectedAdapter(),
            )
            run_config_2 = CrawlerRunConfig(
                word_count_threshold=0,
                cache_mode=CacheMode.BYPASS,
                magic=True,
                simulate_user=True,
                override_navigator=True,
                delay_before_return_html=20.0,  # Give 20s for WAF solve & redirection
            )
            try:
                html, cookies = await _run_tier(strategy_2, run_config_2)
                if not self._is_cloudflare_challenge(html):
                    logger.info("Crawl4AI Tier 2 succeeded for %s.", url)
                    return html, cookies
                raise Exception("Crawl4AI Tier 2 hit Cloudflare challenge.")
            except Exception as exc:
                raise Exception(
                    f"All Crawl4AI fallback tiers failed for {url}: {exc}"
                ) from exc

        return _run_coroutine_sync(_run_crawler())

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def get(self, url: str, headers: dict[str, str] | None = None) -> httpx.Response:
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
            if headers is None: headers = {}
            headers['Cookie'] = '; '.join([f'{k}={v}' for k, v in cookies.items()])

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
                try:
                    res_val = self._get_with_crawl4ai(url)
                    if isinstance(res_val, tuple):
                        html_content, browser_cookies = res_val
                    else:
                        html_content, browser_cookies = res_val, []

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

                    return response
                except Exception as crawl_exc:
                    logger.error(
                        "Direct Crawl4AI fallback failed for %s: %s", url, crawl_exc
                    )
                    with self._failed_stealth_lock:
                        self._stealth_failed_hosts[host] = time.time() + 1800.0
                    raise ScraperBypassError(
                        f"Failed to fetch {url} via direct Crawl4AI routing: {crawl_exc}"
                    ) from crawl_exc

        current_timeout = self.timeout
        session = self._session_pool.get_session(host)

        for attempt in range(1, DEFAULT_RETRY_ATTEMPTS + 1):
            try:
                # 3. Per-domain rate limiting (with jitter)
                self._rate_limiter_for(url).wait()

                # Merge custom headers if provided
                req_headers = self._headers(url)
                if headers:
                    req_headers.update(headers)

                # Fetch with escalating timeout
                try:
                    response = self.client.get(
                        url, headers=req_headers, cookies=session.cookies, timeout=current_timeout
                    )
                    response.raise_for_status()
                    session.cookies.update(response.cookies)
                    session.save_to_disk()
                    if response.cookies:
                        existing = self.session_manager.load_session(host) or {}
                        existing.update(dict(response.cookies.items()))
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

                if status in {403, 401, 429}:
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

                    logger.warning(
                        "GET %s returned %d. Falling back to Crawl4AI...", url, status
                    )

                    # 4b. Browser fallback
                    try:
                        res_val = self._get_with_crawl4ai(url)
                        if isinstance(res_val, tuple):
                            html_content, browser_cookies = res_val
                        else:
                            html_content, browser_cookies = res_val, []

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

                        return response
                    except Exception as crawl_exc:
                        logger.error(
                            "Crawl4AI fallback failed for %s: %s", url, crawl_exc
                        )
                        with self._failed_stealth_lock:
                            self._stealth_failed_hosts[host] = time.time() + 1800.0
                        raise ScraperBypassError(
                            f"Failed to fetch {url} (status {status}) "
                            f"and Crawl4AI fallback failed: {crawl_exc}"
                        ) from exc

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
