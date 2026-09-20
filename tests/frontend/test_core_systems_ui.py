"""
test_core_systems_ui.py — Integration and endpoint tests for Next-Gen Core Systems UI/CLI parity.
"""

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from frontend.app import app

client = TestClient(app)


def test_api_telemetry_node_health():
    """Verify /api/telemetry/node-health returns structured governor and system health."""
    response = client.get("/api/telemetry/node-health")
    assert response.status_code == 200
    data = response.json()

    assert "status" in data
    assert data["status"] in ("healthy", "throttled")
    assert "cpu_percent" in data
    assert "ram_percent" in data
    assert "disk_percent" in data
    assert "concurrency_scale_factor" in data
    assert "is_throttled" in data
    assert "metrics" in data
    assert isinstance(data["concurrency_scale_factor"], (int, float))


def test_htmx_stats_renders_governor_badge():
    """Verify /htmx/stats includes governor status in rendered HTML."""
    response = client.get("/htmx/stats")
    assert response.status_code == 200
    html = response.text

    assert "SYS TELEMETRY" in html
    assert "GOV:" in html
    assert "CPU" in html
    assert "RAM" in html


def test_api_settings_solver_providers(tmp_path):
    """Verify /api/settings/solver accepts multiple providers and updates settings."""
    env_file = tmp_path / ".env"
    with patch("frontend.routers.settings.ENV_PATH", env_file):
        # 1. FreeAudio provider
        r1 = client.post("/api/settings/solver", data={"provider": "free_audio", "api_key": ""})
        assert r1.status_code == 200
        assert "free_audio" in env_file.read_text()

        # 2. 2Captcha provider
        r2 = client.post("/api/settings/solver", data={"provider": "2captcha", "api_key": "dummy_key_2cap"})
        assert r2.status_code == 200
        content = env_file.read_text()
        assert "TWOCAPTCHA_API_KEY=dummy_key_2cap" in content


def test_api_settings_storage(tmp_path):
    """Verify /api/settings/storage updates storage backend and S3 settings."""
    env_file = tmp_path / ".env"
    with patch("frontend.routers.settings.ENV_PATH", env_file):
        resp = client.post("/api/settings/storage", data={
            "backend": "s3",
            "s3_bucket": "test-dataset-bucket",
            "s3_prefix": "crawls/2026/",
            "s3_endpoint_url": "https://s3.us-east-1.amazonaws.com",
        })
        assert resp.status_code == 200
        content = env_file.read_text()
        assert "STORAGE_BACKEND=s3" in content
        assert "S3_BUCKET=test-dataset-bucket" in content
        assert "S3_PREFIX=crawls/2026/" in content


def test_run_scrape_with_core_systems_flags():
    """Verify /api/run forwards ML, storage, and self-healing flags to the CLI engine."""
    mock_popen = MagicMock()
    mock_popen.pid = 99999
    mock_popen.poll.return_value = None
    mock_popen.stdout.readline.return_value = ""

    with patch("frontend.app.Popen", return_value=mock_popen) as mock_p, \
         patch("frontend.routers.jobs.Popen", return_value=mock_popen), \
         patch("frontend.routers.jobs.get_current_process", return_value=None):
        payload = {
            "keyword": "test_core",
            "max_results": 10,
            "workers": 4,
            "aesthetic_score": 6.5,
            "auto_crop": True,
            "tag_dataset": True,
            "export_rag": True,
            "auto_export_db": True,
            "storage_backend": "s3",
            "s3_bucket": "cloud-bucket",
            "s3_prefix": "prod/",
            "enable_self_healing": True,
            "worker_processes": 4,
        }
        resp = client.post("/api/run", json=payload)
        assert resp.status_code == 200

        cmd_args = mock_p.call_args[0][0]
        assert "--aesthetic-score" in cmd_args
        assert "6.5" in cmd_args
        assert "--auto-crop" in cmd_args
        assert "--tag-dataset" in cmd_args
        assert "--export-rag" in cmd_args
        assert "--auto-export-db" in cmd_args
        assert "--storage-backend" in cmd_args
        assert "s3" in cmd_args
        assert "--s3-bucket" in cmd_args
        assert "cloud-bucket" in cmd_args
        assert "--enable-self-healing" in cmd_args
        assert "--worker-processes" in cmd_args
        assert "4" in cmd_args

    from frontend.state import task_state, set_current_process
    task_state["status"] = "idle"
    task_state["pid"] = None
    set_current_process(None)


def test_htmx_run_with_core_systems_flags():
    """Verify /htmx/run parses form data for ML and storage and passes to engine."""
    mock_popen = MagicMock()
    mock_popen.pid = 88888
    mock_popen.poll.return_value = None
    mock_popen.stdout.readline.return_value = ""

    with patch("frontend.app.Popen", return_value=mock_popen) as mock_p, \
         patch("frontend.routers.jobs.Popen", return_value=mock_popen), \
         patch("frontend.routers.jobs.get_current_process", return_value=None):
        form_data = {
            "keyword": "htmx_core",
            "max_results": "20",
            "workers": "4",
            "aesthetic_score": "7.0",
            "auto_crop": "on",
            "tag_dataset": "on",
            "export_rag": "on",
            "auto_export_db": "on",
            "storage_backend": "s3",
            "s3_bucket": "htmx-bucket",
            "s3_prefix": "htmx-prefix/",
            "enable_self_healing": "on",
            "worker_processes": "2",
        }
        resp = client.post("/htmx/run", data=form_data)
        assert resp.status_code == 200

        cmd_args = mock_p.call_args[0][0]
        assert "--aesthetic-score" in cmd_args
        assert "7.0" in cmd_args
        assert "--auto-crop" in cmd_args
        assert "--tag-dataset" in cmd_args
        assert "--export-rag" in cmd_args
        assert "--auto-export-db" in cmd_args
        assert "--storage-backend" in cmd_args
        assert "s3" in cmd_args
        assert "--s3-bucket" in cmd_args
        assert "htmx-bucket" in cmd_args
        assert "--enable-self-healing" in cmd_args
        assert "--worker-processes" in cmd_args
        assert "2" in cmd_args

    from frontend.state import task_state, set_current_process
    task_state["status"] = "idle"
    task_state["pid"] = None
    set_current_process(None)


