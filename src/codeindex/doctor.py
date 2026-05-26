"""codeindex doctor — read-only health / sync diagnostic.

Answers the user's "am I up to date, and what do I upgrade?" across the
three version surfaces that drift independently (per ADR-006):

  1. the CLI itself (`ai-codeindex`, installed via pipx)
  2. the project's `.codeindex.yaml` + language parsers
  3. the project's `CLAUDE.md` codeindex section
  4. the Claude Code plugin (`codeindex-claude`) — only when a Claude Code
     environment is detected; skipped silently otherwise so Cursor / bare-CLI
     users get a clean, editor-agnostic report.

This command NEVER mutates anything — it only reads. The Claude Code plugin
detection reads `~/.claude/plugins/` on an explicit user invocation, which is
allowed by ADR-006 (that ADR forbids *install-time mutation* of ~/.claude,
not read-only diagnostics).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from . import __version__


@dataclass
class Finding:
    """A single diagnostic line. ``status`` is one of ok|warn|error|info."""

    section: str
    status: str
    message: str
    fix: Optional[str] = None


def check_cli() -> Finding:
    return Finding("CLI", "ok", f"ai-codeindex {__version__}")


def check_project(cwd: Path) -> list[Finding]:
    """Config presence + language parser health for the current directory."""
    findings: list[Finding] = []
    config_path = cwd / ".codeindex.yaml"

    if not config_path.exists():
        findings.append(
            Finding(
                "Project",
                "info",
                "no .codeindex.yaml in this directory",
                fix="codeindex init",
            )
        )
        return findings

    findings.append(Finding("Project", "ok", ".codeindex.yaml present"))

    try:
        from .config import Config

        languages = Config.load(config_path).languages
    except Exception:  # pragma: no cover - defensive; bad config shouldn't crash doctor
        findings.append(Finding("Project", "warn", ".codeindex.yaml could not be parsed"))
        return findings

    if not languages:
        return findings

    from .init_wizard import get_parser_install_guidance

    guidance = get_parser_install_guidance(languages)
    if guidance["installed"]:
        findings.append(
            Finding("Project", "ok", f"parsers installed: {', '.join(guidance['installed'])}")
        )
    if guidance["missing"]:
        missing = guidance["missing"]
        inject = " ".join(f"tree-sitter-{lang}" for lang in missing)
        findings.append(
            Finding(
                "Project",
                "error",
                f"missing parsers: {', '.join(missing)}",
                fix=f"pipx inject ai-codeindex {inject}",
            )
        )
    return findings


def check_claude_md(cwd: Path) -> Optional[Finding]:
    """Project CLAUDE.md codeindex-section sync vs the installed CLI."""
    claude_md = cwd / "CLAUDE.md"
    if not claude_md.exists():
        return None

    from .claude_md import extract_version

    marker = extract_version(claude_md)
    if marker is None:
        return Finding(
            "Project",
            "info",
            "CLAUDE.md present but has no codeindex section",
            fix="codeindex claude-md update",
        )
    if marker != __version__:
        return Finding(
            "Project",
            "warn",
            f"CLAUDE.md codeindex section is v{marker} (CLI is v{__version__})",
            fix="codeindex claude-md update",
        )
    return Finding("Project", "ok", f"CLAUDE.md codeindex section current (v{marker})")


def detect_plugin(home: Path) -> Optional[Finding]:
    """Best-effort detection of the codeindex-claude plugin.

    Returns None when this isn't a Claude Code environment (no
    ~/.claude/plugins), so the doctor omits the section entirely for
    non-Claude users.
    """
    plugins_root = home / ".claude" / "plugins"
    if not plugins_root.exists():
        return None

    # Claude Code caches installed plugins under cache/<marketplace>/<plugin>/<version>/
    candidates = list(plugins_root.glob("cache/*/codeindex/*/.claude-plugin/plugin.json"))
    if not candidates:
        return Finding(
            "Claude Code plugin",
            "info",
            "codeindex-claude not detected",
            fix="/plugin install codeindex@codeindex-claude",
        )

    best: Optional[str] = None
    for manifest in candidates:
        try:
            version = json.loads(manifest.read_text()).get("version")
        except Exception:  # pragma: no cover - skip unreadable manifests
            continue
        if version and (best is None or _version_tuple(version) > _version_tuple(best)):
            best = version

    if best is None:
        return Finding("Claude Code plugin", "info", "codeindex-claude detected (version unknown)")
    return Finding("Claude Code plugin", "ok", f"codeindex-claude {best} installed")


def _version_tuple(v: str) -> tuple:
    """Loose semver tuple for comparison; non-numeric parts sort as 0."""
    parts = []
    for p in v.split("."):
        num = "".join(ch for ch in p if ch.isdigit())
        parts.append(int(num) if num else 0)
    return tuple(parts)


def run_doctor(cwd: Optional[Path] = None, home: Optional[Path] = None) -> list[Finding]:
    """Run all checks and return findings in display order."""
    cwd = cwd or Path.cwd()
    home = home or Path.home()

    findings: list[Finding] = [check_cli()]
    findings.extend(check_project(cwd))

    claude_md_finding = check_claude_md(cwd)
    if claude_md_finding is not None:
        findings.append(claude_md_finding)

    plugin_finding = detect_plugin(home)
    if plugin_finding is not None:
        findings.append(plugin_finding)

    return findings


def has_errors(findings: list[Finding]) -> bool:
    return any(f.status == "error" for f in findings)
