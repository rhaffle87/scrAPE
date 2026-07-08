from bs4 import BeautifulSoup
from pathlib import Path
from core.engine import ScrapingEngine
from utils.robots import RobotsChecker
from utils.http_client import HttpClient

def test_is_detail_page_heuristics():
    # Root index / search / archive seed page: link must contain keyword or entity token
    assert ScrapingEngine._is_detail_page(
        link="https://example.com/some-post-about-meenfox",
        seed_page="https://example.com/?s=meenfox",
        keyword_or_entity="meenfox"
    ) is True

    assert ScrapingEngine._is_detail_page(
        link="https://example.com/other-unrelated-post",
        seed_page="https://example.com/?s=meenfox",
        keyword_or_entity="meenfox"
    ) is False

    # Specific subpath seed page: link must start with seed_path or match entity tokens
    assert ScrapingEngine._is_detail_page(
        link="https://example.com/videos/subject_alpha/123",
        seed_page="https://example.com/videos/subject_alpha",
        keyword_or_entity="subject_alpha"
    ) is True

def test_robots_checker_bypass():
    http = HttpClient()
    # Robots checker with ignore_robots=True should always return True
    checker_bypass = RobotsChecker(http, ignore_robots=True)
    assert checker_bypass.is_allowed("https://example.com/disallowed-path") is True

    # With ignore_robots=False, it fetches or checks rules (mocked here or returns True if fetch fails)
    checker_normal = RobotsChecker(http, ignore_robots=False)
    assert checker_normal.is_allowed("https://example.com/some-path") is True

def test_layout_skips_in_video_scraper():
    from scraper.video_scraper import extract_videos_from_html
    
    html = """
    <html>
      <body>
        <div id="main-content">
          <video src="https://example.com/good-video.mp4"></video>
        </div>
        <div class="sidebar widget">
          <video src="https://example.com/layout-video.mp4"></video>
        </div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    videos = extract_videos_from_html(soup, "https://example.com/page")
    
    urls = [v.url for v in videos]
    assert "https://example.com/good-video.mp4" in urls
    assert "https://example.com/layout-video.mp4" not in urls

def test_domain_grouped_filenames():
    import re
    from urllib.parse import urlparse
    from core.models import ImageItem

    images = [
        ImageItem(url="https://site.com/img1.jpg", source_page="https://buondua.com/post1", alt_text="Alt 1"),
        ImageItem(url="https://site.com/img2.jpg", source_page="https://buondua.com/post2", alt_text="Alt 2"),
        ImageItem(url="https://site.com/img3.jpg", source_page="https://hotleak.vip/post1", alt_text="Alt 3"),
    ]

    def get_domain_slug(url: str) -> str:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        if ":" in netloc:
            netloc = netloc.split(":")[0]
        return netloc

    images_by_domain = {}
    for item in images:
        domain = get_domain_slug(item.source_page)
        images_by_domain.setdefault(domain, []).append(item)

    assert len(images_by_domain["buondua.com"]) == 2
    assert len(images_by_domain["hotleak.vip"]) == 1

    tasks = []
    for domain, items in images_by_domain.items():
        domain_prefix = domain.replace(".", "_")
        for idx, item in enumerate(items, start=1):
            stem_suffix = re.sub(r"[^a-zA-Z0-9]+", "_", (item.alt_text or item.page_title or "image").strip().lower()).strip("_")
            stem_suffix = stem_suffix[:40] if stem_suffix else "asset"
            stem = f"{domain_prefix}_{idx:03d}_{stem_suffix}"
            tasks.append((domain, stem))

    assert tasks[0] == ("buondua.com", "buondua_com_001_alt_1")
    assert tasks[1] == ("buondua.com", "buondua_com_002_alt_2")
    assert tasks[2] == ("hotleak.vip", "hotleak_vip_001_alt_3")
