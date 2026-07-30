from __future__ import annotations

from pathlib import Path
import pytest
from unittest.mock import MagicMock, patch

from src.network.http_client import HttpClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_fake_tls_map():
    """Return a synthetic tls_impersonate map that mirrors domain_config.json
    without embedding any production domain names directly in test assertions."""
    return {
        "domain-a.example": "chrome124",
        "domain-b.example": "safari17_0",
    }


def test_get_tls_impersonate_resolution():
    """get_tls_impersonate() must return the correct profile for each domain
    and fall back to chrome120 for unconfigured hosts.

    The map is injected via monkeypatch so the test never depends on real
    production domain names or live domain_config.json content.
    """
    fake_map = _make_fake_tls_map()

    with patch.object(HttpClient, "_tls_impersonate_loaded", True), \
         patch.object(HttpClient, "_tls_impersonate_map", fake_map):

        assert HttpClient.get_tls_impersonate("domain-a.example") == "chrome124"
        assert HttpClient.get_tls_impersonate("domain-b.example") == "safari17_0"
        assert HttpClient.get_tls_impersonate("totally-unknown-domain.example") == "chrome120"


@patch("curl_cffi.requests.get")
def test_get_with_curl_cffi_invocation(mock_curl_get):
    """_get_with_curl_cffi() must pass the domain-configured TLS profile
    to curl_cffi.requests.get as the 'impersonate' kwarg.

    The TLS map is injected so the test does not rely on real domain names.
    """
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = "<html><body>TLS Impersonation Test</body></html>"
    mock_resp.cookies.items.return_value = [("session_id", "abc12345")]
    mock_curl_get.return_value = mock_resp

    fake_map = _make_fake_tls_map()

    with patch.object(HttpClient, "_tls_impersonate_loaded", True), \
         patch.object(HttpClient, "_tls_impersonate_map", fake_map):

        client = HttpClient()
        html, cookies = client._get_with_curl_cffi("https://domain-b.example/gallery/1")

    assert "TLS Impersonation Test" in html
    assert any(c["name"] == "session_id" for c in cookies)
    mock_curl_get.assert_called_once()
    assert mock_curl_get.call_args.kwargs["impersonate"] == "safari17_0"
