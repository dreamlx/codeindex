"""
codeindex - AI-native code indexing tool for large codebases

Usage:
    codeindex scan <path>     # Scan a directory and generate README_AI.md
    codeindex init            # Initialize .codeindex.yaml
    codeindex status          # Show indexing status
"""

import re
from pathlib import Path

__all__ = ["__version__"]


def _source_version(pyproject_path: Path | None = None) -> str | None:
    """Read the package version from the source-tree pyproject.toml.

    Returns None when the source tree is not reachable (wheel/pipx install),
    so the caller falls back to installed metadata instead.
    """
    # src/codeindex/__init__.py -> parents[0]=codeindex, [1]=src, [2]=repo root.
    pyproject = pyproject_path or (Path(__file__).resolve().parents[2] / "pyproject.toml")
    if not pyproject.is_file():
        return None
    try:
        text = pyproject.read_text(encoding="utf-8")
    except OSError:
        return None
    # Match `version = "x.y.z"` at column 0 (the [project] version). Lines like
    # `python_version = "3.10"` in [tool.mypy] don't start with `version`, so
    # they can't shadow it.
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return match.group(1) if match else None


def _resolve_version() -> str:
    """Resolve the package version, preferring source pyproject over metadata.

    Why: editable installs bake the version into dist-info at install time, so
    `codeindex --version` goes stale after a pyproject bump until reinstall.
    That once masked a shipped fix — a stale `--version` made a reader conclude
    the fix hadn't landed. Reading the source pyproject when it is reachable
    keeps `--version` honest in editable/dev setups; wheel/pipx installs (no
    source tree) fall back to installed metadata, which is correct for released
    wheels.
    """
    source = _source_version()
    if source:
        return source
    try:
        from importlib.metadata import version

        return version("ai-codeindex")
    except Exception:
        return "0.0.0-dev"


__version__ = _resolve_version()
