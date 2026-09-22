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
        except Exception as _exc:
            import logging as _log
            _log.getLogger(__name__).debug("Settings DB read failed for key '%s': %s", key, _exc)
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

    # S3 / Cloud CAS Configuration Accessors (Canonical Single Source of Truth)
    def get_s3_endpoint_url(self) -> str | None:
        val = self.get("S3_ENDPOINT_URL", "").strip()
        return val or None

    def get_s3_bucket(self) -> str:
        return self.get("S3_BUCKET", "").strip()

    def get_s3_region(self) -> str:
        return self.get("S3_REGION", "us-east-1").strip() or "us-east-1"

    def get_aws_access_key_id(self) -> str | None:
        val = self.get("AWS_ACCESS_KEY_ID", "").strip()
        return val or None

    def get_aws_secret_access_key(self) -> str | None:
        val = self.get("AWS_SECRET_ACCESS_KEY", "").strip()
        return val or None

    def is_local_s3_endpoint_allowed(self) -> bool:
        return self.get("SCRAPE_ALLOW_LOCAL_S3_ENDPOINT", "false").lower() in ("true", "1")

    def is_s3_insecure_skip_verify(self) -> bool:
        return self.get("S3_INSECURE_SKIP_VERIFY", "false").lower() in ("true", "1")

    def is_cloud_cas_sync_enabled(self) -> bool:
        return self.get("ENABLE_CLOUD_CAS_SYNC", "false").lower() in ("true", "1")

# Global singleton instance
settings = SettingsManager()
