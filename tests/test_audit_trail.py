import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from unittest.mock import MagicMock, patch
import httpx
from core.models import ImageItem, VideoItem, ScrapeResult
from core.engine import ScrapingEngine
from core.filters import is_allowed_path
from utils.http_client import HttpClient, ScraperBypassError


def test_item_default_audit_fields():
    """Verify default audit trail fields in models."""
    img = ImageItem(url="https://example.com/img.jpg", source_page="https://example.com")
    assert img.status == "pending"
    assert img.file_path == ""
    assert img.failure_reason == ""
    assert img.hash == ""

    vid = VideoItem(url="https://example.com/vid.mp4", source_page="https://example.com", type="direct")
    assert vid.status == "pending"
    assert vid.file_path == ""
    assert vid.failure_reason == ""
    assert vid.hash == ""


def test_engine_in_place_audit_mapping():
    """Verify that the engine updates item attributes in-place during download."""
    engine = ScrapingEngine(workers=1)
    
    # Prepare items to be scraped
    img = ImageItem(url="https://example.com/img.jpg", source_page="https://example.com/page.html", alt_text="Test Alt")
    vid = VideoItem(url="https://example.com/vid.mp4", source_page="https://example.com/page.html", type="direct", page_title="Test Video")

    # Mock page scraping to return our test items
    engine.search_provider.scrape_page = MagicMock(
        return_value=([img], [vid], "ok")
    )
    
    # Mock downloader._download_file to simulate success for image and failure for video
    def mock_download(url, directory, prefix, media_kind, referer=None, min_image_size=None, thumbnail_prefix_pattern=None, cdn_hosts=None):
        if media_kind == "image":
            return True, {
                "reason": "ok",
                "file_path": "images/example_001.jpg",
                "hash": "abc123hash",
                "width": 800,
                "height": 600,
                "file_size_bytes": 12345,
                "mime_type": "image/jpeg",
            }
        else:
            return False, {"reason": "low_resolution"}

    engine.downloader._download_file = mock_download

    # Execute engine run which will crawl the page and trigger downloads
    result = engine.run(
        keyword="test",
        max_results=10,
        output_format="json",
        download_media=True,
        use_search=False,
        seed_urls=["https://example.com/page.html"],
    )

    # Assert changes were made in-place and both kept in results
    assert img.status == "downloaded"
    assert img.file_path == "images/example_001.jpg"
    assert img.hash == "abc123hash"
    assert img.width == 800
    assert img.height == 600

    assert vid.status == "skipped"
    assert vid.failure_reason == "low_resolution"
    assert len(result.images) == 1
    assert len(result.videos) == 1


def test_stealth_timed_block_expiry():
    """Verify that stealth failed hosts expire after the 30-minute block."""
    client = HttpClient()
    client._load_cache = MagicMock(return_value=None)
    # Reset stealth_failed_hosts state for testing
    HttpClient._stealth_failed_hosts = {}

    host = "testblocked.com"
    url = f"https://{host}/page.html"

    # Verify initial state
    assert host not in HttpClient._stealth_failed_hosts

    # Simulate a stealth failure (normally added on Crawl4AI fallback exception)
    with patch("utils.http_client.time.time", return_value=1000.0):
        # Trigger fallback failure directly or simulate adding it
        with HttpClient._failed_stealth_lock:
            HttpClient._stealth_failed_hosts[host] = 1000.0 + 1800.0

    assert HttpClient._stealth_failed_hosts[host] == 2800.0

    # Verify that requesting while cooldown is active throws ScraperBypassError
    with patch("utils.http_client.time.time", return_value=2000.0):
        with pytest.raises(ScraperBypassError) as exc_info:
            client.get(url)
        assert "Stealth cooldown active" in str(exc_info.value)

    # Verify that requesting after expiry removes the host and attempts standard flow
    with patch("utils.http_client.time.time", return_value=3000.0), \
         patch.object(client.client, "get") as mock_get:
        mock_get.return_value = httpx.Response(200, text="success", request=httpx.Request("GET", url))
        resp = client.get(url)
        assert resp.status_code == 200
        assert host not in HttpClient._stealth_failed_hosts


def test_new_shopping_and_json_filters():
    """Verify that shopping/account paths and static JSON files are rejected."""
    # Test shopping path filters
    assert is_allowed_path("https://example.com/shop/account") is False
    assert is_allowed_path("https://example.com/store/account") is False
    assert is_allowed_path("https://example.com/cart") is False
    assert is_allowed_path("https://example.com/checkout") is False
    assert is_allowed_path("https://example.com/goto/account") is False

    # Test static files rejection
    assert is_allowed_path("https://example.com/manifest.json") is False
    assert is_allowed_path("https://example.com/sitemap.xml") is False
    assert is_allowed_path("https://example.com/style.css") is False
    assert is_allowed_path("https://example.com/app.js") is False

    # Test allowed paths
    assert is_allowed_path("https://example.com/blog/my-journey") is True
    assert is_allowed_path("https://example.com/category/nature") is True


def test_csv_audit_trail_columns(tmp_path):
    """Verify that CSV output includes the correct audit trail columns."""
    from storage.csv_writer import write_csv
    import csv

    # Create dummy ScrapeResult
    img = ImageItem(
        url="https://example.com/img.jpg",
        source_page="https://example.com",
        status="downloaded",
        file_path="images/img.jpg",
        failure_reason="none",
        hash="hash123",
    )
    vid = VideoItem(
        url="https://example.com/vid.mp4",
        source_page="https://example.com",
        type="direct",
        status="skipped",
        file_path="",
        failure_reason="low_resolution",
        hash="",
    )
    result = ScrapeResult(keyword="test")
    result.images = [img]
    result.videos = [vid]

    # Write to temp path
    write_csv(result, tmp_path)

    # Read and check images.csv
    image_csv = tmp_path / "images.csv"
    assert image_csv.exists()
    with image_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["status"] == "downloaded"
        assert rows[0]["file_path"] == "images/img.jpg"
        assert rows[0]["failure_reason"] == "none"
        assert rows[0]["hash"] == "hash123"

    # Read and check videos.csv
    video_csv = tmp_path / "videos.csv"
    assert video_csv.exists()
    with video_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["status"] == "skipped"
        assert rows[0]["file_path"] == ""
        assert rows[0]["failure_reason"] == "low_resolution"
        assert rows[0]["hash"] == ""

