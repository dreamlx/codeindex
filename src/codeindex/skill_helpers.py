"""
Skill helpers for codeindex-update-guide.

Epic #25, Story #27: Provides helper functions for the
/codeindex-update-guide skill to analyze projects, generate
diffs, and apply personalized CLAUDE.md updates.
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# Language extension mapping
_LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".swift": "swift",
    ".java": "java",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".php": "php",
    ".go": "go",
    ".rs": "rust",
    ".m": "objc",
    ".h": "objc",
}

# Directories to ignore during language detection
_IGNORE_DIRS = {
    "node_modules", ".venv", "venv", "__pycache__", ".git",
    "vendor", "build", "dist", ".tox", ".mypy_cache",
    ".pytest_cache", ".eggs", "egg-info",
}


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
    detected = set()

    try:
        for item in project_path.rglob("*"):
            # Skip ignored directories
            if any(part in _IGNORE_DIRS for part in item.parts):
                continue

            if item.is_file() and item.suffix in _LANGUAGE_EXTENSIONS:
                detected.add(_LANGUAGE_EXTENSIONS[item.suffix])
    except (PermissionError, OSError) as e:
        logger.warning(f"Error scanning project: {e}")

    return sorted(detected)


def detect_codeindex_config(project_path: Path) -> Optional[dict]:
    """
    Detect and parse .codeindex.yaml configuration.

    Args:
        project_path: Root directory of the project

    Returns:
        Parsed config dict, or None if not found
    """
    config_path = project_path / ".codeindex.yaml"
    if not config_path.exists():
        return None

    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        logger.warning(f"Error reading config: {e}")
        return None


def detect_loomgraph_integration(project_path: Path) -> bool:
    """
    Detect if LoomGraph is configured for the project.

    Args:
        project_path: Root directory of the project

    Returns:
        True if LoomGraph config found, False otherwise
    """
    loomgraph_indicators = [
        ".loomgraph.yaml",
        ".loomgraph.yml",
        "loomgraph.config.json",
    ]
    return any((project_path / f).exists() for f in loomgraph_indicators)


def generate_version_diff(old_version: str, new_version: str) -> str:
    """
    Generate a readable diff between two versions.

    Args:
        old_version: Previous codeindex version
        new_version: Current codeindex version

    Returns:
        Markdown-formatted diff string
    """
    if old_version == new_version:
        return "No change - versions are the same."

    return (
        f"### Version Update\n\n"
        f"- **Old**: v{old_version}\n"
        f"+ **New**: v{new_version}\n"
    )


def generate_language_table_diff(old_languages: list[str], new_languages: list[str]) -> str:
    """
    Generate diff for language support changes.

    Args:
        old_languages: Previously supported languages
        new_languages: Currently supported languages

    Returns:
        Markdown-formatted diff showing new/removed languages
    """
    old_set = set(old_languages)
    new_set = set(new_languages)

    added = new_set - old_set
    removed = old_set - new_set

    if not added and not removed:
        return "No change in language support."

    lines = ["### Language Support Changes\n"]

    if added:
        for lang in sorted(added):
            lines.append(f"+ **{lang}** (newly supported)")

    if removed:
        for lang in sorted(removed):
            lines.append(f"- **{lang}** (removed)")

    return "\n".join(lines)


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
    suggestions = []
    languages = profile.get("languages", [])
    guide_version = profile.get("current_guide_version")

    # Version update suggestion
    if guide_version and guide_version != current_version:
        suggestions.append(
            f"Update version from v{guide_version} to v{current_version} "
            f"to get latest features and command references."
        )

    # Language-specific suggestions
    if "swift" in languages:
        suggestions.append(
            "Add Swift language support documentation — codeindex v0.21.0+ "
            "supports Swift classes, structs, enums, protocols, and extensions."
        )

    if "objc" in languages:
        suggestions.append(
            "Add Objective-C support documentation — codeindex v0.21.0+ "
            "supports Objective-C classes, protocols, categories, and methods."
        )

    if "java" in languages:
        suggestions.append(
            "Add Java support documentation — includes classes, methods, "
            "fields, annotations, and Spring Boot route extraction."
        )

    if "typescript" in languages or "javascript" in languages:
        suggestions.append(
            "Add TypeScript/JavaScript documentation — supports classes, "
            "interfaces, functions, imports, and type definitions."
        )

    # LoomGraph suggestions
    if profile.get("has_loomgraph"):
        suggestions.append(
            "Add LoomGraph integration section — configure semantic code "
            "search with `codeindex scan --output json | loomgraph inject`."
        )

    # Config suggestions
    if not profile.get("has_codeindex_config"):
        suggestions.append(
            "Run `codeindex init` to create .codeindex.yaml configuration "
            "for optimized scanning and language detection."
        )

    # Tech debt suggestion (always useful)
    suggestions.append(
        "Add tech-debt analysis commands — use `codeindex tech-debt ./src` "
        "for code quality monitoring and test smells detection (v0.22.0+)."
    )

    # Ensure minimum 2 suggestions
    if len(suggestions) < 2:
        suggestions.append(
            "Run `codeindex scan-all --fallback` to generate comprehensive "
            "README_AI.md documentation for all project directories."
        )

    return suggestions


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
    try:
        # Determine which updates to apply
        if select_all:
            to_apply = updates
        elif selected_indices:
            to_apply = [updates[i] for i in selected_indices if i < len(updates)]
        else:
            return False

        # Read existing content or create new
        if file_path.exists():
            content = file_path.read_text()
        else:
            content = ""

        # Append each update's content
        for update in to_apply:
            content += "\n" + update["content"]

        file_path.write_text(content)
        return True

    except (OSError, IndexError) as e:
        logger.error(f"Failed to apply updates: {e}")
        return False


def create_backup(file_path: Path) -> Optional[Path]:
    """
    Create a timestamped backup of the file.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file, or None if failed
    """
    try:
        if not file_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.parent / f"{file_path.name}.backup.{timestamp}"
        shutil.copy2(file_path, backup_path)

        return backup_path

    except OSError as e:
        logger.error(f"Failed to create backup: {e}")
        return None


def rollback_from_backup(file_path: Path, backup_path: Path) -> bool:
    """
    Restore file from backup.

    Args:
        file_path: Path to file to restore
        backup_path: Path to backup file

    Returns:
        True if successful, False otherwise
    """
    try:
        if not backup_path.exists():
            logger.warning(f"Backup not found: {backup_path}")
            return False

        shutil.copy2(backup_path, file_path)
        return True

    except OSError as e:
        logger.error(f"Failed to rollback: {e}")
        return False
