from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.cli.monitor_agent import AdaptiveBackoffTracker, load_watchdog_config, notify_telegram_summary
from storage.state_cache import StateCache


def test_adaptive_backoff_tracker_yield_and_backoff():
    tracker = AdaptiveBackoffTracker(min_interval_s=60, max_interval_s=3600, backoff_factor=2.0)
    subject = "test_subject"

    # Harvest > 0 -> min_interval_s
    delay1 = tracker.get_next_delay(subject, harvest_yield=10)
    assert delay1 == 60.0

    # Harvest == 0 -> double to 120
    delay2 = tracker.get_next_delay(subject, harvest_yield=0)
    assert delay2 == 120.0

    # Harvest == 0 -> double to 240
    delay3 = tracker.get_next_delay(subject, harvest_yield=0)
    assert delay3 == 240.0

    # Harvest > 0 -> reset back to min_interval_s (60)
    delay4 = tracker.get_next_delay(subject, harvest_yield=5)
    assert delay4 == 60.0


def test_adaptive_backoff_tracker_max_cap():
    tracker = AdaptiveBackoffTracker(min_interval_s=100, max_interval_s=300, backoff_factor=2.0)
    subject = "test_subject"

    delay1 = tracker.get_next_delay(subject, harvest_yield=0)  # 200
    assert delay1 == 200.0

    delay2 = tracker.get_next_delay(subject, harvest_yield=0)  # 400 -> capped at 300
    assert delay2 == 300.0


def test_state_cache_7_day_ttl_pruning(tmp_path):
    db_file = tmp_path / "test_state_cache.db"
    cache = StateCache(db_path=db_file)

    fresh_url = "https://example.com/fresh"
    stale_url = "https://example.com/stale"

    # Insert fresh entry (now)
    with cache._get_connection() as conn:
        conn.execute(
            "INSERT INTO processed_urls (url_hash, url, timestamp) VALUES (?, ?, ?)",
            (cache._hash_url(fresh_url), fresh_url, time.time()),
        )
        # Insert stale entry (10 days old)
        conn.execute(
            "INSERT INTO processed_urls (url_hash, url, timestamp) VALUES (?, ?, ?)",
            (cache._hash_url(stale_url), stale_url, time.time() - (10 * 86400)),
        )
        conn.commit()

    # Prune with 7-day TTL
    pruned = cache.prune_expired(max_age_days=7)
    assert pruned == 1

    # Verify fresh entry remains
    res = cache.is_processed_batch([fresh_url, stale_url])
    assert res[fresh_url] is True
    assert res[stale_url] is False


def test_load_watchdog_config():
    cfg = load_watchdog_config("data/domain_config.json")
    assert "min_interval_s" in cfg
    assert "ttl_days" in cfg
    assert cfg["ttl_days"] == 7


@patch("src.cli.monitor_agent.notify_telegram")
def test_notify_telegram_summary_formatting(mock_notify):
    notify_telegram_summary("test_subject", cycle=1, code=0, yield_info=(12, 3, 45))
    mock_notify.assert_called_once()
    msg = mock_notify.call_args[0][0]
    assert "test_subject" in msg
    assert "12" in msg
    assert "SUCCESS" in msg
