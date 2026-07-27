"""
capsolver_strategy.py — CapSolver Turnstile Auto-Solving Strategy for WAF Fallback Pipeline.

Integrates CapSolver API auto-solving into StealthPipeline, detecting sitekeys,
polling CapSolver for Turnstile tokens, and persisting solved cf_clearance cookies.
"""

from __future__ import annotations

import re
from typing import Any

from config import CAPSOLVER_API_KEY
from utils.capsolver import CapSolverClient
from utils.logger import get_logger
from utils.stealth_pipeline import StealthResponse, StealthStrategy

LOGGER = get_logger(__name__)


class CapSolverStrategy(StealthStrategy):
    """StealthStrategy tier that auto-solves Cloudflare Turnstile via CapSolver API."""

    name = "capsolver"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = (api_key or CAPSOLVER_API_KEY or "").strip()
        self.client = CapSolverClient(api_key=self.api_key)

    def is_available(self) -> bool:
        """Returns True if CapSolver API key is configured."""
        return bool(self.api_key)

    def _extract_sitekey(self, html: str) -> str | None:
        """Extract data-sitekey or sitekey parameter from Cloudflare Turnstile HTML."""
        if not html:
            return None
        match = re.search(r'data-sitekey=["\']([^"\']+)["\']', html)
        if match:
            return match.group(1)
        match = re.search(r'sitekey:\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
        if match:
            return match.group(1)
        match = re.search(r'0x4AAAAAA[a-zA-Z0-9_-]{10,40}', html)
        if match:
            return match.group(0)
        return None

    def execute(self, url: str, client: Any) -> StealthResponse | None:
        if not self.is_available():
            return None

        # Fetch initial page to inspect Turnstile sitekey
        headers = client._headers(url) if hasattr(client, "_headers") else {}
        try:
            resp = client.client.get(url, headers=headers) if hasattr(client, "client") else None
            html = resp.text if resp else ""
        except Exception as exc:
            LOGGER.debug("CapSolverStrategy initial fetch failed: %s", exc)
            return None

        if not client._is_cloudflare_challenge(html):
            # Not a challenge page; standard fetch succeeds
            if resp and resp.status_code < 400:
                return StealthResponse(
                    status_code=resp.status_code,
                    text=resp.text,
                    headers=dict(resp.headers),
                    strategy_name=self.name,
                )
            return None

        sitekey = self._extract_sitekey(html)
        if not sitekey:
            LOGGER.warning("CapSolverStrategy: Cloudflare challenge detected on %s, but sitekey not found.", url)
            return None

        LOGGER.info("CapSolverStrategy: Solving Cloudflare Turnstile for %s (sitekey: %s)...", url, sitekey)
        token = self.client.solve_turnstile(website_url=url, website_key=sitekey, timeout=30)
        if not token:
            LOGGER.warning("CapSolverStrategy: Turnstile token solving returned empty result for %s.", url)
            return None

        LOGGER.info("CapSolverStrategy: Successfully obtained Turnstile token for %s. Injecting and retrying...", url)

        # Retry request with Turnstile response token in headers/cookies
        retry_headers = dict(headers)
        retry_headers["X-Turnstile-Response"] = token
        retry_headers["cf-turnstile-response"] = token

        try:
            retry_resp = client.client.get(url, headers=retry_headers)
            if retry_resp and retry_resp.status_code < 400 and not client._is_cloudflare_challenge(retry_resp.text):
                cookie_dict = dict(retry_resp.cookies)
                # Save solved cookies to domain session pool if client supports it
                if hasattr(client, "_save_domain_cookies"):
                    client._save_domain_cookies(url, cookie_dict)
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
