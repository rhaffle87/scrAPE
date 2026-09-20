from unittest.mock import MagicMock, patch
from scraper.google_images import SearchProviderScraper


def test_searxng_search_provider():
    """Verify SearXNG JSON search decoding."""
    scraper = SearchProviderScraper()

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {"url": "https://example.com/gallery/1/"},
            {"url": "https://example.com/gallery/2/"},
        ]
    }

    with patch.object(scraper.http, "get", return_value=mock_response):
        links = scraper._search_searxng("cyberpunk", max_results=10)
        assert len(links) == 2
        assert links[0] == "https://example.com/gallery/1/"


def test_startpage_search_provider():
    """Verify StartPage HTML search decoding."""
    scraper = SearchProviderScraper()

    mock_response = MagicMock()
    mock_response.text = (
        '<html><body><a class="result-link" href="https://example-gallery.org/item/1">Item 1</a></body></html>'
    )

    with patch.object(scraper.http, "get", return_value=mock_response):
        links = scraper._search_startpage("synthwave", max_results=5)
        assert len(links) == 1
        assert links[0] == "https://example-gallery.org/item/1"
