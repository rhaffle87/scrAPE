"""
test_e2e_seed_studio_subjects.py — Fast End-to-end test for Seed Studio subject creation.

Tests creating, discovering, validating, saving, and parsing thorough seed manifests
using generic test fixtures without hardcoded subject names or domain URLs.
"""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from frontend.app import app, SEEDS_DIR
from src.core.seed_manifest import SeedManifest

client = TestClient(app)


@patch("src.utils.http_client.HttpClient.get")
def test_e2e_seed_studio_subject_alpha(mock_http_get):
    """End-to-end Seed Studio creation and validation for a generic subject."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "<html><body>Found content</body></html>"
    mock_http_get.return_value = mock_resp

    subject_name = "test_subject_alpha"
    filename = "test_subject_alpha.txt"

    # 1. Run Auto Discovery for candidate search URLs across target domains
    target_domains = ["example.com", "test-images.example.org"]
    disc_res = client.post("/api/seeds/discover", json={"query": subject_name, "domains": target_domains})
    assert disc_res.status_code == 200
    disc_data = disc_res.json()
    assert "discovered_urls" in disc_data
    assert disc_data["tested_count"] > 0

    # 2. Build thorough seed manifest content with rich domain annotations
    content = f"""# Subject : {subject_name} / alpha / test_alpha_cos

# -- example.com --
# type: mixed
# crawl: direct
# [CDN] cdn.example.com
https://www.example.com/search?q={subject_name}
https://www.example.com/a/{subject_name}_album1
https://www.example.com/a/{subject_name}_album2

# -- test-images.example.org --
# type: mixed
# crawl: index->detail
# depth: 1
# Rate-limit: 0.5 req/s
# [CDN] cdn.example.org
https://test-images.example.org/videos/{subject_name}
https://test-images.example.org/search/{subject_name}

# -- gallery.example.net --
# type: image
# crawl: index->detail
# depth: 1
# [CDN] static.example.net
https://gallery.example.net/category/{subject_name}/
https://gallery.example.net/{subject_name}-collection-photos/

# -- archive.example.io --
# type: image
# crawl: direct
# [CDN] files.example.io
https://archive.example.io/?s={subject_name}
https://archive.example.io/tag/{subject_name}/

# -- social.example.com --
# type: image
# crawl: direct
# engine: camoufox
https://social.example.com/{subject_name}/

# -- search.example.com --
# type: image
# crawl: direct
# engine: flaresolverr
https://search.example.com/search?q={subject_name}&f=media
"""

    # 3. Validate manifest content via Seed Studio validation endpoint
    val_res = client.post("/api/seeds/validate", json={"content": content})
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["is_valid"] is True
    assert len(val_data["warnings"]) == 0

    # 4. Save manifest via Seed Studio save endpoint
    save_res = client.post("/api/seeds", json={"filename": filename, "content": content, "overwrite": True})
    assert save_res.status_code == 200
    assert save_res.json()["success"] is True

    # 5. Read back manifest details via API
    get_res = client.get(f"/api/seeds/{filename}")
    assert get_res.status_code == 200
    seed_json = get_res.json()
    assert seed_json["filename"] == filename
    assert subject_name in seed_json["content"]
    assert len(seed_json["domains"]) >= 5

    # 6. Verify file on disk and parse with core SeedManifest
    target_file = SEEDS_DIR / filename
    assert target_file.exists()

    manifest = SeedManifest.from_file(target_file)
    assert manifest.subject_name is not None
    assert len(manifest.domains) >= 5
    assert len(manifest.all_seed_urls) >= 10

    # Check annotations parsed correctly
    domain_map = manifest.domain_map
    assert any(d == "example.com" or d.endswith(".example.com") for d in domain_map)
    assert domain_map.get("test-images.example.org") is not None
    assert domain_map["test-images.example.org"].rate_limit == 0.5
    assert domain_map.get("social.example.com") is not None
    assert domain_map["social.example.com"].preferred_engine == "camoufox"

    # Cleanup test file
    if target_file.exists():
        target_file.unlink()


@patch("src.utils.http_client.HttpClient.get")
def test_e2e_seed_studio_subject_beta(mock_http_get):
    """End-to-end Seed Studio creation and validation for a second generic subject."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "<html><body>Found content</body></html>"
    mock_http_get.return_value = mock_resp

    subject_name = "test subject beta"
    query_slug = "test_subject_beta"
    filename = "test_subject_beta.txt"

    # 1. Run Auto Discovery
    target_domains = ["example.com", "test-images.example.org"]
    disc_res = client.post("/api/seeds/discover", json={"query": query_slug, "domains": target_domains})
    assert disc_res.status_code == 200
    disc_data = disc_res.json()
    assert "discovered_urls" in disc_data
    assert disc_data["tested_count"] > 0

    # 2. Build seed manifest content
    content = f"""# Subject : Test Subject Beta / Beta / beta_cos

# -- example.com --
# type: mixed
# crawl: direct
# [CDN] cdn.example.com
https://www.example.com/search?q={query_slug}
https://www.example.com/a/{query_slug}_set1
https://www.example.com/a/{query_slug}_set2

# -- test-images.example.org --
# type: mixed
# crawl: index->detail
# depth: 1
# Rate-limit: 0.5 req/s
# [CDN] cdn.example.org
https://test-images.example.org/videos/{query_slug}
https://test-images.example.org/search/{query_slug}

# -- gallery.example.net --
# type: image
# crawl: index->detail
# depth: 1
# [CDN] static.example.net
https://gallery.example.net/category/{query_slug}/
https://gallery.example.net/{query_slug}-collection-photos/

# -- archive.example.io --
# type: image
# crawl: direct
# [CDN] files.example.io
https://archive.example.io/?s={query_slug}
https://archive.example.io/tag/{query_slug}/

# -- social.example.com --
# type: image
# crawl: direct
# engine: camoufox
https://social.example.com/{query_slug}/

# -- search.example.com --
# type: image
# crawl: direct
# engine: flaresolverr
https://search.example.com/search?q={query_slug}&f=media
"""

    # 3. Validate
    val_res = client.post("/api/seeds/validate", json={"content": content})
    assert val_res.status_code == 200
    val_data = val_res.json()
    assert val_data["is_valid"] is True
    assert len(val_data["warnings"]) == 0

    # 4. Save
    save_res = client.post("/api/seeds", json={"filename": filename, "content": content, "overwrite": True})
    assert save_res.status_code == 200
    assert save_res.json()["success"] is True

    # 5. Read back
    get_res = client.get(f"/api/seeds/{filename}")
    assert get_res.status_code == 200
    seed_json = get_res.json()
    assert seed_json["filename"] == filename
    assert "Test Subject Beta" in seed_json["content"]
    assert len(seed_json["domains"]) >= 5

    # 6. Parse with SeedManifest
    target_file = SEEDS_DIR / filename
    assert target_file.exists()

    manifest = SeedManifest.from_file(target_file)
    assert manifest.subject_name is not None
    assert len(manifest.domains) >= 5
    assert len(manifest.all_seed_urls) >= 10

    # Check annotations
    domain_map = manifest.domain_map
    assert any(d == "example.com" or d.endswith(".example.com") for d in domain_map)
    assert domain_map.get("test-images.example.org") is not None
    assert domain_map["test-images.example.org"].rate_limit == 0.5

    # Cleanup test file
    if target_file.exists():
        target_file.unlink()
