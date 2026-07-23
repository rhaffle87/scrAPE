import pytest
from unittest.mock import MagicMock
from utils.http_client import HttpClient


def test_flaresolverr_proxy_and_session_forwarding(monkeypatch):
    client = HttpClient(proxy="http://user:pass@proxy.com:8080")
    url = "https://advanced-fs-test.com/gallery"

    posted_payloads = []

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "ok",
        "solution": {
            "response": "<html>FlareSolverr Advanced Solved</html>",
            "cookies": [],
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

        def post(self, url, json=None, **kwargs):
            posted_payloads.append(json)
            return mock_response

    monkeypatch.setattr("httpx.Client", MockHttpxClient)
    HttpClient._flaresolverr_online = True

    html, cookies = client._get_with_flaresolverr(url)
    assert "FlareSolverr Advanced Solved" in html
    assert len(posted_payloads) == 1
    payload = posted_payloads[0]
    assert payload["cmd"] == "request.get"
    assert payload["url"] == url
    assert payload["session"] == "session_advanced-fs-test_com"
    assert payload["proxy"] == {"url": "http://user:pass@proxy.com:8080"}


def test_flaresolverr_health_check_offline(monkeypatch):
    client = HttpClient()
    url = "https://offline-fs-test.com"

    HttpClient._flaresolverr_online = None

    class MockHttpxClientFail:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get(self, *args, **kwargs):
            raise Exception("Connection refused")

    monkeypatch.setattr("httpx.Client", MockHttpxClientFail)

    with pytest.raises(Exception) as exc_info:
        client._get_with_flaresolverr(url)

    assert "FlareSolverr health-check failed" in str(exc_info.value)
    assert getattr(HttpClient, "_flaresolverr_online") is False

    # Second call should fail fast without pinging
    with pytest.raises(Exception) as exc_info_2:
        client._get_with_flaresolverr(url)

    assert "FlareSolverr service is offline" in str(exc_info_2.value)


def test_waf_solve_counts_telemetry(monkeypatch):
    client = HttpClient()
    url = "https://telemetry-test.com/page"

    initial_count = HttpClient._waf_solve_counts.get("flaresolverr", 0)

    def mock_flaresolverr(u):
        return "<html>FlareSolverr Telemetry</html>", []

    monkeypatch.setattr(client, "_get_with_flaresolverr", mock_flaresolverr)

    html, _ = client._execute_fallbacks(url, preferred_engine="flaresolverr")
    assert html is not None
    assert "FlareSolverr Telemetry" in html

    new_count = HttpClient._waf_solve_counts.get("flaresolverr", 0)
    assert new_count == initial_count + 1
