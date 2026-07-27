"""
test_open_web_seed_manifests.py — Live unmocked integration test for open web seed manifests.

Dynamically discovers all seed files in seeds/ and validates each through
SeedManifest parsing and API endpoints.
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from frontend.app import app, SEEDS_DIR
from src.core.seed_manifest import SeedManifest

client = TestClient(app)

# Dynamically discover all seed files
_seed_files = sorted(SEEDS_DIR.glob("*.txt")) if SEEDS_DIR.exists() else []


@pytest.mark.parametrize("seed_file", _seed_files, ids=[f.stem for f in _seed_files])
def test_live_manifest_parse(seed_file):
    """Unmocked validation of a seed manifest file."""
    assert seed_file.exists(), f"{seed_file.name} must exist"

    # 1. Parse using SeedManifest
    manifest = SeedManifest.from_file(seed_file)
    assert manifest.subject_name is not None and len(manifest.subject_name) > 0
    assert len(manifest.domains) > 0
    assert len(manifest.all_seed_urls) > 0


@pytest.mark.parametrize("seed_file", _seed_files, ids=[f.stem for f in _seed_files])
def test_live_manifest_api_validate(seed_file):
    """Validate seed manifest content via API endpoint."""
    content = seed_file.read_text(encoding="utf-8")
    val_res = client.post("/api/seeds/validate", json={"content": content})
    assert val_res.status_code == 200
    assert val_res.json()["is_valid"] is True
    assert len(val_res.json()["warnings"]) == 0


@pytest.mark.parametrize("seed_file", _seed_files, ids=[f.stem for f in _seed_files])
def test_live_manifest_api_read(seed_file):
    """Read back seed manifest via API endpoint."""
    get_res = client.get(f"/api/seeds/{seed_file.name}")
    assert get_res.status_code == 200
    assert get_res.json()["filename"] == seed_file.name
