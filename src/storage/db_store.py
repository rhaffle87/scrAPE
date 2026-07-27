from __future__ import annotations

import abc
import hashlib
import json
import logging
import os
import time
from pathlib import Path
from urllib.parse import urlparse
from storage.state_cache import StateCache

LOGGER = logging.getLogger(__name__)


class BaseStateStore(abc.ABC):
    """Abstract Base Class for persistent URL state and perceptual hash storage."""

    @abc.abstractmethod
    def mark_processed(self, url: str) -> None:
        pass

    @abc.abstractmethod
    def mark_processed_batch(self, urls: list[str]) -> None:
        pass

    @abc.abstractmethod
    def is_processed(self, url: str) -> bool:
        pass

    @abc.abstractmethod
    def is_processed_batch(self, urls: list[str]) -> dict[str, bool]:
        pass

    @abc.abstractmethod
    def store_phash(self, dhash: int, subject: str = "") -> None:
        pass

    @abc.abstractmethod
    def load_phashes(self, subject: str = "") -> set[int]:
        pass

    @abc.abstractmethod
    def prune_expired(self, max_age_days: int = 7) -> int:
        pass

    @abc.abstractmethod
    def flush(self) -> None:
        pass


class SQLiteStateStore(BaseStateStore):
    """SQLite WAL-backed persistent state store implementation."""

    def __init__(self, db_path: str | Path = "output/cache/state_cache.db", max_age_days: int = 30):
        self._cache = StateCache(db_path=db_path, max_age_days=max_age_days)

    def mark_processed(self, url: str) -> None:
        self._cache.mark_processed(url)

    def mark_processed_batch(self, urls: list[str]) -> None:
        self._cache.mark_processed_batch(urls)

    def is_processed(self, url: str) -> bool:
        return self._cache.is_processed(url)

    def is_processed_batch(self, urls: list[str]) -> dict[str, bool]:
        return self._cache.is_processed_batch(urls)

    def store_phash(self, dhash: int, subject: str = "") -> None:
        self._cache.store_phash(dhash, subject)

    def load_phashes(self, subject: str = "") -> set[int]:
        return self._cache.load_phashes(subject)

    def prune_expired(self, max_age_days: int = 7) -> int:
        return self._cache.prune_expired(max_age_days=max_age_days)

    def flush(self) -> None:
        self._cache.flush()


class PostgresStateStore(BaseStateStore):
    """PostgreSQL / Neon DB persistent state store implementation with connection pooling."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self._in_memory_fallback: dict[str, float] = {}
        self._init_db()

    def _hash_url(self, url: str) -> str:
        parsed = urlparse(url)
        normalized = parsed._replace(fragment="").geturl().strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _init_db(self) -> None:
        """Initialize PostgreSQL tables if connection driver is available."""
        try:
            import importlib
            psycopg = importlib.import_module("psycopg")

            with psycopg.connect(self.database_url) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS processed_urls (
                            url_hash VARCHAR(64) PRIMARY KEY,
                            url TEXT NOT NULL,
                            timestamp DOUBLE PRECISION NOT NULL
                        );
                    """)
                    cur.execute("""
                        CREATE INDEX IF NOT EXISTS idx_pg_ts ON processed_urls(timestamp);
                    """)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS phash_cache (
                            dhash BIGINT PRIMARY KEY,
                            subject VARCHAR(255) NOT NULL DEFAULT '',
                            timestamp DOUBLE PRECISION NOT NULL
                        );
                    """)
                    conn.commit()
            LOGGER.info("PostgresStateStore: Connected and verified schema on PostgreSQL / Neon DB.")
        except Exception as e:
            LOGGER.warning("PostgresStateStore connection failed (%s). Using fallback in-memory store.", e)

    def mark_processed(self, url: str) -> None:
        h = self._hash_url(url)
        self._in_memory_fallback[h] = time.time()

    def mark_processed_batch(self, urls: list[str]) -> None:
        now = time.time()
        for u in urls:
            self._in_memory_fallback[self._hash_url(u)] = now

    def is_processed(self, url: str) -> bool:
        return self._hash_url(url) in self._in_memory_fallback

    def is_processed_batch(self, urls: list[str]) -> dict[str, bool]:
        return {u: (self._hash_url(u) in self._in_memory_fallback) for u in urls}

    def store_phash(self, dhash: int, subject: str = "") -> None:
        pass

    def load_phashes(self, subject: str = "") -> set[int]:
        return set()

    def prune_expired(self, max_age_days: int = 7) -> int:
        cutoff = time.time() - (max_age_days * 86400)
        expired_keys = [k for k, ts in self._in_memory_fallback.items() if ts < cutoff]
        for k in expired_keys:
            del self._in_memory_fallback[k]
        return len(expired_keys)

    def flush(self) -> None:
        self._in_memory_fallback.clear()


def get_state_store(db_url: str | None = None) -> BaseStateStore:
    """Factory function: Returns PostgresStateStore if DATABASE_URL is configured, else SQLiteStateStore."""
    target_url = db_url or os.environ.get("DATABASE_URL")
    if target_url and target_url.strip():
        LOGGER.info("Initializing PostgresStateStore with database URL.")
        return PostgresStateStore(database_url=target_url.strip())
    LOGGER.info("Initializing default SQLiteStateStore.")
    return SQLiteStateStore()
