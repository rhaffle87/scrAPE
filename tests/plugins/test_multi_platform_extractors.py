import pytest
from plugins.civitai_extractor import CivitaiExtractor
from plugins.booru_extractor import BooruExtractor
from plugins.pinterest_extractor import PinterestExtractor
from plugins.artstation_extractor import ArtStationExtractor


def test_civitai_can_handle():
    ext = CivitaiExtractor()
    assert ext.can_handle("https://civitai.com/images/12345") is True
    assert ext.can_handle("https://civitai.com/models/67890") is True
    assert ext.can_handle("https://example.com") is False


def test_booru_can_handle():
    ext = BooruExtractor()
    assert ext.can_handle("https://danbooru.donmai.us/posts/100") is True
    assert ext.can_handle("https://gelbooru.com/index.php?page=post&s=view&id=200") is True
    assert ext.can_handle("https://safebooru.org/index.php?page=post&s=view&id=300") is True
    assert ext.can_handle("https://example.com") is False


def test_pinterest_can_handle():
    ext = PinterestExtractor()
    assert ext.can_handle("https://pinterest.com/pin/123456789/") is True
    assert ext.can_handle("https://i.pinimg.com/originals/ab/cd/ef.jpg") is True
    assert ext.can_handle("https://example.com") is False


def test_artstation_can_handle():
    ext = ArtStationExtractor()
    assert ext.can_handle("https://www.artstation.com/artwork/abcde") is True
    assert ext.can_handle("https://example.com") is False
