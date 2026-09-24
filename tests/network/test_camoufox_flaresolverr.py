import pytest
from typing import Any
from unittest.mock import MagicMock
from network.http_client import HttpClient


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


def test_camoufox_launcher_kwargs_and_viewport_isolation(monkeypatch):
    """Targeted regression test: verify Camoufox is launched without invalid Playwright Firefox kwargs

    (window_size, user_data_dir) and that viewport geometry is configured on new_page().
    """
    import sys
    from unittest.mock import MagicMock

    client = HttpClient()
    url = "https://example-turnstile.com/gallery"

    captured_init_kwargs = {}
    captured_new_page_kwargs = {}

    mock_page = MagicMock()
    mock_page.content.return_value = "<html><body>Target Gallery Content</body></html>"
    mock_page.context.cookies.return_value = [{"name": "cf_clearance", "value": "camou_token"}]

    class MockBrowser:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def new_page(self, **kwargs):
            captured_new_page_kwargs.update(kwargs)
            return mock_page

    class MockCamoufox:
        def __init__(self, **kwargs):
            # Adversarial simulation: mimic Playwright Firefox launch behavior
            forbidden_args = {"window_size", "user_data_dir"}
            invalid_found = forbidden_args.intersection(kwargs.keys())
            if invalid_found:
                raise TypeError(f"BrowserType.launch() got an unexpected keyword argument '{list(invalid_found)[0]}'")
            captured_init_kwargs.update(kwargs)

        def __enter__(self):
            return MockBrowser()

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_sync_api = MagicMock()
    mock_sync_api.Camoufox = MockCamoufox
    mock_camoufox_module = MagicMock()
    mock_camoufox_module.sync_api = mock_sync_api

    monkeypatch.setitem(sys.modules, "camoufox", mock_camoufox_module)
    monkeypatch.setitem(sys.modules, "camoufox.sync_api", mock_sync_api)

    html, cookies = client._get_with_camoufox(url)

    # 1. Assert invalid kwargs are never passed to Camoufox launch
    assert "window_size" not in captured_init_kwargs
    assert "user_data_dir" not in captured_init_kwargs

    # 2. Assert valid stealth kwargs are properly supplied
    assert "headless" in captured_init_kwargs
    assert "os" in captured_init_kwargs
    assert captured_init_kwargs.get("humanize") is True

    # 3. Assert viewport geometry is set on new_page()
    assert captured_new_page_kwargs == {"viewport": {"width": 1920, "height": 1080}}

    # 4. Assert returned HTML and extracted cookies
    assert "Target Gallery Content" in html
    assert any(c["name"] == "cf_clearance" for c in cookies)


def test_preferred_engine_routing_and_host_memory(monkeypatch):
    client = HttpClient()
    url = "https://preferred-engine-test.com/page"
    host = "preferred-engine-test.com"

    # Reset host memory cache
    HttpClient._preferred_engine_by_host.clear()

    executed_order = []

    from network.stealth.base import StealthStrategy, StealthResponse

    class MockCamoufoxStrategy(StealthStrategy):
        name = "camoufox"
        def is_available(self) -> bool: return True
        def can_handle(self, url: str, host: str) -> bool: return True
        def execute(self, url: str, client: Any) -> StealthResponse | None:
            executed_order.append("camoufox")
            return StealthResponse(200, "<html>Camoufox Solved</html>", {})

    class MockCrawl4AIStrategy(StealthStrategy):
        name = "crawl4ai"
        def is_available(self) -> bool: return True
        def can_handle(self, url: str, host: str) -> bool: return True
        def execute(self, url: str, client: Any) -> StealthResponse | None:
            executed_order.append("crawl4ai")
            return StealthResponse(200, "<html>Crawl4AI Solved</html>", {})
            
    class MockOtherStrategy(StealthStrategy):
        name = "other"
        def is_available(self) -> bool: return True
        def can_handle(self, url: str, host: str) -> bool: return True
        def execute(self, url: str, client: Any) -> StealthResponse | None:
            executed_order.append("other")
            return None # Simulate failure

    # Replace pipeline strategies with our mocks
    client.stealth_pipeline.strategies = [
        MockOtherStrategy(),
        MockCrawl4AIStrategy(),
        MockCamoufoxStrategy()
    ]

    # Call with preferred_engine="camoufox"
    print("Running with strategies:", [s.name for s in client.stealth_pipeline.strategies])
    html, _ = client._execute_fallbacks(url, preferred_engine="camoufox")
    print("Returned HTML:", html)
    print("Executed Order:", executed_order)
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

