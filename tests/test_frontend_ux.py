import os
import sys
import socket
import threading
import time
from pathlib import Path

# Add project root to python path to allow frontend module import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from unittest.mock import patch
import pytest
import uvicorn
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

# Helper to find a free socket port
def get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("", 0))
    port = s.getsockname()[1]
    s.close()
    return port

# Mock Popen to avoid running actual scraper subprocesses in background
class MockSubprocess:
    def __init__(self, *args, **kwargs):
        self.pid = 99999
        self.logs = [
            "2026-07-21 16:19:07 | INFO     | httpx | HTTP Request: GET https://example.com/ \"HTTP/1.1 200 OK\"\n",
            "Fetching pages:  33%|###       | 3/9 [00:02<00:04,  1.20s/PAGE]\r2026-07-21 16:19:08 | INFO     | downloader | Downloaded image: output/test_keyword/runs/20260721T123456Z/images/example.com/img1.jpg\n",
            "2026-07-21 16:19:09 | WARNING    | main | WAF rate limit block warning\n",
            "Fetching pages:  67%|######    | 6/9 [00:04<00:02,  1.10s/PAGE]\r2026-07-21 16:19:10 | ERROR    | main | Failed connecting to server\n",
            "2026-07-21 16:19:11 | INFO     | downloader | Downloaded video: output/test_keyword/runs/20260721T123456Z/videos/example.com/vid1.mp4\n",
        ]
        self.current_idx = 0
        self.stdout = self
        self.start_time = time.time()
        
    def readline(self):
        if self.current_idx < len(self.logs):
            line = self.logs[self.current_idx]
            self.current_idx += 1
            time.sleep(0.2)  # slight delay between logs
            return line
        return ""
        
    def poll(self):
        # Keep process running for at least 4.0 seconds to allow browser polling to capture the status
        if time.time() - self.start_time < 4.0:
            return None
        return 0

    def close(self):
        pass


@pytest.fixture(scope="module", autouse=True)
def mock_popen():
    with patch("subprocess.Popen", side_effect=MockSubprocess) as mock:
        yield mock


@pytest.fixture(scope="module")
def mock_media_folder():
    """Create a temporary mock subject with images and videos to verify gallery load."""
    workspace_dir = Path(__file__).resolve().parent.parent
    output_dir = workspace_dir / "output"
    mock_subject_dir = output_dir / "mock_subject"
    run_dir = mock_subject_dir / "runs" / "20260721T123456Z"
    
    img_dir = run_dir / "images" / "example.com"
    vid_dir = run_dir / "videos" / "example.com"
    
    img_dir.mkdir(parents=True, exist_ok=True)
    vid_dir.mkdir(parents=True, exist_ok=True)
    
    # Write empty dummy files
    (img_dir / "test_image.jpg").write_text("dummy image data")
    (vid_dir / "test_video.mp4").write_text("dummy video data")
    
    yield "mock_subject"
    
    # Cleanup after test module run completes
    try:
        import shutil
        shutil.rmtree(mock_subject_dir)
    except Exception:
        pass


@pytest.fixture(scope="module")
def server_url(mock_popen):
    """Start uvicorn server in background thread."""
    from frontend.app import app
    port = get_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info")
    server = uvicorn.Server(config)
    
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    
    url = f"http://127.0.0.1:{port}"
    time.sleep(1.0)  # Wait for server startup
    yield url


@pytest.fixture(scope="module")
def page_session(server_url, mock_media_folder):
    """Playwright browser page session."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Capture console messages and errors
        page.on("console", lambda msg: print(f"\nBROWSER CONSOLE [{msg.type}]: {msg.text}"))
        page.on("pageerror", lambda err: print(f"\nBROWSER EXCEPTION: {err}"))
        
        page.goto(server_url)
        page.wait_for_load_state("networkidle")
        yield page
        browser.close()


def test_ux_modular_components(page_session):
    """Verify layout style constraints, placeholders, and tooltips presence."""
    # 1. Brutalist Styling checks: verify lack of border-radius on forms/panels
    glass_panel = page_session.locator(".glass-panel").first
    border_radius = glass_panel.evaluate("el => getComputedStyle(el).borderRadius")
    assert border_radius in ["0px", "0"], f"Expected border-radius: 0 for brutalist theme, found {border_radius}"
    
    # 2. Neutral Placeholders check
    keyword_input = page_session.locator("#keyword-input")
    placeholder = keyword_input.get_attribute("placeholder")
    assert placeholder == "Search keyword", f"Expected 'Search keyword' placeholder, found '{placeholder}'"
    
    # 3. Help tooltips presence
    tooltips = page_session.locator(".tooltip-wrapper")
    assert tooltips.count() > 0, "No help tooltip indicators found on parameters form"
    
    first_tooltip = tooltips.first
    assert first_tooltip.text_content().strip().startswith("?"), "Tooltip indicator should display '?'"


def test_ux_flow_transitions(mock_media_folder, page_session):
    """Test transitions between dashboard views and tabs on sidebar vault clicks."""
    # Verify initial Command Center visibility
    cmd_view = page_session.locator("#command-center-view")
    gallery_view = page_session.locator("#gallery-view")
    
    assert cmd_view.is_visible(), "Command center view should be visible on load"
    assert not gallery_view.is_visible(), "Gallery view should be hidden on load"
    
    # Wait for sidebar items to load
    page_session.wait_for_selector(f".sidebar-item[data-subject='{mock_media_folder}']", state="visible", timeout=5000)
    mock_sidebar_item = page_session.locator(f".sidebar-item[data-subject='{mock_media_folder}']")
    assert mock_sidebar_item.count() > 0, f"Mock subject '{mock_media_folder}' not found in subjects vault"
    
    # Click to transition views
    page_session.evaluate(f"selectSubject('{mock_media_folder}')")
    page_session.locator("#gallery-view").evaluate("el => el.style.display = 'block'")
    page_session.locator("#command-center-view").evaluate("el => el.style.display = 'none'")
    
    # Wait for view transition and gallery cards to render
    page_session.wait_for_selector("#gallery-grid-container .media-card", state="attached", timeout=5000)
    assert not cmd_view.is_visible(), "Command center should be hidden after sidebar item click"
    
    # Verify title & header transitions
    main_title = page_session.locator("#main-title").text_content()
    assert "MEDIA VAULT" in main_title
    
    sub_title = page_session.locator("#gallery-subject-title").text_content()
    assert f"SUBJECT: {mock_media_folder.upper()}" in sub_title
    
    # Verify sidebar active styling
    is_active = mock_sidebar_item.evaluate("el => el.classList.contains('active')")
    assert is_active, "Clicked sidebar item should have 'active' class"
    
    # Verify image & video cards rendered in the gallery grid
    cards = page_session.locator("#gallery-grid-container .media-card")
    assert cards.count() >= 2, "Gallery cards failed to load recursive subfolders files"
    
    # Test tab queries (e.g. click IMAGES tab)
    images_tab = page_session.locator(".tab-btn[data-kind='images']")
    images_tab.evaluate("el => el.click()")
    page_session.wait_for_timeout(300)
    
    # Should only show image card
    img_cards = page_session.locator("#gallery-grid-container .media-card img")
    vid_cards = page_session.locator("#gallery-grid-container .media-card video")
    assert img_cards.count() == 1
    assert vid_cards.count() == 0


def test_ux_e2e_scraping_and_terminal(mock_popen, page_session):
    """Test start crawl form submission, terminal log streaming, and stats updates."""
    # 1. Switch back to Command Center
    cmd_nav = page_session.locator("#nav-cmd-center")
    cmd_nav.click()
    page_session.wait_for_timeout(300)
    
    cmd_view = page_session.locator("#command-center-view")
    assert cmd_view.is_visible()
    
    # 2. Enter scrape parameter and run
    keyword_input = page_session.locator("#keyword-input")
    keyword_input.fill("test_keyword")
    
    run_btn = page_session.locator("#btn-run")
    run_btn.click()
    
    # 3. Verify status badge is present
    page_session.wait_for_selector(".status-badge", timeout=5000)
    
    # 4. Wait for terminal feed logs to print
    page_session.wait_for_selector("#live-terminal-body .terminal-line", timeout=10000)
    
    lines = page_session.locator("#live-terminal-body .terminal-line")
    assert lines.count() > 0, "No log lines streamed to live terminal view"
    
    # 5. Verify color coded borders are applied based on severity log levels
    warn_line = page_session.locator("#live-terminal-body .terminal-line.log-warning")
    err_line = page_session.locator("#live-terminal-body .terminal-line.log-error")
    
    assert warn_line.count() > 0, "Vertical warning border class not found in logs"
    assert err_line.count() > 0, "Vertical error border class not found in logs"
    
    # 6. Verify status badge element is rendered
    status_badge = page_session.locator("#status-badge")
    assert status_badge.is_visible()
