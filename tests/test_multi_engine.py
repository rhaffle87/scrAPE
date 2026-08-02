import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import logging
from scraper.google_images import SearchProviderScraper

logging.basicConfig(level=logging.INFO)

from unittest.mock import patch

def test_multi_engine():
    scraper = SearchProviderScraper()
    print("Executing search_pages...")
    with patch.object(scraper, 'search_pages', return_value=["https://example.com/mock_link"]):
        links = scraper.search_pages("cats", max_results=10)
        print(f"Found {len(links)} links.")
        for link in links:
            print(link)
        assert len(links) > 0

if __name__ == "__main__":
    test_multi_engine()
