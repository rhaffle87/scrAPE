from __future__ import annotations

import argparse
import datetime
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))


def update_file_content(path: Path, pattern: str, replacement: str) -> bool:
    if not path.exists():
        return False
    content = path.read_text(encoding="utf-8")
    new_content, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
    if count > 0:
        path.write_text(new_content, encoding="utf-8")
        return True
    return False


def bump_all_versions(version_clean: str) -> dict[str, bool]:
    version_tag = f"v{version_clean}"
    results: dict[str, bool] = {}

    # 1. pyproject.toml
    results["pyproject.toml"] = update_file_content(
        ROOT_DIR / "pyproject.toml",
        r'version = "[0-9]+\.[0-9]+\.[0-9]+"',
        f'version = "{version_clean}"',
    )

    # 2. launcher.py
    results["launcher.py"] = update_file_content(
        ROOT_DIR / "src" / "cli" / "launcher.py",
        r'VERSION = "v[0-9]+\.[0-9]+\.[0-9]+"',
        f'VERSION = "{version_tag}"',
    )

    # 3. frontend/app.py
    results["frontend/app.py"] = update_file_content(
        ROOT_DIR / "frontend" / "app.py",
        r'version="[0-9]+\.[0-9]+\.[0-9]+"',
        f'version="{version_clean}"',
    )

    # 4. frontend/templates/index.html
    results["frontend/index.html"] = update_file_content(
        ROOT_DIR / "frontend" / "templates" / "index.html",
        r'<span class="logo-version">v[0-9]+\.[0-9]+\.[0-9]+</span>',
        f'<span class="logo-version">{version_tag}</span>',
    )

    # 5. crawlee_bridge/package.json
    results["crawlee_bridge/package.json"] = update_file_content(
        ROOT_DIR / "crawlee_bridge" / "package.json",
        r'"version": "[0-9]+\.[0-9]+\.[0-9]+"',
        f'"version": "{version_clean}"',
    )

    # 6. README.md
    results["README.md"] = update_file_content(
        ROOT_DIR / "README.md",
        r'RELEASE-V[0-9]+\.[0-9]+\.[0-9]+-orange',
        f'RELEASE-V{version_clean}-orange',
    )

    # 7. DESIGN.md
    results["DESIGN.md"] = update_file_content(
        ROOT_DIR / "DESIGN.md",
        r'`v[0-9]+\.[0-9]+\.[0-9]+` version badge',
        f'`{version_tag}` version badge',
    )

    return results


def append_changelog_entry(version_clean: str, highlights: list[str]) -> bool:
    changelog_path = ROOT_DIR / "docs" / "CHANGELOG.md"
    if not changelog_path.exists():
        return False

    today_str = datetime.date.today().isoformat()
    header_title = f"## [{version_clean}] — {today_str}\n"

    content = changelog_path.read_text(encoding="utf-8")
    if header_title in content:
        return True

    bullet_items = "\n".join(f"- {h}" for h in highlights if h.strip())
    if not bullet_items:
        bullet_items = f"- **Release {version_clean}**: Maintenance release and engine updates."

    section_text = (
        f"{header_title}\n"
        f"### Added & Changed ({version_clean})\n\n"
        f"{bullet_items}\n\n"
    )

    new_content = re.sub(r"(# Changelog\s*\n\n)", r"\1" + section_text, content, count=1)
    changelog_path.write_text(new_content, encoding="utf-8")
    return True


def run_command(cmd: list[str], check: bool = True) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT_DIR),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            check=check,
        )
        return proc.returncode, proc.stdout
    except subprocess.CalledProcessError as e:
        return e.returncode, e.stdout or str(e)
    except Exception as e:
        return 1, str(e)


encoding = "utf-8"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Automated Release Helper for scrAPE (Version Bumps, Git Tagging & GitHub Release)"
    )
    parser.add_argument("--version", type=str, help="Target version string (e.g. 0.21.0 or v0.21.0)")
    parser.add_argument("--notes", type=str, help="Release highlights summary (comma or newline separated)")
    parser.add_argument("--dry-run", action="store_true", help="Perform version bumps without git commit or push")
    parser.add_argument("--push", action="store_true", help="Push commit/tag to GitHub origin and publish gh release")
    parser.add_argument("--no-push", action="store_true", help="Commit and tag locally, but skip git push and gh release")

    args = parser.parse_args()

    version_raw = args.version
    if not version_raw:
        print("\n========================================================")
        print("          scrAPE — AUTOMATED RELEASE WIZARD             ")
        print("========================================================\n")
        version_raw = input("Enter target release version (e.g. 0.21.0): ").strip()

    if not version_raw:
        print("Error: No version string provided. Exiting.")
        sys.exit(1)

    version_clean = version_raw.lstrip("v").strip()
    if not re.match(r"^\d+\.\d+\.\d+$", version_clean):
        print(f"Error: Invalid version format '{version_clean}'. Expected X.Y.Z format (e.g. 0.21.0).")
        sys.exit(1)

    version_tag = f"v{version_clean}"
    print(f"\n[1/5] Updating version references to {version_clean} ({version_tag})...")
    bump_results = bump_all_versions(version_clean)
    for file_key, ok in bump_results.items():
        status = "UPDATED" if ok else "SKIPPED/NOT MATCHED"
        print(f"  - {file_key}: {status}")

    highlights: list[str] = []
    if args.notes:
        highlights = [n.strip() for n in args.notes.split(",") if n.strip()]
    elif not args.dry_run:
        print("\nEnter release highlights (leave empty line to finish):")
        while True:
            line = input("> ").strip()
            if not line:
                break
            highlights.append(line)

    print("\n[2/5] Updating docs/CHANGELOG.md...")
    append_changelog_entry(version_clean, highlights)

    if args.dry_run:
        print("\n[DRY RUN COMPLETE] Files updated locally. Skipping git commit, tagging, and GitHub release.")
        return

    print("\n[3/5] Staging and committing changes...")
    _, add_out = run_command(["git", "add", "-A"])
    print(add_out.strip() or "  Git add complete.")

    code, commit_out = run_command(["git", "commit", "-m", f"release: {version_tag} - release deployment"])
    print(f"  {commit_out.strip()}")

    print(f"\n[4/5] Creating annotated git tag {version_tag}...")
    tag_msg = f"Release {version_tag} — scrAPE extraction engine"
    run_command(["git", "tag", "-a", version_tag, "-m", tag_msg], check=False)

    should_push = args.push
    if not args.push and not args.no_push:
        confirm = input("\nPush commit & tag to remote GitHub origin? [y/N]: ").strip().lower()
        should_push = confirm == "y" or confirm == "yes"

    if not should_push or args.no_push:
        print("\n[COMPLETE] Committed and tagged locally. Skiped push and GitHub release.")
        return

    print(f"\n[5/5] Pushing commit and tag to GitHub origin...")
    _, push_main_out = run_command(["git", "push", "origin", "main"], check=False)
    print(f"  Main branch push: {push_main_out.strip()}")

    _, push_tag_out = run_command(["git", "push", "origin", version_tag], check=False)
    print(f"  Tag push: {push_tag_out.strip()}")

    print(f"\nCreating GitHub Release {version_tag} via gh CLI...")
    notes_file = ROOT_DIR / "scratch" / "_release_tmp_notes.md"
    notes_file.parent.mkdir(parents=True, exist_ok=True)
    notes_content = f"## scrAPE {version_tag}\n\n" + "\n".join(f"- {h}" for h in highlights)
    notes_file.write_text(notes_content, encoding="utf-8")

    gh_code, gh_out = run_command([
        "gh", "release", "create", version_tag,
        "--title", f"scrAPE {version_tag}",
        "--notes-file", str(notes_file)
    ], check=False)

    if notes_file.exists():
        notes_file.unlink()

    if gh_code == 0:
        print(f"\nSuccessfully published GitHub Release {version_tag}!")
        print(f"URL: {gh_out.strip()}")
    else:
        print(f"\nNote: gh release output: {gh_out.strip()}")

    print(f"\nRelease {version_tag} workflow completed successfully!")


if __name__ == "__main__":
    main()
