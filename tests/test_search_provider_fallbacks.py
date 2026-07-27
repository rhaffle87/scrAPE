from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from scraper.google_images import SearchProviderScraper


def test_ddg_and_bing_redirect_decoding():
    ddg_redirect = "https://duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Ftarget"
    decoded_ddg = SearchProviderScraper._extract_result_href(ddg_redirect)
    assert decoded_ddg == "https://example.com/target"

    bing_redirect = "https://www.bing.com/linker?url=https%3A%2F%2Fexample.org%2Fpage"
    decoded_bing = SearchProviderScraper._extract_bing_result_href(bing_redirect)
    assert decoded_bing == "https://example.org/page"


def test_search_pages_fallback_to_bing():
    scraper = SearchProviderScraper(ignore_robots=True)

    bing_html_sample = """
    <html>
        <body>
            <li class="b_algo">
                <h2><a href="https://www.bing.com/linker?url=https%3A%2F%2Ftargetsite.com%2Fgallery">Target Gallery</a></h2>
            </li>
        </body>
    </html>
    """

    mock_resp_ddg = MagicMock()
    mock_resp_ddg.text = "<html><body>No results</body></html>"

    mock_resp_bing = MagicMock()
    mock_resp_bing.text = bing_html_sample

    def mock_get(url, *args, **kwargs):
        if "duckduckgo" in url:
            return mock_resp_ddg
        if "bing.com" in url:
            return mock_resp_bing
        raise RuntimeError("Unexpected URL")

    with patch.object(scraper.http, "get", side_effect=mock_get):
        links = scraper.search_pages("nature photos", max_results=5)

    assert "https://targetsite.com/gallery" in links
