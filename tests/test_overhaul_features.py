import pytest
from pathlib import Path
import json
import httpx
from utils.session_pool import Session, FlatCookies
from core.filters import is_thumbnail_url
from storage.file_downloader import MediaDownloader
from core.models import ScrapeResult


def test_flat_cookies_no_conflict():
    cookies = FlatCookies()
    
    # Test setting values
    cookies.set("test_cookie", "val1")
    assert cookies.get("test_cookie") == "val1"
    
    # Test updating from dict
    cookies.update({"test_cookie": "val2", "another": "val3"})
    assert cookies["test_cookie"] == "val2"
    assert cookies["another"] == "val3"
    
    # Simulate response.cookies update with duplicates/conflicts
    # Standard httpx.Cookies can have multiple values for same key on different paths.
    # In FlatCookies we collapse to single values per name.
    mock_response_cookies = httpx.Cookies()
    mock_response_cookies.set("conflicting_cookie", "domain_val", domain="example.com", path="/")
    mock_response_cookies.set("conflicting_cookie", "subdomain_val", domain="sub.example.com", path="/")
    
    # Converting to dict collapses to one value safely, updating FlatCookies
    cookies.update({c.name: c.value for c in mock_response_cookies.jar})
    assert "conflicting_cookie" in cookies
    # Should not throw any conflict error, collapses to one of the values
    assert cookies["conflicting_cookie"] in ("domain_val", "subdomain_val")


def test_wordpress_thumbnail_filtering():
    # Suffixes should match
    assert is_thumbnail_url("http://example.com/wp-content/uploads/2026/05/img-320x180.jpg") is True
    assert is_thumbnail_url("https://cdn.example.com/assets/example-150x150.png") is True
    assert is_thumbnail_url("https://example.com/image-404x360.webp") is True
    
    # Directory dimension structures (like /320x180/) should match if low-res
    assert is_thumbnail_url("https://epawg.com/contents/videos_screenshots/268000/268635/320x180/5.jpg") is True
    # Directory dimension structures should NOT match if high-res enough (e.g. 640x360 is >= 300x300)
    assert is_thumbnail_url("https://epawg.com/contents/videos_screenshots/268000/268635/640x360/5.jpg") is False

    # Normal image paths should NOT match
    assert is_thumbnail_url("http://example.com/wp-content/uploads/2026/05/img.jpg") is False
    assert is_thumbnail_url("https://cdn.example.com/assets/example-320x.png") is False
    assert is_thumbnail_url("https://example.com/image-12345.webp") is False


class MockOptions:
    def __init__(self, output_dir):
        self.output_dir = output_dir
        self.download_media = True
        self.domain_profiles = {}


def test_dead_url_tracking(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    downloader = MediaDownloader()
    
    # Simulate a dead URL getting registered
    url_404 = "http://example.com/deleted-video.mp4"
    
    # Assert initial empty state
    assert url_404 not in downloader._dead_urls
    
    # Register the 404 dead URL
    with downloader._dead_urls_lock:
        downloader._dead_urls.add(url_404)
        
    # Check that download_file returns False, 404_dead_url
    # _download_file parameters: url, directory, prefix, media_kind
    success, res = downloader._download_file(
        url_404, tmp_path, "prefix", "video"
    )
    assert success is False
    assert res["reason"] == "404_dead_url"
    
    # Test saving dead URLs to file via a mock scrape result in execute_deferred_downloads
    # We will import and call execute_deferred_downloads
    from core.managers import MediaProcessor
    processor = MediaProcessor(downloader)
    
    result = ScrapeResult(
        keyword="test",
        run_id="run123",
        images=[],
        videos=[],
    )
    
    options = MockOptions(output_dir)
    
    # Run processor execute deferred downloads (which is empty but will save dead URLs)
    processor.execute_deferred_downloads(result, options)
    
    # Verify file was written to output/test/dead_urls.json
    dead_urls_file = output_dir / "test" / "dead_urls.json"
    assert dead_urls_file.exists()
    
    with open(dead_urls_file, "r", encoding="utf-8") as f:
        saved_urls = json.load(f)
    assert url_404 in saved_urls
