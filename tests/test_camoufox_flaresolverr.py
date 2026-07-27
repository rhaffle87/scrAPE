import pytest
from unittest.mock import MagicMock
from utils.http_client import HttpClient


def test_flaresolverr_fallback_success(monkeypatch):
    client = HttpClient()
    url = "https://flaresolverr-test.com"
    HttpClient._flaresolverr_online = True

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "ok",
        "message": "Challenge solved!",
        "solution": {
            "response": "<html>FlareSolverr HTML</html>",
            "cookies": [{"name": "cf_clearance", "value": "test_clearance", "domain": "flaresolverr-test.com"}],
        },
    }

    class MockHttpxClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, *args, **kwargs):
            res = MagicMock()
            res.status_code = 200
            return res

        def post(self, *args, **kwargs):
            return mock_response

    monkeypatch.setattr("httpx.Client", MockHttpxClient)

    html, cookies = client._get_with_flaresolverr(url)
    assert "FlareSolverr HTML" in html
    assert len(cookies) == 1
    assert cookies[0]["name"] == "cf_clearance"
    assert cookies[0]["value"] == "test_clearance"


def test_flaresolverr_fallback_error(monkeypatch):
    client = HttpClient()
    url = "https://flaresolverr-error.com"
    HttpClient._flaresolverr_online = True

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "error",
        "message": "Error solving challenge",
    }

    class MockHttpxClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, *args, **kwargs):
            res = MagicMock()
            res.status_code = 200
            return res

        def post(self, *args, **kwargs):
            return mock_response

    monkeypatch.setattr("httpx.Client", MockHttpxClient)

    with pytest.raises(Exception) as exc_info:
        client._get_with_flaresolverr(url)

    assert "FlareSolverr error" in str(exc_info.value)


def test_camoufox_fallback_not_installed(monkeypatch):
    client = HttpClient()
    url = "https://camoufox-test.com"

    import sys

    monkeypatch.setitem(sys.modules, "camoufox", None)
    monkeypatch.setitem(sys.modules, "camoufox.sync_api", None)

    with pytest.raises(Exception) as exc_info:
        client._get_with_camoufox(url)

    assert "Camoufox" in str(exc_info.value)


def test_preferred_engine_routing_and_host_memory(monkeypatch):
    client = HttpClient()
    url = "https://preferred-engine-test.com/page"
    host = "preferred-engine-test.com"

    # Reset host memory cache
    HttpClient._preferred_engine_by_host.clear()

    executed_order = []

    def mock_camoufox(u):
        executed_order.append("camoufox")
        return "<html>Camoufox Solved</html>", []

    def mock_crawl4ai(u):
        executed_order.append("crawl4ai")
        return "<html>Crawl4AI Solved</html>", []

    monkeypatch.setattr(client, "_get_with_camoufox", mock_camoufox)
    monkeypatch.setattr(client, "_get_with_crawl4ai", mock_crawl4ai)

    # Call with preferred_engine="camoufox"
    html, _ = client._execute_fallbacks(url, preferred_engine="camoufox")
    assert html is not None
    assert "Camoufox Solved" in html
    assert executed_order == ["camoufox"]

    # Verify host memory cache was recorded
    assert HttpClient._preferred_engine_by_host.get(host) == "camoufox"

    # Subsequent fallback call without preferred_engine parameter should use cached host memory (Camoufox first)
    executed_order.clear()
    html_2, _ = client._execute_fallbacks(url)
    assert html_2 is not None
    assert "Camoufox Solved" in html_2
    assert executed_order == ["camoufox"]


def test_seed_manifest_engine_annotation(tmp_path):
    from core.seed_manifest import SeedManifest

    seed_file = tmp_path / "test_engine_seed.txt"
    seed_file.write_text(
        "# Subject: Test Engine\n"
        "# ---------------------------------------------------------------------------\n"
        "# engine: camoufox\n"
        "https://custom-engine-site.com/gallery\n",
        encoding="utf-8",
    )

    manifest = SeedManifest.from_file(seed_file)
    assert len(manifest.domains) == 1
    profile = manifest.domains[0]
    assert profile.domain == "custom-engine-site.com"
    assert profile.preferred_engine == "camoufox"

