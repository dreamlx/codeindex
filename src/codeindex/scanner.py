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


LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "php": [".php", ".phtml"],
}


def get_language_extensions(languages: list[str]) -> set[str]:
    """Get file extensions for specified languages."""
    extensions = set()
    for lang in languages:
        extensions.update(LANGUAGE_EXTENSIONS.get(lang, []))
    return extensions


def should_exclude(path: Path, exclude_patterns: list[str], base_path: Path) -> bool:
    """Check if path matches any exclude pattern."""
    # Resolve both paths to handle symlinks (e.g., /var -> /private/var on macOS)
    rel_path = str(path.resolve().relative_to(base_path.resolve()))

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

    If config.include is specified, recursively finds all subdirectories
    with indexable files under those paths.
    Otherwise, walks the entire directory tree.

    Args:
        root: Root directory to start from
        config: Configuration object

    Returns:
        List of directory paths to index
    """
    dirs_to_index: list[Path] = []

    def walk_directory(current: Path):
        """Recursively walk a directory and collect all dirs with files."""
        if should_exclude(current, config.exclude, root):
            return

        # Check if this directory has indexable files (non-recursive scan)
        has_files = False
        for item in current.iterdir():
            if item.is_file():
                if item.suffix == ".py" and "python" in config.languages:
                    has_files = True
                    break
                elif item.suffix in (".php", ".phtml") and "php" in config.languages:
                    has_files = True
                    break

        if has_files:
            dirs_to_index.append(current)

        # Recurse into subdirectories
        for item in sorted(current.iterdir()):
            if item.is_dir() and not should_exclude(item, config.exclude, root):
                walk_directory(item)

    # If include paths are specified, walk each one recursively
    if config.include:
        for include_path in config.include:
            full_path = root / include_path
            if full_path.exists() and full_path.is_dir():
                walk_directory(full_path)
        return dirs_to_index

    # Otherwise, walk the entire directory tree from root
    walk_directory(root)
    return dirs_to_index
