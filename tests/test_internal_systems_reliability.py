from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from src.storage.state_cache import StateCache, retry_on_db_lock
from src.network.stealth_pipeline import StealthPipeline, _StrategyCircuitBreaker
from src.storage.file_downloader import MediaDownloader
from src.monitoring.hardware_governor import HardwareLoadGovernor


def test_stealth_circuit_breaker_auto_heal():
    cb = _StrategyCircuitBreaker(failure_threshold=1, cooldown_seconds=0.01)
    cb.record_failure("crawlee", "example.com")
    assert cb.is_cooling_down("crawlee", "example.com") is True

    time.sleep(0.02)
    healed = cb.auto_heal_quarantined_tiers()
    assert healed == 1
    assert cb.is_cooling_down("crawlee", "example.com") is False


def test_sqlite_retry_on_db_lock_decorator():
    call_count = 0

    @retry_on_db_lock(max_retries=3, initial_delay=0.01)
    def flaky_db_op():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise sqlite3.OperationalError("database is locked")
        return "success"

    res = flaky_db_op()
    assert res == "success"
    assert call_count == 2


def test_state_cache_wal_checkpoint(tmp_path):
    db_path = tmp_path / "test_wal.db"
    cache = StateCache(db_path=db_path)
    res = cache.wal_checkpoint()
    assert res is True


def test_media_downloader_verify_magic_bytes(tmp_path):
    downloader = MediaDownloader()

    # Valid JPEG file
    jpeg_file = tmp_path / "valid.jpg"
    jpeg_file.write_bytes(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01")
    assert downloader.verify_magic_bytes(jpeg_file) is True

    # Corrupt file
    corrupt_file = tmp_path / "corrupt.jpg"
    corrupt_file.write_bytes(b"INVALID_HEADER_BYTES_12345")
    assert downloader.verify_magic_bytes(corrupt_file) is False


def test_hardware_governor_trigger_memory_cleanup():
    gov = HardwareLoadGovernor()
    collected = gov.trigger_memory_cleanup()
    assert isinstance(collected, int)
    assert collected >= 0
