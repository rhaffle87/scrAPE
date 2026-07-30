"""
twocaptcha_provider.py - 2Captcha API integration for captcha solving.
"""
from __future__ import annotations

import time
import httpx
from typing import Optional

from captcha.captcha_solvers.base import CaptchaSolverProvider
from monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class TwoCaptchaProvider(CaptchaSolverProvider):
    """Solves captchas using the 2Captcha API (api.2captcha.com)."""

    API_URL = "https://api.2captcha.com"

    def _create_task_and_poll(self, task_payload: dict, timeout: int) -> str | None:
        """Helper to create a task and poll for the result."""
        if not self.api_key:
            return None

        try:
            with httpx.Client(timeout=15.0) as client:
                # 1. Create Task
                create_resp = client.post(
                    f"{self.API_URL}/createTask",
                    json={"clientKey": self.api_key, "task": task_payload},
                )
                create_resp.raise_for_status()
                create_data = create_resp.json()

                if create_data.get("errorId") != 0:
                    LOGGER.error("2Captcha task creation failed: %s", create_data)
                    return None

                task_id = create_data.get("taskId")
                if not task_id:
                    return None

                LOGGER.debug("2Captcha task created. ID: %s. Waiting for solution...", task_id)

                # 2. Poll for Result
                start_time = time.time()
                while time.time() - start_time < timeout:
                    time.sleep(5)  # 2Captcha recommends waiting 5 seconds between polls
                    poll_resp = client.post(
                        f"{self.API_URL}/getTaskResult",
                        json={"clientKey": self.api_key, "taskId": task_id},
                    )
                    poll_resp.raise_for_status()
                    poll_data = poll_resp.json()

                    if poll_data.get("errorId") != 0:
                        LOGGER.error("2Captcha polling error: %s", poll_data)
                        return None

                    status = poll_data.get("status")
                    if status == "ready":
                        solution = poll_data.get("solution", {})
                        # Turnstile/reCAPTCHA usually returns 'token' or 'gRecaptchaResponse'
                        return solution.get("token") or solution.get("gRecaptchaResponse")

                LOGGER.warning("2Captcha solving timed out after %d seconds.", timeout)
                return None
        except Exception as exc:
            LOGGER.error("2Captcha exception: %s", exc)
            return None

    def _build_task(self, type_proxyless: str, type_proxy: str, website_url: str, website_key: str, proxy: str | None, user_agent: str | None) -> dict:
        if proxy:
            # 2Captcha proxy format: login:password@IP:PORT or IP:PORT
            parts = proxy.split("://")
            proxy_str = parts[-1] if len(parts) > 1 else proxy
            proxy_type = parts[0] if len(parts) > 1 else "http"
            
            task = {
                "type": type_proxy,
                "websiteURL": website_url,
                "websiteKey": website_key,
                "proxyType": proxy_type,
                "proxyAddress": proxy_str,
                "userAgent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
        else:
            task = {
                "type": type_proxyless,
                "websiteURL": website_url,
                "websiteKey": website_key,
            }
        return task

    def solve_turnstile(
        self,
        website_url: str,
        website_key: str,
        timeout: int = 60,
        proxy: str | None = None,
        user_agent: str | None = None,
    ) -> str | None:
        """Solve a Cloudflare Turnstile challenge using 2Captcha."""
        task = self._build_task(
            "TurnstileTaskProxyless", "TurnstileTask",
            website_url, website_key, proxy, user_agent
        )
        return self._create_task_and_poll(task, timeout)

    def solve_recaptcha(
        self,
        website_url: str,
        website_key: str,
        timeout: int = 60,
        proxy: str | None = None,
        user_agent: str | None = None,
    ) -> str | None:
        """Solve a reCAPTCHA v2 challenge using 2Captcha."""
        task = self._build_task(
            "RecaptchaV2TaskProxyless", "RecaptchaV2Task",
            website_url, website_key, proxy, user_agent
        )
        return self._create_task_and_poll(task, timeout)

    def solve_hcaptcha(
        self,
        website_url: str,
        website_key: str,
        timeout: int = 60,
        proxy: str | None = None,
        user_agent: str | None = None,
    ) -> str | None:
        """Solve an hCaptcha challenge using 2Captcha."""
        task = self._build_task(
            "HCaptchaTaskProxyless", "HCaptchaTask",
            website_url, website_key, proxy, user_agent
        )
        return self._create_task_and_poll(task, timeout)
