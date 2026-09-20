import tempfile
from pathlib import Path
from storage.state_cache import StateCache


def _make_temp_cache(max_age_days: int = 30) -> StateCache:
    tmp = tempfile.mkdtemp()
    return StateCache(db_path=Path(tmp) / "test_state_cache.db", max_age_days=max_age_days)


def test_vacuum_db_returns_size():
    """Verify vacuum_db() runs without error and returns a non-negative file size."""
    cache = _make_temp_cache()
    cache.mark_processed("https://example.com/page/1")
    cache.flush()
    size = cache.vacuum_db()
    assert isinstance(size, int)
    assert size >= 0


def test_clear_domain_removes_matching_urls():
    """Verify clear_domain() removes only URLs belonging to the target domain."""
    cache = _make_temp_cache()
    cache.mark_processed("https://gallery.example.com/img/1.jpg")
    cache.mark_processed("https://gallery.example.com/img/2.jpg")
    cache.mark_processed("https://other-site.org/item/1")

    deleted = cache.clear_domain("example.com")
    assert deleted == 2
    assert not cache.is_processed("https://gallery.example.com/img/1.jpg")
    assert cache.is_processed("https://other-site.org/item/1")


def test_get_db_stats_returns_metrics():
    """Verify get_db_stats() returns correct total_urls and journal_mode."""
    cache = _make_temp_cache()
    cache.mark_processed("https://example.com/a")
    cache.mark_processed("https://example.com/b")

    stats = cache.get_db_stats()
    assert stats["total_urls"] == 2
    assert "db_size_bytes" in stats
    assert stats["journal_mode"] == "wal"
