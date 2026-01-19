"""Incremental update logic for codeindex.

This module analyzes git changes and determines which directories
need README_AI.md updates based on configurable thresholds.
"""

import subprocess
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .config import Config


class UpdateLevel(Enum):
    """Update decision levels."""

    SKIP = "skip"  # Changes too small, skip update
    CURRENT = "current"  # Update current directory only
    AFFECTED = "affected"  # Update all affected directories
    FULL = "full"  # Suggest full project update


@dataclass
class FileChange:
    """Represents a changed file."""

    path: Path
    additions: int = 0
    deletions: int = 0

    @property
    def total_lines(self) -> int:
        return self.additions + self.deletions

    @property
    def directory(self) -> Path:
        return self.path.parent


@dataclass
class ChangeAnalysis:
    """Analysis result of git changes."""

    files: list[FileChange] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    affected_dirs: set[Path] = field(default_factory=set)
    level: UpdateLevel = UpdateLevel.SKIP
    message: str = ""

    @property
    def total_lines(self) -> int:
        return self.total_additions + self.total_deletions

    def to_dict(self) -> dict:
        """Convert to dictionary for CLI output."""
        return {
            "total_lines": self.total_lines,
            "additions": self.total_additions,
            "deletions": self.total_deletions,
            "files_changed": len(self.files),
            "affected_dirs": [str(d) for d in sorted(self.affected_dirs)],
            "level": self.level.value,
            "message": self.message,
        }


def run_git_command(args: list[str], cwd: Path | None = None) -> str:
    """Run a git command and return output."""
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_changed_files(
    since: str = "HEAD~1",
    until: str = "HEAD",
    cwd: Path | None = None,
) -> list[FileChange]:
    """Get list of changed files with line counts.

    Args:
        since: Starting commit reference (default: HEAD~1)
        until: Ending commit reference (default: HEAD)
        cwd: Working directory

    Returns:
        List of FileChange objects
    """
    # Get numstat for line counts
    output = run_git_command(
        ["diff", "--numstat", since, until],
        cwd=cwd,
    )

    if not output:
        return []

    changes = []
    for line in output.split("\n"):
        if not line.strip():
            continue

        parts = line.split("\t")
        if len(parts) != 3:
            continue

        additions, deletions, filepath = parts

        # Handle binary files (shown as -)
        try:
            add_count = int(additions) if additions != "-" else 0
            del_count = int(deletions) if deletions != "-" else 0
        except ValueError:
            continue

        changes.append(
            FileChange(
                path=Path(filepath),
                additions=add_count,
                deletions=del_count,
            )
        )

    return changes


def filter_code_files(
    changes: list[FileChange],
    languages: list[str],
) -> list[FileChange]:
    """Filter changes to only include code files.

    Args:
        changes: List of all file changes
        languages: List of supported languages

    Returns:
        Filtered list of code file changes
    """
    extensions = {
        "python": {".py"},
        "javascript": {".js", ".jsx"},
        "typescript": {".ts", ".tsx"},
        "java": {".java"},
        "go": {".go"},
        "rust": {".rs"},
    }

    valid_extensions = set()
    for lang in languages:
        valid_extensions.update(extensions.get(lang, set()))

    return [c for c in changes if c.path.suffix in valid_extensions]


def analyze_changes(
    config: Config,
    since: str = "HEAD~1",
    until: str = "HEAD",
    cwd: Path | None = None,
) -> ChangeAnalysis:
    """Analyze git changes and determine update strategy.

    Args:
        config: codeindex configuration
        since: Starting commit reference
        until: Ending commit reference
        cwd: Working directory

    Returns:
        ChangeAnalysis with update recommendation
    """
    inc = config.incremental

    # Get all changes
    all_changes = get_changed_files(since, until, cwd)

    # Filter to code files only
    code_changes = filter_code_files(all_changes, config.languages)

    if not code_changes:
        return ChangeAnalysis(
            level=UpdateLevel.SKIP,
            message="No code files changed",
        )

    # Calculate totals
    total_add = sum(c.additions for c in code_changes)
    total_del = sum(c.deletions for c in code_changes)
    total_lines = total_add + total_del

    # Get affected directories
    affected_dirs = {c.directory for c in code_changes}

    # Determine update level based on thresholds
    if total_lines < inc.skip_lines:
        level = UpdateLevel.SKIP
        message = f"Changes ({total_lines} lines) below skip threshold ({inc.skip_lines})"
    elif total_lines < inc.current_only:
        level = UpdateLevel.CURRENT
        message = f"Small changes ({total_lines} lines), update current dirs only"
    elif total_lines < inc.suggest_full:
        level = UpdateLevel.AFFECTED
        message = f"Medium changes ({total_lines} lines), update affected dirs"
    else:
        level = UpdateLevel.FULL
        message = f"Large changes ({total_lines} lines), consider full update"

    return ChangeAnalysis(
        files=code_changes,
        total_additions=total_add,
        total_deletions=total_del,
        affected_dirs=affected_dirs,
        level=level,
        message=message,
    )


def get_dirs_to_update(
    analysis: ChangeAnalysis,
    config: Config,
) -> list[Path]:
    """Get list of directories that should be updated.

    Args:
        analysis: Change analysis result
        config: codeindex configuration

    Returns:
        List of directory paths to update
    """
    if analysis.level == UpdateLevel.SKIP:
        return []

    # For CURRENT, AFFECTED, FULL - update affected dirs
    dirs = list(analysis.affected_dirs)

    # Filter to only include configured directories
    include_patterns = config.include
    filtered_dirs = []

    for d in dirs:
        d_str = str(d)
        for pattern in include_patterns:
            # Simple prefix matching (could be enhanced with glob)
            pattern_clean = pattern.rstrip("/")
            if d_str.startswith(pattern_clean) or d_str == pattern_clean:
                filtered_dirs.append(d)
                break

    return sorted(filtered_dirs)


def should_update_project_index(analysis: ChangeAnalysis, config: Config) -> bool:
    """Determine if PROJECT_INDEX.md should be updated.

    Args:
        analysis: Change analysis result
        config: codeindex configuration

    Returns:
        True if PROJECT_INDEX.md should be updated
    """
    if not config.incremental.auto_project_index:
        return False

    # Update project index for large changes or multiple directories
    return analysis.level == UpdateLevel.FULL or len(analysis.affected_dirs) > 2
