import pytest
import time
from urllib.parse import urlparse

from core.filters import transform_to_highres, is_search_page_url
from storage.file_downloader import _host_semaphore_for
from utils.http_client import HttpClient


def test_transform_to_highres_extended_rules():
    # WordPress dimension pattern
    upscaled, orig = transform_to_highres("https://cosplaytele.com/wp-content/uploads/2026/01/image-150x150.jpg")
    assert upscaled == "https://cosplaytele.com/wp-content/uploads/2026/01/image.jpg"

    # Thumbnail subpath replacement
    upscaled, orig = transform_to_highres("https://indoporn.mobi/thumbs/2026/preview.jpg")
    assert "/images/" in upscaled

    # Video thumbs replacement
    upscaled, orig = transform_to_highres("https://epawg.com/video_thumbs/123/cover.jpg")
    assert "/video_sources/" in upscaled

    # Twitter name parameter
    upscaled, orig = transform_to_highres("https://pbs.twimg.com/media/abc?format=jpg&name=small")
    assert "name=large" in upscaled


def test_is_search_page_url():
    assert is_search_page_url("https://www.flickr.com/search/?text=apple") is True
    assert is_search_page_url("https://vimeo.com/search?q=apple") is True
    assert is_search_page_url("https://example.com/gallery/123") is False


def test_dynamic_host_semaphore_scaling():
    sem = _host_semaphore_for("test_dynamic_host.com", max_concurrent=16)
    assert sem._value == 16


def test_flaresolverr_escalation_attribute():
    client = HttpClient()
    assert hasattr(client, "_get_with_flaresolverr")
