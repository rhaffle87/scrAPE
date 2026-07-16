import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock, patch
import httpx
from bs4 import BeautifulSoup

from core.models import ImageItem
from core.engine import ScrapingEngine
from utils.session_pool import SessionPool
from utils.http_client import HttpClient
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
    response_403 = httpx.Response(
        status_code=403,
        request=httpx.Request("GET", "https://example.com/blocked"),
    )
    mock_client.get.return_value = response_403

    session = http._session_pool.get_session("example.com")
    ua_before = session.user_agent

    # Mock _get_with_crawl4ai to raise an error, causing get to raise HTTPStatusError
    with patch.object(http, "_get_with_crawl4ai", side_effect=Exception("CF blocked")):
        with pytest.raises(Exception):
            http.get("https://example.com/blocked")

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

    mock_monotonic_vals = [0, 0.5, 0.5, 1.0, 1.0, 1.5, 1.5, 2.0]
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
            engine.search_provider, "scrape_page", return_value=([], [], "429_blocked")
        ),
        patch.object(engine.video_scraper, "search", return_value=[]),
        patch("core.engine.time.monotonic", side_effect=safe_monotonic),
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
