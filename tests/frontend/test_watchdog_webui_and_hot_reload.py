"""
test_watchdog_webui_and_hot_reload.py — Unit tests for HotSeedReloader, Watchdog telemetry, and FastAPI WebUI Watchdog control endpoints.
"""

import time
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from cli.monitor_agent import (
    HotSeedReloader,
    get_watchdog_telemetry_snapshot,
    update_watchdog_snapshot,
)
from fastapi.testclient import TestClient
from frontend.app import app


def test_hot_seed_reloader_detects_mtime_change(tmp_path):
    seed_file = tmp_path / "test_seed.txt"
    seed_file.write_text("https://example.com/item1\n", encoding="utf-8")

    reloader = HotSeedReloader(str(seed_file))
    assert reloader.check_and_reload() is False

    # Simulate file modification
    time.sleep(0.05)
    seed_file.write_text("https://example.com/item1\nhttps://example.com/item2\n", encoding="utf-8")

    assert reloader.check_and_reload() is True
    assert reloader.check_and_reload() is False


def test_watchdog_telemetry_snapshot():
    update_watchdog_snapshot({
        "status": "active",
        "cycle": 3,
        "current_keyword": "test_keyword",
    })
    snap = get_watchdog_telemetry_snapshot()
    assert snap["status"] == "active"
    assert snap["cycle"] == 3
    assert snap["current_keyword"] == "test_keyword"


def test_webui_watchdog_status_and_control_endpoints():
    client = TestClient(app)

    # Status route should return 200 and initial state
    resp = client.get("/api/watchdog/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "telemetry" in data

    # Stop route on idle watchdog should return gracefully
    stop_resp = client.post("/api/watchdog/stop")
    assert stop_resp.status_code == 200
    assert stop_resp.json()["status"] == "idle"


@patch("src.core.watchdog_manager.subprocess.Popen")
def test_webui_watchdog_start_endpoint(mock_popen):
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None
    mock_proc.pid = 9999
    mock_popen.return_value = mock_proc

    client = TestClient(app)
    resp = client.post("/api/watchdog/start", json={"keyword": "cyberpunk", "interval": 30})
    assert resp.status_code == 200
    assert resp.json()["pid"] == 9999
    mock_popen.assert_called_once()
