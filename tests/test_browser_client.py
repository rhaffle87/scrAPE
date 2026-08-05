"""
tests/test_browser_client.py
Unit tests for BrowserClientMixin and browser_client.py:
  - Verifies BrowserClientMixin exports and method presence
  - Verifies HttpClient inherits BrowserClientMixin
"""
from __future__ import annotations

from network.browser_client import BrowserClientMixin
from network.http_client import HttpClient


def test_browser_client_mixin_methods_exist():
    """BrowserClientMixin must define all expected _get_with_* browser methods."""
    expected_methods = [
        "_get_with_crawlee_cheerio",
        "_get_with_crawlee_puppeteer",
        "_get_with_drissionpage",
        "_get_with_helium",
        "_get_with_uc",
        "_solve_cloudflare_captcha_uc",
        "_get_with_camoufox",
        "_get_with_nodriver",
        "_get_with_flaresolverr",
        "_get_with_crawl4ai",
    ]
    for method_name in expected_methods:
        assert hasattr(BrowserClientMixin, method_name), (
            f"BrowserClientMixin is missing method '{method_name}'"
        )


def test_http_client_inherits_browser_client_mixin():
    """HttpClient must inherit from BrowserClientMixin."""
    assert issubclass(HttpClient, BrowserClientMixin), (
        "HttpClient must inherit from BrowserClientMixin"
    )
    client = HttpClient()
    assert isinstance(client, BrowserClientMixin), (
        "HttpClient instance must be an instance of BrowserClientMixin"
    )


def test_http_client_has_all_browser_fallback_methods():
    """HttpClient instance must have all browser fallback methods available."""
    client = HttpClient()
    expected_methods = [
        "_get_with_crawlee_cheerio",
        "_get_with_crawlee_puppeteer",
        "_get_with_drissionpage",
        "_get_with_helium",
        "_get_with_uc",
        "_get_with_camoufox",
        "_get_with_nodriver",
        "_get_with_flaresolverr",
        "_get_with_crawl4ai",
    ]
    for method_name in expected_methods:
        assert hasattr(client, method_name), (
            f"HttpClient is missing browser fallback method '{method_name}'"
        )
