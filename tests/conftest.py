import os
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
            "video_heavy": {"priority_domains": ["rule34video.com"], "block_image_only_domains": ["pixiv.net"], "max_results": 100},
            "image_heavy": {"priority_domains": ["buondua.com"], "block_video_only_domains": [], "max_results": 200}
        }), encoding="utf-8")
        
    yield
    
    # Teardown: only delete files if we created them
    if created_domain_config:
        domain_config_path.unlink(missing_ok=True)
    if created_subject_profiles:
        subject_profiles_path.unlink(missing_ok=True)
