import pytest
from plugins.ytdlp_extractor import YtDlpExtractor


def test_ytdlp_can_handle_stream_urls():
    extractor = YtDlpExtractor()

    assert extractor.can_handle("https://example.com/live/stream.m3u8") is True
    assert extractor.can_handle("https://example.com/dash/manifest.mpd") is True
    assert extractor.can_handle("https://www.youtube.com/watch?v=12345") is True
    assert extractor.can_handle("https://tiktok.com/@user/video/67890") is True
    assert extractor.can_handle("https://example.com/index.html") is False


def test_ytdlp_quality_format_spec(monkeypatch):
    import config
    monkeypatch.setattr(config, "DEFAULT_VIDEO_QUALITY", "1080p")

    extractor = YtDlpExtractor()
    captured_format = []

    class MockYoutubeDL:
        def __init__(self, opts):
            captured_format.append(opts.get("format"))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def extract_info(self, url, download=False):
            return {"url": "https://cdn.com/1080p.mp4"}

    import sys
    mock_yt_dlp = type(sys)("yt_dlp")
    mock_yt_dlp.YoutubeDL = MockYoutubeDL
    monkeypatch.setitem(sys.modules, "yt_dlp", mock_yt_dlp)

    res = extractor.extract("https://example.com/stream.m3u8")
    assert len(res.videos) == 1
    assert res.videos[0] == "https://cdn.com/1080p.mp4"
    assert "height<=1080" in captured_format[0]
