import os
import json
from monitoring.logger import get_logger

logger = get_logger(__name__)

SESSION_DIR = "data/sessions"


import threading
import sys
from pathlib import Path

class SessionManager:
    _local_cookie_cache: dict[str, dict[str, str]] = {}
    _local_cookie_lock = threading.Lock()

    def __init__(self):
        os.makedirs(SESSION_DIR, exist_ok=True)
        # Ensure the directory is only accessible by the owner
        if os.name != 'nt':
            try:
                os.chmod(SESSION_DIR, 0o700)  # nosemgrep: python.lang.security.audit.insecure-file-permissions.insecure-file-permissions
            except OSError as exc:
                logger.warning("Failed to set permissions on session directory: %s", exc)

    def get_session_file(self, domain):
        return os.path.join(SESSION_DIR, f"{domain.replace('.', '_')}.json")

    def save_session(self, domain, cookies):
        file_path = self.get_session_file(domain)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f)
            
        # Enforce strict file permissions for sensitive session cookies
        if os.name != 'nt':
            try:
                os.chmod(file_path, 0o600)  # nosemgrep: python.lang.security.audit.insecure-file-permissions.insecure-file-permissions
            except OSError as exc:
                logger.warning("Failed to set permissions on session file: %s", exc)

    def load_session(self, domain):
        file = self.get_session_file(domain)
        if not os.path.exists(file):
            return None
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)

    def evict_session(self, domain):
        file = self.get_session_file(domain)
        if os.path.exists(file):
            try:
                os.remove(file)
            except OSError as exc:
                logger.warning("Failed to remove session file: %s", exc)

    @classmethod
    def _harvest_firefox_cookies_windows(cls, firefox_profiles_dir: Path, host: str) -> dict[str, str]:
        import sqlite3
        import tempfile
        import shutil
        import random
        harvested = {}
        domains_to_try = [host]
        if host.startswith("www."):
            domains_to_try.append(host[4:])
        else:
            domains_to_try.append(f".{host}")

        try:
            for profile in firefox_profiles_dir.glob("*"):
                db_path = profile / "cookies.sqlite"
                if db_path.exists():
                    temp_db = Path(tempfile.gettempdir()) / f"temp_ff_cookies_{random.randint(1000, 9999)}.sqlite"
                    try:
                        shutil.copy2(db_path, temp_db)
                        conn = sqlite3.connect(str(temp_db))
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='moz_cookies'")
                        if not cursor.fetchone():
                            conn.close()
                            continue
                        query = "SELECT name, value, host FROM moz_cookies WHERE " + " OR ".join(["host LIKE ?"] * len(domains_to_try))
                        params = [f"%{dom}%" for dom in domains_to_try]
                        cursor.execute(query, params)
                        for name, value, host_key in cursor.fetchall():
                            harvested[name] = value
                        conn.close()
                    except Exception as err:
                        logger.debug("Failed to read from Firefox db %s: %s", db_path, err)
                    finally:
                        if temp_db.exists():
                            try:
                                temp_db.unlink()
                            except Exception:
                                pass
        except Exception as err:
            logger.debug("Failed searching Firefox profiles: %s", err)
        return harvested

    @classmethod
    def _harvest_chromium_cookies_windows(cls, user_data_dir: Path, host: str) -> dict[str, str]:
        import sqlite3
        import tempfile
        import shutil
        import random
        import base64
        try:
            import win32crypt
            from Crypto.Cipher import AES
        except ImportError:
            logger.warning("pypiwin32 or pycryptodome not installed, skipping Chromium DPAPI decryption")
            return {}

        harvested = {}
        domains_to_try = [host]
        if host.startswith("www."):
            domains_to_try.append(host[4:])
        else:
            domains_to_try.append(f".{host}")

        def get_encryption_key():
            local_state_path = user_data_dir / "Local State"
            if not local_state_path.exists():
                return None
            try:
                with open(local_state_path, "r", encoding="utf-8") as f:
                    local_state = json.load(f)
                encrypted_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                encrypted_key = encrypted_key[5:]
                return win32crypt.CryptUnprotectData(encrypted_key, None, None, None, 0)[1]
            except Exception as e:
                logger.debug("Failed to get Chromium encryption key: %s", e)
                return None

        def decrypt_value(encrypted_value, key):
            try:
                if encrypted_value[:3] == b'v10' or encrypted_value[:3] == b'v11':
                    nonce = encrypted_value[3:15]
                    ciphertext = encrypted_value[15:-16]
                    tag = encrypted_value[-16:]
                    cipher = AES.new(key, AES.MODE_GCM, nonce)
                    return cipher.decrypt_and_verify(ciphertext, tag).decode('utf-8')
                else:
                    return win32crypt.CryptUnprotectData(encrypted_value, None, None, None, 0)[1].decode('utf-8')
            except Exception:
                return ""

        key = get_encryption_key()
        if not key:
            return harvested

        profiles = ["Default", "Profile 1", "Profile 2", "Profile 3"]
        for profile in profiles:
            db_path = user_data_dir / profile / "Network" / "Cookies"
            if not db_path.exists():
                db_path = user_data_dir / profile / "Cookies"
            if db_path.exists():
                temp_db = Path(tempfile.gettempdir()) / f"temp_chr_cookies_{random.randint(1000, 9999)}.sqlite"
                try:
                    shutil.copy2(db_path, temp_db)
                    conn = sqlite3.connect(str(temp_db))
                    cursor = conn.cursor()
                    query = "SELECT name, encrypted_value, host_key FROM cookies WHERE " + " OR ".join(["host_key LIKE ?"] * len(domains_to_try))
                    params = [f"%{dom}%" for dom in domains_to_try]
                    cursor.execute(query, params)
                    for name, enc_val, host_key in cursor.fetchall():
                        dec_val = decrypt_value(enc_val, key)
                        if dec_val:
                            harvested[name] = dec_val
                    conn.close()
                except Exception as err:
                    logger.debug("Failed to read from Chromium db %s: %s", db_path, err)
                finally:
                    if temp_db.exists():
                        try:
                            temp_db.unlink()
                        except Exception:
                            pass
        return harvested

    @classmethod
    def get_local_cookies(cls, domain: str) -> dict[str, str]:
        """Harvest local cookies for *domain* from browsers with a thread-safe singleton cache."""
        from config import ENABLE_COOKIE_HARVESTING
        if not ENABLE_COOKIE_HARVESTING:
            return {}

        with cls._local_cookie_lock:
            if domain in cls._local_cookie_cache:
                return cls._local_cookie_cache[domain]

            logger.info("Harvesting local cookies for %s (Synchronous)", domain)
            harvested = {}
            if sys.platform.startswith("win"):
                local_appdata = os.environ.get("LOCALAPPDATA", "")
                appdata = os.environ.get("APPDATA", "")
                
                if local_appdata:
                    chrome_user_data = Path(local_appdata) / "Google" / "Chrome" / "User Data"
                    brave_user_data = Path(local_appdata) / "BraveSoftware" / "Brave-Browser" / "User Data"
                    edge_user_data = Path(local_appdata) / "Microsoft" / "Edge" / "User Data"
                    
                    if chrome_user_data.exists():
                        harvested.update(cls._harvest_chromium_cookies_windows(chrome_user_data, domain))
                    if brave_user_data.exists():
                        harvested.update(cls._harvest_chromium_cookies_windows(brave_user_data, domain))
                    if edge_user_data.exists():
                        harvested.update(cls._harvest_chromium_cookies_windows(edge_user_data, domain))
                
                if appdata:
                    opera_user_data = Path(appdata) / "Opera Software" / "Opera Stable"
                    firefox_profiles = Path(appdata) / "Mozilla" / "Firefox" / "Profiles"
                    
                    if opera_user_data.exists():
                        harvested.update(cls._harvest_chromium_cookies_windows(opera_user_data, domain))
                    if firefox_profiles.exists():
                        harvested.update(cls._harvest_firefox_cookies_windows(firefox_profiles, domain))
                        
                if harvested:
                    logger.info("Successfully harvested %d cookies for '%s' using Windows custom pipeline", len(harvested), domain)
                    cls._local_cookie_cache[domain] = harvested
                    return harvested
            
            try:
                import browser_cookie3
                browsers_to_try = [
                    ("chrome", browser_cookie3.chrome),
                    ("firefox", browser_cookie3.firefox),
                    ("edge", browser_cookie3.edge),
                    ("brave", browser_cookie3.brave),
                    ("opera", browser_cookie3.opera),
                ]
                domains_to_try = [domain]
                if domain.startswith("www."):
                    domains_to_try.append(domain[4:])
                else:
                    domains_to_try.append(f".{domain}")

                for b_name, b_func in browsers_to_try:
                    for dom in domains_to_try:
                        try:
                            cj = b_func(domain_name=dom)
                            for cookie in cj:
                                harvested[cookie.name] = cookie.value
                            if harvested:
                                logger.info("Successfully harvested %d cookies for '%s' from local %s (browser_cookie3)", len(harvested), dom, b_name)
                                cls._local_cookie_cache[domain] = harvested
                                return harvested
                        except Exception as exc:
                            logger.debug("Local cookie harvest fallback from %s failed: %s", b_name, exc)
            except ImportError:
                logger.warning("browser-cookie3 not installed, skipping fallback")

            cls._local_cookie_cache[domain] = harvested
            return harvested
