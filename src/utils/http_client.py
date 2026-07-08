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
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

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
)
from utils.rate_limiter import RateLimiter


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
        self.consecutive_failures: int = 0    # consecutive timeouts or connection failures
        self.cooldown_count: int = 0          # how many cooldowns have been triggered
        self.cooldown_until: float = 0.0      # monotonic timestamp

    def record_429(self) -> float | None:
        """Increment the 429 counter.  Returns cooldown duration if threshold crossed, else None."""
        with self._lock:
            self.consecutive_429s += 1
            if self.consecutive_429s >= DOMAIN_COOLDOWN_THRESHOLD:
                duration = DOMAIN_COOLDOWN_SECONDS[
                    min(self.cooldown_count, len(DOMAIN_COOLDOWN_SECONDS) - 1)
                ]
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
            if self.consecutive_failures >= 3:  # Cooldown after 3 consecutive timeouts/connect errors
                duration = DOMAIN_COOLDOWN_SECONDS[
                    min(self.cooldown_count, len(DOMAIN_COOLDOWN_SECONDS) - 1)
                ]
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
            return time.monotonic() < self.cooldown_until

    def cooldown_remaining(self) -> float:
        with self._lock:
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
        # Convert seconds_per_request (delays) to requests_per_second (RPS)
        converted_delays = {}
        if domain_delays:
            for host, delay in domain_delays.items():
                if delay > 0:
                    converted_delays[host] = 1.0 / delay
        # Merged overrides: CLI-supplied > config defaults
        self._domain_rps_overrides: dict[str, float] = {**DOMAIN_REQUESTS_PER_SECOND, **converted_delays}
        # Per-hostname RateLimiter (lazy-created)
        self._rate_limiters: dict[str, RateLimiter] = {}
        self._rl_lock = threading.Lock()
        # Per-hostname 429 circuit-breaker state (lazy-created)
        self._cooldown_states: dict[str, _DomainCooldownState] = {}
        self._cd_lock = threading.Lock()
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
                self._rate_limiters[host] = RateLimiter(rps, jitter=RATE_LIMIT_JITTER_SECONDS)
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

    def _headers(self) -> dict[str, str]:
        """Return a request header dict with a randomly rotated User-Agent."""
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
        return httpx.Response(status_code=200, text=cache_path.read_text(encoding="utf-8"))

    def _store_cache(self, url: str, response: httpx.Response) -> None:
        """Persist a text/HTML/JSON response body to disk."""
        content_type = response.headers.get("content-type", "")
        if "text" not in content_type and "json" not in content_type and "xml" not in content_type:
            return
        self._cache_path(url).write_text(response.text, encoding="utf-8")

    # ------------------------------------------------------------------
    # Cloudflare challenge detection
    # ------------------------------------------------------------------

    def _is_cloudflare_challenge(self, html: str) -> bool:
        """Return True if the HTML is a Cloudflare interstitial challenge page."""
        if not html:
            return False
        title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip().lower()
            if "just a moment" in title or "checking your browser" in title or "attention required" in title:
                return True
        lower_html = html.lower()
        if "challenges.cloudflare.com" in lower_html or "cf-challenge" in lower_html:
            if "just a moment" in lower_html or "please enable javascript" in lower_html:
                return True
        return False

    # ------------------------------------------------------------------
    # Crawl4AI browser fallback (runs on the shared background event loop)
    # ------------------------------------------------------------------

    def _get_with_crawl4ai(self, url: str) -> str:
        """Fetch *url* via headless browser, escalating through two stealth tiers.

        Runs on the shared background asyncio event loop to avoid spawning a
        new event loop and browser process per call.

        Returns the raw HTML string on success.
        Raises ``Exception`` if both tiers fail.
        """
        import crawl4ai.async_webcrawler

        # Disable crawl4ai's built-in block detector — we detect Cloudflare ourselves.
        crawl4ai.async_webcrawler.is_blocked = lambda status_code, html: (False, "")

        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode, UndetectedAdapter
        from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy

        async def _run_tier(strategy, run_config) -> str:
            async with AsyncWebCrawler(crawler_strategy=strategy) as crawler:
                res = await crawler.arun(url=url, config=run_config)
                if res and res.success:
                    return res.html
                raise Exception(res.error_message if res else "Unknown crawler error")

        async def _run_crawler() -> str:
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
            logger.info("Crawl4AI Fallback: Trying Tier 1 (Standard Stealth) for %s...", url)
            browser_cfg_1 = BrowserConfig(
                headless=True,
                verbose=False,
                enable_stealth=True,
                extra_args=["--disable-gpu"],
            )
            strategy_1 = AsyncPlaywrightCrawlerStrategy(browser_config=browser_cfg_1)
            try:
                html = await _run_tier(strategy_1, run_config)
                if not self._is_cloudflare_challenge(html):
                    logger.info("Crawl4AI Tier 1 succeeded for %s.", url)
                    return html
                logger.warning("Crawl4AI Tier 1 hit Cloudflare challenge for %s. Escalating to Tier 2...", url)
            except Exception as exc:
                logger.warning("Crawl4AI Tier 1 failed for %s: %s. Escalating to Tier 2...", url, exc)

            # --- Tier 2: UndetectedAdapter (bypasses deep fingerprinting / Turnstile) ---
            browser_cfg_2 = BrowserConfig(
                headless=True,
                verbose=False,
                enable_stealth=False,
                extra_args=["--disable-gpu"],
            )
            strategy_2 = AsyncPlaywrightCrawlerStrategy(
                browser_config=browser_cfg_2,
                browser_adapter=UndetectedAdapter(),
            )
            try:
                html = await _run_tier(strategy_2, run_config)
                if not self._is_cloudflare_challenge(html):
                    logger.info("Crawl4AI Tier 2 succeeded for %s.", url)
                    return html
                raise Exception("Crawl4AI Tier 2 hit Cloudflare challenge.")
            except Exception as exc:
                raise Exception(f"All Crawl4AI fallback tiers failed for {url}: {exc}") from exc

        return _run_coroutine_sync(_run_crawler())

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @retry(
        stop=stop_after_attempt(DEFAULT_RETRY_ATTEMPTS),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.HTTPError),
        reraise=True,
    )
    def get(self, url: str, headers: dict[str, str] | None = None) -> httpx.Response:
        """Fetch *url*, using the disk cache and WAF fallback as needed.

        Retried up to ``DEFAULT_RETRY_ATTEMPTS`` times on transient
        ``httpx.HTTPError`` network errors.  ``ScraperBypassError`` and
        domain-cooldown errors are NOT retried.
        """
        from utils.logger import get_logger
        logger = get_logger(__name__)

        # 1. Cache
        cached = self._load_cache(url)
        if cached is not None:
            return cached

        # 2. Circuit-breaker: skip cooldown domains immediately
        cd_state = self._cooldown_state_for(url)
        if cd_state.is_cooling_down():
            remaining = cd_state.cooldown_remaining()
            host = self._hostname(url)
            raise ScraperBypassError(
                f"Domain '{host}' is in 429 cooldown for {remaining:.0f}s more. Skipping {url}."
            )

        # Check if the domain is known to require stealth
        host = self._hostname(url)
        with self._stealth_lock:
            requires_stealth = host in self._stealth_required_hosts

        if requires_stealth:
            from core.filters import looks_like_media
            if not looks_like_media(url):
                logger.info("Domain '%s' is marked as requiring stealth. Routing directly to Crawl4AI fallback.", host)
                # Apply rate limiting before direct fallback
                self._rate_limiter_for(url).wait()
                try:
                    html_content = self._get_with_crawl4ai(url)
                    response = httpx.Response(
                        status_code=200,
                        content=html_content.encode("utf-8"),
                        request=httpx.Request("GET", url),
                    )
                    cd_state.record_success()
                    self._store_cache(url, response)
                    return response
                except Exception as crawl_exc:
                    logger.error("Direct Crawl4AI fallback failed for %s: %s", url, crawl_exc)
                    raise ScraperBypassError(
                        f"Failed to fetch {url} via direct Crawl4AI routing: {crawl_exc}"
                    ) from crawl_exc

        # 3. Per-domain rate limiting (with jitter)
        self._rate_limiter_for(url).wait()

        # Merge custom headers if provided
        req_headers = self._headers()
        if headers:
            req_headers.update(headers)

        try:
            response = self.client.get(url, headers=req_headers)
            response.raise_for_status()
            cd_state.record_success()
            self._store_cache(url, response)
            return response

        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code

            if status in {403, 401, 429}:
                # 4a. Track 429 consecutive hits for circuit-breaker
                if status == 429:
                    cooldown_duration = cd_state.record_429()
                    if cooldown_duration is not None:
                        host = self._hostname(url)
                        logger.warning(
                            "Domain '%s' hit 429 circuit-breaker threshold. "
                            "Entering cooldown for %ds.",
                            host,
                            cooldown_duration,
                        )

                # Skip Crawl4AI fallback for direct media assets
                from core.filters import looks_like_media
                if looks_like_media(url):
                    raise exc

                logger.warning("GET %s returned %d. Falling back to Crawl4AI...", url, status)

                # 4b. Browser fallback
                try:
                    html_content = self._get_with_crawl4ai(url)
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
                        
                    return response
                except Exception as crawl_exc:
                    logger.error("Crawl4AI fallback failed for %s: %s", url, crawl_exc)
                    raise ScraperBypassError(
                        f"Failed to fetch {url} (status {status}) "
                        f"and Crawl4AI fallback failed: {crawl_exc}"
                    ) from exc

            raise exc

        except httpx.HTTPError as exc:
            # Handle other HTTP errors like read timeouts, connection errors
            cooldown_duration = cd_state.record_failure()
            if cooldown_duration is not None:
                host = self._hostname(url)
                logger.warning(
                    "Domain '%s' hit connection/timeout failure threshold. "
                    "Entering cooldown for %ds.",
                    host,
                    cooldown_duration,
                )
            raise exc
