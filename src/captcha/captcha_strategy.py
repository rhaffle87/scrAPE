"""
captcha_strategy.py — Third-Party Captcha Auto-Solving Strategy.

Integrates Captcha Solver APIs into StealthPipeline, detecting sitekeys from
Cloudflare Turnstile, reCAPTCHA, and hCaptcha challenge pages, polling for
tokens, and persisting solved sessions to SessionPool.
"""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from monitoring.logger import get_logger
from network.stealth_pipeline import StealthResponse, StealthStrategy
from captcha.captcha_solvers.base import CaptchaSolverProvider

LOGGER = get_logger(__name__)

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


class ThirdPartyCaptchaStrategy(StealthStrategy):
    """StealthStrategy tier that auto-solves captchas via a configured provider."""

    name = "third_party_captcha"

    def __init__(self, provider: CaptchaSolverProvider | None = None) -> None:
        self.provider = provider
        if not self.provider:
            self._auto_select_provider()

    def _auto_select_provider(self) -> None:
        from config.settings_manager import settings
        from captcha.captcha_solvers.capsolver_provider import CapSolverProvider
        from captcha.captcha_solvers.twocaptcha_provider import TwoCaptchaProvider
        from captcha.captcha_solvers.anticaptcha_provider import AntiCaptchaProvider

        capsolver_key = settings.get("CAPSOLVER_API_KEY")
        twocaptcha_key = settings.get("TWOCAPTCHA_API_KEY")
        anticaptcha_key = settings.get("ANTICAPTCHA_API_KEY")

        if capsolver_key:
            self.provider = CapSolverProvider(api_key=capsolver_key)
        elif twocaptcha_key:
            self.provider = TwoCaptchaProvider(api_key=twocaptcha_key)
        elif anticaptcha_key:
            self.provider = AntiCaptchaProvider(api_key=anticaptcha_key)
        else:
            try:
                from captcha.captcha_solvers.free_audio_provider import FreeAudioCaptchaProvider
                self.provider = FreeAudioCaptchaProvider()
                if not self.provider.is_available():
                    self.provider = None
            except ImportError:
                pass

    def is_available(self) -> bool:
        return bool(self.provider and self.provider.is_available())

    def _detect_challenge_type(self, html: str) -> str | None:
        if not html:
            return None
        if any(p.search(html) for p in [_TURNSTILE_PATTERNS[0]]):
            return "turnstile"
        if any(p.search(html) for p in [_RECAPTCHA_PATTERNS[0], _RECAPTCHA_PATTERNS[1]]):
            return "recaptcha"
        if any(p.search(html) for p in [_HCAPTCHA_PATTERNS[0], _HCAPTCHA_PATTERNS[1]]):
            return "hcaptcha"
        if re.search(r'data-sitekey=["\']', html):
            return "turnstile"
        return None

    def _extract_sitekey(self, html: str, challenge_type: str = "turnstile") -> str | None:
        if not html:
            return None
        match = re.search(r'data-sitekey=["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)
        if challenge_type == "turnstile":
            match = re.search(r'sitekey:\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if match:
                return match.group(1)
            match = re.search(r'(0x4AAAAAA[a-zA-Z0-9_-]{8,40})', html)
            if match:
                return match.group(0)
        return None

    def _inject_session(self, url: str, cookie_dict: dict, client: Any) -> None:
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
            LOGGER.info("ThirdPartyCaptchaStrategy: Injected %d cookie(s) into session pool for %s", len(cookie_dict), host)
        except Exception as exc:
            LOGGER.warning("ThirdPartyCaptchaStrategy: Failed to persist session for %s: %s", host, exc)

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        if not self.is_available() or not self.provider:
            return None

        headers = client._headers(url) if hasattr(client, "_headers") else {}
        try:
            resp = client.client.get(url, headers=headers) if hasattr(client, "client") else None
            html = resp.text if resp else ""
        except Exception as exc:
            LOGGER.debug("ThirdPartyCaptchaStrategy initial fetch failed: %s", exc)
            return None

        is_challenge = hasattr(client, "_is_cloudflare_challenge") and client._is_cloudflare_challenge(html)
        if not is_challenge:
            if resp and resp.status_code < 400:
                return StealthResponse(
                    status_code=resp.status_code, text=resp.text,
                    headers=dict(resp.headers), strategy_name=self.name,
                )
            return None

        challenge_type = self._detect_challenge_type(html)
        if not challenge_type:
            LOGGER.debug("ThirdPartyCaptchaStrategy: Challenge detected on %s but type unknown.", url)
            return None

        sitekey = self._extract_sitekey(html, challenge_type)
        if not sitekey:
            LOGGER.warning("ThirdPartyCaptchaStrategy: %s challenge detected on %s but no sitekey found.", challenge_type, url)
            return None

        LOGGER.info("ThirdPartyCaptchaStrategy: Solving %s for %s (sitekey: %s)...", challenge_type, url, sitekey[:20] + "...")
        
        # Get proxy and user-agent from client
        proxy = getattr(client, "proxy", None)
        user_agent = headers.get("User-Agent")

        token: str | None = None
        if challenge_type == "turnstile":
            token = self.provider.solve_turnstile(website_url=url, website_key=sitekey, timeout=60, proxy=proxy, user_agent=user_agent)
        elif challenge_type == "recaptcha":
            token = self.provider.solve_recaptcha(website_url=url, website_key=sitekey, timeout=60, proxy=proxy, user_agent=user_agent)
        elif challenge_type == "hcaptcha":
            token = self.provider.solve_hcaptcha(website_url=url, website_key=sitekey, timeout=60, proxy=proxy, user_agent=user_agent)

        if not token:
            LOGGER.warning("ThirdPartyCaptchaStrategy: Token solving returned empty for %s.", url)
            return None

        LOGGER.info("ThirdPartyCaptchaStrategy: Obtained token for %s — retrying.", url)

        retry_headers = dict(headers)
        retry_headers["X-Turnstile-Response"] = token
        retry_headers["cf-turnstile-response"] = token
        if challenge_type == "recaptcha":
            retry_headers["X-ReCaptcha-Response"] = token
        elif challenge_type == "hcaptcha":
            retry_headers["X-HCaptcha-Response"] = token

        try:
            retry_resp = client.client.get(url, headers=retry_headers)
            if retry_resp and retry_resp.status_code < 400 and not (hasattr(client, "_is_cloudflare_challenge") and client._is_cloudflare_challenge(retry_resp.text)):
                cookie_dict = dict(retry_resp.cookies)
                self._inject_session(url, cookie_dict, client)
                return StealthResponse(
                    status_code=retry_resp.status_code, text=retry_resp.text,
                    cookies=cookie_dict, headers=dict(retry_resp.headers),
                    strategy_name=self.name,
                )

            # Fallback to form POST if the GET request still fails or hits a challenge
            LOGGER.info("ThirdPartyCaptchaStrategy: GET with headers failed for %s, trying form POST fallback.", url)
            form_data = {}
            if challenge_type == "turnstile":
                form_data["cf-turnstile-response"] = token
            elif challenge_type == "recaptcha":
                form_data["g-recaptcha-response"] = token
            elif challenge_type == "hcaptcha":
                form_data["h-captcha-response"] = token
            elif challenge_type == "datadome":
                form_data["datadome"] = token

            if form_data:
                post_resp = client.client.post(url, headers=headers, data=form_data)
                if post_resp and post_resp.status_code < 400 and not (hasattr(client, "_is_cloudflare_challenge") and client._is_cloudflare_challenge(post_resp.text)):
                    cookie_dict = dict(post_resp.cookies)
                    self._inject_session(url, cookie_dict, client)
                    return StealthResponse(
                        status_code=post_resp.status_code, text=post_resp.text,
                        cookies=cookie_dict, headers=dict(post_resp.headers),
                        strategy_name=self.name,
                    )
        except Exception as exc:
            LOGGER.warning("ThirdPartyCaptchaStrategy retry fetch failed: %s", exc)

        return None
