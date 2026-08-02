import sqlite3
import logging
from pathlib import Path
from dataclasses import asdict
from typing import Any

from core.models import ScrapeResult

LOGGER = logging.getLogger(__name__)

class DatabaseExporter:
    """Exports a ScrapeResult to a SQLite database."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _init_db(self, conn: sqlite3.Connection):
        """Initialize the database schema."""
        cursor = conn.cursor()
        
        # Images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                source_page TEXT,
                original_url TEXT,
                alt_text TEXT,
                score INTEGER,
                page_title TEXT,
                mime_type TEXT,
                width INTEGER,
                height INTEGER,
                file_size_bytes INTEGER,
                in_layout_container BOOLEAN,
                parent_anchor_text TEXT,
                parent_anchor_href TEXT,
                status TEXT,
                file_path TEXT,
                failure_reason TEXT,
                hash TEXT,
                source_domain TEXT
            )
        """)

        # Videos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS videos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL,
                source_page TEXT,
                type TEXT,
                score INTEGER,
                page_title TEXT,
                mime_type TEXT,
                file_size_bytes INTEGER,
                duration_seconds INTEGER,
                in_layout_container BOOLEAN,
                parent_anchor_text TEXT,
                parent_anchor_href TEXT,
                status TEXT,
                file_path TEXT,
                failure_reason TEXT,
                hash TEXT,
                source_domain TEXT
            )
        """)
        
        conn.commit()

    def export(self, result: ScrapeResult):
        """Export the scrape result to the SQLite database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                self._init_db(conn)
                cursor = conn.cursor()

                # Export Images
                image_records = []
                for img in result.images:
                    image_records.append((
                        img.url, img.source_page, img.original_url, img.alt_text,
                        img.score, img.page_title, img.mime_type, img.width, img.height,
                        img.file_size_bytes, img.in_layout_container, img.parent_anchor_text,
                        img.parent_anchor_href, img.status, img.file_path, img.failure_reason,
                        img.hash, img.source_domain
                    ))
                
                if image_records:
                    cursor.executemany("""
                        INSERT INTO images (
                            url, source_page, original_url, alt_text, score, page_title,
                            mime_type, width, height, file_size_bytes, in_layout_container,
                            parent_anchor_text, parent_anchor_href, status, file_path,
                            failure_reason, hash, source_domain
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, image_records)

                # Export Videos
                video_records = []
                for vid in result.videos:
                    video_records.append((
                        vid.url, vid.source_page, vid.type, vid.score, vid.page_title,
                        vid.mime_type, vid.file_size_bytes, vid.duration_seconds,
                        vid.in_layout_container, vid.parent_anchor_text, vid.parent_anchor_href,
                        vid.status, vid.file_path, vid.failure_reason, vid.hash, vid.source_domain
                    ))
                
                if video_records:
                    cursor.executemany("""
                        INSERT INTO videos (
                            url, source_page, type, score, page_title, mime_type,
                            file_size_bytes, duration_seconds, in_layout_container,
                            parent_anchor_text, parent_anchor_href, status, file_path,
                            failure_reason, hash, source_domain
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, video_records)
                
                conn.commit()
                LOGGER.info("Successfully exported data to SQLite database at %s", self.db_path)
        except Exception as e:
            LOGGER.error("Failed to export results to SQLite: %s", e)
