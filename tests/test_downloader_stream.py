import struct
import pytest
import httpx
import contextlib
from pathlib import Path
from storage.file_downloader import MediaDownloader

def test_downloader_stream_early_resolution_abort(monkeypatch):
    downloader = MediaDownloader()
    
    # Track stream chunk reads
    chunks_read = 0
    
    @contextlib.contextmanager
    def mock_stream(client_self, method, url, **kwargs):
        nonlocal chunks_read
        # Construct a response with a generator of chunks
        # The first chunk is 8KB of a too-small image (e.g. 100x100 PNG)
        # PNG signature + IHDR header with width=100, height=100
        first_chunk = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + struct.pack(">II", 100, 100) + b"\x00" * 8100
        # If we continue reading, we'd get a second chunk
        second_chunk = b"\x00" * 8192
        
        def iter_bytes(chunk_size=8192):
            nonlocal chunks_read
            chunks_read += 1
            yield first_chunk
            chunks_read += 1
            yield second_chunk

        resp = httpx.Response(
            status_code=200,
            request=httpx.Request(method, url)
        )
        resp.headers["content-type"] = "image/png"
        resp.headers["content-length"] = "16384"
        monkeypatch.setattr(resp, "iter_bytes", iter_bytes)
        yield resp

    monkeypatch.setattr(httpx.Client, "stream", mock_stream)
    
    temp_dir = Path("output/test_stream_abort")
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        success, reason = downloader._download_file(
            url="https://example.com/small_image.png",
            directory=temp_dir,
            prefix="test_prefix",
            media_kind="image"
        )
        # Should fail download validation
        assert success is False
        assert reason == "low_resolution"
        # The stream should have been aborted after the first chunk (1 iteration)
        assert chunks_read == 1
    finally:
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
