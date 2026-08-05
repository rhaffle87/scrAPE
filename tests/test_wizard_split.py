"""
tests/test_wizard_split.py
Unit tests for cli_wizard split:
  - cli_wizard_standard module
  - cli_wizard_watchdog module
  - cli_wizard shim re-exports
"""
from __future__ import annotations

import src.cli.cli_wizard_standard as wizard_std
import src.cli.cli_wizard_watchdog as wizard_wd
import src.cli.cli_wizard as wizard_shim


def test_standard_wizard_exports():
    """cli_wizard_standard must export validation and mode functions."""
    assert callable(wizard_std.validate_not_empty)
    assert callable(wizard_std.validate_number)
    assert callable(wizard_std.load_subject_profiles)
    assert callable(wizard_std.mode_general_scraping)
    assert callable(wizard_std.mode_specified_scraping)


def test_watchdog_wizard_exports():
    """cli_wizard_watchdog must export mode_continuous_watchdog."""
    assert callable(wizard_wd.mode_continuous_watchdog)


def test_wizard_shim_reexports_all():
    """cli_wizard shim must re-export standard and watchdog mode functions."""
    expected_symbols = [
        "validate_not_empty",
        "validate_number",
        "load_subject_profiles",
        "mode_general_scraping",
        "mode_specified_scraping",
        "mode_continuous_watchdog",
        "run_cli_wizard",
    ]
    for symbol in expected_symbols:
        assert hasattr(wizard_shim, symbol), (
            f"cli_wizard shim is missing symbol '{symbol}'"
        )
