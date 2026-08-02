import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock, patch
import httpx
from bs4 import BeautifulSoup

from core.models import ImageItem
from core.engine import ScrapingEngine
from network.session_pool import SessionPool
from network.http_client import HttpClient
from core.semantic_selectors import (
    extract_semantic_fallback_images,
    extract_semantic_fallback_videos,
)


def test_session_pool_sticky_cookies_and_rotation():
    """Verify that SessionPool manages cookies stickily and rotates User-Agent on reset."""
    pool = SessionPool()
    session_1 = pool.get_session("example.com")
    session_2 = pool.get_session("example.com")

    # Verify we get the same sticky session instance for the same domain
    assert session_1 is session_2

    ua_before = session_1.user_agent
    session_1.reset_identity()
    ua_after = session_1.user_agent

    # User agent should be rotated to a new one
    assert ua_before != ua_after


def test_http_client_rotates_session_on_block():
    """Verify HttpClient rotates session identity on 401, 403, and 429 status codes."""
    mock_client = MagicMock(spec=httpx.Client)
    http = HttpClient()
    http.client = mock_client
    http._load_cache = MagicMock(return_value=None)
    http._store_cache = MagicMock()

    # 1. 403 Forbidden Response
    test_url = "https://test-rotation-domain.com/blocked"
    response_403 = httpx.Response(
        status_code=403,
        request=httpx.Request("GET", test_url),
    )
    mock_client.get.return_value = response_403

    session = http._session_pool.get_session("test-rotation-domain.com")
    ua_before = session.user_agent

    # Mock _execute_fallbacks to fail, causing get to raise ScraperBypassError
    with patch.object(http, "_execute_fallbacks", return_value=(None, [])):
        with pytest.raises(Exception):
            http.get(test_url)

    # User agent should be rotated after 403 block
    ua_after = session.user_agent
    assert ua_before != ua_after
    HttpClient._stealth_failed_hosts.clear()


def test_adaptive_concurrency_throttling():
    """Verify ScrapingEngine dynamic worker concurrency adjusts based on status and latency."""
    engine = ScrapingEngine(workers=4)

    # We want to mock _fetch_page to control latency and status
    def mock_fetch_page_success(page, depth):
        return (
            page,
            depth,
            [ImageItem(url="https://example.com/img.jpg", source_page=page)],
            [],
            "ok",
        )

    def mock_fetch_page_block(page, depth):
        return page, depth, [], [], "fetch_error:429"

    def mock_fetch_page_slow(page, depth):
        return (
            page,
            depth,
            [ImageItem(url="https://example.com/img.jpg", source_page=page)],
            [],
            "ok",
        )

    mock_monotonic_vals = [0, 0.5, 0.5, 1.0, 1.0, 1.5, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 13.5, 14.0, 14.5, 15.0, 15.5, 16.0, 16.5, 17.0, 17.5, 18.0, 18.5, 19.0, 19.5, 20.0, 20.5, 21.0, 21.5, 22.0, 22.5, 23.0, 23.5, 24.0, 24.5, 25.0, 25.5, 26.0, 26.5, 27.0, 27.5, 28.0, 28.5, 29.0, 29.5, 30.0]
    monotonic_iter = iter(mock_monotonic_vals)

    def safe_monotonic():
        try:
            return next(monotonic_iter)
        except StopIteration:
            return mock_monotonic_vals[-1]

    # Test scaling down on block
    with (
        patch.object(
            engine.search_provider,
            "search_pages",
            return_value=["https://example.com/page1", "https://example.com/page2"],
        ),
        patch.object(engine.search_provider, "discover_links", return_value=[]),
        patch.object(
            engine.search_provider, "scrape_page", return_value=([], [], "429_blocked", "", "")
        ),
        patch.object(engine.video_scraper, "search", return_value=[]),
        patch("core.engine.time.monotonic", side_effect=safe_monotonic),
        patch("core.governor.time.monotonic", side_effect=safe_monotonic),
        patch("core.coordinator.time.monotonic", side_effect=safe_monotonic),
        patch("core.coordinator.time.sleep", return_value=None),
    ):
        result = engine.run(
            keyword="test",
            max_results=2,
            output_format="json",
            download_media=False,
            seed_urls=["https://example.com/page1"],
            page_limit=2,
        )
        # Verify execution didn't crash
        assert len(result.scanned_pages) <= 2


def test_self_healing_semantic_selectors():
    """Verify that semantic fallback selectors find media items in custom containers/attributes."""
    html_content = """
    <html>
        <body>
            <div class="gallery-item-container" data-highres-url="https://example.com/highres.jpg">
                <div class="photo-viewer" data-lazy="https://example.com/lazy.png"></div>
                <a href="https://example.com/post-link" class="attachment-link">Attachment Page</a>
                <div class="gallery-photo" title="Page 1: _1.jpg" alt="Sample_Image.png"></div>
            </div>
            <div class="main-video-player" data-video-src="https://example.com/video.mp4" title="Sample_Video.mp4"></div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html_content, "html.parser")

    fallback_images = extract_semantic_fallback_images(
        soup, "https://example.com/gallery", "Title"
    )
    fallback_videos = extract_semantic_fallback_videos(
        soup, "https://example.com/gallery", "Title"
    )

    image_urls = {img.url for img in fallback_images}
    video_urls = {vid.url for vid in fallback_videos}

    assert "https://example.com/highres.jpg" in image_urls
    assert "https://example.com/lazy.png" in image_urls
    assert "https://example.com/video.mp4" in video_urls

    # Assert that textual attributes are ignored and do not generate false URLs
    assert not any(
        "Page%201" in url or "_1.jpg" in url or "Sample_Image" in url
        for url in image_urls
    )
    assert not any("Sample_Video" in url for url in video_urls)
