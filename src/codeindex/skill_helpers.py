"""
Skill helpers for codeindex-update-guide.

Epic #25, Story #27: Provides helper functions for the
/codeindex-update-guide skill to analyze projects, generate
diffs, and apply personalized CLAUDE.md updates.
"""

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def detect_project_languages(project_path: Path) -> list[str]:
    """
    Detect programming languages used in a project.

    Scans for source files, ignoring common vendor directories
    (node_modules, .venv, vendor, etc.)

    Args:
        project_path: Root directory of the project

    Returns:
        List of detected language names (e.g., ["python", "swift", "java"])
    """
    raise NotImplementedError("TDD: implement in Green phase")


def detect_codeindex_config(project_path: Path) -> Optional[dict]:
    """
    Detect and parse .codeindex.yaml configuration.

    Args:
        project_path: Root directory of the project

    Returns:
        Parsed config dict, or None if not found
    """
    raise NotImplementedError("TDD: implement in Green phase")


def detect_loomgraph_integration(project_path: Path) -> bool:
    """
    Detect if LoomGraph is configured for the project.

    Args:
        project_path: Root directory of the project

    Returns:
        True if LoomGraph config found, False otherwise
    """
    raise NotImplementedError("TDD: implement in Green phase")


def generate_version_diff(old_version: str, new_version: str) -> str:
    """
    Generate a readable diff between two versions.

    Args:
        old_version: Previous codeindex version
        new_version: Current codeindex version

    Returns:
        Markdown-formatted diff string
    """
    raise NotImplementedError("TDD: implement in Green phase")


def generate_language_table_diff(old_languages: list[str], new_languages: list[str]) -> str:
    """
    Generate diff for language support changes.

    Args:
        old_languages: Previously supported languages
        new_languages: Currently supported languages

    Returns:
        Markdown-formatted diff showing new/removed languages
    """
    raise NotImplementedError("TDD: implement in Green phase")


def generate_suggestions(profile: dict, current_version: str) -> list[str]:
    """
    Generate personalized suggestions based on project profile.

    Args:
        profile: Project profile dict with keys:
            - languages: list of detected languages
            - has_codeindex_config: bool
            - has_loomgraph: bool
            - project_path: str
            - current_guide_version: str (optional)
        current_version: Current codeindex version

    Returns:
        List of suggestion strings (at least 2)
    """
    raise NotImplementedError("TDD: implement in Green phase")


def apply_updates(
    file_path: Path,
    updates: list[dict],
    select_all: bool = False,
    selected_indices: Optional[list[int]] = None,
) -> bool:
    """
    Apply updates to CLAUDE.md file.

    Args:
        file_path: Path to CLAUDE.md
        updates: List of update dicts with 'section' and 'content' keys
        select_all: If True, apply all updates
        selected_indices: Indices of updates to apply (if not select_all)

    Returns:
        True if successful, False otherwise
    """
    raise NotImplementedError("TDD: implement in Green phase")


def create_backup(file_path: Path) -> Optional[Path]:
    """
    Create a timestamped backup of the file.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file, or None if failed
    """
    raise NotImplementedError("TDD: implement in Green phase")


def rollback_from_backup(file_path: Path, backup_path: Path) -> bool:
    """
    Restore file from backup.

    Args:
        file_path: Path to file to restore
        backup_path: Path to backup file

    Returns:
        True if successful, False otherwise
    """
    raise NotImplementedError("TDD: implement in Green phase")
