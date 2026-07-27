from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from frontend.app import app, task_state


@pytest.fixture
def client():
    return TestClient(app)


def test_htmx_controls_idle_state(client):
    task_state["status"] = "idle"
    response = client.get("/htmx/controls")
    assert response.status_code == 200
    assert "START SCRAPE" in response.text


def test_htmx_controls_running_state(client):
    task_state["status"] = "running"
    response = client.get("/htmx/controls")
    assert response.status_code == 200
    assert "PAUSE" in response.text
    assert "TERMINATE" in response.text


def test_htmx_controls_paused_state(client):
    task_state["status"] = "paused"
    response = client.get("/htmx/controls")
    assert response.status_code == 200
    assert "RESUME" in response.text
    assert "TERMINATE" in response.text


def test_htmx_status_badge(client):
    task_state["status"] = "idle"
    res_idle = client.get("/htmx/status-badge")
    assert res_idle.status_code == 200
    assert "IDLE" in res_idle.text

    task_state["status"] = "running"
    res_running = client.get("/htmx/status-badge")
    assert res_running.status_code == 200
    assert "RUNNING" in res_running.text
    assert "running" in res_running.text

    task_state["status"] = "paused"
    res_paused = client.get("/htmx/status-badge")
    assert res_paused.status_code == 200
    assert "PAUSED" in res_paused.text
    assert "paused" in res_paused.text


def test_pause_resume_no_process_graceful_handling(client):
    task_state["status"] = "idle"

    # Pause on idle should return graceful notice
    res_pause = client.post("/htmx/pause")
    assert res_pause.status_code == 200
    assert "NO RUNNING PROCESS TO PAUSE" in res_pause.text

    # Resume on idle should return graceful notice
    res_resume = client.post("/htmx/resume")
    assert res_resume.status_code == 200
    assert "NO PAUSED PROCESS TO RESUME" in res_resume.text

    # Stop on idle should return graceful notice
    res_stop = client.post("/htmx/stop")
    assert res_stop.status_code == 200
    assert "NO ACTIVE PROCESS" in res_stop.text


def test_api_json_job_control_endpoints(client):
    task_state["status"] = "idle"

    res_pause = client.post("/api/pause")
    assert res_pause.status_code == 200
    assert res_pause.json()["status"] == "idle"

    res_resume = client.post("/api/resume")
    assert res_resume.status_code == 200
    assert res_resume.json()["status"] == "idle"

    res_stop = client.post("/api/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] == "idle"
