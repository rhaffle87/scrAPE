"""
test_zero_copy_inline_stream_downloader.py — Tests for zero-copy streaming and inline SHA-256 calculation (v0.27.0).
"""

import hashlib

from storage.downloader.manager import MediaDownloader


def test_download_manager_compute_sha256_helper(tmp_path):
    """Verify _compute_sha256 calculates correct SHA-256 digest on disk files."""
    test_file = tmp_path / "sample.bin"
    sample_data = b"scrAPE high performance zero copy streaming pipeline " * 200
    test_file.write_bytes(sample_data)

    expected_hash = hashlib.sha256(sample_data).hexdigest()
    computed_hash = MediaDownloader._compute_sha256(test_file)

    assert computed_hash == expected_hash


def test_inline_streaming_sha256_matches_full_file(tmp_path):
    """Verify inline socket-to-disk streaming SHA-256 matches independent file hash exactly."""
    data = b"Video payload chunk bytes for inline streaming verification\n" * 1024
    expected_hash = hashlib.sha256(data).hexdigest()

    temp_target = tmp_path / "video.mp4.tmp"
    inline_hasher = hashlib.sha256()
    header_bytes = b""
    bytes_read = 0

    # Simulate streaming 8192-byte chunks
    chunk_size = 8192
    with open(temp_target, "wb") as f:
        for i in range(0, len(data), chunk_size):
            chunk = data[i : i + chunk_size]
            if len(header_bytes) < 1024:
                header_bytes += chunk[: 1024 - len(header_bytes)]
            f.write(chunk)
            inline_hasher.update(chunk)
            bytes_read += len(chunk)

    final_target = tmp_path / "video.mp4"
    temp_target.rename(final_target)

    # Inline computed hash
    inline_hash = inline_hasher.hexdigest()
    assert inline_hash == expected_hash

    # Compare with fresh read of final target
    file_disk_hash = MediaDownloader._compute_sha256(final_target)
    assert file_disk_hash == inline_hash
    assert bytes_read == len(data)
    assert len(header_bytes) == 1024


def test_inline_streaming_resumption_sha256(tmp_path):
    """Verify that seeding the inline hasher with pre-existing partial bytes yields exact full SHA-256."""
    full_data = b"Resumed video download test across multiple range requests.\n" * 512
    expected_full_hash = hashlib.sha256(full_data).hexdigest()

    part1 = full_data[: 10000]
    part2 = full_data[10000 :]

    temp_target = tmp_path / "video_resumed.mp4.tmp"
    # Write initial partial bytes
    temp_target.write_bytes(part1)

    bytes_written = len(part1)
    inline_hasher = hashlib.sha256()

    # Pre-seed inline hasher from existing file (as done in manager.py)
    with open(temp_target, "rb") as prev_f:
        for prev_chunk in iter(lambda: prev_f.read(65536), b""):
            inline_hasher.update(prev_chunk)

    # Stream remaining bytes in append mode
    with open(temp_target, "ab") as f:
        chunk_size = 4096
        for i in range(0, len(part2), chunk_size):
            chunk = part2[i : i + chunk_size]
            f.write(chunk)
            inline_hasher.update(chunk)

    final_target = tmp_path / "video_resumed.mp4"
    temp_target.rename(final_target)

    assert inline_hasher.hexdigest() == expected_full_hash
    assert MediaDownloader._compute_sha256(final_target) == expected_full_hash
