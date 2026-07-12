import json
import os
from datetime import datetime

BLACKLIST_PATH = "data/blacklist.json"

def load_blacklist():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(BLACKLIST_PATH):
        return {}
    with open(BLACKLIST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_blacklist(blacklist):
    with open(BLACKLIST_PATH, "w", encoding="utf-8") as f:
        json.dump(blacklist, f, indent=4)

def add_to_blacklist(domain, reason="404"):
    blacklist = load_blacklist()
    blacklist[domain] = {
        "reason": reason,
        "timestamp": datetime.now().isoformat()
    }
    save_blacklist(blacklist)

def is_blacklisted(domain):
    blacklist = load_blacklist()
    dom = domain.lower()
    for b_domain in blacklist:
        b_dom = b_domain.lower()
        if dom == b_dom or dom.endswith("." + b_dom):
            return True
    return False

