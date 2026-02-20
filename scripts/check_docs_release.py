#!/usr/bin/env python3
"""Check documentation consistency before/after release.

Detects stale patterns in docs that commonly need updating when a new
version is released (language support tables, epic status, metrics, etc.).

Usage:
    python scripts/check_docs_release.py          # Check and print warnings
    python scripts/check_docs_release.py --strict  # Exit 1 if issues found

This script is called by `make pre-release-check` and `make release`.
"""
# ruff: noqa: T201

import re
import sys
from pathlib import Path


def get_pyproject_version() -> str:
    """Read version from pyproject.toml."""
    content = Path("pyproject.toml").read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    return match.group(1) if match else "unknown"


def get_supported_languages() -> set[str]:
    """Read actually supported languages from scanner.py LANGUAGE_EXTENSIONS."""
    scanner = Path("src/codeindex/scanner.py")
    if not scanner.exists():
        return set()

    content = scanner.read_text()
    # Match keys in LANGUAGE_EXTENSIONS dict
    return set(re.findall(r'"(\w+)":\s*\[', content))


# --- Checks ---

def check_language_tables(supported: set[str]) -> list[str]:
    """Find docs that mark supported languages as 'Planned'."""
    warnings = []

    files_patterns = [
        ("docs/planning/ROADMAP.md", r'\|\s*\*\*(\w[\w/]*)\*\*\s*\|[^|]*\|\s*📋\s*Planned'),
        ("docs/guides/configuration.md", r'#\s*-\s*(\w+)\s'),  # commented-out languages
    ]

    for filepath, pattern in files_patterns:
        path = Path(filepath)
        if not path.exists():
            continue

        content = path.read_text()
        for match in re.finditer(pattern, content):
            lang = match.group(1).lower().replace("/", "")
            # Normalize: "TypeScript/JavaScript" -> check both
            if lang in ("typescriptjavascript", "typescript", "javascript"):
                if "typescript" in supported or "javascript" in supported:
                    warnings.append(
                        f"  {filepath}: '{match.group(0).strip()}' — language is now supported"
                    )
            elif lang in supported:
                warnings.append(
                    f"  {filepath}: '{match.group(0).strip()}' — language is now supported"
                )

    # Check configuration.md for commented-out supported languages
    config_path = Path("docs/guides/configuration.md")
    if config_path.exists():
        content = config_path.read_text()
        for lang in supported:
            # Look for "# - language" (commented out)
            if re.search(rf'#\s*-\s*{lang}\b', content):
                warnings.append(
                    f"  docs/guides/configuration.md: '{lang}' is commented out but now supported"
                )

    return warnings


def check_roadmap_stale_next(version: str) -> list[str]:
    """Check ROADMAP.md for current version still marked as 'Next'."""
    warnings = []
    path = Path("docs/planning/ROADMAP.md")
    if not path.exists():
        return warnings

    content = path.read_text()

    # Pattern: "### v0.19.0 - ... (Next)"
    pattern = rf'###\s+v{re.escape(version)}\s+.*\(Next\)'
    if re.search(pattern, content):
        warnings.append(
            f"  docs/planning/ROADMAP.md: v{version} section still marked '(Next)' — should be '✅ (Released)'"
        )

    # Pattern: unchecked success criteria "- [ ]" under current version section
    # Find the section for current version
    section_match = re.search(
        rf'###\s+v{re.escape(version)}\b.*?\n(.*?)(?=\n###\s|\n---|\Z)',
        content, re.DOTALL
    )
    if section_match:
        section = section_match.group(1)
        unchecked = section.count("- [ ]")
        if unchecked > 0:
            warnings.append(
                f"  docs/planning/ROADMAP.md: v{version} has {unchecked} unchecked success criteria '- [ ]'"
            )

    return warnings


def check_roadmap_epic_status(version: str) -> list[str]:
    """Check ROADMAP.md for epics matching current version still in Future."""
    warnings = []
    path = Path("docs/planning/ROADMAP.md")
    if not path.exists():
        return warnings

    content = path.read_text()

    # Look for current version in Future Epics table
    pattern = rf'\|\s*\*\*Epic \d+\*\*\s*\|\s*v{re.escape(version)}\s*\|.*📋'
    for match in re.finditer(pattern, content):
        warnings.append(
            f"  docs/planning/ROADMAP.md: '{match.group(0).strip()}' — should be in Completed Epics"
        )

    return warnings


def check_planning_readme(version: str) -> list[str]:
    """Check Planning README for current version epics still in Planned section."""
    warnings = []
    path = Path("docs/planning/README.md")
    if not path.exists():
        return warnings

    content = path.read_text()

    # Find "Planned Epics" section and check for current version
    planned_match = re.search(
        r'## 📋 Planned Epics.*?\n(.*?)(?=\n## |\Z)',
        content, re.DOTALL
    )
    if planned_match:
        section = planned_match.group(1)
        if f"v{version}" in section:
            warnings.append(
                f"  docs/planning/README.md: v{version} epic still in 'Planned Epics' — move to 'Completed'"
            )

    return warnings


def check_roadmap_metrics(version: str) -> list[str]:
    """Check ROADMAP.md metrics table for stale version references."""
    warnings = []
    path = Path("docs/planning/ROADMAP.md")
    if not path.exists():
        return warnings

    content = path.read_text()

    # Look for metrics table with old "Current" version
    # Pattern: "Current (v0.X.0)" where X is not current
    for match in re.finditer(r'Current\s*\(v(\d+\.\d+\.\d+)\)', content):
        found = match.group(1)
        if found != version:
            warnings.append(
                f"  docs/planning/ROADMAP.md: Metrics table says 'Current (v{found})' — should be v{version}"
            )

    # Check "Current Status" header
    for match in re.finditer(r'Current Status\s*\(v(\d+\.\d+\.\d+)\)', content):
        found = match.group(1)
        if found != version:
            warnings.append(
                f"  docs/planning/ROADMAP.md: Status header says 'v{found}' — should be v{version}"
            )

    return warnings


def check_priority_matrix(version: str, supported: set[str]) -> list[str]:
    """Check Feature Priorities Matrix for completed items not marked done."""
    warnings = []
    path = Path("docs/planning/ROADMAP.md")
    if not path.exists():
        return warnings

    content = path.read_text()

    # Find rows in P0/P1 tables that have current version but no ✅ or ~~strikethrough~~
    pattern = rf'\|\s*(?!~~)(\w[^|]*?)\s*\|\s*v{re.escape(version)}\s*\|'
    for match in re.finditer(pattern, content):
        feature = match.group(1).strip()
        if "✅" not in match.group(0):
            warnings.append(
                f"  docs/planning/ROADMAP.md: P0/P1 feature '{feature}' (v{version}) not marked ✅"
            )

    return warnings


def main():
    strict = "--strict" in sys.argv
    version = get_pyproject_version()
    supported = get_supported_languages()

    print(f"📋 Documentation Release Checklist (v{version})")
    print(f"   Supported languages: {', '.join(sorted(supported))}")
    print()

    all_warnings = []

    checks = [
        ("Language support tables", lambda: check_language_tables(supported)),
        ("ROADMAP version sections", lambda: check_roadmap_stale_next(version)),
        ("ROADMAP epic status", lambda: check_roadmap_epic_status(version)),
        ("ROADMAP metrics", lambda: check_roadmap_metrics(version)),
        ("ROADMAP priority matrix", lambda: check_priority_matrix(version, supported)),
        ("Planning README", lambda: check_planning_readme(version)),
    ]

    for name, check_fn in checks:
        warnings = check_fn()
        all_warnings.extend(warnings)
        status = f"⚠ {len(warnings)} issue(s)" if warnings else "✓ OK"
        print(f"  [{status}] {name}")
        for w in warnings:
            print(w)

    print()
    if all_warnings:
        print(f"⚠ {len(all_warnings)} documentation issue(s) found")
        print("  Fix these before or immediately after release.")
        if strict:
            return 1
        return 0
    else:
        print("✅ All documentation checks passed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
