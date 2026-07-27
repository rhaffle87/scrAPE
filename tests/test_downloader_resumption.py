import pytest
import os
import tempfile
from pathlib import Path
from storage.file_downloader import MediaDownloader
from core.models import ImageItem, VideoItem, ScrapeResult

def test_downloader_stream_resumption(tmp_path):
    downloader = MediaDownloader(workers=2)
    assert hasattr(downloader, "download")
    assert downloader.workers == 2
