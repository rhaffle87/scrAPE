from bs4 import BeautifulSoup

from scraper.google_images import SearchProviderScraper


def test_extract_page_links_returns_absolute_internal_links() -> None:
    scraper = SearchProviderScraper()
    soup = BeautifulSoup(
        '<html><body><a href="/about">About</a><a href="https://example.com/contact">Contact</a><a href="https://other.com">Other</a></body></html>',
        "html.parser",
    )

    links = scraper._extract_page_links(soup, "https://example.com/home")

    assert links == ["https://example.com/about", "https://example.com/contact"]


def test_extract_page_links_skips_media_links() -> None:
    scraper = SearchProviderScraper()
    soup = BeautifulSoup(
        '<html><body><a href="/about">About</a><a href="https://example.com/photo.webp">Photo</a><a href="https://example.com/video.mp4">Video</a></body></html>',
        "html.parser",
    )

    links = scraper._extract_page_links(soup, "https://example.com/home")

    assert links == ["https://example.com/about"]


def test_discover_links_skips_media() -> None:
    scraper = SearchProviderScraper()
    links = scraper.discover_links("https://example.com/photo.webp")
    assert links == []


def test_extract_images_from_anchors() -> None:
    scraper = SearchProviderScraper()
    soup = BeautifulSoup(
        '<html><body><a href="https://example.com/highres.jpg">High Res Link</a></body></html>',
        "html.parser",
    )
    images = scraper._extract_images(soup, "https://example.com/page", "Test Title")
    assert len(images) == 1
    assert images[0].url == "https://example.com/highres.jpg"
    assert images[0].alt_text == "High Res Link"


def test_is_detail_page() -> None:
    from core.managers import DomainRulesManager
    
    rules = DomainRulesManager()

    # Test nested path (classic detail page pattern: index listing -> individual item)
    assert (
        rules.is_detail_page(
            "https://example.com/videos/subject/123",
            "https://example.com/videos/subject",
            ["subject"],
        )
        is True
    )

    # Test non-nested path with listing prefix & correct token in slug
    assert (
        rules.is_detail_page(
            "https://example.com/video/123/subject-portrait",
            "https://example.com/videos/subject",
            ["subject"],
        )
        is True
    )

    # Test non-nested path with wrong token in listing prefix (different subject)
    assert (
        rules.is_detail_page(
            "https://example.com/videos/other-model",
            "https://example.com/videos/subject",
            ["subject"],
        )
        is False
    )

    # Test pagination sibling rejection
    assert (
        rules.is_detail_page(
            "https://example.com/videos/subject/page/2",
            "https://example.com/videos/subject",
            ["subject"],
        )
        is False
    )

    # Test query param pagination rejection
    assert (
        rules.is_detail_page(
            "https://example.com/videos/subject?page=3",
            "https://example.com/videos/subject",
            ["subject"],
        )
        is False
    )

    # Test static pages rejection
    assert (
        rules.is_detail_page(
            "https://example.com/about",
            "https://example.com/videos/subject",
            ["subject"],
        )
        is False
    )
