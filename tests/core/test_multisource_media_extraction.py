from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup

from core.models import ImageItem, VideoItem
from core.media_processor import (
    parse_image_candidates,
    rank_media_candidates,
    _download_candidate_with_fallbacks,
)
from storage.downloader.manager import FileDownloader


def test_models_media_candidates_and_fallbacks():
    """Verify ImageItem and VideoItem support candidates, extraction_source, and fallback_urls."""
    img = ImageItem(
        url="https://example.com/main.jpg",
        source_page="https://example.com/page",
        fallback_urls=["https://example.com/fallback.jpg"],
        candidates=[{"url": "https://example.com/main.jpg", "score": 1000}],
        extraction_source="srcset",
    )
    assert img.fallback_urls == ["https://example.com/fallback.jpg"]
    assert len(img.candidates) == 1
    assert img.extraction_source == "srcset"

    vid = VideoItem(
        url="https://example.com/main.mp4",
        source_page="https://example.com/page",
        type="direct",
        fallback_urls=["https://example.com/fallback.mp4"],
    )
    assert vid.fallback_urls == ["https://example.com/fallback.mp4"]


def test_parse_image_candidates_and_rank_multi_source():
    """Verify multi-source candidate parsing from zoom attributes, srcset, and src."""
    html = """
    <div class="gallery">
        <a href="https://example.com/uncompressed_raw.jpg">
            <img src="https://example.com/thumb.jpg"
                 data-zoom-image="https://example.com/ultra_zoom.jpg"
                 data-highres="https://example.com/highres.jpg"
                 srcset="https://example.com/card_400.jpg 400w, https://example.com/card_1600.jpg 1600w"
                 alt="Test Product"/>
        </a>
    </div>
    """
    soup = BeautifulSoup(html, "html.parser")
    img_tag = soup.find("img")

    candidates = parse_image_candidates(img_tag, "https://example.com/product")
    assert len(candidates) >= 5

    primary_url, fallbacks = rank_media_candidates(candidates)
    # data-zoom-image has score 1600, card_1600 has 600+1600=2200!
    assert primary_url == "https://example.com/card_1600.jpg"
    assert "https://example.com/ultra_zoom.jpg" in fallbacks
    assert "https://example.com/uncompressed_raw.jpg" in fallbacks
    assert "https://example.com/thumb.jpg" in fallbacks


def test_download_candidate_with_fallbacks_recovery():
    """Verify _download_candidate_with_fallbacks recovers from primary URL failure."""
    item = ImageItem(
        url="https://example.com/broken_primary.jpg",
        source_page="https://example.com/page",
        fallback_urls=[
            "https://example.com/broken_secondary.jpg",
            "https://example.com/working_fallback.jpg",
        ],
    )

    mock_downloader = MagicMock()
    # 1st call fails, 2nd call fails, 3rd call succeeds
    mock_downloader._download_file.side_effect = [
        (False, {"reason": "http_error:404"}),
        (False, {"reason": "http_error:404"}),
        (True, {"file_path": "/path/to/working_fallback.jpg", "hash": "abc"}),
    ]

    success, info = _download_candidate_with_fallbacks(
        mock_downloader,
        item,
        Path("/tmp/downloads"),
        "001_item",
        "image",
        referer=None,
        min_size=None,
        thumb_pattern=None,
        cdn_hosts=None,
    )

    assert success is True
    assert item.url == "https://example.com/working_fallback.jpg"
    assert mock_downloader._download_file.call_count == 3


def test_file_downloader_parallel_chunks_assembly(tmp_path: Path):
    """Verify _download_parallel_chunks correctly partitions and reassembles chunks without mocking out the method."""
    downloader = FileDownloader()
    target_file = tmp_path / "large_asset.bin"
    total_size = 400
    expected_data = b"A" * 100 + b"B" * 100 + b"C" * 100 + b"D" * 100

    chunk_data = {
        "bytes=0-99": b"A" * 100,
        "bytes=100-199": b"B" * 100,
        "bytes=200-299": b"C" * 100,
        "bytes=300-399": b"D" * 100,
    }

    class FakeStreamResp:
        def __init__(self, data):
            self.data = data
            self.status_code = 206
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def iter_bytes(self, chunk_size=16384):
            yield self.data

    class FakeClient:
        def __init__(self, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def stream(self, method, url, headers=None, **kwargs):
            rng = headers.get("Range", "")
            return FakeStreamResp(chunk_data.get(rng, b""))

    with patch("httpx.Client", FakeClient):
        ok = downloader._download_parallel_chunks(
            "https://example.com/large.mp4",
            target_file,
            total_size,
            {"User-Agent": "test"},
            num_chunks=4,
        )
        assert ok is True
        assert target_file.exists()
        assert target_file.read_bytes() == expected_data


import contextlib
import httpx


def test_file_downloader_fallback_urls_execution(monkeypatch, tmp_path: Path):
    """Verify _download_file attempts fallback_urls when primary URL fails."""
    downloader = FileDownloader()

    monkeypatch.setattr("storage.downloader.manager._sleep", lambda s: None)

    @contextlib.contextmanager
    def mock_stream(client_self, method, url, **kwargs):
        if "bad" in url:
            resp = httpx.Response(status_code=404, request=httpx.Request(method, url))
            resp.headers["content-type"] = "video/mp4"
            resp.headers["content-length"] = "0"
            def empty_iter(chunk_size=8192):
                return iter([])
            monkeypatch.setattr(resp, "iter_bytes", empty_iter)
            yield resp
        else:
            resp = httpx.Response(status_code=200, request=httpx.Request(method, url))
            resp.headers["content-type"] = "video/mp4"
            resp.headers["content-length"] = "32768"
            def valid_iter(chunk_size=8192):
                yield b"\x00\x00\x00\x18ftypmp42" + b"\x00" * 32740
            monkeypatch.setattr(resp, "iter_bytes", valid_iter)
            yield resp

    def mock_head(client_self, url, **kwargs):
        if "bad" in str(url):
            return httpx.Response(status_code=404, request=httpx.Request("HEAD", url))
        return httpx.Response(
            status_code=200,
            headers={"content-type": "video/mp4", "content-length": "32768"},
            request=httpx.Request("HEAD", url),
        )

    monkeypatch.setattr(httpx.Client, "stream", mock_stream)
    monkeypatch.setattr(httpx.Client, "head", mock_head)

    ok, res = downloader._download_file(
        "https://example.com/bad_video.mp4",
        tmp_path,
        "001_item",
        "video",
        fallback_urls=["https://example.com/good_video.mp4"],
    )
    assert ok is True
    assert "file_path" in res
    assert (tmp_path / "001_item.mp4").exists()


