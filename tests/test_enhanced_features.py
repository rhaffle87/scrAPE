import struct
from unittest.mock import MagicMock
import pytest

from core.models import ImageItem
from scraper.google_images import SearchProviderScraper
from utils.image_helper import get_image_dimensions


def test_get_image_dimensions_png():
    # PNG signature + IHDR chunk
    # Width 800 (0x320), Height 600 (0x258)
    png_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + struct.pack(">II", 800, 600)
    w, h = get_image_dimensions(png_data)
    assert w == 800
    assert h == 600


def test_get_image_dimensions_gif():
    # GIF89a + Logical Screen Width/Height
    # Width 100 (0x64), Height 150 (0x96) (little-endian)
    gif_data = b"GIF89a" + struct.pack("<HH", 100, 150)
    w, h = get_image_dimensions(gif_data)
    assert w == 100
    assert h == 150


def test_get_image_dimensions_webp_vp8x():
    # RIFF/WEBP + VP8X header
    # VP8X has flags, width (3 bytes), height (3 bytes)
    # Width: 1920 -> 1919 (stored value = width - 1)
    # Height: 1080 -> 1079 (stored value = height - 1)
    stored_w = 1920 - 1
    stored_h = 1080 - 1
    w_bytes = struct.pack("<I", stored_w)[:3]
    h_bytes = struct.pack("<I", stored_h)[:3]
    webp_data = (
        b"RIFF\x00\x00\x00\x00WEBPVP8X\n\x00\x00\x00\x00\x00\x00\x00"
        + w_bytes
        + h_bytes
    )
    w, h = get_image_dimensions(webp_data)
    assert w == 1920
    assert h == 1080


def test_get_image_dimensions_webp_vp8():
    # RIFF/WEBP + VP8 (lossy) chunk
    # VP8 chunk header is 'VP8 ', size (4 bytes), frame tag (3 bytes), start code (3 bytes), width/height (4 bytes)
    # Width: 200, Height: 200
    vp8_data = (
        b"RIFF\x00\x00\x00\x00WEBPVP8 \x00\x00\x00\x00"  # RIFF header + VP8 chunk header
        b"\x00\x00\x00"  # Frame tag (3 bytes)
        b"\x9d\x01\x2a" + struct.pack("<HH", 200, 200)  # Start code  # Width, Height
    )
    w, h = get_image_dimensions(vp8_data)
    assert w == 200
    assert h == 200


def test_get_image_dimensions_webp_vp8l():
    # RIFF/WEBP + VP8L (lossless) chunk
    # VP8L chunk header is 'VP8L', size (4 bytes), signature 0x2f (1 byte), width/height (4 bytes)
    # Width: 400 -> 399, Height: 300 -> 299
    # Packed format: 14 bits width, 14 bits height, 4 bits other
    val = (399 & 0x3FFF) | ((299 & 0x3FFF) << 14)
    vp8l_data = (
        b"RIFF\x00\x00\x00\x00WEBPVP8L\x00\x00\x00\x00"  # RIFF header + VP8L chunk header
        b"\x2f" + struct.pack("<I", val)  # Signature  # Packed width/height
    )
    w, h = get_image_dimensions(vp8l_data)
    assert w == 400
    assert h == 300


def test_get_image_dimensions_jpeg():
    # JPEG SOI + SOF0 segment
    # Width 1024 (0x400), Height 768 (0x300)
    # SOF0 marker: 0xFFC0, length: 8 (usually, let's pass a dummy block)
    # SOF0 format: marker(1 byte), length(2 bytes), precision(1 byte), height(2 bytes), width(2 bytes)
    jpeg_data = (
        b"\xff\xd8"
        b"\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00"
        b"\xff\xc0\x00\x11\x08" + struct.pack(">HH", 768, 1024)
    )
    w, h = get_image_dimensions(jpeg_data)
    assert w == 1024
    assert h == 768


def test_parse_srcset_highest_res():
    srcset_str = (
        "https://example.com/small.jpg 400w, "
        "https://example.com/large.jpg 1200w, "
        "https://example.com/medium.jpg 800w"
    )
    res = SearchProviderScraper._parse_srcset_highest_res(srcset_str)
    assert res == "https://example.com/large.jpg"

    # Test density descriptor
    srcset_density = (
        "https://example.com/1x.jpg 1x, "
        "https://example.com/3x.jpg 3x, "
        "https://example.com/2x.jpg 2x"
    )
    res_density = SearchProviderScraper._parse_srcset_highest_res(srcset_density)
    assert res_density == "https://example.com/3x.jpg"


def test_json_api_media_extraction():
    scraper = SearchProviderScraper()
    # Mock json response containing image, video and other urls
    api_payload = {
        "results": [
            {
                "title": "Awesome Apple Image",
                "image_url": "https://example.com/assets/apple_high.png",
                "details": {
                    "preview": "https://example.com/assets/preview.jpg",
                },
            },
            {
                "title": "Apple Video",
                "video_link": "https://example.com/assets/apple.mp4",
                "subpage": "https://example.com/subpage/details?id=123",
            },
        ]
    }

    images, videos = scraper._extract_media_from_json(
        api_payload, "https://example.com/api"
    )

    urls_found = {img.url for img in images}
    assert "https://example.com/assets/apple_high.png" in urls_found
    assert "https://example.com/assets/preview.jpg" in urls_found

    video_urls = {vid.url for vid in videos}
    assert "https://example.com/assets/apple.mp4" in video_urls


def test_json_api_link_discovery():
    scraper = SearchProviderScraper()
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {
        "next": "https://example.com/api?page=2",
        "results": [
            {
                "image": "https://example.com/img.jpg",
                "related": "https://example.com/related-page",
            }
        ],
    }
    scraper.http.get = MagicMock(return_value=mock_response)
    scraper.robots.is_allowed = MagicMock(return_value=True)

    links = scraper.discover_links("https://example.com/api")

    # img.jpg is an image, next and related are links
    # So discovered links should contain next and related, but NOT the image itself
    assert "https://example.com/api?page=2" in links
    assert "https://example.com/related-page" in links
    assert "https://example.com/img.jpg" not in links


def test_strict_subject_narrowing():
    # 1. Test discover_links skips crawling when keyword is not mentioned
    scraper = SearchProviderScraper()
    mock_response = MagicMock()
    mock_response.headers = {"content-type": "text/html"}
    mock_response.text = "This is a generic article about sports and politics."
    scraper.http.get = MagicMock(return_value=mock_response)
    scraper.robots.is_allowed = MagicMock(return_value=True)

    links = scraper.discover_links(
        "https://example.com/page", keyword="Messi", entity_tokens=["Lionel"]
    )
    assert len(links) == 0  # skipped due to no subject relevance

    # 2. Test rejection_reason_for_image rejects image with no subject text
    from core.models import ImageItem
    from core.filters import rejection_reason_for_image

    # Image has high attributes (alt_text, page_title, is_probable_image -> score = 4)
    # but does NOT mention Messi/Lionel anywhere in url, alt_text, source_page, or page_title
    item = ImageItem(
        url="https://example.com/some_unrelated_photo.jpg",
        source_page="https://example.com/some-page",
        alt_text="A beautiful sunset",
        page_title="My Personal Blog",
    )

    reason = rejection_reason_for_image(item, keyword="Messi", entity_tokens=["Lionel"])
    assert reason == "low_subject_relevance"


def test_is_archive_or_index_page():
    from core.filters import is_archive_or_index_page

    assert (
        is_archive_or_index_page(
            "https://example.com/category/subject", "Subject Archives"
        )
        is True
    )
    assert (
        is_archive_or_index_page(
            "https://example.com/actor/subject/", "Subject Actor Profile"
        )
        is True
    )
    assert (
        is_archive_or_index_page(
            "https://example.com/search?q=subject", "Search Results"
        )
        is True
    )
    assert (
        is_archive_or_index_page(
            "https://example.com/post/subject-photos",
            "Subject Cosplay Eula",
        )
        is False
    )


def test_layout_container_detection():
    from bs4 import BeautifulSoup
    from scraper.google_images import SearchProviderScraper

    html = """
    <html>
      <body>
        <div id="main-content">
          <img id="img1" src="https://example.com/content.jpg" alt="Content" />
        </div>
        <div class="sidebar-widget">
          <img id="img2" src="https://example.com/sidebar.jpg" alt="Sidebar" />
        </div>
        <footer>
          <img id="img3" src="https://example.com/footer.jpg" alt="Footer" />
        </footer>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    scraper = SearchProviderScraper()

    img1 = soup.find(id="img1")
    img2 = soup.find(id="img2")
    img3 = soup.find(id="img3")

    assert scraper._is_in_layout_container(img1) is False
    assert scraper._is_in_layout_container(img2) is True
    assert scraper._is_in_layout_container(img3) is True


def test_archive_page_relevance():
    from core.filters import rejection_reason_for_image

    # 1. On an archive/index page:
    # Page title contains "subject", but the image alt and url don't contain "subject"
    # and no parent anchor has it -> should be rejected!
    item1 = ImageItem(
        url="https://example.com/unrelated.jpg",
        source_page="https://example.com/category/subject/",
        alt_text="Some other model",
        page_title="Subject Category List",
        in_layout_container=False,
        parent_anchor_text="Click here",
        parent_anchor_href="https://example.com/other-model",
    )
    assert rejection_reason_for_image(item1, "subject") == "low_subject_relevance"

    # 2. On the same archive page, if parent anchor href contains "subject" -> keep!
    item2 = ImageItem(
        url="https://example.com/unrelated.jpg",
        source_page="https://example.com/category/subject/",
        alt_text="Some image",
        page_title="Subject Category List",
        in_layout_container=False,
        parent_anchor_text="Subject Profile",
        parent_anchor_href="https://example.com/post/subject-latest",
    )
    assert rejection_reason_for_image(item2, "subject") is None

    # 3. If in a layout container (e.g. sidebar), even if it matches "subject" -> reject as layout decoration!
    item3 = ImageItem(
        url="https://example.com/subject.jpg",
        source_page="https://example.com/category/subject/",
        alt_text="Subject Sidebar image",
        page_title="Subject Category List",
        in_layout_container=True,
        parent_anchor_text="Subject Widget",
        parent_anchor_href="https://example.com/post/subject-latest",
    )
    assert rejection_reason_for_image(item3, "subject") == "layout_decoration"


def test_token_based_layout_avoidance():
    from bs4 import BeautifulSoup
    from scraper.google_images import SearchProviderScraper

    html = """
    <html>
      <body>
        <div class="native-content">
          <img id="img_native" src="https://example.com/native.jpg" />
        </div>
        <div class="wp-uploads-container">
          <img id="img_uploads" src="https://example.com/uploads.jpg" />
        </div>
        <div class="slider-nav-circle">
          <img id="img_nav" src="https://example.com/nav.jpg" />
        </div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    scraper = SearchProviderScraper()

    img_native = soup.find(id="img_native")
    img_uploads = soup.find(id="img_uploads")
    img_nav = soup.find(id="img_nav")

    assert scraper._is_in_layout_container(img_native) is False
    assert scraper._is_in_layout_container(img_uploads) is False
    assert scraper._is_in_layout_container(img_nav) is True


def test_dimension_based_filtering():
    from core.filters import rejection_reason_for_image

    img_small_w = ImageItem(
        url="https://example.com/subject.jpg",
        source_page="https://example.com/subject",
        width=150,
        height=600,
    )
    assert rejection_reason_for_image(img_small_w, "subject") == "low_resolution"

    img_small_h = ImageItem(
        url="https://example.com/subject.jpg",
        source_page="https://example.com/subject",
        width=800,
        height=200,
    )
    assert rejection_reason_for_image(img_small_h, "subject") == "low_resolution"

    img_large = ImageItem(
        url="https://example.com/subject.jpg",
        source_page="https://example.com/subject",
        width=1200,
        height=1800,
    )
    assert rejection_reason_for_image(img_large, "subject") is None


def test_max_results_limit_reporting():
    from core.engine import ScrapingEngine
    from core.models import EngineOptions, ScrapeResult, RejectedItem
    from pathlib import Path

    engine = ScrapingEngine()
    result = ScrapeResult(keyword="subject")
    result.images = [
        ImageItem(
            url="https://example.com/subject1.jpg",
            source_page="https://example.com/page",
            score=10,
        ),
        ImageItem(
            url="https://example.com/subject2.jpg",
            source_page="https://example.com/page",
            score=9,
        ),
        ImageItem(
            url="https://example.com/subject3.jpg",
            source_page="https://example.com/page",
            score=8,
        ),
    ]

    options = EngineOptions(
        keyword="subject",
        max_results=2,
        output_format="json",
        download_media=False,
        output_dir=Path("output"),
    )

    result.images = engine._finalize_images(result, options)
    # Perform slice manually as engine.run would
    if len(result.images) > options.max_results:
        discarded = result.images[options.max_results :]
        result.images = result.images[: options.max_results]
        for item in discarded:
            result.rejected_items.append(
                RejectedItem(
                    "image", item.url, item.source_page, "max_results_limit", item.score
                )
            )

    assert len(result.images) == 2
    assert len(result.rejected_items) == 1
    assert result.rejected_items[0].url == "https://example.com/subject3.jpg"
    assert result.rejected_items[0].reason == "max_results_limit"


def test_homepage_index_detection():
    from core.filters import is_archive_or_index_page

    assert is_archive_or_index_page("https://example.com", "Home Page") is True
    assert is_archive_or_index_page("https://example.com/", "Home Page") is True
    assert is_archive_or_index_page("https://example.com/index.html", "Welcome") is True
    assert is_archive_or_index_page("https://example.com/index.php", "Home") is True
    # Non-homepages should not match this unless they have archive/index terms
    assert (
        is_archive_or_index_page("https://example.com/gallery/123", "Some Gallery")
        is False
    )


def test_collage_and_preview_filtering():
    from core.filters import rejection_reason_for_image, rejection_reason_for_video
    from core.models import ImageItem, VideoItem

    # Collage image
    img_collage = ImageItem(
        url="https://example.com/collage_subject.jpg",
        source_page="https://example.com/subject",
        width=600,
        height=800,
    )
    assert (
        rejection_reason_for_image(img_collage, "subject")
        == "preview_or_thumbnail"
    )

    # Preview/trailer video
    video_trailer = VideoItem(
        url="https://example.com/subject_trailer.mp4",
        source_page="https://example.com/subject",
        type="direct",
    )
    assert (
        rejection_reason_for_video(video_trailer, "subject")
        == "preview_or_thumbnail"
    )

    # Short video
    video_short = VideoItem(
        url="https://example.com/subject_short.mp4",
        source_page="https://example.com/subject",
        type="direct",
    )
    assert (
        rejection_reason_for_video(video_short, "subject")
        == "preview_or_thumbnail"
    )


def test_refined_preview_markers_and_context_aware_filtering():
    from core.filters import rejection_reason_for_video
    from core.models import VideoItem

    # 1. Video URL containing a path with "thumbs" but clean filename should NOT be rejected
    video_with_thumbs_path = VideoItem(
        url="https://example.com/subject/thumbs/video_123.mp4",
        source_page="https://example.com/subject",
        type="direct",
        page_title="Subject Video",
    )
    assert rejection_reason_for_video(video_with_thumbs_path, "subject") is None

    # 2. Video URL with a preview-specific filename (e.g. thumb_vid.mp4) IS rejected
    video_preview_filename = VideoItem(
        url="https://example.com/subject/video/thumb_vid.mp4",
        source_page="https://example.com/subject",
        type="direct",
        page_title="Subject Video",
    )
    assert (
        rejection_reason_for_video(video_preview_filename, "subject")
        == "preview_or_thumbnail"
    )

    # 3. Page title containing "preview" but clean video URL is NOT rejected
    video_with_preview_in_title = VideoItem(
        url="https://example.com/subject/video/full_performance_1080p.mp4",
        source_page="https://example.com/subject",
        type="direct",
        page_title="Subject OnlyFans Leak Preview Clip",
    )
    assert (
        rejection_reason_for_video(video_with_preview_in_title, "subject") is None
    )


def test_http_client_crawl4ai_fallback(monkeypatch):
    import httpx
    from utils.http_client import HttpClient

    client = HttpClient()
    # Isolate from other tests
    client._stealth_required_hosts.clear()

    # Mock self.client.get to raise a 403 error
    def mock_get(url, **kwargs):
        response = httpx.Response(status_code=403, request=httpx.Request("GET", url))
        raise httpx.HTTPStatusError(
            "Forbidden", request=httpx.Request("GET", url), response=response
        )

    monkeypatch.setattr(client.client, "get", mock_get)

    # Mock _get_with_crawl4ai to return custom HTML
    monkeypatch.setattr(
        client, "_get_with_crawl4ai", lambda url: "<html>Crawl4AI Page</html>"
    )

    # Clear cache for the test url
    test_url = "https://fallback-test-domain.com/blocked-page"
    cache_path = client._cache_path(test_url)
    if cache_path.exists():
        cache_path.unlink()

    response = client.get(test_url)
    assert response.status_code == 200
    assert response.text == "<html>Crawl4AI Page</html>"


def test_http_client_cloudflare_detection():
    from utils.http_client import HttpClient

    client = HttpClient()

    # 1. Normal HTML
    assert not client._is_cloudflare_challenge(
        "<html><title>subject Videos</title></html>"
    )
    assert not client._is_cloudflare_challenge("")

    # 2. Title challenge match
    assert client._is_cloudflare_challenge(
        "<html><title>Just a moment...</title></html>"
    )
    assert client._is_cloudflare_challenge(
        "<html><title>Checking your browser - Cloudflare</title></html>"
    )
    assert client._is_cloudflare_challenge(
        "<html><title>Attention Required! | Cloudflare</title></html>"
    )

    # 3. Content challenge match
    assert client._is_cloudflare_challenge(
        "<html><body><script src='https://challenges.cloudflare.com/turnstile/v0/api.js'></script>Just a moment...</body></html>"
    )
    assert client._is_cloudflare_challenge(
        "<html><div class='cf-challenge'>Please enable JavaScript</div></html>"
    )


def test_http_client_no_retry_on_bypass_failure(monkeypatch):
    import httpx
    from utils.http_client import HttpClient, ScraperBypassError
    import pytest

    client = HttpClient()
    # Isolate from other tests
    client._stealth_required_hosts.clear()
    call_count = 0

    def mock_get(url, **kwargs):
        nonlocal call_count
        call_count += 1
        response = httpx.Response(status_code=403, request=httpx.Request("GET", url))
        raise httpx.HTTPStatusError(
            "Forbidden", request=httpx.Request("GET", url), response=response
        )

    monkeypatch.setattr(client.client, "get", mock_get)

    def mock_get_with_crawl4ai(url):
        raise Exception("Mocked Crawl4AI Failure")

    monkeypatch.setattr(client, "_get_with_crawl4ai", mock_get_with_crawl4ai)

    test_url = "https://no-retry-test-domain.com/blocked-page-no-retry"
    cache_path = client._cache_path(test_url)
    if cache_path.exists():
        cache_path.unlink()

    with pytest.raises(ScraperBypassError):
        client.get(test_url)

    # Assert that we only attempted once and did not retry
    assert call_count == 1


def test_seed_manifest_parsing(tmp_path):
    from core.seed_manifest import SeedManifest

    manifest_content = """# Subject: Example Subject / Alias Beta
# type: image | crawl: direct
# [CDN] s1.mediasite-alpha.com
# [CDN] s2.mediasite-alpha.com
# depth: 0
# skip-link-discovery
# Rate-limit: 0.4 req/s
# Username: my_user
# Email: my_email@site.com
# Password: my_password_123
https://mediasite-alpha.com/subject

# type: video | crawl: index -> detail
# depth: 2
https://videosite-beta.com/category/subject
"""
    manifest_file = tmp_path / "subject.txt"
    manifest_file.write_text(manifest_content, encoding="utf-8")

    manifest = SeedManifest.from_file(manifest_file)

    assert manifest.subject_name == "Example Subject / Alias Beta"
    assert "example subject" in manifest.entity_tokens
    assert "alias beta" in manifest.entity_tokens

    assert len(manifest.domains) == 2

    # Check mediasite-alpha.com profile
    alpha_prof = manifest.domain_map["mediasite-alpha.com"]
    assert alpha_prof.media_type == "image"
    assert alpha_prof.crawl_strategy == "direct"
    assert alpha_prof.crawl_depth == 0
    assert alpha_prof.effective_crawl_depth == 0
    assert alpha_prof.skip_link_discovery is True
    assert alpha_prof.rate_limit == 0.4
    assert alpha_prof.username == "my_user"
    assert alpha_prof.email == "my_email@site.com"
    assert alpha_prof.password == "my_password_123"
    # CDN wildcards should be normalized (s1.mediasite-alpha.com -> mediasite-alpha.com)
    assert alpha_prof.cdn_hosts == ["mediasite-alpha.com"]
    assert alpha_prof.seed_urls == ["https://mediasite-alpha.com/subject"]

    # Check videosite-beta.com profile
    beta_prof = manifest.domain_map["videosite-beta.com"]
    assert beta_prof.media_type == "video"
    assert beta_prof.crawl_strategy == "index\u2192detail"
    assert beta_prof.crawl_depth == 2
    assert beta_prof.effective_crawl_depth == 2
    assert beta_prof.skip_link_discovery is False
    assert beta_prof.cdn_hosts == []
    assert beta_prof.seed_urls == ["https://videosite-beta.com/category/subject"]

    # Check all allowed hosts
    allowed = manifest.all_allowed_hosts
    assert "mediasite-alpha.com" in allowed
    assert "videosite-beta.com" in allowed


def test_disabled_domain_manifest_parsing(tmp_path):
    from core.seed_manifest import SeedManifest

    manifest_content = """# Subject: Test Subject
# type: image | crawl: direct
# DISABLED: This domain is broken
https://mediasite-alpha.com/subject

# type: video | crawl: index -> detail
# disabled: true
https://videosite-beta.com/category/subject

# type: mixed | crawl: direct
https://activesite.com/page
"""
    manifest_file = tmp_path / "subject.txt"
    manifest_file.write_text(manifest_content, encoding="utf-8")

    manifest = SeedManifest.from_file(manifest_file)

    assert len(manifest.domains) == 3

    alpha_prof = manifest.domain_map["mediasite-alpha.com"]
    assert alpha_prof.disabled is True

    beta_prof = manifest.domain_map["videosite-beta.com"]
    assert beta_prof.disabled is True

    active_prof = manifest.domain_map["activesite.com"]
    assert active_prof.disabled is False

    # Check that disabled domains are filtered out of all_seed_urls and all_allowed_hosts
    assert manifest.all_seed_urls == ["https://activesite.com/page"]
    assert manifest.all_allowed_hosts == ["activesite.com"]



def test_http_client_rate_limiting_delay_conversion():
    from utils.http_client import HttpClient

    # Supplying a delay of 2.5 seconds per request for a domain
    client = HttpClient(domain_delays={"example-site.com": 2.5})
    # Since rps = 1.0 / delay, the rps should be 1.0 / 2.5 = 0.4
    assert client._domain_rps_overrides["example-site.com"] == pytest.approx(0.4)


def test_cache_disposal_and_run_id_passing(tmp_path):
    import os
    import sys

    # Add project root to sys.path if not present to import main
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

    from main import dispose_unnecessary_cache
    from core.engine import ScrapingEngine
    import time
    from unittest.mock import MagicMock

    # 1. Test dispose_unnecessary_cache
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Create two cache files
    fresh_file = cache_dir / "fresh.cache"
    expired_file = cache_dir / "expired.cache"

    fresh_file.write_text("fresh", encoding="utf-8")
    expired_file.write_text("expired", encoding="utf-8")

    # Set expired_file st_mtime to 10 seconds ago
    now = time.time()
    os.utime(expired_file, (now - 10, now - 10))

    logger_mock = MagicMock()

    # Run with TTL = 5 seconds
    dispose_unnecessary_cache(cache_dir, 5, logger_mock)

    assert fresh_file.exists()
    assert not expired_file.exists()
    logger_mock.info.assert_called_once()

    # 2. Test run_id override in engine.run()
    engine = ScrapingEngine()
    engine.search_provider.search_pages = MagicMock(return_value=[])

    result = engine.run(
        keyword="example_subject",
        max_results=0,
        output_format="json",
        download_media=False,
        use_search=False,
        run_id="TEST_RUN_123",
    )
    assert result.run_id == "TEST_RUN_123"


def test_media_downloader_unicode_quoting(monkeypatch):
    from storage.file_downloader import MediaDownloader
    import httpx
    from pathlib import Path

    downloader = MediaDownloader()

    called_url = None
    called_headers = None

    import contextlib

    @contextlib.contextmanager
    def mock_stream(client_self, method, url, **kwargs):
        nonlocal called_url, called_headers
        called_url = str(url)
        called_headers = kwargs.get("headers")
        resp = httpx.Response(
            status_code=200,
            content=b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
            + struct.pack(">II", 800, 800)
            + b"\x00" * 20000,
            request=httpx.Request(method, url),
        )
        resp.headers["content-type"] = "image/png"
        yield resp

    monkeypatch.setattr(httpx.Client, "stream", mock_stream)

    # Pass a url and referer with non-ASCII characters (e.g. from buondua.com)
    unicode_url = "https://buondua.com/path/with/unicode/测试.png"
    unicode_referer = "https://buondua.com/referer/测试"

    # Create a dummy temp directory
    temp_dir = Path("output/test_unicode_dl")
    temp_dir.mkdir(parents=True, exist_ok=True)

    try:
        success, reason = downloader._download_file(
            url=unicode_url,
            directory=temp_dir,
            prefix="test_prefix",
            media_kind="image",
            referer=unicode_referer,
        )
        assert success is True
        assert reason["reason"] == "ok"
        # Check that the request URL was quoted (contains %E6%B5%8B%E8%AF%95 instead of raw 测试)
        assert "%E6%B5%8B%E8%AF%95" in called_url
        assert "测试" not in called_url

        # Check that the Referer and Origin headers were also quoted
        assert "%E6%B5%8B%E8%AF%95" in called_headers["Referer"]
        assert "测试" not in called_headers["Referer"]
        assert called_headers["Origin"].isascii()
    finally:
        # Clean up
        import shutil

        if temp_dir.exists():
            shutil.rmtree(temp_dir)


def test_http_client_direct_stealth_routing(monkeypatch):
    from utils.http_client import HttpClient
    import httpx

    client = HttpClient()

    # Reset class variables
    client._stealth_required_hosts.clear()

    # Mock httpx.Client.get
    get_count = 0

    def mock_get(url, **kwargs):
        nonlocal get_count
        get_count += 1
        # First call returns 403 status to trigger Crawl4AI fallback
        response = httpx.Response(status_code=403, request=httpx.Request("GET", url))
        raise httpx.HTTPStatusError(
            "Forbidden", request=httpx.Request("GET", url), response=response
        )

    monkeypatch.setattr(client.client, "get", mock_get)

    # Mock _get_with_crawl4ai
    crawl4ai_count = 0

    def mock_crawl4ai(url):
        nonlocal crawl4ai_count
        crawl4ai_count += 1
        return "<html>Stealth Page</html>"

    monkeypatch.setattr(client, "_get_with_crawl4ai", mock_crawl4ai)

    # We expect the first fetch to hit standard HTTP GET, fail with 403, fall back to Crawl4AI,
    # and then record the domain as requiring stealth.
    url1 = "https://stealth-domain.com/page1"
    resp1 = client.get(url1)
    assert resp1.text == "<html>Stealth Page</html>"
    assert get_count == 1
    assert crawl4ai_count == 1
    assert "stealth-domain.com" in client._stealth_required_hosts

    # The second fetch to the same domain should bypass standard GET entirely
    # and route directly to Crawl4AI.
    url2 = "https://stealth-domain.com/page2"
    resp2 = client.get(url2)
    assert resp2.text == "<html>Stealth Page</html>"
    # get_count should remain 1 (bypassed standard GET completely), crawl4ai_count should be 2.
    assert get_count == 1
    assert crawl4ai_count == 2


# ---------------------------------------------------------------------------
# normalize_media_url – percent-encoding deduplication
# ---------------------------------------------------------------------------


def test_normalize_media_url_unquotes_path():
    """Percent-encoded and plain-space URLs should produce the same key."""
    from core.filters import normalize_media_url

    encoded = "https://cdn.example-media.com/videos/Subject%20Alpha%20Gallery.mp4"
    plain = "https://cdn.example-media.com/videos/Subject Alpha Gallery.mp4"
    assert normalize_media_url(encoded) == normalize_media_url(plain)


def test_normalize_media_url_strips_query():
    """Query parameters (auth tokens) must be stripped for the dedup key."""
    from core.filters import normalize_media_url

    with_token = (
        "https://video-site.example.com/get_file/3/abc123/vid.mp4?v-acctoken=XYZ"
    )
    without_token = "https://video-site.example.com/get_file/3/abc123/vid.mp4"
    assert normalize_media_url(with_token) == normalize_media_url(without_token)


def test_normalize_media_url_normalises_scheme():
    """http and https should resolve to the same key."""
    from core.filters import normalize_media_url

    http_url = "http://example.com/img.jpg"
    https_url = "https://example.com/img.jpg"
    assert normalize_media_url(http_url) == normalize_media_url(https_url)


# ---------------------------------------------------------------------------
# Engine deduplication – tokenless → tokened URL upgrade
# ---------------------------------------------------------------------------


def test_engine_upgrades_tokenless_to_tokened_url():
    """When a tokenless URL is stored first and then the tokened variant arrives,
    the stored item should have its URL upgraded to the tokened one."""
    from core.models import VideoItem

    # Simulate the dedup dict that the engine maintains
    seen_videos: dict[str, VideoItem] = {}
    from core.filters import normalize_media_url, normalize_url

    tokenless_url = "https://video-site.example.com/get_file/3/abc/vid_1080p.mp4"
    tokened_url = "https://video-site.example.com/get_file/3/abc/vid_1080p.mp4?v-acctoken=SECRETTOKEN"

    # First discovery: tokenless URL
    item1 = VideoItem(
        url=tokenless_url,
        source_page="https://video-site.example.com/video/100/",
        type="direct",
        page_title="Test Video",
    )
    norm_key = normalize_media_url(normalize_url(item1.url))
    seen_videos[norm_key] = item1

    # Confirm key is stored
    assert norm_key in seen_videos
    assert seen_videos[norm_key].url == tokenless_url

    # Second discovery: same path but with auth token
    item2 = VideoItem(
        url=tokened_url,
        source_page="https://video-site.example.com/video/100/",
        type="direct",
        page_title="Test Video",
    )
    norm_key2 = normalize_media_url(normalize_url(item2.url))

    # Both should map to the same norm_key
    assert norm_key == norm_key2

    # Apply the upgrade logic
    existing = seen_videos[norm_key2]
    if "?" in item2.url and "?" not in existing.url:
        existing.url = item2.url

    # The stored item should now carry the tokened URL
    assert seen_videos[norm_key].url == tokened_url


# ---------------------------------------------------------------------------
# Path trailing slash and query param parsing checks
# ---------------------------------------------------------------------------


def test_trailing_slash_detection_and_parsing():
    from scraper.video_scraper import detect_video_type, DIRECT_VIDEO_PATTERN
    from core.filters import is_probable_video, is_probable_image

    # Simulate a site that embeds tokened direct-MP4 URLs with a trailing slash before the query
    tokened_url = (
        "https://video-site.example.com/get_file/3/abc/vid_1080p.mp4/?v-acctoken=123"
    )
    tokened_image_url = (
        "https://video-site.example.com/contents/images/preview.jpg/?w=400"
    )

    # 1. detect_video_type checks
    assert detect_video_type(tokened_url) == "direct"
    assert detect_video_type("https://site.com/file.m3u8/") == "hls"
    assert detect_video_type("https://site.com/file.m3u8/?token=123") == "hls"

    # 2. is_probable_video & is_probable_image checks
    assert is_probable_video(tokened_url) is True
    assert is_probable_image(tokened_image_url) is True
    assert is_probable_video("https://site.com/file.mp4/") is True
    assert is_probable_image("https://site.com/file.png/") is True

    # 3. Regex matching checks — script block embedding trailing-slash tokened URL
    script_content = "video_url: 'https://video-site.example.com/get_file/3/abc/vid_1080p.mp4/?v-acctoken=123'"
    matches = DIRECT_VIDEO_PATTERN.findall(script_content)
    assert len(matches) == 1
    assert (
        matches[0]
        == "https://video-site.example.com/get_file/3/abc/vid_1080p.mp4/?v-acctoken=123"
    )


def test_http_client_escalating_timeout_and_adaptive_rate_limit(monkeypatch):
    import time
    import httpx
    from utils.http_client import HttpClient

    # 1. Test timeout escalation retry
    client = HttpClient(timeout=5.0)

    timeout_calls = 0
    original_client_get = client.client.get

    def mock_get(url, **kwargs):
        nonlocal timeout_calls
        if "timeout-escalate" in url:
            timeout_calls += 1
            if timeout_calls == 1:
                assert kwargs.get("timeout") == 5.0
                raise httpx.TimeoutException("Timeout attempt 1")
            elif timeout_calls == 2:
                assert kwargs.get("timeout") == 10.0
                # Succeed on second attempt
                return httpx.Response(
                    200,
                    content=b"Success after retry",
                    request=httpx.Request("GET", url),
                )
        return original_client_get(url, **kwargs)

    monkeypatch.setattr(client.client, "get", mock_get)
    monkeypatch.setattr(time, "sleep", lambda x: None)  # fast tests

    res = client.get("https://example-test.com/timeout-escalate")
    assert res.status_code == 200
    assert res.text == "Success after retry"
    assert timeout_calls == 2

    # 2. Test adaptive 429 backoff
    limiter = client._rate_limiter_for("https://example-test-429.com/path")
    original_rps = limiter.requests_per_second

    def mock_get_429(url, **kwargs):
        resp = httpx.Response(429, request=httpx.Request("GET", url))
        raise httpx.HTTPStatusError(
            "429 Too Many Requests", request=httpx.Request("GET", url), response=resp
        )

    monkeypatch.setattr(client.client, "get", mock_get_429)
    monkeypatch.setattr(
        client, "_get_with_crawl4ai", lambda url: "<html>Mocked Crawl4AI Page</html>"
    )

    resp = client.get("https://example-test-429.com/path")
    assert resp.status_code == 200
    assert resp.text == "<html>Mocked Crawl4AI Page</html>"
    # The requests_per_second should be halved!
    assert limiter.requests_per_second == original_rps * 0.5


# ---------------------------------------------------------------------------
# Search pagination & stealth registration
# ---------------------------------------------------------------------------

def test_search_pagination_follows_next_page_form():
    """_extract_next_page_url should return a URL when a valid DDG form is present."""
    from bs4 import BeautifulSoup
    from scraper.google_images import SearchProviderScraper

    html_page1 = """
    <html><body>
      <a class="result__a" href="https://example.com/page1">Result 1</a>
      <form method="post" action="/html/">
        <input type="hidden" name="q" value="test keyword">
        <input type="hidden" name="s" value="30">
        <input type="hidden" name="vqd" value="abc123token">
        <input type="hidden" name="kp" value="-2">
        <input type="submit" value="Next">
      </form>
    </body></html>
    """
    soup = BeautifulSoup(html_page1, "html.parser")
    next_url = SearchProviderScraper._extract_next_page_url(soup)
    assert next_url is not None, "Should find next-page URL from form"
    assert "html.duckduckgo.com" in next_url
    assert "vqd=abc123token" in next_url
    assert "s=30" in next_url


def test_search_pagination_returns_none_on_missing_form():
    """_extract_next_page_url should return None when no valid form exists."""
    from bs4 import BeautifulSoup
    from scraper.google_images import SearchProviderScraper

    html_last_page = """
    <html><body>
      <a class="result__a" href="https://example.com/page1">Result 1</a>
      <!-- No next-page form -->
    </body></html>
    """
    soup = BeautifulSoup(html_last_page, "html.parser")
    next_url = SearchProviderScraper._extract_next_page_url(soup)
    assert next_url is None, "Should return None on last page (no next-page form)"


def test_register_stealth_required_marks_host():
    """register_stealth_required should add the hostname to the class-level set."""
    from utils.http_client import HttpClient

    test_host = "stealth-test-host.example"
    # Ensure clean state for this test
    HttpClient._stealth_required_hosts.discard(test_host)
    HttpClient.register_stealth_required(test_host)
    assert test_host in HttpClient._stealth_required_hosts
    # Cleanup
    HttpClient._stealth_required_hosts.discard(test_host)


def test_search_provider_scraper_registers_ddg_stealth():
    """SearchProviderScraper.__init__ must register DDG hosts as stealth-required."""
    from utils.http_client import HttpClient
    from scraper.google_images import SearchProviderScraper

    # Instantiate to trigger __init__ stealth registration
    _scraper = SearchProviderScraper()
    assert "duckduckgo.com" in HttpClient._stealth_required_hosts
    assert "html.duckduckgo.com" in HttpClient._stealth_required_hosts
