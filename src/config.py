"""
src/config.py — Central configuration facade for scrAPE.
Exposes settings singleton and SettingsManager from config.settings_manager.
"""

from __future__ import annotations

from config.settings_manager import SettingsManager, settings

__all__ = ["SettingsManager", "settings"]
