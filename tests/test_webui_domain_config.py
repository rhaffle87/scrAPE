"""Unit tests for WebUI Domain Config Studio router and live hot reload integration."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from frontend.app import app

client = TestClient(app)


def test_get_domain_config_endpoint():
    """Verify GET /api/domain-config returns configuration payload and stats."""
    res = client.get("/api/domain-config")
    assert res.status_code == 200
    data = res.json()
    assert "config" in data
    assert "raw_json" in data
    assert "stats" in data
    assert "rate_limits" in data["stats"]
    assert "stealth_required" in data["stats"]


def test_save_domain_config_endpoint_success(tmp_path, monkeypatch):
    """Verify POST /api/domain-config/save updates configuration file and returns success."""
    test_cfg_file = tmp_path / "domain_config.json"
    initial_data = {"rate_limits": {"example.com": 2.0}, "hotlink_protected": []}
    test_cfg_file.write_text(json.dumps(initial_data), encoding="utf-8")

    import frontend.routers.domain_config as dc_module
    monkeypatch.setattr(dc_module, "CONFIG_PATH", test_cfg_file)

    payload = {"config": {"rate_limits": {"example.com": 5.0}, "hotlink_protected": ["example.com"]}}
    res = client.post("/api/domain-config/save", json=payload)
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "ok"

    # Verify file content updated
    updated_disk_data = json.loads(test_cfg_file.read_text(encoding="utf-8"))
    assert updated_disk_data["rate_limits"]["example.com"] == 5.0
    assert "example.com" in updated_disk_data["hotlink_protected"]


def test_save_domain_config_endpoint_invalid_json(tmp_path, monkeypatch):
    """Verify POST /api/domain-config/save rejects invalid JSON payloads gracefully."""
    test_cfg_file = tmp_path / "domain_config.json"
    test_cfg_file.write_text("{}", encoding="utf-8")

    import frontend.routers.domain_config as dc_module
    monkeypatch.setattr(dc_module, "CONFIG_PATH", test_cfg_file)

    res = client.post(
        "/api/domain-config/save",
        data={"raw_json": "INVALID_JSON_{{}"},
        headers={"content-type": "application/x-www-form-urlencoded", "hx-request": "true"},
    )
    assert res.status_code == 400
    assert "Invalid JSON" in res.text


def test_domain_studio_elements_in_index_html():
    """Verify index.html contains Domain Config Studio UI elements and JS handlers."""
    template_path = Path(__file__).parent.parent / "frontend" / "templates" / "index.html"
    content = template_path.read_text(encoding="utf-8")
    assert 'id="domain-studio-view"' in content
    assert 'id="nav-domain-studio"' in content
    assert 'function showDomainStudio()' in content
    assert 'function loadDomainStudio()' in content
    assert 'id="domain-studio-raw-json"' in content

