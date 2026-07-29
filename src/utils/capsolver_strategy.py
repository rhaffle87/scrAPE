"""
capsolver_strategy.py — CapSolver Turnstile / reCAPTCHA / hCaptcha Auto-Solving Strategy.

Integrates CapSolver API auto-solving into StealthPipeline, detecting sitekeys from
Cloudflare Turnstile, reCAPTCHA, and hCaptcha challenge pages, polling CapSolver for
tokens, injecting cf_clearance cookies, and persisting solved sessions to SessionPool.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from config import CAPSOLVER_API_KEY
from utils.capsolver import CapSolverClient
from utils.logger import get_logger
from utils.stealth_pipeline import StealthResponse, StealthStrategy

LOGGER = get_logger(__name__)

# Patterns for challenge type detection
_TURNSTILE_PATTERNS = [
    re.compile(r'cf-turnstile', re.IGNORECASE),
    re.compile(r'data-sitekey=["\']([^"\']+)["\']'),
    re.compile(r'sitekey:\s*["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'(0x4AAAAAA[a-zA-Z0-9_-]{8,40})'),
]
_RECAPTCHA_PATTERNS = [
    re.compile(r'g-recaptcha', re.IGNORECASE),
    re.compile(r'grecaptcha', re.IGNORECASE),
    re.compile(r'data-sitekey=["\']([^"\']+)["\']'),
]
_HCAPTCHA_PATTERNS = [
    re.compile(r'hcaptcha\.com', re.IGNORECASE),
    re.compile(r'h-captcha', re.IGNORECASE),
    re.compile(r'data-sitekey=["\']([^"\']+)["\']'),
]


class CapSolverStrategy(StealthStrategy):
    """StealthStrategy tier that auto-solves Cloudflare Turnstile / reCAPTCHA / hCaptcha
    via CapSolver API, then injects solved tokens and cf_clearance into session pool."""

    name = "capsolver"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (api_key or CAPSOLVER_API_KEY or "").strip()
        self.client = CapSolverClient(api_key=self.api_key)

    def is_available(self) -> bool:
        """Returns True if CapSolver API key is configured."""
        return bool(self.api_key)

    # ------------------------------------------------------------------
    # Sitekey extraction helpers
    # ------------------------------------------------------------------

    def _detect_challenge_type(self, html: str) -> str | None:
        """Return 'turnstile', 'recaptcha', or 'hcaptcha' if detected in HTML."""
        if not html:
            return None
        if any(p.search(html) for p in [_TURNSTILE_PATTERNS[0]]):
            return "turnstile"
        if any(p.search(html) for p in [_RECAPTCHA_PATTERNS[0], _RECAPTCHA_PATTERNS[1]]):
            return "recaptcha"
        if any(p.search(html) for p in [_HCAPTCHA_PATTERNS[0], _HCAPTCHA_PATTERNS[1]]):
            return "hcaptcha"
        # Fallback: any data-sitekey present near a script block → assume turnstile
        if re.search(r'data-sitekey=["\']', html):
            return "turnstile"
        return None

    def _extract_sitekey(self, html: str, challenge_type: str = "turnstile") -> str | None:
        """Extract data-sitekey value from HTML for the given challenge type."""
        if not html:
            return None
        # Generic data-sitekey attribute (works for all types)
        match = re.search(r'data-sitekey=["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)
        # Turnstile-specific heuristics
        if challenge_type == "turnstile":
            match = re.search(r'sitekey:\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if match:
                return match.group(1)
            match = re.search(r'(0x4AAAAAA[a-zA-Z0-9_-]{8,40})', html)
            if match:
                return match.group(0)
        return None

    # ------------------------------------------------------------------
    # Session injection helper
    # ------------------------------------------------------------------

    def _inject_session(self, url: str, cookie_dict: dict, client: Any) -> None:
        """Persist solved cf_clearance and captcha cookies to session pool and disk."""
        if not cookie_dict:
            return
        host = urlparse(url).hostname or ""
        try:
            if hasattr(client, "_save_domain_cookies"):
                client._save_domain_cookies(url, cookie_dict)
            if hasattr(client, "_session_pool"):
                client._session_pool.update_session(host, cookies=cookie_dict, user_agent=None)
            if hasattr(client, "session_manager"):
                existing = client.session_manager.load_session(host) or {}
                existing.update(cookie_dict)
                client.session_manager.save_session(host, existing)
            LOGGER.info("CapSolverStrategy: Injected %d cookie(s) into session pool for %s",
                        len(cookie_dict), host)
        except Exception as exc:
            LOGGER.warning("CapSolverStrategy: Failed to persist session for %s: %s", host, exc)

    # ------------------------------------------------------------------
    # Main execute
    # ------------------------------------------------------------------

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        if not self.is_available():
            return None

        # Fetch initial page to inspect challenge HTML
        headers = client._headers(url) if hasattr(client, "_headers") else {}
        try:
            resp = client.client.get(url, headers=headers) if hasattr(client, "client") else None
            html = resp.text if resp else ""
        except Exception as exc:
            LOGGER.debug("CapSolverStrategy initial fetch failed: %s", exc)
            return None

        # If not a challenge page and HTTP status OK, return directly
        is_challenge = hasattr(client, "_is_cloudflare_challenge") and client._is_cloudflare_challenge(html)
        if not is_challenge:
            if resp and resp.status_code < 400:
                return StealthResponse(
                    status_code=resp.status_code,
                    text=resp.text,
                    headers=dict(resp.headers),
                    strategy_name=self.name,
                )
            return None

        challenge_type = self._detect_challenge_type(html)
        if not challenge_type:
            LOGGER.debug("CapSolverStrategy: Challenge detected on %s but type unknown.", url)
            return None

        sitekey = self._extract_sitekey(html, challenge_type)
        if not sitekey:
            LOGGER.warning("CapSolverStrategy: %s challenge detected on %s but no sitekey found.",
                           challenge_type, url)
            return None

        LOGGER.info("CapSolverStrategy: Solving %s for %s (sitekey: %s)...",
                    challenge_type, url, sitekey[:20] + "...")
        token: str | None = None
        if challenge_type == "turnstile":
            token = self.client.solve_turnstile(website_url=url, website_key=sitekey, timeout=60)
        elif challenge_type == "recaptcha":
            token = self.client.solve_recaptcha(website_url=url, website_key=sitekey, timeout=60)
        elif challenge_type == "hcaptcha":
            token = self.client.solve_hcaptcha(website_url=url, website_key=sitekey, timeout=60)

        if not token:
            LOGGER.warning("CapSolverStrategy: Token solving returned empty for %s (%s).",
                           url, challenge_type)
            return None

        LOGGER.info("CapSolverStrategy: Obtained %s token for %s — retrying with injected token.",
                    challenge_type, url)

        # Inject token into retry headers and cookies
        retry_headers = dict(headers)
        retry_headers["X-Turnstile-Response"] = token
        retry_headers["cf-turnstile-response"] = token
        if challenge_type == "recaptcha":
            retry_headers["X-ReCaptcha-Response"] = token
        elif challenge_type == "hcaptcha":
            retry_headers["X-HCaptcha-Response"] = token

        try:
            retry_resp = client.client.get(url, headers=retry_headers)
            if retry_resp and retry_resp.status_code < 400 and \
               not (hasattr(client, "_is_cloudflare_challenge") and
                    client._is_cloudflare_challenge(retry_resp.text)):
                cookie_dict = dict(retry_resp.cookies)
                self._inject_session(url, cookie_dict, client)
                return StealthResponse(
                    status_code=retry_resp.status_code,
                    text=retry_resp.text,
                    cookies=cookie_dict,
                    headers=dict(retry_resp.headers),
                    strategy_name=self.name,
                )
        except Exception as exc:
            LOGGER.warning("CapSolverStrategy retry fetch failed: %s", exc)

        return None
