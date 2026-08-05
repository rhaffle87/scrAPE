"""
cli_wizard_watchdog.py — Continuous Watchdog Mode Wizard Module.

Handles continuous watchdog monitoring wizard prompts, configuration,
state cache binding, and subprocess launching for long-running watchdog loops.
"""

from __future__ import annotations

import os
import sys
import subprocess
from pathlib import Path

__all__ = ["mode_continuous_watchdog"]


def mode_continuous_watchdog():
    """Run continuous watchdog monitoring wizard."""
    print("\n--- Mode 3: Continuous Watchdog Agent ---")
    print("This mode launches monitor_agent.py with periodic domain re-checking.")

    from cli.cli_wizard_standard import (
        get_input,
        get_bool_input,
        validate_not_empty,
        validate_seed_file,
        load_subject_profiles,
        run_command,
    )

    profiles = load_subject_profiles()
    subject_choice = get_input(
        "Enter Subject/Keyword to monitor",
        default="",
        val_fn=validate_not_empty,
    )

    seed_path = f"seeds/{subject_choice}.txt"
    if not os.path.exists(seed_path):
        seed_path = get_input("Enter Seed File Path", default="", val_fn=validate_seed_file)

    interval = get_input("Re-crawl Check Interval (seconds)", default="3600")
    use_cache = get_bool_input("Use SQLite State Cache to skip processed URLs?", default=True)

    cmd = [
        sys.executable,
        "src/cli/monitor_agent.py",
        "--keyword",
        subject_choice,
        "--seed",
        seed_path,
        "--interval",
        str(interval),
    ]

    if use_cache:
        cmd.append("--use-state-cache")

    print(f"\nLaunching Watchdog: {' '.join(cmd)}")
    run_command(cmd)
