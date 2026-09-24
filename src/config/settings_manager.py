from contextlib import contextmanager
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
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS settings (
                        key TEXT PRIMARY KEY,
                        value TEXT
                    )
                    """
                )
        finally:
            conn.close()

    @contextmanager
    def _get_conn(self):
        conn = sqlite3.connect(self.db_path, timeout=10.0, check_same_thread=False)
        try:
            with conn:
                yield conn
        finally:
            conn.close()

    def close(self):
        """Deterministic cleanup hook."""
        pass

    def get(self, key: str, default: str = "") -> str:
        """Get a setting. Tries SQLite first, then os.getenv(), then default."""
        try:
            with self._get_conn() as conn:
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
        with self._get_conn() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value)
            )

    def get_all(self):
        """Get all explicitly set settings from DB."""
        with self._get_conn() as conn:
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

    # Component 3: Vision-Language DOM Healing (VLM) Configuration Accessors
    def get_vlm_provider(self) -> str:
        val = self.get("SCRAPE_VLM_PROVIDER", "").strip() or self.get("VLM_PROVIDER", "").strip()
        return val.lower() if val else "ollama"

    def get_vlm_provider_consent(self) -> bool:
        val = self.get("SCRAPE_VLM_PROVIDER_CONSENT", "").strip() or self.get("VLM_PROVIDER_CONSENT", "").strip()
        return val.lower() in ("true", "1")

    def get_vlm_enable_interaction(self) -> bool:
        val = self.get("SCRAPE_ENABLE_VLM_INTERACTION", "").strip() or self.get("ENABLE_VLM_INTERACTION", "").strip()
        return val.lower() in ("true", "1")

    def get_vlm_max_calls(self) -> int:
        val = self.get("SCRAPE_MAX_VLM_CALLS", "").strip() or self.get("MAX_VLM_CALLS", "").strip()
        try:
            return int(val) if val else 20
        except ValueError:
            return 20

    def get_vlm_model_name(self) -> str:
        return self.get("SCRAPE_VLM_MODEL", "").strip() or self.get("VLM_MODEL", "").strip()

# Global singleton instance
settings = SettingsManager()
