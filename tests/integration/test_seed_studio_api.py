import pytest
from fastapi.testclient import TestClient
from frontend.app import app, SEEDS_DIR

client = TestClient(app)

# ---------------------------------------------------------------------------
# Fixture: ensure at least one seed file exists so list tests pass in CI
# (seeds/ is gitignored; the fixture creates and removes a sentinel file)
# ---------------------------------------------------------------------------
_SENTINEL_SEED = "_test_sentinel.txt"
_SENTINEL_CONTENT = "# Subject : Sentinel Test Subject\n\nhttps://example.com/sentinel/\n"

@pytest.fixture(scope="module", autouse=True)
def ensure_seed_exists():
    """Create a throwaway seed file so SEEDS_DIR is never empty during this module."""
    sentinel = SEEDS_DIR / _SENTINEL_SEED
    created = False
    if not sentinel.exists():
        sentinel.write_text(_SENTINEL_CONTENT, encoding="utf-8")
        created = True
    yield
    if created and sentinel.exists():
        sentinel.unlink(missing_ok=True)


def test_api_list_seeds():
    response = client.get("/api/seeds")
    assert response.status_code == 200
    data = response.json()
    assert "seeds" in data
    assert isinstance(data["seeds"], list)
    assert len(data["seeds"]) > 0


def test_api_get_seed_details():
    response = client.get("/api/seeds")
    seeds = response.json()["seeds"]
    if seeds:
        filename = seeds[0]["filename"]
        res = client.get(f"/api/seeds/{filename}")
        assert res.status_code == 200
        seed_data = res.json()
        assert seed_data["filename"] == filename
        assert "content" in seed_data
        assert "domains" in seed_data

def test_api_save_validate_and_delete_seed():
    test_filename = "_test_studio_manifest.txt"
    test_content = "# Subject : Test Studio Subject\n\n# type: image\nhttps://example.com/gallery/1\n"
    
    # 1. Validate
    val_res = client.post("/api/seeds/validate", json={"content": test_content})
    assert val_res.status_code == 200
    assert val_res.json()["is_valid"] is True

    # 2. Save
    save_res = client.post("/api/seeds", json={"filename": test_filename, "content": test_content, "overwrite": True})
    assert save_res.status_code == 200
    assert save_res.json()["success"] is True

    # 3. Read back
    read_res = client.get(f"/api/seeds/{test_filename}")
    assert read_res.status_code == 200
    assert "Test Studio Subject" in read_res.json()["content"]

    # 4. Delete
    del_res = client.delete(f"/api/seeds/{test_filename}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

def test_api_discover_urls_pattern_generation():
    from unittest.mock import patch
    import httpx
    
    with patch("src.network.http_client.HttpClient.get") as mock_get:
        
        mock_resp = httpx.Response(200, request=httpx.Request("GET", "https://example.com"))
        mock_get.return_value = mock_resp
        
        discover_res = client.post("/api/seeds/discover", json={"query": "testsubject", "domains": ["example.com"]})
        assert discover_res.status_code == 200
        data = discover_res.json()
        assert "discovered_urls" in data
        assert "tested_count" in data
        assert data["tested_count"] >= 10
