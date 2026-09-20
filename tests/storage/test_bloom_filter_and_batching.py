"""Tests for zero-dependency Bitmask Bloom Filter and StateCache transaction batching."""

from __future__ import annotations

import concurrent.futures
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from storage.bloom_filter import BloomFilter
from storage.state_cache import StateCache


def test_bloom_filter_basic_add_and_contains():
    """Verify standard addition, membership checking, and zero false negatives."""
    bf = BloomFilter(capacity=10_000, error_rate=0.01)

    test_urls = [f"https://example.com/page/{i}" for i in range(500)]
    for url in test_urls:
        bf.add(url)

    assert bf.count() == 500

    # 100% of added items must be present (Zero False Negatives)
    for url in test_urls:
        assert url in bf
        assert bf.contains(url) is True

    # Items never added should predominantly return False
    unseen_urls = [f"https://never-added.org/item/{i}" for i in range(500)]
    false_positives = sum(1 for u in unseen_urls if u in bf)
    assert false_positives < 15  # well below 3% threshold


def test_bloom_filter_false_positive_bounds():
    """Verify empirical false positive rate matches configured bounds."""
    capacity = 5_000
    bf = BloomFilter(capacity=capacity, error_rate=0.01)

    for i in range(capacity):
        bf.add(f"item_{i}")

    # Check 1,000 distinct items not in the filter
    trials = 1_000
    false_positives = sum(1 for i in range(trials) if f"unknown_item_{i}" in bf)
    fp_rate = false_positives / trials

    # Expected ~0.01, allowing standard statistical margin
    assert fp_rate <= 0.03


def test_bloom_filter_thread_safety():
    """Verify concurrent reads and writes across multiple worker threads."""
    bf = BloomFilter(capacity=50_000, error_rate=0.01)
    num_threads = 8
    items_per_thread = 200

    def worker(worker_id: int):
        for i in range(items_per_thread):
            item = f"worker_{worker_id}_item_{i}"
            bf.add(item)
            assert bf.contains(item) is True

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker, tid) for tid in range(num_threads)]
        for f in concurrent.futures.as_completed(futures):
            f.result()

    assert bf.count() == num_threads * items_per_thread


def test_bloom_filter_serialization():
    """Verify to_bytes and from_bytes roundtrip fidelity."""
    bf1 = BloomFilter(capacity=20_000, error_rate=0.01)
    urls = [f"https://domain.com/photo_{i}.jpg" for i in range(100)]
    for u in urls:
        bf1.add(u)

    data = bf1.to_bytes()
    assert isinstance(data, bytes)
    assert len(data) > 0

    bf2 = BloomFilter(capacity=20_000, error_rate=0.01)
    bf2.from_bytes(data, count=bf1.count())

    for u in urls:
        assert u in bf2
    assert "https://domain.com/nonexistent.jpg" not in bf2


def test_state_cache_bloom_filter_l1_fast_rejection(tmp_path):
    """Verify Bloom filter serves as an L1 gatekeeper avoiding SQLite queries on missing URLs."""
    db_file = tmp_path / "cache" / "test_state.db"
    cache = StateCache(db_path=db_file)

    test_url = "https://example.com/unique_article"
    assert cache.is_processed(test_url) is False

    cache.mark_processed(test_url, immediate=True)
    assert cache.is_processed(test_url) is True

    # Check that a totally new URL is rejected at L1 without invoking SQLite cursor
    with patch.object(cache, "_get_connection") as mock_conn:
        assert cache.is_processed("https://totally-unseen-domain.xyz/page1") is False
        mock_conn.assert_not_called()

    cache.close()


def test_state_cache_write_buffer_batching(tmp_path):
    """Verify write-staging buffer holds updates and flushes when batch_size is reached."""
    db_file = tmp_path / "cache" / "batch_test.db"
    batch_size = 5
    cache = StateCache(db_path=db_file, batch_size=batch_size, batch_timeout=60.0)

    # Add 4 items (under batch size of 5)
    for i in range(4):
        cache.mark_processed(f"https://site.org/item_{i}")

    # Buffer should hold 4 pending items
    assert len(cache._write_buffer) == 4

    # All 4 items should still test positive in memory
    for i in range(4):
        assert cache.is_processed(f"https://site.org/item_{i}") is True

    # 5th item reaches batch threshold and triggers flush
    cache.mark_processed("https://site.org/item_4")
    assert len(cache._write_buffer) == 0

    # Ensure items are physically committed to SQLite
    with cache._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM processed_urls")
        count = cursor.fetchone()[0]
        assert count == 5

    cache.close()


def test_state_cache_batch_methods_with_bloom(tmp_path):
    """Verify mark_processed_batch and is_processed_batch leverage Bloom filter."""
    db_file = tmp_path / "cache" / "batch_ops.db"
    cache = StateCache(db_path=db_file)

    urls = [f"https://gallery.com/media_{i}.png" for i in range(50)]
    cache.mark_processed_batch(urls)

    # Check status
    results = cache.is_processed_batch(urls + ["https://gallery.com/unprocessed.png"])
    for u in urls:
        assert results[u] is True
    assert results["https://gallery.com/unprocessed.png"] is False

    cache.close()
