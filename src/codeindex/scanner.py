"""Directory scanner for codeindex."""

import fnmatch
from dataclasses import dataclass
from pathlib import Path

from .config import Config


@dataclass
class ScanResult:
    """Result of scanning a directory."""

    path: Path
    files: list[Path]
    subdirs: list[Path]

    @property
    def indexable_files(self) -> list[Path]:
        """Get all indexable files (Python, PHP, etc.)."""
        return self.files

    @property
    def python_files(self) -> list[Path]:
        """Get Python files only."""
        return [f for f in self.files if f.suffix == ".py"]

    @property
    def php_files(self) -> list[Path]:
        """Get PHP files only."""
        return [f for f in self.files if f.suffix in (".php", ".phtml")]


def should_exclude(path: Path, exclude_patterns: list[str], base_path: Path) -> bool:
    """Check if path matches any exclude pattern."""
    rel_path = str(path.relative_to(base_path))

    for pattern in exclude_patterns:
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        if fnmatch.fnmatch(str(path), pattern):
            return True
        # Check if any parent matches
        if "**" in pattern:
            simple_pattern = pattern.replace("**", "*")
            if fnmatch.fnmatch(rel_path, simple_pattern):
                return True

    return False


def scan_directory(
    path: Path,
    config: Config,
    base_path: Path | None = None,
    recursive: bool = True
) -> ScanResult:
    """
    Scan a directory and return its contents.

    Args:
        path: Directory to scan
        config: Configuration object
        base_path: Base path for relative pattern matching
        recursive: Whether to scan subdirectories recursively

    Returns:
        ScanResult with files and subdirectories
    """
    if base_path is None:
        base_path = path

    files: list[Path] = []
    subdirs: list[Path] = []

    if not path.exists() or not path.is_dir():
        return ScanResult(path=path, files=[], subdirs=[])

    for item in sorted(path.iterdir()):
        # Skip excluded paths
        if should_exclude(item, config.exclude, base_path):
            continue

        if item.is_file():
            # Filter by language/extension
            if item.suffix == ".py" and "python" in config.languages:
                files.append(item)
            elif item.suffix in (".php", ".phtml") and "php" in config.languages:
                files.append(item)
            # Add more language support here in V2
        elif item.is_dir() and recursive:
            # Recursively scan subdirectories
            sub_result = scan_directory(item, config, base_path, recursive)
            files.extend(sub_result.files)
            subdirs.extend(sub_result.subdirs)
            subdirs.append(item)  # Track the subdirectory itself

    return ScanResult(path=path, files=files, subdirs=subdirs)


def find_all_directories(root: Path, config: Config) -> list[Path]:
    """
    Find all directories that should be indexed.

    If config.include is specified, returns those directories directly.
    Otherwise, walks the directory tree to find all directories with indexable files.

    Args:
        root: Root directory to start from
        config: Configuration object

    Returns:
        List of directory paths to index
    """
    dirs_to_index: list[Path] = []

    # If include paths are specified, use them directly
    if config.include:
        for include_path in config.include:
            full_path = root / include_path
            if full_path.exists() and full_path.is_dir():
                # Check if this directory has indexable files
                result = scan_directory(full_path, config, root, recursive=True)
                if result.files:
                    dirs_to_index.append(full_path)
        return dirs_to_index

    # Otherwise, walk the directory tree
    def walk(current: Path):
        if should_exclude(current, config.exclude, root):
            return

        # Check if this directory has indexable files
        result = scan_directory(current, config, root, recursive=False)  # Don't recurse here
        if result.files:
            dirs_to_index.append(current)

        # Recurse into subdirectories
        for subdir in result.subdirs:
            if not should_exclude(subdir, config.exclude, root):
                walk(subdir)

    walk(root)
    return dirs_to_index