from __future__ import annotations

from unittest.mock import MagicMock
from bs4 import BeautifulSoup

from core.governor import CrawlGovernor
from core.microdata import extract_jsonld_media, detect_smart_pagination


def test_governor_aimd_additive_increase():
    """Verify AIMD additive increase upon healthy response latencies."""
    gov = CrawlGovernor(initial_concurrency=10, aimd_increase_step=1.0, min_concurrency=1)
    host = "fast-cdn.example.com"

    # Start with initial default window 1.0
    assert gov.host_concurrency.get(host, 1.0) == 1.0

    # Report success with fast latency (0.3s <= 1.5s)
    gov.report_success(host, latency_s=0.3)
    assert gov.host_concurrency[host] == 2.0

    # Repeat successes
    for _ in range(3):
        gov.report_success(host, latency_s=0.4)
    assert gov.host_concurrency[host] == 5.0

    # Ensure it caps at max_concurrency
    for _ in range(15):
        gov.report_success(host, latency_s=0.2)
    assert gov.host_concurrency[host] == 10.0


def test_governor_aimd_multiplicative_decrease_on_429_and_error():
    """Verify AIMD multiplicative decrease cuts host window by 50% on 429 or error."""
    gov = CrawlGovernor(initial_concurrency=16, aimd_decrease_factor=0.5, min_concurrency=1)
    host = "rate-limited.example.com"

    # Set host concurrency high
    gov.host_concurrency[host] = 16.0

    # 429 event
    gov.report_429(host)
    assert gov.host_concurrency[host] == 8.0

    # Consecutive error
    gov.report_error(host)
    assert gov.host_concurrency[host] == 4.0

    # Another error
    gov.report_error(host)
    assert gov.host_concurrency[host] == 2.0

    # Next 429 hits floor (min_concurrency=1)
    gov.report_429(host)
    assert gov.host_concurrency[host] == 1.0


def test_governor_aimd_latency_spike_throttling():
    """Verify latency spikes (>3.0s) trigger multiplicative decrease to protect host."""
    gov = CrawlGovernor(initial_concurrency=8, aimd_decrease_factor=0.5, min_concurrency=1)
    host = "slow-server.example.com"
    gov.host_concurrency[host] = 8.0

    # Latency spike 4.2s
    gov.report_latency(host, latency_s=4.2)
    assert gov.host_concurrency[host] == 4.0

    # Latency within success call
    gov.report_success(host, latency_s=3.5)
    assert gov.host_concurrency[host] == 2.0


def test_governor_dual_governor_hardware_scaling():
    """Verify CrawlGovernor coordinates with HardwareLoadGovernor to scale workers under system load."""
    mock_hw_gov = MagicMock()
    # Simulate critical system CPU/RAM load -> scale factor 0.25
    mock_hw_gov.get_concurrency_scale_factor.return_value = 0.25

    gov = CrawlGovernor(initial_concurrency=8, hardware_governor=mock_hw_gov)
    host = "high-yield.example.com"

    # High media yield unlocks deep scrape
    gov.report_yield(host, 10)
    gov.host_concurrency[host] = 8.0

    # Without hardware stress, allowed would be 8. Under 0.25 load, allowed is 2!
    allowed = gov.get_allowed_concurrency(host)
    assert allowed == 2

    # Global concurrency limit also throttles
    global_cap = gov.get_global_concurrency_limit()
    assert global_cap == 2

    # Recover hardware load to normal (1.0x)
    mock_hw_gov.get_concurrency_scale_factor.return_value = 1.0
    assert gov.get_allowed_concurrency(host) == 8
    assert gov.get_global_concurrency_limit() == 8


def test_extract_jsonld_media_structured_data():
    """Verify extraction of ImageItem and VideoItem models from schema.org JSON-LD scripts."""
    html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Vintage Film Camera",
            "image": [
                "https://example.com/images/cam_full.jpg",
                "https://example.com/images/cam_angle.jpg"
            ]
        }
        </script>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@type": "ImageObject",
                    "contentUrl": "https://example.com/photos/landscape.jpg",
                    "name": "Mountain Sunset",
                    "width": 1920,
                    "height": 1080
                },
                {
                    "@type": "VideoObject",
                    "contentUrl": "https://example.com/videos/sunset.mp4",
                    "name": "Sunset Timelapse",
                    "thumbnailUrl": "https://example.com/videos/sunset_thumb.jpg"
                }
            ]
        }
        </script>
    </head>
    <body><h1>Gallery</h1></body>
    </html>
    """
    images, videos = extract_jsonld_media(html, "https://example.com/catalog/item1")

    # Images: cam_full, landscape
    assert len(images) == 2
    img_urls = [img.url for img in images]
    assert "https://example.com/images/cam_full.jpg" in img_urls
    assert "https://example.com/photos/landscape.jpg" in img_urls

    # Check fallbacks and metadata
    cam_item = next(img for img in images if "cam_full" in img.url)
    assert "https://example.com/images/cam_angle.jpg" in cam_item.fallback_urls
    assert cam_item.extraction_source == "json-ld"

    land_item = next(img for img in images if "landscape" in img.url)
    assert land_item.width == 1920
    assert land_item.height == 1080

    # Videos: sunset.mp4
    assert len(videos) == 1
    vid = videos[0]
    assert vid.url == "https://example.com/videos/sunset.mp4"
    assert vid.page_title == "Sunset Timelapse"
    assert "https://example.com/videos/sunset_thumb.jpg" in vid.fallback_urls
    assert vid.extraction_source == "json-ld"



def test_detect_smart_pagination_markup_and_inference():
    """Verify detection of explicit pagination markup and query parameter step inference."""
    html = """
    <html>
    <head>
        <link rel="next" href="https://example.com/gallery?page=2" />
    </head>
    <body>
        <div class="pagination">
            <a class="pagination-next" href="/gallery?page=2">Next Page</a>
        </div>
    </body>
    </html>
    """
    discovered = detect_smart_pagination(html, "https://example.com/gallery?page=1")
    assert "https://example.com/gallery?page=2" in discovered

    # Test query step inference without explicit HTML links
    empty_html = "<html><body><div>Single Page</div></body></html>"
    inferred = detect_smart_pagination(empty_html, "https://example.com/archive?p=4")
    assert "https://example.com/archive?p=5" in inferred

    # Test path step inference
    path_inferred = detect_smart_pagination(empty_html, "https://example.com/blog/page/3/")
    assert "https://example.com/blog/page/4/" in path_inferred
