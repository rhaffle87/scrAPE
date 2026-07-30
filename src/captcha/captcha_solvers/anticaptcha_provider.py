"""
anticaptcha_provider.py - Anti-Captcha API integration for captcha solving.
"""
from __future__ import annotations

import time
import httpx
from typing import Optional

from captcha.captcha_solvers.base import CaptchaSolverProvider
from monitoring.logger import get_logger

LOGGER = get_logger(__name__)


class AntiCaptchaProvider(CaptchaSolverProvider):
    """Solves captchas using the Anti-Captcha API (api.anti-captcha.com)."""

    API_URL = "https://api.anti-captcha.com"

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
                    LOGGER.error("Anti-Captcha task creation failed: %s", create_data)
                    return None

                task_id = create_data.get("taskId")
                if not task_id:
                    return None

                LOGGER.debug("Anti-Captcha task created. ID: %s. Waiting for solution...", task_id)

                # 2. Poll for Result
                start_time = time.time()
                while time.time() - start_time < timeout:
                    time.sleep(5)  # Wait before polling
                    poll_resp = client.post(
                        f"{self.API_URL}/getTaskResult",
                        json={"clientKey": self.api_key, "taskId": task_id},
                    )
                    poll_resp.raise_for_status()
                    poll_data = poll_resp.json()

                    if poll_data.get("errorId") != 0:
                        LOGGER.error("Anti-Captcha polling error: %s", poll_data)
                        return None

                    status = poll_data.get("status")
                    if status == "ready":
                        solution = poll_data.get("solution", {})
                        # Turnstile/reCAPTCHA usually returns 'token' or 'gRecaptchaResponse'
                        return solution.get("token") or solution.get("gRecaptchaResponse")

                LOGGER.warning("Anti-Captcha solving timed out after %d seconds.", timeout)
                return None
        except Exception as exc:
            LOGGER.error("Anti-Captcha exception: %s", exc)
            return None

    def _build_task(self, type_proxyless: str, type_proxy: str, website_url: str, website_key: str, proxy: str | None, user_agent: str | None) -> dict:
        if proxy:
            # Anti-Captcha proxy format requires separate fields: proxyType, proxyAddress, proxyPort, proxyLogin, proxyPassword
            # Example proxy input: http://user:pass@127.0.0.1:8080 or 127.0.0.1:8080
            proxy_type = "http"
            if "://" in proxy:
                proxy_type, proxy = proxy.split("://", 1)
                
            proxy_login, proxy_password = "", ""
            if "@" in proxy:
                auth, proxy = proxy.split("@", 1)
                if ":" in auth:
                    proxy_login, proxy_password = auth.split(":", 1)
                else:
                    proxy_login = auth
            
            proxy_address, proxy_port = proxy, "80"
            if ":" in proxy:
                proxy_address, proxy_port = proxy.split(":", 1)

            task = {
                "type": type_proxy,
                "websiteURL": website_url,
                "websiteKey": website_key,
                "proxyType": proxy_type,
                "proxyAddress": proxy_address,
                "proxyPort": int(proxy_port) if proxy_port.isdigit() else 80,
                "userAgent": user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            }
            if proxy_login:
                task["proxyLogin"] = proxy_login
                task["proxyPassword"] = proxy_password
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
        """Solve a Cloudflare Turnstile challenge using Anti-Captcha."""
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
        """Solve a reCAPTCHA v2 challenge using Anti-Captcha."""
        task = self._build_task(
            "NoCaptchaTaskProxyless", "NoCaptchaTask",
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
        """Solve an hCaptcha challenge using Anti-Captcha."""
        task = self._build_task(
            "HCaptchaTaskProxyless", "HCaptchaTask",
            website_url, website_key, proxy, user_agent
        )
        return self._create_task_and_poll(task, timeout)
