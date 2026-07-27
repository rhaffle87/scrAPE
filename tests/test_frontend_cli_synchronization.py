from __future__ import annotations

from fastapi.testclient import TestClient
from frontend.app import app
from src.cli.main import build_parser


def test_cli_parser_has_enable_governor_flag():
    parser = build_parser()
    args = parser.parse_args(["--keyword", "test", "--enable-governor"])
    assert args.enable_governor is True


def test_api_telemetry_stats_returns_governor_and_db_engine():
    client = TestClient(app)
    response = client.get("/api/telemetry/stats")
    assert response.status_code == 200
    data = response.json()
    assert "cpu_percent" in data
    assert "ram_percent_available" in data
    assert "governor_scale_factor" in data
    assert "db_engine_name" in data
    assert data["db_engine_name"] in ("SQLITE WAL", "POSTGRES / NEON")


def test_htmx_stats_renders_governor_and_db_badges():
    client = TestClient(app)
    response = client.get("/htmx/stats")
    assert response.status_code == 200
    assert "SYS TELEMETRY" in response.text
    assert "DB:" in response.text
    assert "GOV:" in response.text
