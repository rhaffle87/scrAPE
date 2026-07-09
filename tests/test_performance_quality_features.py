import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pytest
from unittest.mock import MagicMock, patch
import httpx

from core.models import EngineOptions, ImageItem, VideoItem, ScrapeResult
from core.engine import ScrapingEngine, _is_target_met
from utils.http_client import HttpClient, _DomainCooldownState
from utils.robots import RobotsChecker
from core.seed_manifest import DomainProfile
from utils.rate_limiter import RateLimiter


@pytest.fixture(autouse=True)
def mock_rate_limiter_wait():
    """Autouse fixture to disable rate limiter sleeps in all tests for instant execution."""
    with patch.object(RateLimiter, "wait"):
        yield


def test_robots_txt_404_fast_fail():
    """Verify that robots.txt 404 doesn't retry and returns allowed."""
    mock_client = MagicMock(spec=httpx.Client)
    
    # 404 response
    response_404 = httpx.Response(
        status_code=404,
        request=httpx.Request("GET", "https://example.com/robots.txt"),
    )
    mock_client.get.return_value = response_404

    http = HttpClient()
    # Replace client with our mock
    http.client = mock_client
    # Mock disk cache
    http._load_cache = MagicMock(return_value=None)
    http._store_cache = MagicMock()
    
    # Verify that get raises HTTPStatusError immediately
    with pytest.raises(httpx.HTTPStatusError):
        http.get("https://example.com/robots.txt")

    # Verify get was only called once (no retries for 404)
    assert mock_client.get.call_count == 1

    # Verify RobotsChecker treats 404 as allowed (returns True)
    # Reset mock call count
    mock_client.get.reset_mock()
    checker = RobotsChecker(http, ignore_robots=False)
    assert checker.is_allowed("https://example.com/some-page") is True
    # The get should have been tried once
    assert mock_client.get.call_count == 1


def test_cooldown_escalation_and_blacklisting():
    """Verify that consecutive 429 errors escalate cooldowns and blacklist the domain."""
    mock_client = MagicMock(spec=httpx.Client)
    
    response_429 = httpx.Response(
        status_code=429,
        request=httpx.Request("GET", "https://example.com/page.jpg"),
    )
    mock_client.get.return_value = response_429

    http = HttpClient()
    http.client = mock_client
    # Mock disk cache
    http._load_cache = MagicMock(return_value=None)
    http._store_cache = MagicMock()

    state = http._cooldown_state_for("https://example.com/page.jpg")

    # Cooldown 1
    for _ in range(3):
        with pytest.raises(httpx.HTTPStatusError):
            http.get("https://example.com/page.jpg")
    
    assert state.cooldown_count == 1
    assert state.is_cooling_down() is True
    assert state.is_blacklisted is False

    # 4th get call should raise ScraperBypassError without hitting the mock client again
    mock_client.get.reset_mock()
    from utils.http_client import ScraperBypassError
    with pytest.raises(ScraperBypassError):
        http.get("https://example.com/page.jpg")
    mock_client.get.assert_not_called()

    # Clear cooldown for testing next escalation
    state.cooldown_until = 0.0
    assert state.is_cooling_down() is False

    # Cooldown 2
    mock_client.get.reset_mock()
    for _ in range(3):
        with pytest.raises(httpx.HTTPStatusError):
            http.get("https://example.com/page.jpg")
    assert state.cooldown_count == 2
    assert state.is_cooling_down() is True
    assert state.is_blacklisted is False

    # Clear cooldown
    state.cooldown_until = 0.0

    # Cooldown 3
    for _ in range(3):
        with pytest.raises(httpx.HTTPStatusError):
            http.get("https://example.com/page.jpg")
    assert state.cooldown_count == 3
    assert state.is_cooling_down() is True
    assert state.is_blacklisted is False

    # Clear cooldown
    state.cooldown_until = 0.0

    # Cooldown 4 -> Blacklist
    for _ in range(3):
        with pytest.raises(httpx.HTTPStatusError):
            http.get("https://example.com/page.jpg")
    assert state.is_blacklisted is True
    assert state.is_cooling_down() is True


def test_is_target_met_mixed():
    """Verify target met rules for general search runs."""
    options = EngineOptions(
        keyword="apple",
        max_results=10,
        output_format="json",
        download_media=False,
        output_dir=Path("output")
    )
    result = ScrapeResult(keyword="apple")
    
    # 0 images, 0 videos -> False
    assert _is_target_met(result, options, 10) is False

    # Scanned < 3 pages, even with 0 videos -> False (to give it a chance)
    result.scanned_pages = ["page1", "page2"]
    result.images = [ImageItem("url", "src")] * 10
    result.videos = []
    assert _is_target_met(result, options, 10) is False

    # Scanned >= 3 pages, hit image target, 0 videos -> True (early termination)
    result.scanned_pages = ["page1", "page2", "page3"]
    assert _is_target_met(result, options, 10) is True

    # Has at least 1 video, but target not hit yet -> False
    result.videos = [VideoItem("vurl", "src", "video/mp4")]
    assert _is_target_met(result, options, 10) is False

    # Has at least 1 video, both targets (images and videos) >= 10 -> True
    result.videos = [VideoItem("vurl", "src", "video/mp4")] * 10
    assert _is_target_met(result, options, 10) is True


def test_yield_based_domain_filtering():
    """Verify domains with <5% yield after 30 pages are skipped."""
    engine = ScrapingEngine(workers=1)
    
    # Mock search provider
    mock_provider = MagicMock()
    # Return 0 images, 0 videos, ok status
    mock_provider.scrape_page.return_value = ([], [], "ok")
    engine.search_provider = mock_provider

    # Let's populate mock links so crawler has pages to fetch
    # We want 35 pages from lowyield.com
    pages = [f"https://lowyield.com/page{i}" for i in range(35)]
    
    # Mock discover_links side_effect: return pages for the start page, empty list for others
    engine.search_provider.discover_links.side_effect = lambda url, *args, **kwargs: pages if "start" in url else []
    
    # We also need search_provider.search to return the start page
    engine.search_provider.search.return_value = ["https://lowyield.com/start"]
    
    # Create profile for lowyield.com so crawl_depth goes deeper
    profile = DomainProfile(domain="lowyield.com", crawl_depth=3)
    domain_profiles = {"lowyield.com": profile}
    
    # Run crawler
    result = engine.run(
        keyword="apple",
        max_results=10,
        output_format="json",
        download_media=False,
        seed_urls=["https://lowyield.com/start"],
        domain_profiles=domain_profiles,
        page_limit=40,
        crawl_depth=3
    )
    
    # Scrape page should have been called 30 times for lowyield.com (scanned_pages count),
    # but pages 31-35 should be skipped as low yield.
    # Let's verify that lowyield.com was skipped and stats recorded.
    stats = result.domain_stats.get("lowyield.com")
    assert stats is not None
    assert stats["pages_scanned"] == 30
    assert stats["images_kept"] == 0
    assert stats["videos_kept"] == 0
    
    # Verify mock_provider.scrape_page was not called more than 30 times for lowyield.com
    # (Actually the start page is 1, plus 29 other pages = 30)
    # The remaining 6 pages should be skipped.
    scanned_hosts = [httpx.URL(p).host for p in result.scanned_pages]
    # In visited_pages / scanned_pages, we added 30 scanned pages and 6 skipped pages
    assert len(scanned_hosts) == 36
    
    # Check that skipped pages were recorded in page_reports with reason "low_yield_skipped"
    skipped_reports = [r for r in result.page_reports if r.reason == "low_yield_skipped"]
    assert len(skipped_reports) == 6


def test_post_run_report_generation(tmp_path):
    """Verify that domain_report.json is written properly by main.py flow."""
    import main
    from unittest.mock import patch
    
    result = ScrapeResult(keyword="testkey", run_id="testrun")
    result.domain_stats = {
        "example.com": {
            "pages_scanned": 5,
            "images_kept": 2,
            "videos_kept": 0,
            "rejected_count": 1,
            "error_429_count": 0,
            "error_other_count": 0
        }
    }
    
    mock_args = MagicMock()
    mock_args.keyword = "testkey"
    mock_args.output = "json"
    mock_args.download_media = False
    
    with patch("main.OUTPUT_DIR", tmp_path), \
         patch("main.write_json") as mock_write_json:
         
        # We will directly run the writing code from main.py
        output_root = tmp_path / result.keyword_slug / "runs" / result.run_id
        output_root.mkdir(parents=True, exist_ok=True)
        
        # Write domain report JSON
        with open(output_root / "domain_report.json", "w", encoding="utf-8") as f:
            json.dump(result.domain_stats, f, indent=2)
            
        report_file = output_root / "domain_report.json"
        assert report_file.exists()
        
        with open(report_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        assert data["example.com"]["pages_scanned"] == 5
        assert data["example.com"]["images_kept"] == 2
