import pytest
import os
import json
from fastapi.testclient import TestClient
from frontend.app import app
from network.http_client import HttpClient
from network.session import SessionManager

client = TestClient(app)

def test_waf_cookie_auto_persistence(tmp_path):
    sm = SessionManager()
    test_domain = "test-stealth-domain.com"
    test_cookies = [
        {"name": "cf_clearance", "value": "test_token_xyz123", "domain": f".{test_domain}", "path": "/"}
    ]
    
    # Save session cookies
    sm.save_session(test_domain, test_cookies)
    
    # Verify file saved
    session_file = sm.get_session_file(test_domain)
    assert os.path.exists(session_file)
    
    # Verify loaded session
    loaded = sm.load_session(test_domain)
    assert loaded is not None
    assert loaded == test_cookies
    assert loaded[0]["value"] == "test_token_xyz123"
    
    # Clean up
    sm.evict_session(test_domain)
    assert not os.path.exists(session_file)

def test_api_engine_metrics_endpoint():
    response = client.get("/api/engine/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "cpu_percent" in data
    assert "ram_percent" in data
    assert "disk_percent" in data
    assert "waf_solves" in data
    assert "active_sessions_count" in data
    assert "active_threads" in data
    assert isinstance(data["active_sessions_count"], int)
