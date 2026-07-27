from __future__ import annotations

from pathlib import Path
from core.seed_manifest import SeedManifest


def test_seed_manifest_parse_insecure_ssl(tmp_path):
    """Test parsing # ssl: insecure annotation in seed manifest."""
    manifest_content = """# Subject: SSL Test
# type: image | crawl: direct
# ssl: insecure
https://insecure.example.com/tag/test
"""
    manifest_file = tmp_path / "ssl_test.txt"
    manifest_file.write_text(manifest_content, encoding="utf-8")

    manifest = SeedManifest.from_file(manifest_file)
    assert len(manifest.domains) == 1
    profile = manifest.domains[0]
    assert profile.domain == "insecure.example.com"
    assert profile.allow_insecure_ssl is True


def test_telemetry_stats_returns_real_structure():
    """Test that get_telemetry_stats returns real state structure."""
    from frontend.app import get_telemetry_stats

    stats = get_telemetry_stats()
    assert "status" in stats
    assert "rps" in stats
    assert "speed_kbps" in stats
    assert "healthy_proxies" in stats
    assert "http_status_codes" in stats
