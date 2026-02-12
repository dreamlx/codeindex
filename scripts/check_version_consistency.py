#!/usr/bin/env python3
"""Check version consistency across all project files.

Single Source of Truth: pyproject.toml [project] version
All other version references should match.

Usage:
    python scripts/check_version_consistency.py          # Check
    python scripts/check_version_consistency.py --fix     # Fix markdown files

Exit codes:
    0 - All versions consistent
    1 - Version mismatch found
"""
# ruff: noqa: T201

import re
import sys
from pathlib import Path


def get_pyproject_version() -> str:
    """Read version from pyproject.toml (Single Source of Truth)."""
    pyproject = Path("pyproject.toml")
    if not pyproject.exists():
        print("ERROR: pyproject.toml not found")
        sys.exit(1)

    content = pyproject.read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        print("ERROR: version not found in pyproject.toml")
        sys.exit(1)

    return match.group(1)


def check_init_py(expected: str) -> list[str]:
    """Check that __init__.py uses importlib.metadata (not hardcoded)."""
    errors = []
    init_file = Path("src/codeindex/__init__.py")
    if not init_file.exists():
        return errors

    content = init_file.read_text()

    # Should use importlib.metadata, not hardcoded
    hardcoded = re.search(r'__version__\s*=\s*"(\d+\.\d+\.\d+)"', content)
    if hardcoded:
        errors.append(
            f"  src/codeindex/__init__.py: HARDCODED version '{hardcoded.group(1)}'\n"
            f"    Should use: from importlib.metadata import version"
        )

    if "importlib.metadata" not in content:
        errors.append(
            "  src/codeindex/__init__.py: Not using importlib.metadata\n"
            "    Add: from importlib.metadata import version"
        )

    return errors


def check_markdown_files(expected: str, fix: bool = False) -> list[str]:
    """Check markdown files for version references."""
    errors = []

    # Key files to check with their patterns
    files_to_check = [
        ("README.md", r'\*\*Current version\*\*:\s*v?(\d+\.\d+\.\d+)'),
        ("CLAUDE.md", r'\*\*Current version\*\*:\s*v?(\d+\.\d+\.\d+)'),
        ("docs/planning/ROADMAP.md", r'\*\*Current Version\*\*:\s*v?(\d+\.\d+\.\d+)'),
        ("docs/planning/README.md", r'\*\*Current Version\*\*:\s*v?(\d+\.\d+\.\d+)'),
    ]

    for filepath, pattern in files_to_check:
        path = Path(filepath)
        if not path.exists():
            continue

        content = path.read_text()
        matches = list(re.finditer(pattern, content, re.IGNORECASE))

        for match in matches:
            found_version = match.group(1)
            if found_version != expected:
                if fix:
                    # Replace the matched version with expected
                    old_text = match.group(0)
                    new_text = old_text.replace(found_version, expected)
                    content = content.replace(old_text, new_text)
                    path.write_text(content)
                    print(f"  FIXED {filepath}: {found_version} -> {expected}")
                else:
                    errors.append(
                        f"  {filepath}: found v{found_version}, expected v{expected}"
                    )

    return errors


def check_changelog(expected: str) -> list[str]:
    """Check that CHANGELOG.md has an entry for current version."""
    errors = []
    changelog = Path("CHANGELOG.md")
    if not changelog.exists():
        return errors

    content = changelog.read_text()
    # Check if current version has a changelog entry
    if f"## [{expected}]" not in content and f"## [v{expected}]" not in content:
        errors.append(
            f"  CHANGELOG.md: No entry for version {expected}\n"
            f"    Add: ## [{expected}] - YYYY-MM-DD"
        )

    return errors


def main():
    fix_mode = "--fix" in sys.argv
    expected = get_pyproject_version()

    print(f"Version check: pyproject.toml = {expected}")
    print("")

    all_errors = []

    # 1. Check __init__.py
    print("[1/3] Checking src/codeindex/__init__.py...")
    errors = check_init_py(expected)
    all_errors.extend(errors)
    if not errors:
        print("  OK (using importlib.metadata)")

    # 2. Check markdown files
    print(f"[2/3] Checking markdown files...{' (--fix mode)' if fix_mode else ''}")
    errors = check_markdown_files(expected, fix=fix_mode)
    all_errors.extend(errors)
    if not errors:
        print("  OK (all versions match)")

    # 3. Check CHANGELOG
    print("[3/3] Checking CHANGELOG.md...")
    errors = check_changelog(expected)
    all_errors.extend(errors)
    if not errors:
        print("  OK (entry exists)")

    # Summary
    print("")
    if all_errors:
        print(f"FAILED: {len(all_errors)} version inconsistency(ies) found:")
        print("")
        for error in all_errors:
            print(error)
        print("")
        if not fix_mode:
            print("Run with --fix to auto-fix markdown files")
        return 1
    else:
        print(f"PASSED: All versions consistent (v{expected})")
        return 0


if __name__ == "__main__":
    sys.exit(main())
