import sqlite3
import time
from pathlib import Path
from urllib.parse import urlparse
import logging

LOGGER = logging.getLogger(__name__)


class StateCache:
    """
    A SQLite-backed persistent cache for the Watchdog Agent to prevent re-crawling
    and re-downloading identical URLs across multiple intervals.
    """

    def __init__(
        self,
        db_path: str | Path = "output/cache/state_cache.db",
        max_age_days: int = 30,
    ):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_age_seconds = max_age_days * 86400
        self._init_db()
        self._cleanup_old_entries()

    def _get_connection(self):
        return sqlite3.connect(str(self.db_path), timeout=10.0)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS processed_urls (
                    url_hash TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            """)
            # Create an index on timestamp for fast cleanup queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON processed_urls(timestamp)
            """)
            conn.commit()

    def _cleanup_old_entries(self):
        """Delete entries older than max_age_seconds to prevent endless database bloat."""
        cutoff_time = time.time() - self.max_age_seconds
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM processed_urls WHERE timestamp < ?", (cutoff_time,)
                )
                deleted = cursor.rowcount
                conn.commit()
                if deleted > 0:
                    LOGGER.info(f"StateCache cleanup: Removed {deleted} expired URLs.")
        except Exception as e:
            LOGGER.warning(f"StateCache cleanup failed: {e}")

    def is_processed(self, url: str) -> bool:
        """Check if a URL has already been processed and successfully downloaded/scraped."""
        # Using a normalized basic hash (just the URL string for now, could be SHA256)
        url_hash = self._hash_url(url)
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM processed_urls WHERE url_hash = ?", (url_hash,)
                )
                result = cursor.fetchone()
                return result is not None
        except Exception as e:
            LOGGER.warning(f"Error checking state cache for {url}: {e}")
            return False

    def mark_processed(self, url: str):
        """Mark a URL as processed."""
        url_hash = self._hash_url(url)
        now = time.time()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT OR REPLACE INTO processed_urls (url_hash, url, timestamp) VALUES (?, ?, ?)",
                    (url_hash, url, now),
                )
                conn.commit()
        except Exception as e:
            LOGGER.warning(f"Error marking {url} as processed in state cache: {e}")

    def flush(self):
        """Manually clear all cached state."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM processed_urls")
                conn.commit()
                LOGGER.info("StateCache flushed successfully.")
        except Exception as e:
            LOGGER.warning(f"Error flushing StateCache: {e}")

    def _hash_url(self, url: str) -> str:
        """Create a consistent key for the URL. Strips fragments, keeps query params."""
        import hashlib

        parsed = urlparse(url)
        # Strip fragment identifier
        normalized = parsed._replace(fragment="").geturl().strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
