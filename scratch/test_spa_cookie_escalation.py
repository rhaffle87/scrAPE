import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from plugins.base import ExtractorPlugin, SpecializedResult
from plugins.instagram_extractor import InstagramExtractor
from plugins.twitter_extractor import TwitterExtractor
from plugins.ytdlp_extractor import YtDlpExtractor


def test_extractor_base_get_domain_cookies():
    """Verify get_domain_cookies returns a dict on any domain."""
    plugin = InstagramExtractor()
    cookies = plugin.get_domain_cookies("instagram.com")
    assert isinstance(cookies, dict)


def test_instagram_extractor_can_handle():
    """Verify InstagramExtractor URL matching."""
    plugin = InstagramExtractor()
    assert plugin.can_handle("https://www.instagram.com/p/C12345/") is True
    assert plugin.can_handle("https://instagram.com/reel/C67890/") is True
    assert plugin.can_handle("https://example.com/p/123/") is False


def test_twitter_extractor_can_handle():
    """Verify TwitterExtractor URL matching."""
    plugin = TwitterExtractor()
    assert plugin.can_handle("https://twitter.com/user/status/123456789") is True
    assert plugin.can_handle("https://x.com/user/status/987654321") is True
    assert plugin.can_handle("https://example.com/status/123") is False


def test_ytdlp_extractor_can_handle():
    """Verify YtDlpExtractor URL matching."""
    plugin = YtDlpExtractor()
    assert plugin.can_handle("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True
    assert plugin.can_handle("https://vimeo.com/123456") is True
