"""Unit test verifying SSRF protection on target seed URLs."""

from fastapi.testclient import TestClient
from frontend.app import app

client = TestClient(app)

def test_ssrf_protection_rejects_internal_and_loopback_ips():
    blocked_targets = [
        "http://127.0.0.1:8191/v1",
        "http://localhost:10001/",
        "http://169.254.169.254/latest/meta-data",
        "http://10.0.0.1/admin",
        "http://192.168.1.1/gateway",
    ]
    for target in blocked_targets:
        res = client.post("/api/run", json={"keyword": "ssrf_test", "seed_urls": target})
        assert res.status_code == 400, f"Expected 400 for {target}, got {res.status_code}"
        detail = res.json().get("detail", "")
        assert "Blocked internal/private IP" in detail or "SSRF" in detail
