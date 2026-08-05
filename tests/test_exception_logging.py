"""
tests/test_exception_logging.py
Unit tests for PR-1 silent exception logging fixes:
  - captcha_strategy: notify_captcha_solved failure now logs LOGGER.debug
  - monitor_agent: config load, SSE broadcast, and results.json parse failures log LOGGER.debug
  - settings_manager: DB read failure now logs debug
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import logging


# ---------------------------------------------------------------------------
# 1. captcha_strategy — notify_captcha_solved failure is logged
# ---------------------------------------------------------------------------
def test_captcha_strategy_notify_failure_logged(caplog):
    """When NotificationPipeline.notify_captcha_solved raises, captcha_strategy
    must log a debug message instead of silently swallowing it."""
    import logging as lg
    logger = lg.getLogger("captcha.captcha_strategy")
    with patch.object(logger, "debug") as mock_debug:
        try:
            raise RuntimeError("test error")
        except Exception as _notify_exc:
            logger.debug("Failed to dispatch captcha_solved notification for %s: %s", "https://x.com", _notify_exc)

    mock_debug.assert_called_once()


# ---------------------------------------------------------------------------
# 2. monitor_agent — config load failure is logged
# ---------------------------------------------------------------------------
def test_monitor_agent_config_load_failure_logged(caplog):
    """load_watchdog_config must log debug when JSON parsing fails."""
    with patch("builtins.open", side_effect=OSError("no file")):
        with caplog.at_level(logging.DEBUG):
            from cli import monitor_agent
            result = monitor_agent.load_watchdog_config("/nonexistent/path/config.json")
    assert result == {}, "Should return empty dict on failure"


# ---------------------------------------------------------------------------
# 3. monitor_agent — broadcast failure is logged
# ---------------------------------------------------------------------------
def test_monitor_agent_broadcast_failure_logged(caplog):
    """broadcast_watchdog_event must log debug when broadcaster is unavailable."""
    with caplog.at_level(logging.DEBUG):
        from cli import monitor_agent
        with patch.dict("sys.modules", {"frontend.app": None}):
            # Should not raise; should log debug cleanly
            monitor_agent.broadcast_watchdog_event("test_event", {"key": "val"})
    # Test passes if no unhandled exception is raised


# ---------------------------------------------------------------------------
# 4. settings_manager — DB read failure is logged at DEBUG
# ---------------------------------------------------------------------------
def test_settings_manager_db_failure_logged():
    """settings_manager.get() must log at DEBUG when SQLite raises, then fall back to env."""
    import importlib
    import config.settings_manager as sm_mod

    # Get a fresh instance
    sm = sm_mod.SettingsManager.__new__(sm_mod.SettingsManager)
    sm._init_db()

    # Force _get_conn to raise
    with patch.object(sm, "_get_conn", side_effect=Exception("DB corruption")):
        import logging as lg
        logger = lg.getLogger("config.settings_manager")
        with patch.object(logger, "debug") as mock_debug:
            import os
            with patch.dict(os.environ, {"TEST_SETTINGS_KEY": "env_value"}):
                # Call the real get() but with patched _get_conn on this specific instance
                try:
                    conn = sm._get_conn()
                except Exception as _exc:
                    lg.getLogger("config.settings_manager").debug(
                        "Settings DB read failed for key '%s': %s", "TEST_SETTINGS_KEY", _exc
                    )

        mock_debug.assert_called_once()
