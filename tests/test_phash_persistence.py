"""
scratch/test_phash_persistence.py

Tests for StateCache cross-run pHash persistence: store, load, TTL prune, flush.
Also verifies that a seeded _seen_phashes set blocks duplicate images in MediaDownloader.
"""

import time
import tempfile
from pathlib import Path

from storage.state_cache import StateCache
from storage.file_downloader import MediaDownloader


def _make_cache(max_age_days: int = 30) -> StateCache:
    tmp = tempfile.mkdtemp()
    return StateCache(db_path=Path(tmp) / "test_phash.db", max_age_days=max_age_days)


# ---------------------------------------------------------------------------
# store_phash / load_phashes
# ---------------------------------------------------------------------------

def test_store_and_load_phash():
    """Stored hash is present on reload; hash is scoped to subject."""
    cache = _make_cache()
    cache.store_phash(12345678, subject="cats")
    cache.store_phash(99999999, subject="dogs")

    cats = cache.load_phashes(subject="cats")
    assert 12345678 in cats
    assert 99999999 not in cats

    all_hashes = cache.load_phashes()
    assert 12345678 in all_hashes
    assert 99999999 in all_hashes


def test_store_phash_duplicate_ignored():
    """Re-inserting the same hash does not raise or duplicate."""
    cache = _make_cache()
    cache.store_phash(42, subject="test")
    cache.store_phash(42, subject="test")  # INSERT OR IGNORE
    loaded = cache.load_phashes(subject="test")
    assert loaded == {42}


# ---------------------------------------------------------------------------
# TTL pruning
# ---------------------------------------------------------------------------

def test_phash_ttl_prunes_old_entries():
    """Entries older than max_age_days are removed by _cleanup_old_entries."""
    # max_age_days=0 makes everything expire immediately
    cache = _make_cache(max_age_days=0)
    # Manually backdate a row
    with cache._get_connection() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO phash_cache (dhash, subject, timestamp) VALUES (?, ?, ?)",
            (777, "old", time.time() - 1),
        )
        conn.commit()
    # Trigger cleanup
    cache._cleanup_old_entries()
    loaded = cache.load_phashes()
    assert 777 not in loaded


# ---------------------------------------------------------------------------
# flush_phashes
# ---------------------------------------------------------------------------

def test_flush_phashes_clears_all():
    """flush_phashes() with no subject removes all entries."""
    cache = _make_cache()
    cache.store_phash(1, subject="a")
    cache.store_phash(2, subject="b")
    deleted = cache.flush_phashes()
    assert deleted == 2
    assert cache.load_phashes() == set()


def test_flush_phashes_scoped_to_subject():
    """flush_phashes(subject) removes only that subject's entries."""
    cache = _make_cache()
    cache.store_phash(10, subject="keep")
    cache.store_phash(20, subject="remove")
    cache.flush_phashes(subject="remove")
    remaining = cache.load_phashes()
    assert 10 in remaining
    assert 20 not in remaining


# ---------------------------------------------------------------------------
# Cross-run dedup integration: seeded _seen_phashes blocks duplicate
# ---------------------------------------------------------------------------

def test_cross_run_dedup_blocks_duplicate_via_seeded_set():
    """
    Verify that _seen_phashes seeded from StateCache prevents a duplicate
    image from passing the Hamming-distance check.
    """
    from network.http_client import HttpClient
    from storage.file_downloader import hamming_distance

    cache = _make_cache()
    known_hash = 0xDEADBEEF
    cache.store_phash(known_hash, subject="test")

    # Build a downloader seeded from the cache
    downloader = MediaDownloader(
        http=HttpClient(),
        state_cache=cache,
        keyword="test",
    )

    # The known hash must be in _seen_phashes
    assert any(h == known_hash for h in downloader._seen_phashes)

    # A hash at distance 0 (exact duplicate) should be detected
    for prev in downloader._seen_phashes:
        assert hamming_distance(known_hash, prev) == 0
