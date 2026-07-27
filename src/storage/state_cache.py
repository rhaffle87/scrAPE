import functools
import logging
import random
import sqlite3
import time
from pathlib import Path
from urllib.parse import urlparse

LOGGER = logging.getLogger(__name__)


def retry_on_db_lock(max_retries: int = 5, initial_delay: float = 0.05):
    """Decorator to retry SQLite operations on database lock contention."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as exc:
                    if "locked" in str(exc).lower() or "busy" in str(exc).lower():
                        if attempt == max_retries:
                            raise
                        time.sleep(delay + random.uniform(0.01, 0.05))
                        delay *= 2.0
                    else:
                        raise
        return wrapper
    return decorator


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

    def wal_checkpoint(self) -> bool:
        """Executes explicit PRAGMA wal_checkpoint(TRUNCATE) to optimize database WAL size."""
        try:
            with self._get_connection() as conn:
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            return True
        except Exception as exc:
            LOGGER.warning("SQLite WAL checkpoint failed: %s", exc)
            return False

    def _get_connection(self):
        return sqlite3.connect(str(self.db_path), timeout=30.0)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Performance optimization: enable Write-Ahead Logging (WAL) and normal sync
            # to significantly improve concurrency throughput during parallel crawling
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            
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
            # Persistent perceptual-hash store for cross-run image deduplication
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS phash_cache (
                    dhash INTEGER PRIMARY KEY,
                    subject TEXT NOT NULL DEFAULT '',
                    timestamp REAL NOT NULL
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_phash_ts ON phash_cache(timestamp)
            """)
            conn.commit()

    def _cleanup_old_entries(self):
        """Delete entries older than max_age_seconds to prevent endless database bloat."""
        self.prune_expired(max_age_days=int(self.max_age_seconds / 86400))

    def prune_expired(self, max_age_days: int = 30) -> int:
        """Delete entries older than max_age_days to prevent database bloat. Returns number of deleted rows."""
        cutoff_time = time.time() - (max_age_days * 86400)
        total_deleted = 0
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM processed_urls WHERE timestamp < ?", (cutoff_time,)
                )
                deleted_urls = cursor.rowcount
                cursor.execute(
                    "DELETE FROM phash_cache WHERE timestamp < ?", (cutoff_time,)
                )
                deleted_phashes = cursor.rowcount
                conn.commit()
                total_deleted = deleted_urls + deleted_phashes
                if total_deleted > 0:
                    LOGGER.info(
                        "StateCache cleanup: removed %d expired URLs and %d expired pHashes.",
                        deleted_urls,
                        deleted_phashes,
                    )
        except Exception as e:
            LOGGER.warning(f"StateCache cleanup failed: {e}")
        return total_deleted

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

    def mark_processed_batch(self, urls: list[str], chunk_size: int = 500) -> None:
        """Mark a batch of URLs as processed using chunked executemany transactions."""
        if not urls:
            return

        now = time.time()
        items = [(self._hash_url(u), u, now) for u in urls]

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for i in range(0, len(items), chunk_size):
                    chunk = items[i : i + chunk_size]
                    cursor.executemany(
                        "INSERT OR REPLACE INTO processed_urls (url_hash, url, timestamp) VALUES (?, ?, ?)",
                        chunk,
                    )
                conn.commit()
        except Exception as e:
            LOGGER.warning(f"Error marking batch of {len(urls)} URLs as processed in state cache: {e}")

    def is_processed_batch(self, urls: list[str], chunk_size: int = 500) -> dict[str, bool]:
        """Check a batch of URLs against the state cache, returning {url: is_processed}."""
        if not urls:
            return {}

        results: dict[str, bool] = {u: False for u in urls}
        hash_to_url = {self._hash_url(u): u for u in urls}
        hashes = list(hash_to_url.keys())

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                for i in range(0, len(hashes), chunk_size):
                    chunk = hashes[i : i + chunk_size]
                    placeholders = ",".join("?" for _ in chunk)
                    cursor.execute(
                        f"SELECT url_hash FROM processed_urls WHERE url_hash IN ({placeholders})",
                        chunk,
                    )
                    found = cursor.fetchall()
                    for (h,) in found:
                        if h in hash_to_url:
                            results[hash_to_url[h]] = True
        except Exception as e:
            LOGGER.warning(f"Error performing batch state cache check: {e}")

        return results

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

    # ------------------------------------------------------------------
    # Perceptual Hash Persistence (cross-run image deduplication)
    # ------------------------------------------------------------------

    def store_phash(self, dhash: int, subject: str = "") -> None:
        """Persist a perceptual hash so it survives across runs.

        Uses INSERT OR IGNORE so duplicate inserts are silently discarded.
        """
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO phash_cache (dhash, subject, timestamp) VALUES (?, ?, ?)",
                    (dhash, subject.strip().lower(), time.time()),
                )
                conn.commit()
        except Exception as e:
            LOGGER.warning("StateCache store_phash(%d) failed: %s", dhash, e)

    def load_phashes(self, subject: str = "") -> set[int]:
        """Bulk-load all stored perceptual hashes into an in-memory set.

        If *subject* is given, only hashes for that subject are loaded.
        """
        hashes: set[int] = set()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if subject.strip():
                    cursor.execute(
                        "SELECT dhash FROM phash_cache WHERE subject = ?",
                        (subject.strip().lower(),),
                    )
                else:
                    cursor.execute("SELECT dhash FROM phash_cache")
                for (dhash,) in cursor.fetchall():
                    hashes.add(int(dhash))
        except Exception as e:
            LOGGER.warning("StateCache load_phashes failed: %s", e)
        return hashes

    def flush_phashes(self, subject: str = "") -> int:
        """Delete all perceptual hash entries (or only those for *subject*).

        Returns the number of rows deleted.
        """
        deleted = 0
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if subject.strip():
                    cursor.execute(
                        "DELETE FROM phash_cache WHERE subject = ?",
                        (subject.strip().lower(),),
                    )
                else:
                    cursor.execute("DELETE FROM phash_cache")
                deleted = cursor.rowcount
                conn.commit()
            LOGGER.info("StateCache flush_phashes: removed %d entries.", deleted)
        except Exception as e:
            LOGGER.warning("StateCache flush_phashes failed: %s", e)
        return deleted

    def vacuum_db(self) -> int:
        """Run SQLite VACUUM to reclaim disk space after TTL cleanup deletions.

        Returns the file size in bytes after vacuuming.
        """
        try:
            with self._get_connection() as conn:
                conn.execute("VACUUM")
            size_after = self.db_path.stat().st_size if self.db_path.exists() else 0
            LOGGER.info("StateCache VACUUM complete. DB size: %d bytes.", size_after)
            return size_after
        except Exception as e:
            LOGGER.warning("StateCache VACUUM failed: %s", e)
            return 0

    def clear_domain(self, domain: str) -> int:
        """Delete all cached URL entries belonging to *domain*.

        Performs a LIKE-based scan on the stored URL column to find and remove
        all entries whose hostname matches the supplied domain string.

        Returns the number of rows deleted.
        """
        pattern = f"%{domain.strip().lower()}%"
        deleted = 0
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM processed_urls WHERE LOWER(url) LIKE ?", (pattern,)
                )
                deleted = cursor.rowcount
                conn.commit()
            LOGGER.info(
                "StateCache: cleared %d cached entries for domain '%s'.",
                deleted,
                domain,
            )
        except Exception as e:
            LOGGER.warning("StateCache clear_domain('%s') failed: %s", domain, e)
        return deleted

    def get_db_stats(self) -> dict[str, int | str]:
        """Return database telemetry metrics: record count, file size, WAL mode."""
        stats: dict[str, int | str] = {
            "total_urls": 0,
            "db_size_bytes": 0,
            "journal_mode": "unknown",
        }
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM processed_urls")
                row = cursor.fetchone()
                stats["total_urls"] = int(row[0]) if row else 0
                cursor.execute("PRAGMA journal_mode")
                jm_row = cursor.fetchone()
                stats["journal_mode"] = str(jm_row[0]) if jm_row else "unknown"
            stats["db_size_bytes"] = self.db_path.stat().st_size if self.db_path.exists() else 0
        except Exception as e:
            LOGGER.warning("StateCache get_db_stats failed: %s", e)
        return stats

    def _hash_url(self, url: str) -> str:
        """Create a consistent key for the URL. Strips fragments, keeps query params."""
        import hashlib

        parsed = urlparse(url)
        # Strip fragment identifier
        normalized = parsed._replace(fragment="").geturl().strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
