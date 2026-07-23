import pytest
from storage.checkpoint_db import CheckpointDB


def test_checkpoint_db_ops(tmp_path):
    db_file = tmp_path / "test_state.sqlite"
    db = CheckpointDB(db_file)

    url = "https://example.com/page1"
    assert db.is_visited(url) is False

    db.record_visited(url, "example.com")
    assert db.is_visited(url) is True

    # Test download checkpointing
    db.save_checkpoint(url, "output/file.mp4", 500, 1000, "in_progress")
    cp = db.get_checkpoint(url)
    assert cp is not None
    assert cp["file_path"] == "output/file.mp4"
    assert cp["downloaded_bytes"] == 500
    assert cp["total_bytes"] == 1000
    assert cp["status"] == "in_progress"

    db.clear()
    assert db.is_visited(url) is False
