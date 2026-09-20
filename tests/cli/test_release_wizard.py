import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli.release import bump_all_versions, append_changelog_entry


def test_bump_all_versions_dry_run(tmp_path, monkeypatch):
    """Verify bump_all_versions functions without error on existing files."""
    import src.cli.release
    monkeypatch.setattr(src.cli.release, "ROOT_DIR", tmp_path)
    
    # Create dummy files to mock the repository
    (tmp_path / "pyproject.toml").write_text('version = "0.23.0"', encoding="utf-8")
    (tmp_path / "frontend" / "templates").mkdir(parents=True)
    (tmp_path / "frontend" / "templates" / "index.html").write_text('<span class="logo-version">v0.23.0</span>', encoding="utf-8")
    (tmp_path / "crawlee_bridge").mkdir()
    (tmp_path / "crawlee_bridge" / "package.json").write_text('"version": "0.23.0"', encoding="utf-8")
    (tmp_path / "README.md").write_text('RELEASE-V0.23.0-orange', encoding="utf-8")
    (tmp_path / "DESIGN.md").write_text('`v0.23.0` version badge', encoding="utf-8")

    # Test version bump with a new version
    results = bump_all_versions("0.23.0")
    assert isinstance(results, dict)
    assert results["pyproject.toml"] is True
    assert results["frontend/index.html"] is True
    assert results["crawlee_bridge/package.json"] is True
    assert results["README.md"] is True
    assert results["DESIGN.md"] is True


def test_append_changelog_entry(tmp_path, monkeypatch):
    """Verify append_changelog_entry handles version headers properly."""
    import src.cli.release
    monkeypatch.setattr(src.cli.release, "ROOT_DIR", tmp_path)
    
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True)
    changelog = docs_dir / "CHANGELOG.md"
    changelog.write_text("# Changelog\n\n## [0.23.0] — 2026-07-29\n\n", encoding="utf-8")
    
    res = append_changelog_entry("0.23.0", ["Test highlight 1", "Test highlight 2"])
    assert res is True
    
    content = changelog.read_text(encoding="utf-8")
    assert "## [0.23.0]" in content
    assert "Test highlight 1" in content
