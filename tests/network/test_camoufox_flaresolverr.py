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

    Validates that all kwargs passed to Camoufox are strictly checked against
    camoufox.launch_options's actual parameter signature (via inspect.signature),
    rejecting illegal Chromium/arbitrary kwargs like window_size or user_data_dir.
    """
    import inspect
    import sys
    from unittest.mock import MagicMock

    client = HttpClient()
    url = "https://example-turnstile.com/gallery"

    # Derive valid parameter names dynamically from real camoufox.launch_options and Playwright BrowserType.launch signatures
    try:
        import camoufox
        from playwright.sync_api import BrowserType
        valid_camou_params = set(inspect.signature(camoufox.launch_options).parameters.keys())
        valid_playwright_params = set(inspect.signature(BrowserType.launch).parameters.keys())
        allowed_launch_kwargs = valid_camou_params.union(valid_playwright_params)
    except Exception:
        allowed_launch_kwargs = {
            "headless", "os", "humanize", "config", "geoip", "addons",
            "fonts", "screen", "window", "fingerprint", "proxy", "executable_path",
            "args", "env", "timeout", "firefox_user_prefs", "slow_mo"
        }

    # Ensure prohibited chromium/persistent kwargs are not in the allowed signature
    assert "window_size" not in allowed_launch_kwargs
    assert "user_data_dir" not in allowed_launch_kwargs

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
            # Adversarial simulation: strictly enforce signature constraints derived from upstream
            for kw in kwargs:
                if kw not in allowed_launch_kwargs:
                    raise TypeError(f"BrowserType.launch() got an unexpected keyword argument '{kw}'")
            captured_init_kwargs.update(kwargs)

        def __enter__(self):
            return MockBrowser()

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    # Verify MockCamoufox independently rejects arbitrary kwargs based on signature, not hardcoded diff names
    with pytest.raises(TypeError, match="unexpected keyword argument 'arbitrary_invalid_param'"):
        MockCamoufox(arbitrary_invalid_param=True)
    with pytest.raises(TypeError, match="unexpected keyword argument 'window_size'"):
        MockCamoufox(window_size=(1920, 1080))
    with pytest.raises(TypeError, match="unexpected keyword argument 'user_data_dir'"):
        MockCamoufox(user_data_dir="/tmp/test")

    mock_sync_api = MagicMock()
    mock_sync_api.Camoufox = MockCamoufox
    mock_camoufox_module = MagicMock()
    mock_camoufox_module.sync_api = mock_sync_api

    monkeypatch.setitem(sys.modules, "camoufox", mock_camoufox_module)
    monkeypatch.setitem(sys.modules, "camoufox.sync_api", mock_sync_api)

    html, cookies = client._get_with_camoufox(url)

    # 1. Assert all passed kwargs are strictly within the real Camoufox launch signature
    for passed_kw in captured_init_kwargs:
        assert passed_kw in allowed_launch_kwargs, f"Unexpected kwarg '{passed_kw}' passed to Camoufox"

    # 2. Assert specific forbidden Chromium/Playwright kwargs are absent
    assert "window_size" not in captured_init_kwargs
    assert "user_data_dir" not in captured_init_kwargs

    # 3. Assert valid stealth kwargs are properly supplied
    assert "headless" in captured_init_kwargs
    assert "os" in captured_init_kwargs
    assert captured_init_kwargs.get("humanize") is True

    # 4. Assert viewport geometry is set on new_page()
    assert captured_new_page_kwargs == {"viewport": {"width": 1920, "height": 1080}}

    # 5. Assert returned HTML and extracted cookies
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

