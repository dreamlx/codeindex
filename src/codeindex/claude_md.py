"""
CLAUDE.md management for codeindex.

Handles injection, update, and version checking of codeindex sections
in project-level CLAUDE.md files. Uses marker-based injection for
idempotent updates.

Markers:
    <!-- codeindex:start v{version} -->
    ...content...
    <!-- codeindex:end -->
"""

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Unified marker format (with version)
MARKER_START_PREFIX = "<!-- codeindex:start"
MARKER_END = "<!-- codeindex:end -->"

# Regex patterns
# Matches both old (no version) and new (with version) markers
MARKER_PATTERN = re.compile(
    r"<!-- codeindex:start(?:\s+v[\d.]+)?\s*-->.*?<!-- codeindex:end -->",
    re.DOTALL,
)
VERSION_PATTERN = re.compile(
    r"<!-- codeindex:start\s+v([\d.]+)\s*-->"
)


# Locale detection (GH #77): match the injected section to the host
# CLAUDE.md's language so a zh project doesn't get an English section mid-file.
# English docs carry ~0 CJK, so even a small CJK ratio is a strong "host is
# Chinese" signal. Threshold kept low deliberately — technical docs are
# CJK-sparse (code blocks, commands, identifiers dominate the char count).
_CJK_RATIO_THRESHOLD = 0.05
_SUPPORTED_LOCALES = ("en", "zh")


def _is_cjk(ch: str) -> bool:
    """True for CJK ideographs (covers the common Chinese range)."""
    return "一" <= ch <= "鿿"


def detect_locale(content: str) -> str:
    """Detect the host CLAUDE.md language: 'zh' or 'en' (default).

    Strips any existing codeindex section first so our own prose never biases
    detection (keeps `claude-md update` idempotent — it re-matches the *host*,
    not the section we previously wrote).
    """
    host = MARKER_PATTERN.sub("", content or "")
    cjk = sum(1 for ch in host if _is_cjk(ch))
    non_ws = sum(1 for ch in host if not ch.isspace())
    if non_ws == 0:
        return "en"
    return "zh" if (cjk / non_ws) >= _CJK_RATIO_THRESHOLD else "en"


def _get_current_version() -> str:
    """Get current codeindex package version.

    Uses the module's ``__version__`` resolver (source pyproject first,
    installed metadata as fallback). GH #161: this previously did its own
    importlib-first lookup, which goes stale under editable installs
    (dist-info baked at install time) — a freshly injected CLAUDE.md then
    triggered a self-contradictory "v0.35.1 vs v0.35.1, run update" hint
    on every CLI invocation.
    """
    from . import __version__

    return __version__


def _load_template(version: str, lang: str = "en") -> str:
    """Load and render the CLAUDE.md template with version.

    ``lang`` selects the localized template (``en`` default, ``zh`` for the
    Chinese variant — GH #77). Unknown locales fall back to English.
    """
    suffix = "_zh" if lang == "zh" else ""
    template_path = Path(__file__).parent / "templates" / f"claude_md_core{suffix}.md"
    content = template_path.read_text()
    return content.replace("{version}", version)


def build_section(version: Optional[str] = None, lang: str = "en") -> str:
    """
    Build the full codeindex section with markers.

    Args:
        version: Version string. If None, uses current package version.
        lang: Locale for the section body ('en' or 'zh'). See GH #77.

    Returns:
        Complete section string with start/end markers.
    """
    if version is None:
        version = _get_current_version()

    template_content = _load_template(version, lang)
    marker_start = f"<!-- codeindex:start v{version} -->"
    return f"{marker_start}\n{template_content}\n{MARKER_END}"


def extract_version(file_path: Path) -> Optional[str]:
    """
    Extract codeindex version from CLAUDE.md markers.

    Args:
        file_path: Path to CLAUDE.md file.

    Returns:
        Version string (e.g., "0.23.0") or None if not found.
    """
    try:
        content = file_path.read_text()
        match = VERSION_PATTERN.search(content)
        return match.group(1) if match else None
    except (FileNotFoundError, OSError):
        return None


def inject(
    file_path: Path,
    version: Optional[str] = None,
    lang: Optional[str] = None,
) -> bool:
    """
    Inject or update codeindex section in CLAUDE.md.

    - Creates file if it doesn't exist
    - Replaces existing section between markers (idempotent)
    - Appends section if no existing markers found

    Args:
        file_path: Path to CLAUDE.md file.
        version: Version string. If None, uses current package version.
        lang: Section locale — 'en' / 'zh' to force, or None/'auto' to detect
            from the host CLAUDE.md language (GH #77). A fresh file with no
            host content detects as 'en'.

    Returns:
        True if successful, False otherwise.
    """
    try:
        existing = file_path.read_text() if file_path.exists() else ""

        if lang in (None, "auto"):
            resolved_lang = detect_locale(existing)
        else:
            resolved_lang = lang if lang in _SUPPORTED_LOCALES else "en"

        section = build_section(version, resolved_lang)

        if not existing:
            file_path.write_text(section + "\n")
            return True

        content = existing

        if MARKER_PATTERN.search(content):
            # Replace existing section (idempotent update)
            new_content = MARKER_PATTERN.sub(section, content)
        else:
            # Append to end of file
            new_content = content.rstrip() + "\n\n" + section + "\n"

        file_path.write_text(new_content)
        return True

    except (OSError, FileNotFoundError) as e:
        logger.error(f"Failed to inject CLAUDE.md section: {e}")
        return False


def check_outdated(project_dir: Optional[Path] = None) -> Optional[str]:
    """
    Check if project CLAUDE.md has an outdated codeindex section.

    Args:
        project_dir: Project root directory. Defaults to CWD.

    Returns:
        Outdated version string if update needed, None if up-to-date or no markers.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    claude_md = project_dir / "CLAUDE.md"
    if not claude_md.exists():
        return None

    injected_version = extract_version(claude_md)
    if injected_version is None:
        return None  # No codeindex markers, nothing to update

    current_version = _get_current_version()
    if injected_version != current_version:
        return injected_version

    return None


# GH #177: commands/mechanisms removed by the v0.37.0 BREAKING (#167) — the
# post-commit hook and its escape hatches. The v0.33.3-era injected CLAUDE.md
# section documented these, so an AI agent following a stale section runs the
# deleted commands. Each tuple is (substring, human-readable label); the
# substring is matched inside the codeindex section only (not host prose),
# matching #167's changelog exactly. `hooks rerun` never collides with
# `--retry-all`; `hooks install post-commit` doesn't match the still-valid
# `hooks install/uninstall/status` shorthand (that has no `post-commit`).
_REMOVED_COMMAND_PATTERNS = [
    ("hooks rerun", "the `hooks rerun` escape hatch"),
    ("hooks run", "the hidden `hooks run` command"),
    ("hooks install post-commit", "`hooks install post-commit`"),
    ("post_commit", "the `hooks.post_commit` config section"),
]


def find_removed_command_docs(project_dir: Optional[Path] = None) -> list[str]:
    """Scan the codeindex section of CLAUDE.md for deleted commands (GH #177).

    The v0.37.0 BREAKING (#167) removed the post-commit hook, but CLAUDE.md
    sections injected by older templates still document ``hooks rerun``,
    ``hooks install post-commit``, the hidden ``hooks run``, and the
    ``hooks.post_commit`` config. An AI agent following the stale section runs
    commands that no longer exist. The startup hint uses this to escalate
    from a generic "run update" to a specific "these deleted mechanisms are
    still documented" warning.

    Only the codeindex-injected section (between markers) is scanned — host
    prose outside the section is the author's own content, not stale docs we
    injected, so it's excluded to avoid false positives.

    Args:
        project_dir: Project root directory. Defaults to CWD.

    Returns:
        Sorted list of the matched substrings (e.g. ``["hooks rerun",
        "post_commit"]``). Empty when CLAUDE.md is absent, has no codeindex
        markers, or the section is clean.
    """
    if project_dir is None:
        project_dir = Path.cwd()

    claude_md = project_dir / "CLAUDE.md"
    if not claude_md.exists():
        return []

    try:
        content = claude_md.read_text()
    except (OSError, FileNotFoundError):
        return []

    match = MARKER_PATTERN.search(content)
    if not match:
        return []  # no codeindex section — host prose only, not stale docs

    section = match.group(0)
    hits = [pat for pat, _label in _REMOVED_COMMAND_PATTERNS if pat in section]
    return sorted(set(hits))
