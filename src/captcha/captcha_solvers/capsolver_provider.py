"""
capsolver_provider.py - CapSolver integration.
"""
from __future__ import annotations

import logging
import os
import time
import requests
from typing import Any

from notifications.notification_manager import NotificationPipeline
from captcha.captcha_solvers.base import CaptchaSolverProvider

LOGGER = logging.getLogger(__name__)


class CapSolverProvider(CaptchaSolverProvider):
    """Client for CapSolver Captcha Auto-Solving API."""

    def __init__(
        self,
        api_key: str | None = None,
        max_spend_per_run: float | None = None,
        api_url: str = "https://api.capsolver.com",
        min_balance_threshold: float | None = None,
    ):
        super().__init__(api_key=api_key, max_spend=max_spend_per_run)
        self.api_url = api_url.rstrip("/")
        
        env_max_spend = float(os.getenv("CAPSOLVER_MAX_SPEND_PER_RUN", "0.50"))
        env_min_balance = float(os.getenv("CAPSOLVER_MIN_BALANCE", "0.20"))

        self.max_spend = self.max_spend if self.max_spend is not None else env_max_spend
        self.min_balance_threshold = min_balance_threshold if min_balance_threshold is not None else env_min_balance
        self.current_run_spend = 0.0
        self.cached_balance: float | None = None
        self._spend_warning_sent = False
        self._balance_warning_sent = False

    def reset_run_spend(self) -> None:
        self.current_run_spend = 0.0
        self._spend_warning_sent = False
        self._balance_warning_sent = False

    def check_budget_safety(self, estimated_cost: float = 0.003) -> bool:
        if not self.api_key:
            return False

        if self.max_spend is not None and self.current_run_spend + estimated_cost > self.max_spend:
            LOGGER.warning(
                "CapSolver per-run spend limit reached ($%.3f + $%.3f > $%.2f cap).",
                self.current_run_spend,
                estimated_cost,
                self.max_spend,
            )
            if not self._spend_warning_sent:
                self._spend_warning_sent = True
                NotificationPipeline().notify_watchdog_status("CapSolver per-run spend cap reached.")
            return False

        balance = self.get_balance()
        if balance < self.min_balance_threshold:
            LOGGER.warning("CapSolver balance ($%.3f) below threshold.", balance)
            if not self._balance_warning_sent:
                self._balance_warning_sent = True
                NotificationPipeline().notify_watchdog_status("CapSolver balance below threshold.")
            return False

        return True

    def get_balance(self) -> float:
        if not self.api_key:
            return 0.0
        try:
            res = requests.post(f"{self.api_url}/getBalance", json={"clientKey": self.api_key}, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get("errorId") == 0:
                    val = float(data.get("balance", 0.0))
                    self.cached_balance = val
                    return val
        except Exception as exc:
            LOGGER.debug("CapSolver get_balance failed: %s", exc)
        return self.cached_balance or 0.0

    def solve_turnstile(self, website_url: str, website_key: str, timeout: int = 60, proxy: str | None = None, user_agent: str | None = None) -> str | None:
        task_type = "AntiTurnstileTask" if proxy else "AntiTurnstileTaskProxyLess"
        return self._create_and_poll_task(task_type, website_url, website_key, timeout, proxy, user_agent)

    def solve_recaptcha(self, website_url: str, website_key: str, timeout: int = 60, proxy: str | None = None, user_agent: str | None = None) -> str | None:
        task_type = "ReCaptchaV2Task" if proxy else "ReCaptchaV2TaskProxyLess"
        return self._create_and_poll_task(task_type, website_url, website_key, timeout, proxy, user_agent)

    def solve_hcaptcha(self, website_url: str, website_key: str, timeout: int = 60, proxy: str | None = None, user_agent: str | None = None) -> str | None:
        task_type = "HCaptchaTask" if proxy else "HCaptchaTaskProxyLess"
        return self._create_and_poll_task(task_type, website_url, website_key, timeout, proxy, user_agent)

    def _create_and_poll_task(self, task_type: str, website_url: str, website_key: str, timeout: int = 60, proxy: str | None = None, user_agent: str | None = None, estimated_cost: float = 0.003) -> str | None:
        if not self.is_available():
            return None
        if not self.check_budget_safety(estimated_cost):
            return None

        task_payload = {
            "type": task_type,
            "websiteURL": website_url,
            "websiteKey": website_key,
        }
        if proxy:
            task_payload["proxy"] = proxy
        if user_agent:
            task_payload["userAgent"] = user_agent

        payload = {"clientKey": self.api_key, "task": task_payload}
        
        try:
            res = requests.post(f"{self.api_url}/createTask", json=payload, timeout=10)
            if res.status_code != 200:
                return None

            data = res.json()
            if data.get("errorId") != 0:
                return None

            self.current_run_spend += estimated_cost
            task_id = data.get("taskId")
            if not task_id:
                return None

            start_time = time.time()
            while time.time() - start_time < timeout:
                time.sleep(2)
                res = requests.post(f"{self.api_url}/getTaskResult", json={"clientKey": self.api_key, "taskId": task_id}, timeout=10)
                if res.status_code != 200:
                    continue

                rdata = res.json()
                if rdata.get("status") == "ready":
                    sol = rdata.get("solution", {})
                    return sol.get("token") or sol.get("gRecaptchaResponse")
                elif rdata.get("status") == "failed":
                    return None
        except Exception:
            pass
        return None
