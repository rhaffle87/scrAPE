import os
os.environ["DISABLE_PROXY_BACKGROUND_REFRESH"] = "1"
import json
import pytest
from pathlib import Path

@pytest.fixture(scope="session", autouse=True)
def ensure_config_files_exist():
    project_root = Path(__file__).resolve().parent.parent
    
    # 1. ensure data/domain_config.json exists
    data_dir = project_root / "data"
    data_dir.mkdir(exist_ok=True)
    domain_config_path = data_dir / "domain_config.json"
    created_domain_config = False
    if not domain_config_path.exists():
        created_domain_config = True
        domain_config_path.write_text(json.dumps({
            "highres_transforms": {
                "booru": {
                    "host_contains": ["rule34", "booru"],
                    "rules": [{"pattern": "\\\\.pic\\\\d+\\\\.(jpe?g|png|webp)$", "replacement": ".\\\\1", "target": "path"}]
                }
            },
            "watchdog": {
                "min_interval_s": 60,
                "ttl_days": 7
            }
        }), encoding="utf-8")

    # 2. ensure src/config/subject_profiles.json exists
    config_dir = project_root / "src" / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    subject_profiles_path = config_dir / "subject_profiles.json"
    created_subject_profiles = False
    if not subject_profiles_path.exists():
        created_subject_profiles = True
        subject_profiles_path.write_text(json.dumps({
            "video_heavy": {"priority_domains": ["video-test-domain.com"], "block_image_only_domains": ["image-test-domain.com"], "max_results": 100},
            "image_heavy": {"priority_domains": ["gallery-test-domain.com"], "block_video_only_domains": [], "max_results": 200}
        }), encoding="utf-8")
        
    # 3. ensure data/url_normalisation_rules.json exists
    url_rules_path = data_dir / "url_normalisation_rules.json"
    created_url_rules = False
    if not url_rules_path.exists():
        created_url_rules = True
        url_rules_path.write_text(json.dumps({
            "rules": [
                {
                    "description": "Generic 2-letter locale prefix collapse rule for test URLs",
                    "pattern": "([a-z0-9-]+(?:\\.[a-z0-9-]+)+)/[a-z]{2}/",
                    "replacement": "\\1/"
                }
            ]
        }), encoding="utf-8")

    import config
    config._load_dynamic_config()

    yield

    # Teardown: only delete files if we created them
    if created_domain_config:
        domain_config_path.unlink(missing_ok=True)
    if created_subject_profiles:
        subject_profiles_path.unlink(missing_ok=True)
    if created_url_rules:
        url_rules_path.unlink(missing_ok=True)

# -----------------------------------------------------------------------------
# STRICT ISOLATION FIXTURES
# -----------------------------------------------------------------------------

def pytest_runtest_setup():
    """Globally disable network sockets, allowing only loopback."""
    try:
        import pytest_socket
        pytest_socket.socket_allow_hosts(["127.0.0.1", "localhost", "::1"])
    except ImportError:
        pass

import subprocess

@pytest.fixture(autouse=True)
def block_subprocess(request, monkeypatch):
    """Globally block external subprocess calls (e.g., Node/Playwright)."""
    if request.node.get_closest_marker("e2e"):
        return
        
    original_run = subprocess.run
    original_popen_init = subprocess.Popen.__init__
    
    def is_allowed_cmd(cmd_args):
        if not cmd_args:
            return False
        cmd = cmd_args[0] if isinstance(cmd_args, (list, tuple)) else cmd_args
        return cmd in ('/sbin/ldconfig', 'ver')

    def blocked_run(*args, **kwargs):
        if args and is_allowed_cmd(args[0]):
            return original_run(*args, **kwargs)
        raise RuntimeError(f"Subprocess execution is blocked in tests by default. Explicitly mock it if needed. Args: {args}")
    
    def blocked_popen_init(self, *args, **kwargs):
        if args and is_allowed_cmd(args[0]):
            return original_popen_init(self, *args, **kwargs)
        raise RuntimeError(f"Subprocess execution is blocked in tests by default. Explicitly mock it if needed. Args: {args}")
    
    monkeypatch.setattr(subprocess, "run", blocked_run)
    monkeypatch.setattr(subprocess.Popen, "__init__", blocked_popen_init)

@pytest.fixture(autouse=True)
def isolate_filesystem(tmp_path, monkeypatch):
    """Override global config paths to a temporary directory to prevent state leaks."""
    try:
        import src.config as config
        monkeypatch.setattr(config, "OUTPUT_DIR", tmp_path / "output")
        monkeypatch.setattr(config, "CACHE_DIR", tmp_path / "cache")
        # LOG_DIR might not be in config directly, but let's patch it if it is
        if hasattr(config, "LOG_DIR"):
            monkeypatch.setattr(config, "LOG_DIR", tmp_path / "logs")
    except ImportError:
        pass

@pytest.fixture(autouse=True)
def mock_preflight(request, monkeypatch):
    if "test_preflight" in request.node.name or "test_preflight" in str(request.node.fspath):
        return
    async def mock_run_preflight(self, urls):
        return urls
    try:
        from core.coordinator import CrawlCoordinator
        monkeypatch.setattr(CrawlCoordinator, '_run_preflight', mock_run_preflight)
    except ImportError:
        pass

import threading
import uvicorn
import time
import socket


def get_free_port() -> int:
    """Return a free ephemeral port on the loopback interface."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))  # loopback-only; satisfies CodeQL CWE-605
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def e2e_mock_server():
    """Spins up the FastAPI mock server on an ephemeral port in a background thread."""
    from tests.mock_target_server import app

    port = get_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="critical")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    for _ in range(50):
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                break
        except OSError:
            time.sleep(0.1)
    else:
        raise RuntimeError(f"Could not connect to mock server on port {port}")

    yield f"http://127.0.0.1:{port}"

    server.should_exit = True
    thread.join(timeout=2)
