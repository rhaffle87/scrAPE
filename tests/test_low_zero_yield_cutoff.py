import pytest
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse
import httpx

from core.engine import ScrapingEngine
from core.models import ImageItem, VideoItem, EngineOptions, ScrapeResult
from core.seed_manifest import DomainProfile
from utils.http_client import ScraperBypassError

def test_consecutive_failures_circuit_breaker():
    """Verify domains with 3 consecutive fetch errors are cut off from crawling completely."""
    engine = ScrapingEngine(workers=1)
    
    # Mock search provider to fail with exceptions
    mock_provider = MagicMock()
    mock_provider.scrape_page.side_effect = Exception("Mocked WAF bypass failure")
    engine.search_provider = mock_provider

    # Mock video scraper
    mock_video_scraper = MagicMock()
    mock_video_scraper.search.return_value = []
    engine.video_scraper = mock_video_scraper

    # Enqueue 10 pages for test-fail.com
    pages = [f"https://test-fail.com/page{i}" for i in range(10)]
    engine.search_provider.discover_links.side_effect = (
        lambda url, *args, **kwargs: pages if "start" in url else []
    )
    engine.search_provider.search.return_value = ["https://test-fail.com/start"]

    profile = DomainProfile(domain="test-fail.com", crawl_depth=2)
    domain_profiles = {"test-fail.com": profile}

    result = engine.run(
        keyword="test",
        max_results=5,
        output_format="json",
        download_media=False,
        seed_urls=["https://test-fail.com/start"],
        domain_profiles=domain_profiles,
        page_limit=20,
        crawl_depth=2,
        ignore_robots=True,
    )

    # The scrape_page should be called exactly 3 times (for page0, page1, page2)
    # after which the consecutive failure circuit-breaker flags the host and skips the rest.
    # Note: the start page also gets crawled first. If it succeeds or fails, let's trace:
    # If the start page fails, it is failure 1. Then page0 is failure 2, page1 is failure 3.
    # So start page + page0 + page1 = 3 failures total.
    # Therefore, scrape_page should be called exactly 3 times.
    assert mock_provider.scrape_page.call_count == 3
    
    stats = result.domain_stats.get("test-fail.com")
    assert stats is not None
    # We scanned 3 pages (start page + 2 subpages) before cutoff
    assert stats["pages_scanned"] == 3
    assert stats["error_other_count"] == 3

    # The remaining 8 pages should be marked as "host_failed_skipped"
    skipped_reports = [
        r for r in result.page_reports if r.reason == "host_failed_skipped"
    ]
    assert len(skipped_reports) == 8


def test_auth_wall_redirect_cutoff():
    """Verify that a single redirect to a login/auth page triggers immediate host cutoff."""
    engine = ScrapingEngine(workers=1)
    
    # Mock search provider
    mock_provider = MagicMock()
    
    # First call (start page): succeeds and returns links.
    # Second call (page0): returns login_wall status.
    # Subsequent calls should not happen because it is immediately cut off.
    def scrape_side_effect(url, *args, **kwargs):
        if "start" in url:
            return [], [], "ok"
        return [], [], "fetch_error:login_wall"

    mock_provider.scrape_page.side_effect = scrape_side_effect
    engine.search_provider = mock_provider

    # Mock video scraper
    mock_video_scraper = MagicMock()
    mock_video_scraper.search.return_value = []
    engine.video_scraper = mock_video_scraper

    pages = [f"https://auth-wall.com/page{i}" for i in range(10)]
    engine.search_provider.discover_links.side_effect = (
        lambda url, *args, **kwargs: pages if "start" in url else []
    )
    engine.search_provider.search.return_value = ["https://auth-wall.com/start"]

    profile = DomainProfile(domain="auth-wall.com", crawl_depth=2)
    domain_profiles = {"auth-wall.com": profile}

    result = engine.run(
        keyword="test",
        max_results=5,
        output_format="json",
        download_media=False,
        seed_urls=["https://auth-wall.com/start"],
        domain_profiles=domain_profiles,
        page_limit=20,
        crawl_depth=2,
        ignore_robots=True,
    )

    # Scrape page should be called:
    # 1. start page -> returns "ok" (consecutive failures = 0)
    # 2. page0 -> returns "fetch_error:login_wall" -> immediate cutoff!
    # page1 through page9 are skipped immediately.
    assert mock_provider.scrape_page.call_count == 2
    
    stats = result.domain_stats.get("auth-wall.com")
    assert stats is not None
    assert stats["pages_scanned"] == 2
    
    skipped_reports = [
        r for r in result.page_reports if r.reason == "host_failed_skipped"
    ]
    assert len(skipped_reports) == 9


def test_cached_response_has_request(tmp_path):
    """Verify that HttpClient._load_cache returns an httpx.Response with request and url populated."""
    from utils.http_client import HttpClient

    client = HttpClient()
    url = "https://cached-site.com/subpage"

    mock_response = httpx.Response(
        status_code=200,
        text="<html>Cached content</html>",
        request=httpx.Request("GET", url)
    )
    mock_response.headers["content-type"] = "text/html"

    with patch.object(client, "_cache_path") as mock_cache_path:
        cache_file = tmp_path / "cached_file.txt"
        mock_cache_path.return_value = cache_file

        # Store cache
        client._store_cache(url, mock_response)

        # Load cache
        loaded_response = client._load_cache(url)

        assert loaded_response is not None
        assert loaded_response.status_code == 200
        assert loaded_response.text == "<html>Cached content</html>"

        # Verify response.url works and matches the source URL
        assert loaded_response.url == httpx.URL(url)

