import sqlite3
import threading
from pathlib import Path
from typing import Any
from utils.logger import get_logger

LOGGER = get_logger(__name__)


class CheckpointDB:
    """Thread-safe SQLite database for persisting crawl queue, visited URLs, and download checkpoints."""

    def __init__(self, db_path: Path | str = "output/.crawl_state.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS visited_urls (
                    url TEXT PRIMARY KEY,
                    domain TEXT,
                    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS frontier_queue (
                    url TEXT PRIMARY KEY,
                    domain TEXT,
                    depth INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS download_checkpoints (
                    url TEXT PRIMARY KEY,
                    file_path TEXT,
                    downloaded_bytes INTEGER,
                    total_bytes INTEGER,
                    status TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    def record_visited(self, url: str, domain: str) -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO visited_urls (url, domain) VALUES (?, ?)",
                (url, domain),
            )
            conn.commit()

    def is_visited(self, url: str) -> bool:
        with self._lock, self._get_connection() as conn:
            cur = conn.execute("SELECT 1 FROM visited_urls WHERE url = ?", (url,))
            return cur.fetchone() is not None

    def save_checkpoint(self, url: str, file_path: str, downloaded_bytes: int, total_bytes: int, status: str = "in_progress") -> None:
        with self._lock, self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO download_checkpoints (url, file_path, downloaded_bytes, total_bytes, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (url, file_path, downloaded_bytes, total_bytes, status),
            )
            conn.commit()

    def get_checkpoint(self, url: str) -> dict[str, Any] | None:
        with self._lock, self._get_connection() as conn:
            cur = conn.execute("SELECT * FROM download_checkpoints WHERE url = ?", (url,))
            row = cur.fetchone()
            if row:
                return dict(row)
            return None

    def clear(self) -> None:
        with self._lock, self._get_connection() as conn:
            conn.executescript("""
                DELETE FROM visited_urls;
                DELETE FROM frontier_queue;
                DELETE FROM download_checkpoints;
            """)
            conn.commit()
