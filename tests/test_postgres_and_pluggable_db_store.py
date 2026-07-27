from __future__ import annotations

import os
from unittest.mock import patch
from src.storage.db_store import get_state_store, SQLiteStateStore, PostgresStateStore


def test_get_state_store_factory_default_sqlite(tmp_path):
    with patch.dict(os.environ, {}, clear=True):
        store = get_state_store()
        assert isinstance(store, SQLiteStateStore)


def test_get_state_store_factory_postgres(tmp_path):
    fake_url = "postgresql://user:pass@localhost:5432/testdb"
    with patch.dict(os.environ, {"DATABASE_URL": fake_url}):
        store = get_state_store()
        assert isinstance(store, PostgresStateStore)
        assert store.database_url == fake_url


def test_sqlite_state_store_operations(tmp_path):
    db_file = tmp_path / "test_store.db"
    store = SQLiteStateStore(db_path=db_file)

    url1 = "https://example.com/page1"
    url2 = "https://example.com/page2"

    store.mark_processed(url1)
    assert store.is_processed(url1) is True
    assert store.is_processed(url2) is False

    store.mark_processed_batch([url2])
    batch_res = store.is_processed_batch([url1, url2, "https://example.com/page3"])
    assert batch_res[url1] is True
    assert batch_res[url2] is True
    assert batch_res["https://example.com/page3"] is False


def test_postgres_state_store_fallback_operations():
    fake_url = "postgresql://invalid_user:invalid_pass@127.0.0.1:54321/nonexistent?sslmode=disable"
    store = PostgresStateStore(database_url=fake_url)

    url1 = "https://example.com/pg1"
    store.mark_processed(url1)
    assert store.is_processed(url1) is True

    batch_res = store.is_processed_batch([url1, "https://example.com/pg2"])
    assert batch_res[url1] is True
    assert batch_res["https://example.com/pg2"] is False
