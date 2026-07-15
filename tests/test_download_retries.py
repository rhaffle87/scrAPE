import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock, patch
import httpx
from storage.file_downloader import MediaDownloader
from utils.http_client import HttpClient


def test_downloader_sticky_user_agent():
    """Verify that MediaDownloader uses the sticky User-Agent from the HttpClient's session pool."""
    http = HttpClient()
    # Pre-populate session with a specific User-Agent for a target host
    host = "example.com"
    session = http._session_pool.get_session(host)
    expected_ua = session.user_agent

    downloader = MediaDownloader(http=http)
    headers = downloader._make_download_headers("https://example.com/image.jpg")
    
    assert headers["User-Agent"] == expected_ua


def test_download_file_retry_on_network_error(tmp_path):
    """Verify that MediaDownloader._download_file retries on transient network errors."""
    http = HttpClient()
    mock_client = MagicMock()
    http.client = mock_client
    
    # We want to mock client.stream to raise a ConnectError twice, then succeed
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "image/jpeg", "content-length": "20000"}
    mock_response.iter_bytes.return_value = [b"\xff\xd8\xff" + b"\x00" * 19997]

    calls = []
    def mock_stream(*args, **kwargs):
        calls.append(args)
        if len(calls) < 3:
            raise httpx.ConnectError("Connection failed")
        
        # Return a context manager that yields mock_response
        class MockCM:
            def __enter__(self):
                return mock_response
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        return MockCM()

    mock_client.stream = mock_stream

    downloader = MediaDownloader(http=http)
    
    # Mock rate limiter wait to speed up the test
    http._rate_limiter_for("https://example.com/img.jpg").wait = MagicMock()

    mock_fast_rl = MagicMock()
    mock_fast_rl.wait = MagicMock()

    with patch("time.sleep") as mock_sleep, \
         patch("storage.file_downloader.get_image_dimensions", return_value=(800, 600)), \
         patch("storage.file_downloader._fast_limiter_for", return_value=mock_fast_rl):
        success, reason = downloader._download_file(
            url="https://example.com/img.jpg",
            directory=tmp_path,
            prefix="test_img",
            media_kind="image"
        )
        
        # Verify it succeeded after retries
        assert success is True
        assert reason["reason"] == "ok"
        assert len(calls) == 3
        # Sleep should be called with exponential backoff (2^1 = 2s, 2^2 = 4s)
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(2.0)
        mock_sleep.assert_any_call(4.0)


def test_download_file_retry_on_server_error(tmp_path):
    """Verify that MediaDownloader._download_file retries on transient 5xx HTTP status codes."""
    http = HttpClient()
    mock_client = MagicMock()
    http.client = mock_client
    
    # Mock stream to return 503 Service Unavailable once, then 200 OK
    resp_503 = MagicMock()
    resp_503.status_code = 503
    resp_503.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Service Unavailable", request=MagicMock(), response=resp_503
    )

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.headers = {"content-type": "image/jpeg", "content-length": "20000"}
    resp_200.iter_bytes.return_value = [b"\xff\xd8\xff" + b"\x00" * 19997]

    calls = []
    def mock_stream(*args, **kwargs):
        calls.append(args)
        response = resp_503 if len(calls) == 1 else resp_200
        class MockCM:
            def __enter__(self):
                return response
            def __exit__(self, exc_type, exc_val, exc_tb):
                pass
        return MockCM()

    mock_client.stream = mock_stream

    downloader = MediaDownloader(http=http)
    http._rate_limiter_for("https://example.com/img.jpg").wait = MagicMock()

    mock_fast_rl2 = MagicMock()
    mock_fast_rl2.wait = MagicMock()

    with patch("time.sleep") as mock_sleep, \
         patch("storage.file_downloader.get_image_dimensions", return_value=(800, 600)), \
         patch("storage.file_downloader._fast_limiter_for", return_value=mock_fast_rl2):
        success, reason = downloader._download_file(
            url="https://example.com/img.jpg",
            directory=tmp_path,
            prefix="test_img",
            media_kind="image"
        )
        
        assert success is True
        assert reason["reason"] == "ok"
        assert len(calls) == 2
        assert mock_sleep.call_count == 1
        mock_sleep.assert_called_once_with(2.0)


def test_downloader_session_cookie_enrichment():
    """Verify that MediaDownloader gets session cookies from HttpClient.session_manager."""
    http = HttpClient()
    host = "example-enrichment.com"
    cookies_to_save = {"cf_clearance": "bypass123", "session_token": "abc789"}
    
    try:
        http.session_manager.save_session(host, cookies_to_save)

        downloader = MediaDownloader(http=http)
        headers = downloader._make_download_headers("https://example-enrichment.com/image.jpg")
        
        assert "Cookie" in headers
        cookie_header = headers["Cookie"]
        assert "cf_clearance=bypass123" in cookie_header
        assert "session_token=abc789" in cookie_header
    finally:
        # Clean up session file
        session_file = Path(http.session_manager.get_session_file(host))
        if session_file.exists():
            session_file.unlink()
