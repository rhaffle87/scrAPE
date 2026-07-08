from bs4 import BeautifulSoup

from scraper.video_scraper import extract_videos_from_html


def test_extract_videos_from_html_finds_direct_video_links() -> None:
    soup = BeautifulSoup(
        '<html><body><video><source src="/clip.mp4"></video><a href="https://example.com/demo.mp4">Demo</a></body></html>',
        "html.parser",
    )

    videos = extract_videos_from_html(soup, "https://example.com/page")

    assert len(videos) == 2
    assert videos[0].url == "https://example.com/clip.mp4"
    assert videos[1].url == "https://example.com/demo.mp4"


def test_extract_videos_from_html_finds_text_embedded_video_links() -> None:
    soup = BeautifulSoup(
        '<html><body><div>Watch https://www.youtube.com/watch?v=abc123xyz</div></body></html>',
        "html.parser",
    )

    videos = extract_videos_from_html(soup, "https://example.com/page")

    assert len(videos) == 1
    assert videos[0].url == "https://www.youtube.com/watch?v=abc123xyz"
