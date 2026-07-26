import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli.release import bump_all_versions, append_changelog_entry


def test_bump_all_versions_dry_run():
    """Verify bump_all_versions functions without error on existing files."""
    # Test version bump with current version 0.20.0
    results = bump_all_versions("0.20.0")
    assert isinstance(results, dict)
    assert "pyproject.toml" in results
    assert "launcher.py" in results
    assert "frontend/app.py" in results
    assert "frontend/index.html" in results
    assert "crawlee_bridge/package.json" in results
    assert "README.md" in results
    assert "DESIGN.md" in results


def test_append_changelog_entry():
    """Verify append_changelog_entry handles version headers properly."""
    res = append_changelog_entry("0.20.0", ["Test highlight 1", "Test highlight 2"])
    assert res is True
