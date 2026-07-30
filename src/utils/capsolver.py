from __future__ import annotations

import logging
import os
import time
from typing import Any
import requests

from utils.notification_manager import NotificationPipeline

LOGGER = logging.getLogger(__name__)


class CapSolverClient:
    """Client for CapSolver Captcha Auto-Solving API (Cloudflare Turnstile, reCAPTCHA, hCaptcha)."""

    def __init__(
        self,
        api_key: str | None = None,
        api_url: str = "https://api.capsolver.com",
        max_spend_per_run: float | None = None,
        min_balance_threshold: float | None = None,
    ):
        self.api_key = (api_key or "").strip()
        self.api_url = api_url.rstrip("/")

        env_max_spend = float(os.getenv("CAPSOLVER_MAX_SPEND_PER_RUN", "0.50"))
        env_min_balance = float(os.getenv("CAPSOLVER_MIN_BALANCE", "0.20"))

        self.max_spend_per_run: float = max_spend_per_run if max_spend_per_run is not None else env_max_spend
        self.min_balance_threshold: float = min_balance_threshold if min_balance_threshold is not None else env_min_balance
        self.current_run_spend: float = 0.0
        self.cached_balance: float | None = None
        self._spend_warning_sent: bool = False
        self._balance_warning_sent: bool = False

    def reset_run_spend(self) -> None:
        """Reset per-run spend counter and warning flags."""
        self.current_run_spend = 0.0
        self._spend_warning_sent = False
        self._balance_warning_sent = False

    def check_budget_safety(self, estimated_cost: float = 0.003) -> bool:
        """Verify that per-run spend cap and minimum balance threshold are respected."""
        if not self.api_key:
            return False

        if self.current_run_spend + estimated_cost > self.max_spend_per_run:
            LOGGER.warning(
                "CapSolver per-run spend limit reached ($%.3f + $%.3f > $%.2f cap). Auto-pausing solves.",
                self.current_run_spend,
                estimated_cost,
                self.max_spend_per_run,
            )
            if not self._spend_warning_sent:
                self._spend_warning_sent = True
                NotificationPipeline().notify_watchdog_status(
                    "CapSolver per-run spend cap reached ($0.50 cap)."
                )
            return False

        balance = self.get_balance()
        self.cached_balance = balance

        if balance < self.min_balance_threshold:
            LOGGER.warning(
                "CapSolver account balance ($%.3f) is below minimum safety threshold ($%.2f). Auto-pausing solves.",
                balance,
                self.min_balance_threshold,
            )
            if not self._balance_warning_sent:
                self._balance_warning_sent = True
                NotificationPipeline().notify_watchdog_status(
                    "CapSolver balance ($0.20) below minimum safety threshold."
                )
            return False

        return True

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
                    val = float(data.get("balance", 0.0))
                    self.cached_balance = val
                    return val
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
        self, task_type: str, website_url: str, website_key: str, timeout: int = 30, estimated_cost: float = 0.003
    ) -> str | None:
        if not self.api_key:
            LOGGER.warning("CapSolver API key not provided.")
            return None

        if not self.check_budget_safety(estimated_cost=estimated_cost):
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

            self.current_run_spend += estimated_cost
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
