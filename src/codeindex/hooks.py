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
    import re

    try:
        content = file_path.read_text()
        # Match pattern: <!-- CODEINDEX_GUIDE_START v0.21.0 -->
        match = re.search(r"<!-- CODEINDEX_GUIDE_START v(\d+\.\d+\.\d+) -->", content)
        if match:
            return match.group(1)
        return None
    except (FileNotFoundError, OSError):
        return None


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
    import re

    try:
        # Load template
        template_path = Path(__file__).parent / "templates" / "claude_md_core.md"
        template_content = template_path.read_text()

        # Replace version placeholder
        guide_content = template_content.replace("{version}", version)

        # Create markers
        marker_start = CODEINDEX_GUIDE_MARKER_START.format(version=version)
        marker_end = CODEINDEX_GUIDE_MARKER_END

        # Full guide section with markers
        full_guide = f"{marker_start}\n{guide_content}\n{marker_end}"

        # Read existing content
        if file_path.exists():
            existing_content = file_path.read_text()
        else:
            existing_content = "# CLAUDE.md\n\n"

        # Check if markers exist (any version)
        marker_pattern = r"<!-- CODEINDEX_GUIDE_START v\d+\.\d+\.\d+ -->.*?<!-- CODEINDEX_GUIDE_END -->"

        if re.search(marker_pattern, existing_content, re.DOTALL):
            # Replace existing guide (idempotent update)
            updated_content = re.sub(
                marker_pattern, full_guide, existing_content, flags=re.DOTALL
            )
        else:
            # Append guide to end of file
            updated_content = existing_content.rstrip() + "\n\n" + full_guide + "\n"

        # Write updated content
        file_path.write_text(updated_content)
        return True

    except (FileNotFoundError, OSError) as e:
        logger.error(f"Failed to inject guide: {e}")
        return False


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
    import os

    ci_vars = ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_HOME", "CIRCLECI"]
    return any(os.getenv(var) for var in ci_vars)


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
    import importlib.metadata
    import shutil
    from datetime import datetime

    try:
        # Skip in CI environments
        if _is_ci_environment():
            logger.info("Skipping CLAUDE.md update in CI environment")
            return

        # Check if ~/.claude directory exists
        claude_dir = Path.home() / ".claude"
        if not claude_dir.exists():
            logger.info("~/.claude directory not found, skipping update")
            return

        claude_md = claude_dir / "CLAUDE.md"

        # Create backup if file exists
        if claude_md.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = claude_dir / f"CLAUDE.md.backup.{timestamp}"
            shutil.copy2(claude_md, backup_path)
            logger.info(f"Created backup: {backup_path}")

        # Get current package version
        try:
            current_version = importlib.metadata.version("ai-codeindex")
        except importlib.metadata.PackageNotFoundError:
            # Fallback for development mode
            current_version = "0.22.2"

        # Inject or update guide
        success = _inject_core_guide(claude_md, current_version)

        if success:
            logger.info(f"Updated CLAUDE.md with codeindex v{current_version}")
        else:
            logger.warning("Failed to update CLAUDE.md")

    except PermissionError as e:
        logger.warning(f"Permission denied when updating CLAUDE.md: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in post_install_update_guide: {e}")
