from __future__ import annotations

import logging
import time
from typing import Any
import requests

LOGGER = logging.getLogger(__name__)


class CapSolverClient:
    """Client for CapSolver Captcha Auto-Solving API (Cloudflare Turnstile, reCAPTCHA, hCaptcha)."""

    def __init__(self, api_key: str | None = None, api_url: str = "https://api.capsolver.com"):
        self.api_key = (api_key or "").strip()
        self.api_url = api_url.rstrip("/")

    def get_balance(self) -> float:
        """Query account balance from CapSolver API."""
        if not self.api_key:
            return 0.0
        try:
            res = requests.post(
                f"{self.api_url}/getBalance",
                json={"clientKey": self.api_key},
                timeout=10,
            )
            if res.status_code == 200:
                data = res.json()
                if data.get("errorId") == 0:
                    return float(data.get("balance", 0.0))
        except Exception as exc:
            LOGGER.debug("CapSolver get_balance failed: %s", exc)
        return 0.0

    def solve_turnstile(self, website_url: str, website_key: str, timeout: int = 30) -> str | None:
        """Solve Cloudflare Turnstile challenge and return g-recaptcha-response / token."""
        return self._create_and_poll_task(
            task_type="AntiTurnstileTaskProxyLess",
            website_url=website_url,
            website_key=website_key,
            timeout=timeout,
        )

    def solve_recaptcha(self, website_url: str, website_key: str, timeout: int = 30) -> str | None:
        """Solve reCAPTCHA v2 / v3 challenge."""
        return self._create_and_poll_task(
            task_type="ReCaptchaV2TaskProxyLess",
            website_url=website_url,
            website_key=website_key,
            timeout=timeout,
        )

    def solve_hcaptcha(self, website_url: str, website_key: str, timeout: int = 30) -> str | None:
        """Solve hCaptcha challenge."""
        return self._create_and_poll_task(
            task_type="HCaptchaTaskProxyLess",
            website_url=website_url,
            website_key=website_key,
            timeout=timeout,
        )

    def _create_and_poll_task(
        self, task_type: str, website_url: str, website_key: str, timeout: int = 30
    ) -> str | None:
        if not self.api_key:
            LOGGER.warning("CapSolver API key not provided.")
            return None

        payload = {
            "clientKey": self.api_key,
            "task": {
                "type": task_type,
                "websiteURL": website_url,
                "websiteKey": website_key,
            },
        }

        try:
            res = requests.post(f"{self.api_url}/createTask", json=payload, timeout=10)
            if res.status_code != 200:
                LOGGER.warning("CapSolver createTask failed with HTTP %d", res.status_code)
                return None

            data = res.json()
            if data.get("errorId") != 0:
                LOGGER.warning("CapSolver createTask error: %s", data.get("errorDescription"))
                return None

            task_id = data.get("taskId")
            if not task_id:
                return None

            start_time = time.time()
            while time.time() - start_time < timeout:
                time.sleep(2)
                res = requests.post(
                    f"{self.api_url}/getTaskResult",
                    json={"clientKey": self.api_key, "taskId": task_id},
                    timeout=10,
                )
                if res.status_code != 200:
                    continue

                rdata = res.json()
                if rdata.get("status") == "ready":
                    solution = rdata.get("solution", {})
                    token = solution.get("token") or solution.get("gRecaptchaResponse")
                    return token
                elif rdata.get("status") == "failed":
                    LOGGER.warning("CapSolver task failed: %s", rdata.get("errorDescription"))
                    return None

        except Exception as exc:
            LOGGER.warning("CapSolver task error: %s", exc)

        return None
