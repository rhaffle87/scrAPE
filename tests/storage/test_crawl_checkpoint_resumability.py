"""
test_crawl_checkpoint_resumability.py — Tests for transactional crawl checkpoints and resumability (v0.27.0).
"""

from unittest.mock import MagicMock

from core.coordinator import CrawlCoordinator
from core.models import ScrapeResult
from storage.state_cache import StateCache


class DummyOptions:
    def __init__(self, keyword="supercars", max_results=10, resume_run_id=None):
        self.keyword = keyword
        self.max_results = max_results
        self.resume_run_id = resume_run_id


def test_state_cache_checkpoint_crud(tmp_path):
    """Verify save, load, list, and clear operations for crawl checkpoints."""
    db_file = tmp_path / "state_cache.db"
    cache = StateCache(db_path=db_file)

    run_id = "run_ckpt_123"
    keyword = "nature"
    queue_items = [
        {"url": "https://example.com/page1", "depth": 0, "retry_count": 0, "score": 85.5},
        {"url": "https://example.com/page2", "depth": 1, "retry_count": 1, "score": 62.0},
    ]

    # 1. Save checkpoint
    saved = cache.save_crawl_checkpoint(
        run_id=run_id,
        keyword=keyword,
        total_pages_scanned=5,
        current_concurrency=4,
        queue_items=queue_items,
        state_metadata={"progress": 25, "custom_field": "val"},
    )
    assert saved is True

    # 2. List checkpoints
    ckpts = cache.list_crawl_checkpoints()
    assert len(ckpts) == 1
    assert ckpts[0]["run_id"] == run_id
    assert ckpts[0]["queue_size"] == 2

    # 3. Load checkpoint
    loaded = cache.load_crawl_checkpoint(run_id)
    assert loaded is not None
    assert loaded["run_id"] == run_id
    assert loaded["keyword"] == keyword
    assert loaded["total_pages_scanned"] == 5
    assert loaded["current_concurrency"] == 4
    assert loaded["state_metadata"]["progress"] == 25
    assert len(loaded["queue_items"]) == 2
    assert loaded["queue_items"][0]["url"] == "https://example.com/page1"
    assert loaded["queue_items"][0]["score"] == 85.5

    # 4. Atomic overwrite
    updated_queue = [
        {"url": "https://example.com/page3", "depth": 2, "retry_count": 0, "score": 90.0}
    ]
    cache.save_crawl_checkpoint(
        run_id=run_id,
        keyword=keyword,
        total_pages_scanned=10,
        current_concurrency=2,
        queue_items=updated_queue,
        state_metadata={"progress": 50},
    )
    loaded2 = cache.load_crawl_checkpoint(run_id)
    assert loaded2["total_pages_scanned"] == 10
    assert len(loaded2["queue_items"]) == 1
    assert loaded2["queue_items"][0]["url"] == "https://example.com/page3"

    # 5. Clear checkpoint
    cleared = cache.clear_crawl_checkpoint(run_id)
    assert cleared is True
    assert cache.load_crawl_checkpoint(run_id) is None
    assert len(cache.list_crawl_checkpoints()) == 0


def test_coordinator_resume_from_checkpoint_helper(tmp_path):
    """Verify CrawlCoordinator provides resume_from_checkpoint hook."""
    db_file = tmp_path / "state_cache_resume.db"
    cache = StateCache(db_path=db_file)

    run_id = "run_test_resume"
    cache.save_crawl_checkpoint(
        run_id=run_id,
        keyword="cars",
        total_pages_scanned=8,
        current_concurrency=4,
        queue_items=[{"url": "https://cars.com/1", "depth": 0, "retry_count": 0, "score": 75.0}],
        state_metadata={"progress": 40},
    )

    options = DummyOptions(keyword="cars", resume_run_id=run_id)
    res = ScrapeResult(keyword="cars", run_id=run_id)
    coord = CrawlCoordinator(
        search_provider=MagicMock(),
        video_scraper=MagicMock(),
        options=options,
        result=res,
        state_cache=cache,
        workers=4,
    )

    ckpt = coord.resume_from_checkpoint(run_id)
    assert ckpt is not None
    assert ckpt["total_pages_scanned"] == 8
    assert len(ckpt["queue_items"]) == 1
