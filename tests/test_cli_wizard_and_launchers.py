from __future__ import annotations

from pathlib import Path
import pytest
from src.cli.cli_wizard import (
    load_subject_profiles,
    validate_not_empty,
    validate_number,
    validate_seed_file,
)


def test_load_subject_profiles():
    profiles = load_subject_profiles()
    assert isinstance(profiles, dict)
    assert len(profiles) > 0


def test_cli_wizard_validation_functions():
    ok, _ = validate_not_empty("test")
    assert ok is True

    fail, err = validate_not_empty("   ")
    assert fail is False
    assert "cannot be empty" in err

    num_ok, _ = validate_number("100")
    assert num_ok is True

    num_fail, _ = validate_number("abc")
    assert num_fail is False

    seed_ok, _ = validate_seed_file("")
    assert seed_ok is True


def test_master_launcher_script_existence_and_options():
    root = Path(__file__).resolve().parent.parent

    run_bat = root / "run.bat"
    assert run_bat.exists()
    bat_content = run_bat.read_text(encoding="utf-8")
    assert "Launch Continuous Watchdog Agent" in bat_content

    run_sh = root / "run.sh"
    assert run_sh.exists()
    sh_content = run_sh.read_text(encoding="utf-8")
    assert "Launch Continuous Watchdog Agent" in sh_content
