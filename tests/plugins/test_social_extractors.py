import pytest
from src.plugins.instagram_extractor import InstagramExtractor
from src.plugins.twitter_extractor import TwitterExtractor
from src.plugins.telegram_extractor import TelegramExtractor
from src.scraper.specialized import SpecializedExtractor

def test_instagram_extractor_can_handle():
    ext = InstagramExtractor()
    assert ext.can_handle("https://www.instagram.com/p/C_12345/")
    assert ext.can_handle("https://instagram.com/reel/C_98765/?hl=en")
    assert ext.can_handle("https://instagr.am/tv/C_112233/")
    assert not ext.can_handle("https://www.facebook.com/photo.php")

def test_twitter_extractor_can_handle():
    ext = TwitterExtractor()
    assert ext.can_handle("https://twitter.com/user/status/123456789")
    assert ext.can_handle("https://x.com/user/status/987654321?s=20")
    assert ext.can_handle("https://vxtwitter.com/user/status/111222333")
    assert not ext.can_handle("https://twitter.com/search?q=test")

def test_telegram_extractor_can_handle():
    ext = TelegramExtractor()
    assert ext.can_handle("https://t.me/s/durov/123")
    assert ext.can_handle("https://t.me/telegram/456")
    assert ext.can_handle("https://telegram.me/s/news/789")
    assert not ext.can_handle("https://t.com/test")

def test_specialized_extractor_auto_discovery():
    assert SpecializedExtractor.is_supported("https://www.instagram.com/p/C_12345/")
    assert SpecializedExtractor.is_supported("https://x.com/user/status/987654321")
    assert SpecializedExtractor.is_supported("https://t.me/s/durov/123")
