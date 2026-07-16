import os
import json

SESSION_DIR = "data/sessions"


class SessionManager:
    def __init__(self):
        if not os.path.exists(SESSION_DIR):
            os.makedirs(SESSION_DIR)

    def get_session_file(self, domain):
        return os.path.join(SESSION_DIR, f"{domain.replace('.', '_')}.json")

    def save_session(self, domain, cookies):
        with open(self.get_session_file(domain), "w", encoding="utf-8") as f:
            json.dump(cookies, f)

    def load_session(self, domain):
        file = self.get_session_file(domain)
        if not os.path.exists(file):
            return None
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
