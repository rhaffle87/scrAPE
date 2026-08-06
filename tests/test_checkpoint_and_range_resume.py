import pytest
from storage.state_cache import StateCache


def test_state_cache_checkpoint_ops(tmp_path):
    db_file = tmp_path / "test_state.sqlite"
    cache = StateCache(db_path=db_file)

    url = "https://example.com/page1"
    assert cache.is_processed(url) is False

    cache.mark_processed(url)
    assert cache.is_processed(url) is True

    stats = cache.get_db_stats()
    assert int(stats["total_urls"]) >= 1


    cache.clear_domain("example.com")
    assert cache.is_processed(url) is False
