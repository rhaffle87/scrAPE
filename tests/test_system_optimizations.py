import json
import pytest
from unittest.mock import patch
from urllib.parse import urlparse

from core.filters import transform_to_highres, is_search_page_url
from storage.file_downloader import MediaDownloader
from network.http_client import HttpClient


def test_transform_to_highres_extended_rules():
    # WordPress dimension pattern
    upscaled, orig = transform_to_highres("https://example.com/wp-content/uploads/2026/01/image-150x150.jpg")
    assert upscaled == "https://example.com/wp-content/uploads/2026/01/image.jpg"

    # Thumbnail subpath replacement (generic fallback: /thumbs/ → /images/)
    upscaled, orig = transform_to_highres("https://example.org/thumbs/2026/preview.jpg")
    assert "/images/" in upscaled

    # Video thumbs replacement (generic fallback: /video_thumbs/ → /video_sources/)
    upscaled, orig = transform_to_highres("https://example.net/video_thumbs/123/cover.jpg")
    assert "/video_sources/" in upscaled

    # Twitter name parameter (generic fallback: name=small → name=large)
    upscaled, orig = transform_to_highres("https://pbs.twimg.com/media/abc?format=jpg&name=small")
    assert "name=large" in upscaled

    # Generic /thumbs/ → /images/ (no domain-specific config for example.com)
    upscaled, orig = transform_to_highres("https://example.com/thumbs/thumb_photo_001.jpg")
    assert "/images/" in upscaled

    # Generic /preview/ path is converted to /images/ by the generic fallback
    # (domain-specific /preview/→/original/ only fires for configured hosts)
    upscaled, orig = transform_to_highres("https://example.xyz/preview/thumbnail_abc123.jpg")
    assert "/images/" in upscaled


def test_transform_to_highres_domain_config_rules():
    """Verify that domain_config.json highres_transforms rules fire for configured hosts.

    We inject a fake config payload via patching json.loads inside core.filters so
    the test is fully isolated from the real data/domain_config.json file and from
    any real production domain names.
    """
    fake_config = {
        "highres_transforms": {
            "example_xyz": {
                "host_contains": ["example.xyz"],
                "rules": [
                    {"pattern": "/preview/", "replacement": "/original/", "target": "path"},
                    {"pattern": "thumbnail_", "replacement": "", "target": "path"},
                ],
            },
            "example": {
                "host_contains": ["example.com"],
                "rules": [
                    {"pattern": "/thumb_", "replacement": "/img_", "target": "path"},
                    {"pattern": "/thumbs/", "replacement": "/images/", "target": "path"},
                ],
            },
        }
    }

    # Patch pathlib.Path.exists to signal the config file exists, and
    # Path.read_text to return our fake payload — both on the pathlib module
    # directly so the local alias inside filters.py is intercepted.
    from pathlib import Path as _RealPath
    import pathlib

    _orig_exists = _RealPath.exists
    _orig_read_text = _RealPath.read_text

    def _fake_exists(self):
        if self.name == "domain_config.json":
            return True
        return _orig_exists(self)

    def _fake_read_text(self, encoding="utf-8"):
        if self.name == "domain_config.json":
            return json.dumps(fake_config)
        return _orig_read_text(self, encoding=encoding)

    with patch.object(pathlib.Path, "exists", _fake_exists), \
         patch.object(pathlib.Path, "read_text", _fake_read_text):
        from core.filters import _reset_highres_cache
        _reset_highres_cache()  # bust G1 mtime-cache so monkeypatch is effective

        # rule34.xyz: /preview/ → /original/, thumbnail_ stripped
        upscaled, _ = transform_to_highres("https://example.xyz/preview/thumbnail_abc123.jpg")
        assert "/original/" in upscaled
        assert "thumbnail_" not in upscaled

        # kusowanka.com: /thumbs/ → /images/
        upscaled, _ = transform_to_highres("https://example.com/thumbs/photo.jpg")
        assert "/images/" in upscaled


def test_is_search_page_url():
    assert is_search_page_url("https://example.com/search/?text=test") is True
    assert is_search_page_url("https://example.org/search?q=test") is True
    assert is_search_page_url("https://example.com/gallery/123") is False


def test_dynamic_host_semaphore_scaling():
    """_host_semaphore_for (now an instance method) must honour max_concurrent."""
    from unittest.mock import MagicMock, patch
    mock_http = MagicMock()
    mock_http.get_proxy = MagicMock(return_value=None)
    with patch("storage.file_downloader.HttpClient", return_value=mock_http), \
         patch("network.bandwidth_limiter.BandwidthLimiter", MagicMock()), \
         patch("ml.aesthetic_scorer.AestheticScorer", MagicMock()):
        dl = MediaDownloader(http=mock_http)
    sem = dl._host_semaphore_for("test_dynamic_host.com", max_concurrent=16)
    assert sem._value == 16


def test_flaresolverr_escalation_attribute():
    client = HttpClient()
    assert hasattr(client, "_get_with_flaresolverr")
