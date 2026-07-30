"""
test_budget_guardrails.py — Unit tests for CapSolver spend caps, balance auto-pause,
and Proxy pool bandwidth quota tracking guardrails.
"""

import os
import pytest
from unittest.mock import MagicMock

from utils.capsolver import CapSolverClient
from utils.proxy_manager import ProxyInfo, ProxyPoolManager
from utils.notification_manager import NotificationPipeline


def test_capsolver_spend_limit_guardrail(monkeypatch):
    client = CapSolverClient(api_key="test_key", max_spend_per_run=0.010, min_balance_threshold=0.05)

    # Mock get_balance to return a healthy balance of $1.00
    monkeypatch.setattr(client, "get_balance", lambda: 1.00)

    notification_logs = []
    monkeypatch.setattr(
        NotificationPipeline,
        "notify_watchdog_status",
        lambda self, msg, level="warning": notification_logs.append((msg, level)),
    )

    # Spend $0.003 * 3 = $0.009
    assert client.check_budget_safety(0.003) is True
    client.current_run_spend += 0.009

    # Next attempt ($0.009 + $0.003 = $0.012 > $0.010 cap) should fail safety check
    assert client.check_budget_safety(0.003) is False
    assert len(notification_logs) == 1
    assert "spend cap reached" in notification_logs[0][0].lower()

    # Reset run spend should re-enable budget safety
    client.reset_run_spend()
    assert client.current_run_spend == 0.0
    assert client.check_budget_safety(0.003) is True


def test_capsolver_minimum_balance_threshold(monkeypatch):
    client = CapSolverClient(api_key="test_key", max_spend_per_run=0.50, min_balance_threshold=0.20)

    # Mock get_balance to return low balance $0.10 (< $0.20 threshold)
    monkeypatch.setattr(client, "get_balance", lambda: 0.10)

    notification_logs = []
    monkeypatch.setattr(
        NotificationPipeline,
        "notify_watchdog_status",
        lambda self, msg, level="warning": notification_logs.append((msg, level)),
    )

    assert client.check_budget_safety(0.003) is False
    assert len(notification_logs) == 1
    assert "balance" in notification_logs[0][0].lower()


def test_proxy_pool_bandwidth_quota_and_auto_halt(monkeypatch):
    # Create manager with 10 MB limit (10,485,760 bytes)
    manager = ProxyPoolManager(max_bandwidth_mb=10.0)
    manager.reset_bandwidth_stats()
    manager.set_proxies(["http://127.0.0.1:8080", "http://127.0.0.1:8081"])

    notification_logs = []
    monkeypatch.setattr(
        NotificationPipeline,
        "notify_watchdog_status",
        lambda self, msg, level="warning": notification_logs.append((msg, level)),
    )

    assert manager.get_best_proxy() == "http://127.0.0.1:8080"

    # Record 7 MB (70% of 10 MB) -> no warning
    manager.record_bytes_transferred("http://127.0.0.1:8080", 7 * 1024 * 1024)
    assert manager.get_total_bytes_transferred() == 7 * 1024 * 1024
    assert len(notification_logs) == 0

    # Record 1.5 MB -> Total 8.5 MB (85% > 80%) -> Triggers 80% warning
    manager.record_bytes_transferred("http://127.0.0.1:8080", int(1.5 * 1024 * 1024))
    assert len(notification_logs) == 1
    assert "80%" in notification_logs[0][0]

    # Record 2 MB -> Total 10.5 MB (> 10 MB limit) -> Triggers 100% halt alert
    manager.record_bytes_transferred("http://127.0.0.1:8080", 2 * 1024 * 1024)
    assert len(notification_logs) == 2
    assert "quota exhausted" in notification_logs[1][0].lower()

    # Routing should now auto-halt and return None
    assert manager.get_best_proxy() is None
    assert manager.get_proxy_for_domain("example.com") is None


def test_telemetry_stealth_endpoint():
    from fastapi.testclient import TestClient
    from frontend.app import app

    client = TestClient(app)
    response = client.get("/api/telemetry/stealth")
    assert response.status_code == 200
    data = response.json()

    assert "solve_counts" in data
    assert "health_stats" in data
    assert "capsolver_run_spend" in data
    assert "capsolver_max_spend" in data
    assert "proxy_total_bytes" in data
    assert "proxy_max_bytes" in data
