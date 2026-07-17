import os
import json

SESSION_DIR = "data/sessions"


class SessionManager:
    def __init__(self):
        os.makedirs(SESSION_DIR, exist_ok=True)
        # Ensure the directory is only accessible by the owner
        if os.name != 'nt':
            try:
                os.chmod(SESSION_DIR, 0o700)
            except Exception:
                pass

    def get_session_file(self, domain):
        return os.path.join(SESSION_DIR, f"{domain.replace('.', '_')}.json")

    def save_session(self, domain, cookies):
        file_path = self.get_session_file(domain)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f)
            
        # Enforce strict file permissions for sensitive session cookies
        if os.name != 'nt':
            try:
                os.chmod(file_path, 0o600)
            except Exception:
                pass

    def load_session(self, domain):
        file = self.get_session_file(domain)
        if not os.path.exists(file):
            return None
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
