from fastapi.testclient import TestClient
from frontend.app import app
from src.cli.seed_studio import PatternGenerator, SeedDiscoverer, SeedLinter

client = TestClient(app)


def test_seed_linter_validation():
    """Verify SeedLinter identifies warnings and invalid URLs."""
    linter = SeedLinter()
    content = (
        "# Subject: Test Subject\n"
        "# type: image | crawl: index→detail\n"
        "https://example.com/gallery/1/\n"
        "https://example.com/gallery/2/\n"
        "not_a_valid_url\n"
    )
    report = linter.lint_manifest_text(content)
    assert report["valid"] is False
    assert len(report["errors"]) == 1
    assert "Line 5: Invalid URL" in report["errors"][0]
    assert report["domains_count"] == 1


def test_pattern_generator():
    """Verify PatternGenerator expands paginated URL templates."""
    generator = PatternGenerator()
    urls = generator.generate_paginated_urls("https://example.com/category/{page}/", 1, 3)
    assert len(urls) == 3
    assert urls[0] == "https://example.com/category/1/"
    assert urls[2] == "https://example.com/category/3/"


def test_seed_discoverer():
    """Verify SeedDiscoverer creates formatted manifest text."""
    discoverer = SeedDiscoverer()
    manifest = discoverer.discover_seeds_for_subject("Anime Cyberpunk")
    assert "# Subject: Anime Cyberpunk" in manifest
    assert "https://example.com/gallery/anime-cyberpunk/" in manifest


def test_api_seed_studio_endpoints():
    """Verify WebUI endpoints for seed discovery and linting."""
    resp_discover = client.post("/api/seed/discover", json={"subject": "Neon City"})
    assert resp_discover.status_code == 200
    assert "# Subject: Neon City" in resp_discover.json()["manifest"]

    resp_lint = client.post("/api/seed/lint", json={"content": "https://example.com/\n"})
    assert resp_lint.status_code == 200
    assert resp_lint.json()["valid"] is True
