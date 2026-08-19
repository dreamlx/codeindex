"""Directory scanner for codeindex."""

import fnmatch
from collections import Counter
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

    @property
    def java_files(self) -> list[Path]:
        """Get Java files only."""
        return [f for f in self.files if f.suffix == ".java"]

    @property
    def typescript_files(self) -> list[Path]:
        """Get TypeScript files only."""
        return [f for f in self.files if f.suffix in (".ts", ".tsx")]

    @property
    def javascript_files(self) -> list[Path]:
        """Get JavaScript files only."""
        return [f for f in self.files if f.suffix in (".js", ".jsx")]


LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "php": [".php", ".phtml"],
    "java": [".java"],
    "typescript": [".ts", ".tsx"],
    "javascript": [".js", ".jsx"],
    "swift": [".swift"],
    # Objective-C: match parser.FILE_EXTENSIONS exactly (.h + .m, not .mm —
    # the parser does not dispatch .mm). Keep these two maps in lockstep;
    # tests/test_scanner_swift_objc_extensions.py guards the drift (GH #80).
    "objc": [".h", ".m"],
}


# Derived inverse of LANGUAGE_EXTENSIONS (extension → config language). Single
# source of truth for both directions: add a language once to
# LANGUAGE_EXTENSIONS and detection (skill_helpers.detect_project_languages)
# stays in lockstep — it cannot drift to include an unparseable language
# (GH #112: the old skill_helpers table had drifted to carry .go/.rs).
EXTENSION_TO_LANGUAGE = {
    ext: lang for lang, exts in LANGUAGE_EXTENSIONS.items() for ext in exts
}


def get_language_extensions(languages: list[str]) -> set[str]:
    """Get file extensions for specified languages."""
    extensions = set()
    for lang in languages:
        extensions.update(LANGUAGE_EXTENSIONS.get(lang, []))
    return extensions


def is_pass_through(dir_path: Path, config: Config) -> bool:
    """Check if directory is a pass-through (no code files, single subdirectory).

    A pass-through directory has:
    1. No code files of its own (only subdirectories/non-code files)
    2. Exactly one non-excluded subdirectory

    This avoids redundant README_AI.md generation in deep directory structures
    like Java Maven: src/main/java/com/zcyl/module/

    Args:
        dir_path: Directory path to check
        config: Configuration with language and exclude settings

    Returns:
        True if directory is a pass-through, False otherwise
    """
    supported_exts = get_language_extensions(config.languages)

    try:
        items = list(dir_path.iterdir())
    except (PermissionError, OSError):
        return False

    # Check for code files
    code_files = [
        item for item in items
        if item.is_file() and item.suffix in supported_exts
    ]
    if code_files:
        return False

    # Count non-excluded subdirectories
    subdirs = [
        item for item in items
        if item.is_dir() and not should_exclude(item, config.exclude, dir_path)
    ]

    return len(subdirs) == 1


def should_exclude(path: Path, exclude_patterns: list[str], base_path: Path) -> bool:
    """Check if path matches any exclude pattern.

    Optimized for Windows path length limitations by using relative paths
    when possible, falling back to absolute paths only when necessary.

    Args:
        path: Path to check for exclusion
        exclude_patterns: List of glob patterns to match against
        base_path: Base path for relative path calculation

    Returns:
        True if path matches any exclude pattern, False otherwise
    """
    # Try relative path first (Windows path length optimization)
    # This avoids unnecessary .resolve() calls that make paths much longer
    try:
        rel_path = str(path.relative_to(base_path))
    except ValueError:
        # Fall back to absolute if paths are incompatible
        # (e.g., different drives on Windows, or one is not subpath of other)
        try:
            # Resolve both paths to handle symlinks (e.g., /var -> /private/var on macOS)
            rel_path = str(path.resolve().relative_to(base_path.resolve()))
        except ValueError:
            # Paths are completely incompatible, use string comparison
            rel_path = str(path)

    # Normalize path separators for consistent pattern matching across platforms
    rel_path = rel_path.replace("\\", "/")

    for pattern in exclude_patterns:
        # Direct pattern match
        if fnmatch.fnmatch(rel_path, pattern):
            return True
        if fnmatch.fnmatch(str(path), pattern):
            return True

        # Enhanced ** handling: ** should match 0 or more path segments
        if "**" in pattern:
            # Try matching with ** as a wildcard for any number of segments
            simple_pattern = pattern.replace("**", "*")
            if fnmatch.fnmatch(rel_path, simple_pattern):
                return True

            # Check if path contains any component that matches the pattern
            # e.g., **/__pycache__/** should match any path containing __pycache__
            # Extract the core pattern (remove leading/trailing **)
            core_pattern = pattern.strip("*/")
            if core_pattern and core_pattern in rel_path.split("/"):
                return True

            # Also check if rel_path matches when ** is treated as zero segments
            # e.g., **/__pycache__/** should match __pycache__/*, __pycache__, etc.
            if pattern.startswith("**/"):
                suffix_pattern = pattern[3:]  # Remove leading **/
                # Check if rel_path matches the suffix pattern
                if fnmatch.fnmatch(rel_path, suffix_pattern):
                    return True
                # Also match just the directory name without trailing /**
                if suffix_pattern.endswith("/**"):
                    dir_pattern = suffix_pattern[:-3]  # Remove trailing /**
                    if fnmatch.fnmatch(rel_path, dir_pattern):
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
            # Filter by language/extension using unified extension map
            if item.suffix in get_language_extensions(config.languages):
                files.append(item)
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
        supported_exts = get_language_extensions(config.languages)
        has_files = any(
            item.is_file() and item.suffix in supported_exts
            for item in current.iterdir()
        )

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


# Walk-skip set shared by the diagnostic and the scanner — common noise dirs
# we should never count when classifying a project's file types.
_DIAGNOSTIC_SKIP_DIRS = {
    "node_modules",
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    ".tox",
    ".eggs",
    "dist",
    "build",
    # GH #156 D3: Android .gradle/<hash>/.../sources/*.java are AGP-generated
    # accessor classes (pure build cache) — don't let them inflate the count.
    ".gradle",
}

# Fingerprint walk skips these on top of the diagnostic set. Pods/vendor are
# where the stray ``.py`` files that mask a non-Python repo come from (RN
# ``ios/Pods/<Pod>/build.py``, vendored C extensions), so excluding them keeps
# the fingerprint honest about the repo's *own* language. Mirrors loomgraph's
# ``_FINGERPRINT_SKIP_DIRS`` (loomgraph#161) — kept in lockstep so both tools
# agree on what "the repo's main language" means.
_FINGERPRINT_SKIP_DIRS = _DIAGNOSTIC_SKIP_DIRS | {"Pods", "vendor"}
# Below this many files a language isn't "the repo's main language missed by
# config" — just stray tool scripts. Keeps small repos + the codeindex self-dogfood
# (fixtures in tests/) warning-free. Mirrors loomgraph's threshold.
_FINGERPRINT_MIN_FILES = 10


def diagnose_language_mismatch(root: Path, config: Config) -> dict:
    """When ``find_all_directories`` returns empty, figure out why.

    Walks the include roots, counts file extensions actually present, and
    compares them against ``config.languages``'s expected extensions and the
    canonical ``LANGUAGE_EXTENSIONS`` map (which covers every language the
    scanner knows). Used by ``list-dirs`` to turn silent empty results into
    actionable error messages (GH #74).

    Returns:
        Dict with keys:
            - ``extensions_present``: Counter[str] — extension → file count
              across the include roots, top-skipped.
            - ``configured_languages``: list[str] — ``config.languages``.
            - ``configured_extensions``: set[str] — extensions the current
              ``languages`` setting accepts.
            - ``candidate_languages``: list[str] — sorted languages NOT in
              ``config.languages`` whose extensions appear in the project.
              These are what the user likely wants to add.
    """
    extension_counts: Counter[str] = Counter()

    include_roots = (
        [root / p for p in config.include] if config.include else [root]
    )
    for include_root in include_roots:
        if not include_root.exists() or not include_root.is_dir():
            continue
        for path in include_root.rglob("*"):
            # Skip files under noisy dirs (node_modules etc.) so the
            # diagnostic doesn't suggest "you have js" when it's all
            # vendored.
            if any(part in _DIAGNOSTIC_SKIP_DIRS for part in path.parts):
                continue
            # GH #156 D1: honor config.exclude so a user can suppress vendored
            # / reference dirs (e.g. C++ firmware headers under docs/_assets/)
            # instead of having them drive false "Add X" suggestions. base_path
            # is ``root`` (exclude patterns are project-relative), matching the
            # real scanner's ``should_exclude`` call sites.
            if should_exclude(path, config.exclude, root):
                continue
            if path.is_file():
                ext = path.suffix.lower()
                if ext:
                    extension_counts[ext] += 1

    configured_exts = get_language_extensions(config.languages)

    # Which languages NOT in config would cover the seen extensions?
    candidates: list[str] = []
    for lang, exts in LANGUAGE_EXTENSIONS.items():
        if lang in config.languages:
            continue
        # GH #156 D2: .h is shared by C/C++/ObjC and codeindex ships no C/C++.
        # Require objc's unambiguous indicator (.m) so a C/C++ repo with only
        # .h headers isn't told to add objc (the objc grammar can't parse C++
        # → parse errors, zero entities). Don't mutate LANGUAGE_EXTENSIONS —
        # it drives parse dispatch and is kept in lockstep with the parser.
        if lang == "objc":
            if ".m" in extension_counts:
                candidates.append(lang)
            continue
        if any(ext in extension_counts for ext in exts):
            candidates.append(lang)

    return {
        "extensions_present": extension_counts,
        "configured_languages": list(config.languages),
        "configured_extensions": configured_exts,
        "candidate_languages": sorted(candidates),
    }


def language_mismatch_hint(root: Path, config: Config) -> str | None:
    """Render an actionable diagnostic when no directories would be indexed.

    Single source for the GH #74 / #105 language-mismatch message, shared by
    ``list-dirs`` and ``scan-all`` so both surface the same guidance instead of
    a silent empty result (the footgun: ``languages: [python]`` on a TS repo →
    ``scan-all`` scans nothing and exits 0, indistinguishable from "done").

    Returns:
        A multi-line hint string when source files are present under the
        include roots but their extensions aren't covered by
        ``config.languages``. ``None`` when the include roots are genuinely
        empty (nothing to act on — caller should stay silent).
    """
    diag = diagnose_language_mismatch(root, config)
    present = diag["extensions_present"]
    if not present:
        return None

    top = ", ".join(f"{ext} ({n})" for ext, n in present.most_common(5))
    candidates = diag["candidate_languages"]
    if candidates:
        cand = " / ".join(candidates)
        return (
            "no indexable directories found.\n"
            f"  Configured languages: {diag['configured_languages']}\n"
            f"  Detected file types in include roots: {top}\n"
            f"  Hint: add {cand} to .codeindex.yaml `languages:`\n"
            "        (run: codeindex config explain languages)"
        )
    return (
        "no indexable directories found.\n"
        f"  Configured languages: {diag['configured_languages']}\n"
        "  Files are present but no codeindex-supported language "
        "matches their extensions.\n"
        f"  Top extensions: {top}"
    )


def language_fingerprint_hint(root: Path, config: Config) -> str | None:
    """Detect a repo whose main language isn't in ``config.languages`` (GH #175).

    ``diagnose_language_mismatch`` (above) walks ``config.include`` — by default
    ``[src/, lib/, tests/, examples/]`` — so it's blind to a repo whose real
    source lives elsewhere (a RN app with TS under ``app/``, or a root-level
    project). graph-export with no explicit ``include`` scans the *whole* tree,
    so it sees (and silently under-captures) that source while the diagnose
    hint returns None. This walks the whole tree too, closing that blind spot.

    Advisory only: the caller decides exit code. graph-export treats a hit on a
    0-entity export as data-loss (empty graph → fail-loud, mirroring #147) and
    a hit on a >0-entity export as a partial-graph warning (exit 0).

    Mirrors loomgraph's ``_language_fingerprint_warning`` (loomgraph#161) —
    same threshold, same skip dirs, same prefix ``"language fingerprint:"`` —
    so the two tools emit the same guidance.

    Returns:
        A ``"language fingerprint: …"`` string when a supported language not in
        ``config.languages`` has ≥ ``_FINGERPRINT_MIN_FILES`` source files AND
        more than the configured languages cover combined (so a 2-file stray
        ``.py`` can't mask a TS repo, but a mixed repo isn't warned when its
        configured languages already cover the bulk). ``None`` otherwise.
    """
    ext_to_lang = {ext: lang for lang, exts in LANGUAGE_EXTENSIONS.items() for ext in exts}
    configured = set(config.languages)

    counts: Counter[str] = Counter()
    for path in root.rglob("*"):
        if any(part in _FINGERPRINT_SKIP_DIRS for part in path.parts):
            continue
        if should_exclude(path, config.exclude, root):
            continue
        if path.is_file():
            lang = ext_to_lang.get(path.suffix.lower())
            if lang:
                counts[lang] += 1

    if not counts:
        return None

    covered = sum(counts.get(lang, 0) for lang in configured)
    for lang, n in counts.most_common():
        if lang in configured or n < _FINGERPRINT_MIN_FILES or n <= covered:
            continue
        return (
            f"language fingerprint: detected {n} {lang} source files, none "
            f"indexed — add '{lang}' to `languages` in .codeindex.yaml "
            f"(effective languages: {', '.join(sorted(configured))})"
        )
    return None
