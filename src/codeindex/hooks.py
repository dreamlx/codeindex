"""
Post-install hook for automatic CLAUDE.md updates.

Epic #25, Story #26: Implement post-install hook that updates
~/.claude/CLAUDE.md with latest codeindex guide after pip install/upgrade.

Usage:
    Automatically invoked by pip after installation.
    Configured in pyproject.toml: [project.entry-points."pip.post-install"]
"""

import logging
from pathlib import Path
from typing import Optional

# Marker format for idempotent updates
CODEINDEX_GUIDE_MARKER_START = "<!-- CODEINDEX_GUIDE_START v{version} -->"
CODEINDEX_GUIDE_MARKER_END = "<!-- CODEINDEX_GUIDE_END -->"

logger = logging.getLogger(__name__)


def _extract_version_from_file(file_path: Path) -> Optional[str]:
    """
    Extract version number from CODEINDEX_GUIDE_MARKER_START in file.

    Args:
        file_path: Path to CLAUDE.md file

    Returns:
        Version string (e.g., "0.21.0") or None if not found
    """
    raise NotImplementedError("TDD: implement in Green phase")


def _inject_core_guide(file_path: Path, version: str) -> bool:
    """
    Inject or update codeindex core guide in CLAUDE.md.

    Uses marker-based injection for idempotent updates.

    Args:
        file_path: Path to CLAUDE.md file
        version: Current codeindex version

    Returns:
        True if successful, False otherwise
    """
    raise NotImplementedError("TDD: implement in Green phase")


def _is_ci_environment() -> bool:
    """
    Detect if running in CI/CD environment.

    Checks common CI environment variables:
    - GITHUB_ACTIONS
    - GITLAB_CI
    - JENKINS_HOME
    - CIRCLECI
    - CI (generic)

    Returns:
        True if in CI environment, False otherwise
    """
    raise NotImplementedError("TDD: implement in Green phase")


def post_install_update_guide() -> None:
    """
    Post-install hook entry point.

    Called automatically by pip after package installation.
    Updates ~/.claude/CLAUDE.md with latest codeindex guide.

    Behavior:
        - Skips update in CI environments
        - Skips if ~/.claude directory doesn't exist
        - Creates backup before updating
        - Handles permission errors gracefully (silent failure)
        - Idempotent: multiple runs produce same result
    """
    raise NotImplementedError("TDD: implement in Green phase")
