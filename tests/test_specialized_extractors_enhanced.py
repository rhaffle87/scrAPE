"""
test_specialized_extractors_enhanced.py — Unit tests for enhanced specialized extractors.
"""

from unittest.mock import MagicMock
from plugins.ytdlp_extractor import YtDlpExtractor
from plugins.instagram_extractor import InstagramExtractor
from plugins.twitter_extractor import TwitterExtractor


def test_ytdlp_extractor_hls_stream_resolution(monkeypatch):
    extractor = YtDlpExtractor()
    url = "https://www.example.com/athletes/test-subject"

    # Mock yt_dlp info payload containing both HLS playlist and direct mp4 formats
    mock_info = {
        "id": "test_video",
        "url": "https://hdm-streaming-otfp.hearst.io/master.m3u8",
        "formats": [
            {"ext": "m3u8", "url": "https://hdm-streaming-otfp.hearst.io/master.m3u8", "height": 1080},
            {"ext": "mp4", "url": "https://hdm-streaming.hearst.io/video_16x9_720p.mp4", "height": 720},
            {"ext": "mp4", "url": "https://hdm-streaming.hearst.io/video_16x9_1080p.mp4", "height": 1080},
        ],
    }

    mock_ydl = MagicMock()
    mock_ydl.extract_info.return_value = mock_info
    mock_ydl_cls = MagicMock(return_value=mock_ydl)
    mock_ydl_cls.__enter__ = MagicMock(return_value=mock_ydl)
    mock_ydl_cls.__exit__ = MagicMock(return_value=None)

    monkeypatch.setattr("yt_dlp.YoutubeDL", lambda opts: mock_ydl_cls)

    res = extractor.extract(url)
    assert res is not None
    assert len(res.videos) == 1
    assert res.videos[0] == "https://hdm-streaming.hearst.io/video_16x9_1080p.mp4"


def test_instagram_extractor_carousel_and_cookie_forwarding(monkeypatch):
    extractor = InstagramExtractor()
    url = "https://www.instagram.com/p/C123456789/"

    monkeypatch.setattr(extractor, "get_domain_cookies", lambda domain: {"sessionid": "mock_session_123"})

    # Mock API JSON response returning a 2-slide carousel
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "graphql": {
            "shortcode_media": {
                "display_url": "https://instagram.fcc.net/slide1_hero.jpg",
                "edge_sidecar_to_children": {
                    "edges": [
                        {"node": {"display_url": "https://instagram.fcc.net/slide1.jpg"}},
                        {"node": {"display_url": "https://instagram.fcc.net/slide2.jpg"}},
                    ]
                },
            }
        }
    }

    monkeypatch.setattr("requests.get", lambda u, **kwargs: mock_resp)

    res = extractor.extract(url)
    assert len(res.images) == 3
    assert "https://instagram.fcc.net/slide1.jpg" in res.images
    assert "https://instagram.fcc.net/slide2.jpg" in res.images


def test_twitter_extractor_highres_transform(monkeypatch):
    extractor = TwitterExtractor()
    url = "https://x.com/user/status/1234567890"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "media_extended": [
            {"type": "image", "url": "https://pbs.twimg.com/media/ABC.jpg?format=jpg&name=small"},
            {"type": "image", "url": "https://pbs.twimg.com/media/DEF.jpg?format=jpg"},
        ]
    }

    import requests
    requests_get_orig = requests.get

    def mock_get(url, **kwargs):
        if "vxtwitter" in url:
            return mock_resp
        return requests_get_orig(url, **kwargs)

    monkeypatch.setattr("requests.get", mock_get)

    res = extractor.extract(url)
    assert len(res.images) == 2
    assert "name=large" in res.images[0]
    assert "name=large" in res.images[1]
