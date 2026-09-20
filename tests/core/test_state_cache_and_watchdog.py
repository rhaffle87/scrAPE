from __future__ import annotations

import time
import pytest
from storage.state_cache import StateCache
from cli.monitor_agent import (
    shutdown_event,
    discover_rotation_targets,
    broadcast_watchdog_event,
)


def test_state_cache_mark_and_is_processed_batch(tmp_path):
    db_file = tmp_path / "state_cache.db"
    cache = StateCache(db_path=db_file)

    urls = [f"https://example.com/item_{i}" for i in range(1200)]

    # Batch mark processed
    cache.mark_processed_batch(urls, chunk_size=500)

    # Batch check processed
    mixed_urls = urls[:10] + [f"https://example.com/new_item_{i}" for i in range(10)]
    batch_res = cache.is_processed_batch(mixed_urls, chunk_size=500)

    for i in range(10):
        assert batch_res[f"https://example.com/item_{i}"] is True
        assert batch_res[f"https://example.com/new_item_{i}"] is False


def test_state_cache_single_and_batch_consistency(tmp_path):
    db_file = tmp_path / "state_cache_consistency.db"
    cache = StateCache(db_path=db_file)

    test_urls = ["https://site.org/p1", "https://site.org/p2"]
    cache.mark_processed(test_urls[0])
    cache.mark_processed_batch([test_urls[1]])

    assert cache.is_processed(test_urls[0]) is True
    assert cache.is_processed(test_urls[1]) is True
    assert cache.is_processed("https://site.org/unseen") is False

    batch_check = cache.is_processed_batch(test_urls + ["https://site.org/unseen"])
    assert batch_check[test_urls[0]] is True
    assert batch_check[test_urls[1]] is True
    assert batch_check["https://site.org/unseen"] is False


def test_watchdog_shutdown_event_flag():
    shutdown_event.clear()
    assert shutdown_event.is_set() is False

    shutdown_event.set()
    assert shutdown_event.is_set() is True
    shutdown_event.clear()


def test_discover_rotation_targets(tmp_path):
    seeds_dir = tmp_path / "seeds"
    seeds_dir.mkdir()

    (seeds_dir / "apple_tech.txt").write_text("https://apple.com", encoding="utf-8")
    (seeds_dir / "tesla_motors.txt").write_text("https://tesla.com", encoding="utf-8")

    targets = discover_rotation_targets(str(seeds_dir))
    assert len(targets) == 2
    assert targets[0] == ("apple tech", str(seeds_dir / "apple_tech.txt"))
    assert targets[1] == ("tesla motors", str(seeds_dir / "tesla_motors.txt"))


def test_broadcast_watchdog_event_resilience():
    # Calling broadcast_watchdog_event should fail silently if frontend is not running
    broadcast_watchdog_event("watchdog", {"type": "test_ping", "cycle": 1})
