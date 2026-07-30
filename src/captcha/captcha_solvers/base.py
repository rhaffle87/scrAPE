"""
base.py - Base interface for third-party Captcha Solver providers.
"""
from __future__ import annotations

import abc
from typing import Optional


class CaptchaSolverProvider(abc.ABC):
    """Abstract base class for Captcha solving services."""

    def __init__(self, api_key: str | None = None, max_spend: float | None = None):
        self.api_key = (api_key or "").strip()
        self.max_spend = max_spend

    @abc.abstractmethod
    def solve_turnstile(
        self,
        website_url: str,
        website_key: str,
        timeout: int = 60,
        proxy: str | None = None,
        user_agent: str | None = None,
    ) -> str | None:
        """Solve a Cloudflare Turnstile challenge and return the token."""
        pass

    @abc.abstractmethod
    def solve_recaptcha(
        self,
        website_url: str,
        website_key: str,
        timeout: int = 60,
        proxy: str | None = None,
        user_agent: str | None = None,
    ) -> str | None:
        """Solve a reCAPTCHA v2/v3 challenge and return the token."""
        pass

    @abc.abstractmethod
    def solve_hcaptcha(
        self,
        website_url: str,
        website_key: str,
        timeout: int = 60,
        proxy: str | None = None,
        user_agent: str | None = None,
    ) -> str | None:
        """Solve an hCaptcha challenge and return the token."""
        pass

    def is_available(self) -> bool:
        """Return True if the provider is properly configured."""
        return bool(self.api_key)
