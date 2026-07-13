import sys
from pathlib import Path
import pytest

# Add scratch directory to sys.path to import analyze_results
scratch_path = Path(__file__).parent.parent / "scratch"
sys.path.insert(0, str(scratch_path))

import analyze_results

def test_normalize_log_message():
    # Test URL normalization
    assert "Failed for [URL]" in analyze_results.normalize_log_message("Failed for http://example.com/some/path?param=1")
    assert "Failed for [URL]" in analyze_results.normalize_log_message("Failed for https://sub.domain.org")
    
    # Test path normalization (Windows style)
    assert "File is [FILE_PATH] now" in analyze_results.normalize_log_message("File is C:\\Users\\user\\Documents\\file.txt now")
    
    # Test number normalization
    assert "Count: [NUM]" in analyze_results.normalize_log_message("Count: 42")
    
    # Test single quote normalization
    assert "Key '[VAL]'" in analyze_results.normalize_log_message("Key 'my_key'")

def test_format_size():
    assert analyze_results.format_size(None) == "N/A"
    assert analyze_results.format_size("not-a-number") == "N/A"
    assert analyze_results.format_size(500) == "500 B"
    assert analyze_results.format_size(2048) == "2.00 KB"
    assert analyze_results.format_size(1024 * 1024 * 1.5) == "1.50 MB"

def test_analyze_results_json_missing(tmp_path):
    non_existent = tmp_path / "does_not_exist.json"
    res = analyze_results.analyze_results_json(non_existent)
    assert "error" in res
    assert "not found" in res["error"]

def test_analyze_results_json_malformed(tmp_path):
    # Invalid JSON syntax
    bad_syntax = tmp_path / "bad_syntax.json"
    bad_syntax.write_text("{invalid json", encoding="utf-8")
    res = analyze_results.analyze_results_json(bad_syntax)
    assert "error" in res
    assert "Failed to load JSON" in res["error"]

    # Valid JSON but not a dictionary (e.g. list)
    not_dict = tmp_path / "not_dict.json"
    not_dict.write_text("[1, 2, 3]", encoding="utf-8")
    res = analyze_results.analyze_results_json(not_dict)
    assert "error" in res
    assert "not a dictionary" in res["error"]

def test_analyze_results_json_partial(tmp_path):
    # Missing optional keys/partial dictionary
    partial = tmp_path / "partial.json"
    partial.write_text('{"keyword": "test_kw"}', encoding="utf-8")
    res = analyze_results.analyze_results_json(partial)
    
    assert res["keyword"] == "test_kw"
    assert res["run_id"] == "N/A"
    assert res["page_count"] == 0
    assert res["images_count"] == 0
    assert res["videos_count"] == 0
    assert res["rejected_count"] == 0
    assert res["total_img_size"] == 0
    assert res["total_vid_size"] == 0

def test_analyze_results_json_full(tmp_path):
    full = tmp_path / "full.json"
    data = {
        "keyword": "full_test",
        "run_id": "test_id_123",
        "page_count": 5,
        "images": [
            {"url": "https://example.com/img1.jpg", "size_bytes": 1000},
            {"url": "https://example.com/img2.jpg", "size_bytes": 2000},
            {"url": "https://other.org/img3.png", "size_bytes": None}
        ],
        "videos": [
            {"url": "https://example.com/vid1.mp4", "size_bytes": 50000}
        ],
        "rejected_items": [
            {"reason": "low_resolution"},
            {"reason": "duplicate"},
            "invalid_item_format"
        ],
        "scanned_pages": [
            "https://example.com/page1",
            "https://example.com/page2",
            "https://other.org/page1"
        ]
    }
    import json
    full.write_text(json.dumps(data), encoding="utf-8")
    res = analyze_results.analyze_results_json(full)
    
    assert res["keyword"] == "full_test"
    assert res["images_count"] == 3
    assert res["videos_count"] == 1
    assert res["total_img_size"] == 3000
    assert res["total_vid_size"] == 50000
    assert res["rejected_count"] == 3
    assert res["rejections"]["low_resolution"] == 1
    assert res["rejections"]["unknown"] == 1
    assert res["scanned_domains"]["example.com"] == 2
    assert res["scanned_domains"]["other.org"] == 1
    assert res["kept_domains"]["example.com"] == 3
    assert res["kept_domains"]["other.org"] == 1

def test_analyze_log_file_missing(tmp_path):
    non_existent = tmp_path / "missing.log"
    res = analyze_results.analyze_log_file(non_existent)
    assert "error" in res

def test_analyze_log_file_robustness(tmp_path):
    log_file = tmp_path / "test.log"
    log_content = """
2026-07-13 09:57:13 | INFO     | __main__ | Start run
2026-07-13 09:57:15 | WARNING  | utils.http_client | GET https://example.com returned 429. Falling back to Crawl4AI...
2026-07-13 09:57:20 | WARNING  | utils.http_client | GET https://example.com returned 403. Falling back to Crawl4AI...
2026-07-13 09:58:00 | ERROR    | utils.http_client | All Crawl4AI fallback tiers failed for https://example.com: Crawl4AI Tier 2 hit Cloudflare challenge.
2026-07-13 09:58:05 | INFO     | __main__ | downloaded media https://example.com/img.jpg
random malformed line without standard format
2026-07-13 09:58:10 | INFO     | __main__ | downloaded media https://example.com/img2.jpg
2026-07-13 09:58:15 | WARNING  | __main__ | download failed for https://example.com/img3.jpg
"""
    log_file.write_text(log_content, encoding="utf-8")
    res = analyze_results.analyze_log_file(log_file)
    
    assert "error" not in res
    assert res["start_time"] is not None
    assert res["end_time"] is not None
    assert res["cf_challenges"] == 1
    assert res["cf_challenge_errors"] == 1
    assert res["download_success"] == 2
    assert res["download_failed"] == 1
    assert res["http_429s"]["example.com"] == 1
    assert res["other_http_errors"]["403 on example.com"] == 1
    
    # Check normalized errors/warnings
    assert any("All Crawl4AI fallback tiers failed for [URL]" in k for k in res["errors"].keys())
    assert any("GET [URL] returned [NUM]. Falling back to Crawl4AI..." in k for k in res["warnings"].keys())
