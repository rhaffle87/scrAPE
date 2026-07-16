import json
from utils.session_pool import Session


def test_session_cookie_persistence(tmp_path):
    cookie_file = tmp_path / "cookies" / "test-persist.com.json"

    # Instantiate with a temporary cookie file path
    domain = "test-persist.com"
    session = Session(domain)
    session._cookie_file = cookie_file

    # Ensure file doesn't exist yet
    if cookie_file.exists():
        cookie_file.unlink()

    # 1. Verify initial empty state
    assert len(session.cookies) == 0

    # 2. Add cookies and save to disk
    session.cookies.set("session_id", "xyz123")
    session.cookies.set("logged_in", "true")
    session.save_to_disk()

    assert cookie_file.exists()

    # Read and verify content on disk
    file_content = json.loads(cookie_file.read_text(encoding="utf-8"))
    assert file_content["cookies"]["session_id"] == "xyz123"
    assert file_content["cookies"]["logged_in"] == "true"
    assert file_content["user_agent"] == session.user_agent

    # 3. Create a new Session and verify it loads the cookies
    session2 = Session(domain)
    session2._cookie_file = cookie_file
    session2._load_from_disk()

    assert session2.cookies.get("session_id") == "xyz123"
    assert session2.cookies.get("logged_in") == "true"
    assert session2.user_agent == session.user_agent

    # 4. Reset identity should clear cookies and delete file
    session2.reset_identity()
    assert len(session2.cookies) == 0
    assert not cookie_file.exists()
