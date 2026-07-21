import contextlib
import httpx
import pytest
from pathlib import Path
from storage.file_downloader import MediaDownloader


def test_resumable_download_206_append(monkeypatch, tmp_path):
    downloader = MediaDownloader()
    
    # 1. Create a partial temp file
    prefix = "test_resumable_206"
    temp_target = tmp_path / f"{prefix}.mp4.tmp"
    temp_target.write_bytes(b"part1_" * 2000)  # 12000 bytes
    
    range_header_received = None
    
    @contextlib.contextmanager
    def mock_stream(client_self, method, url, **kwargs):
        nonlocal range_header_received
        headers = kwargs.get("headers", {})
        range_header_received = headers.get("Range")
        
        # Mock 206 Partial Content
        resp = httpx.Response(status_code=206, request=httpx.Request(method, url))
        resp.headers["content-type"] = "video/mp4"
        
        def iter_bytes(chunk_size=8192):
            yield b"part2_completed" * 2000  # 30000 bytes
            
        monkeypatch.setattr(resp, "iter_bytes", iter_bytes)
        yield resp
        
    monkeypatch.setattr(httpx.Client, "stream", mock_stream)
    
    success, result = downloader._download_file(
        url="https://example.com/test_video.mp4",
        directory=tmp_path,
        prefix=prefix,
        media_kind="video"
    )
    print("TEST 206 RESULT:", success, result)
    assert success is True
    assert range_header_received == "bytes=12000-"
    
    # Verify that the final target exists and has the concatenated content
    target = tmp_path / f"{prefix}.mp4"
    assert target.exists()
    assert target.read_bytes() == b"part1_" * 2000 + b"part2_completed" * 2000
    assert not temp_target.exists()


def test_resumable_download_200_overwrite(monkeypatch, tmp_path):
    downloader = MediaDownloader()
    
    # 1. Create a partial temp file
    prefix = "test_resumable_200"
    temp_target = tmp_path / f"{prefix}.mp4.tmp"
    temp_target.write_bytes(b"stale_part1_" * 1000)  # 12000 bytes
    
    range_header_received = None
    
    @contextlib.contextmanager
    def mock_stream(client_self, method, url, **kwargs):
        nonlocal range_header_received
        headers = kwargs.get("headers", {})
        range_header_received = headers.get("Range")
        
        # Mock 200 OK (server ignored Range header)
        resp = httpx.Response(status_code=200, request=httpx.Request(method, url))
        resp.headers["content-type"] = "video/mp4"
        
        def iter_bytes(chunk_size=8192):
            yield b"fresh_full_content" * 2000  # 36000 bytes
            
        monkeypatch.setattr(resp, "iter_bytes", iter_bytes)
        yield resp
        
    monkeypatch.setattr(httpx.Client, "stream", mock_stream)
    
    success, result = downloader._download_file(
        url="https://example.com/test_video.mp4",
        directory=tmp_path,
        prefix=prefix,
        media_kind="video"
    )
    
    assert success is True
    assert range_header_received == "bytes=12000-"
    
    # Verify that the target has ONLY the fresh content (truncated the stale parts)
    target = tmp_path / f"{prefix}.mp4"
    assert target.exists()
    assert target.read_bytes() == b"fresh_full_content" * 2000
    assert not temp_target.exists()


def test_resumable_download_416_retry(monkeypatch, tmp_path):
    downloader = MediaDownloader()
    
    # 1. Create a partial temp file
    prefix = "test_resumable_416"
    temp_target = tmp_path / f"{prefix}.mp4.tmp"
    temp_target.write_bytes(b"invalid_offset_data" * 1000)  # 19000 bytes
    
    attempts = 0
    range_headers_received = []
    
    @contextlib.contextmanager
    def mock_stream(client_self, method, url, **kwargs):
        nonlocal attempts, range_headers_received
        attempts += 1
        headers = kwargs.get("headers", {})
        range_headers_received.append(headers.get("Range"))
        
        if attempts == 1:
            # First attempt: Mock 416 Range Not Satisfiable
            resp = httpx.Response(status_code=416, request=httpx.Request(method, url))
            yield resp
        else:
            # Second attempt: Mock 200 OK downloading from scratch
            resp = httpx.Response(status_code=200, request=httpx.Request(method, url))
            resp.headers["content-type"] = "video/mp4"
            
            def iter_bytes(chunk_size=8192):
                yield b"brand_new_clean_download" * 1000  # 24000 bytes
                
            monkeypatch.setattr(resp, "iter_bytes", iter_bytes)
            yield resp
            
    monkeypatch.setattr(httpx.Client, "stream", mock_stream)
    
    success, result = downloader._download_file(
        url="https://example.com/test_video.mp4",
        directory=tmp_path,
        prefix=prefix,
        media_kind="video"
    )
    
    assert success is True
    # First attempt requested Range, second attempt (after 416 failure and unlink) did NOT request Range
    assert range_headers_received == ["bytes=19000-", None]
    
    # Verify the final target has the correct clean content
    target = tmp_path / f"{prefix}.mp4"
    assert target.exists()
    assert target.read_bytes() == b"brand_new_clean_download" * 1000
    assert not temp_target.exists()
