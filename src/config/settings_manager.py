import os
import sqlite3
import threading
from pathlib import Path
from dotenv import load_dotenv

# Ensure .env is loaded
load_dotenv()

class SettingsManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(SettingsManager, cls).__new__(cls)
                cls._instance._init_db()
            return cls._instance

    def _init_db(self):
        self.db_path = Path("data/settings.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn_local = threading.local()

    def _get_conn(self):
        if not hasattr(self.conn_local, "conn"):
            self.conn_local.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn_local.conn.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
                """
            )
            self.conn_local.conn.commit()
        return self.conn_local.conn

    def get(self, key: str, default: str = "") -> str:
        """Get a setting. Tries SQLite first, then os.getenv(), then default."""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row and row[0]:
                return row[0]
        except Exception:
            pass
        return os.getenv(key, default)

    def set(self, key: str, value: str):
        """Set a setting in the SQLite database."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value)
        )
        conn.commit()

    def get_all(self):
        """Get all explicitly set settings from DB."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return {row[0]: row[1] for row in cursor.fetchall()}

# Global singleton instance
settings = SettingsManager()
