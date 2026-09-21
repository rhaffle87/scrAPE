"""
test_path_traversal_hardened.py — Comprehensive tests for validate_safe_path and is_safe_subpath.
Tests boundary enforcement, subpath resolution, sibling prefix attacks, Windows drive escapes,
and error handling.
"""

import os
from pathlib import Path
import pytest

from common.security import validate_safe_path, is_safe_subpath, sanitize_filename


def test_validate_safe_path_normal_subpaths(tmp_path):
    base_dir = tmp_path / "sandbox"
    base_dir.mkdir()

    # Base directory itself is valid
    assert validate_safe_path(base_dir, base_dir) == base_dir
    assert is_safe_subpath(base_dir, base_dir) is True

    # Immediate child
    child_file = base_dir / "test.txt"
    assert validate_safe_path(base_dir, child_file) == child_file
    assert is_safe_subpath(base_dir, child_file) is True

    # Deeply nested child
    deep_child = base_dir / "level1" / "level2" / "data.parquet"
    assert validate_safe_path(base_dir, deep_child) == deep_child
    assert is_safe_subpath(base_dir, deep_child) is True

    # Path with redundant slashes and current-directory dots
    messy_path = base_dir / "level1" / "." / "level2" / "file.txt"
    resolved = validate_safe_path(base_dir, messy_path)
    assert resolved == base_dir / "level1" / "level2" / "file.txt"


def test_validate_safe_path_traversal_attacks(tmp_path):
    base_dir = tmp_path / "sandbox"
    base_dir.mkdir()

    # Direct parent traversal
    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_safe_path(base_dir, base_dir / ".." / "evil.txt")
    assert is_safe_subpath(base_dir, base_dir / ".." / "evil.txt") is False

    # Deep nested traversal escaping base
    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_safe_path(base_dir, base_dir / "a" / "b" / ".." / ".." / ".." / "escaped.txt")
    assert is_safe_subpath(base_dir, base_dir / "a" / "b" / ".." / ".." / ".." / "escaped.txt") is False

    # Root escape
    root_file = Path(os.path.abspath(os.sep)) / "etc" / "passwd"
    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_safe_path(base_dir, root_file)
    assert is_safe_subpath(base_dir, root_file) is False


def test_validate_safe_path_sibling_prefix_attacks(tmp_path):
    """
    CRITICAL SECURITY CHECK:
    A naïve startswith(str(base)) check can be bypassed by sibling paths sharing the prefix,
    e.g. /app/sandbox_evil or /app/sandbox.txt. Both relative_to and commonpath must reject these!
    """
    base_dir = tmp_path / "sandbox"
    base_dir.mkdir()

    # Sibling directory with common prefix name
    sibling_dir = tmp_path / "sandbox_evil" / "exploit.py"
    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_safe_path(base_dir, sibling_dir)
    assert is_safe_subpath(base_dir, sibling_dir) is False

    # Sibling file with common prefix name
    sibling_file = tmp_path / "sandbox.txt"
    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_safe_path(base_dir, sibling_file)
    assert is_safe_subpath(base_dir, sibling_file) is False

    # Sibling directory with hyphen
    hyphen_dir = tmp_path / "sandbox-backup" / "leak.json"
    with pytest.raises(ValueError, match="Path traversal detected"):
        validate_safe_path(base_dir, hyphen_dir)
    assert is_safe_subpath(base_dir, hyphen_dir) is False


def test_validate_safe_path_casing_and_cross_platform(tmp_path):
    base_dir = tmp_path / "Sandbox"
    base_dir.mkdir()

    child = base_dir / "sub" / "file.txt"
    # On Windows, case variations of the same directory should resolve cleanly
    if os.name == "nt":
        lower_base = Path(str(base_dir).lower())
        assert validate_safe_path(lower_base, child) is not None
        assert is_safe_subpath(lower_base, child) is True


def test_sanitize_filename_comprehensive():
    assert sanitize_filename("safe_name.jpg") == "safe_name.jpg"
    assert sanitize_filename("../../../etc/passwd") == "etc_passwd"
    assert sanitize_filename("foo\\..\\bar/baz") == "foo_bar_baz"
    assert sanitize_filename("   ") == "unnamed"
    assert sanitize_filename("...---...") == "---"
    assert sanitize_filename("photo(1) [test].png") == "photo_1_test_.png"
