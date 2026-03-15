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

import importlib.metadata
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


def _get_current_version() -> str:
    """Get current codeindex package version."""
    try:
        return importlib.metadata.version("ai-codeindex")
    except importlib.metadata.PackageNotFoundError:
        from . import __version__
        return __version__


def _load_template(version: str) -> str:
    """Load and render the CLAUDE.md template with version."""
    template_path = Path(__file__).parent / "templates" / "claude_md_core.md"
    content = template_path.read_text()
    return content.replace("{version}", version)


def build_section(version: Optional[str] = None) -> str:
    """
    Build the full codeindex section with markers.

    Args:
        version: Version string. If None, uses current package version.

    Returns:
        Complete section string with start/end markers.
    """
    if version is None:
        version = _get_current_version()

    template_content = _load_template(version)
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


def inject(file_path: Path, version: Optional[str] = None) -> bool:
    """
    Inject or update codeindex section in CLAUDE.md.

    - Creates file if it doesn't exist
    - Replaces existing section between markers (idempotent)
    - Appends section if no existing markers found

    Args:
        file_path: Path to CLAUDE.md file.
        version: Version string. If None, uses current package version.

    Returns:
        True if successful, False otherwise.
    """
    try:
        section = build_section(version)

        if not file_path.exists():
            file_path.write_text(section + "\n")
            return True

        content = file_path.read_text()

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
