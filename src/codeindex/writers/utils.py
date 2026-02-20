"""Shared pure utility functions for README generation.

These functions were extracted from SmartWriter's private methods.
They are stateless and take explicit parameters instead of using self.
"""

import re
from collections import defaultdict
from fnmatch import fnmatch
from pathlib import Path

from ..config import IndexingConfig
from ..framework_detect import RouteInfo
from ..parser import ParseResult, Symbol


def collect_recursive_stats(
    child_dirs: list[Path], output_file: str = "README_AI.md"
) -> dict:
    """Aggregate file/symbol counts from child README_AI.md files."""
    total_files = 0
    total_symbols = 0
    for child in child_dirs:
        readme = child / output_file
        if readme.exists():
            try:
                content = readme.read_text(encoding="utf-8", errors="replace")
                files_match = re.search(r'\*\*Files\*\*:\s*(\d+)', content)
                symbols_match = re.search(r'\*\*Symbols\*\*:\s*(\d+)', content)
                if files_match:
                    total_files += int(files_match.group(1))
                if symbols_match:
                    total_symbols += int(symbols_match.group(1))
            except Exception:
                pass
    return {"files": total_files, "symbols": total_symbols}


def extract_module_description(
    dir_path: Path, output_file: str = "README_AI.md"
) -> str:
    """Extract brief description from a child module's README.

    Strategies (in order):
    1. Parse structured stats (Files/Symbols) + class names from README_AI.md
    2. Find first free-text line (non-header, non-list)
    3. Fallback to "Module directory"
    """
    readme_path = dir_path / output_file
    if not readme_path.exists():
        return "Module directory"

    try:
        content = readme_path.read_text(encoding="utf-8", errors="replace")

        # Strategy 1: Structured info from codeindex output
        files_match = re.search(r'\*\*Files\*\*:\s*(\d+)', content)
        symbols_match = re.search(r'\*\*Symbols\*\*:\s*(\d+)', content)
        classes = re.findall(r'\*\*class\*\*\s+`(?:class\s+)?(\w+)`', content)

        parts = []
        if files_match:
            parts.append(f"{files_match.group(1)} files")
        if symbols_match:
            parts.append(f"{symbols_match.group(1)} symbols")
        if classes:
            top_classes = classes[:5]
            class_str = f"classes: {', '.join(top_classes)}"
            if len(classes) > 5:
                class_str += f" +{len(classes) - 5} more"
            parts.append(class_str)

        if parts:
            return " | ".join(parts)

        # Strategy 2: First free-text line
        lines = content.split("\n")
        for line in lines[2:15]:
            line = line.strip()
            if line and not line.startswith("#") and not line.startswith("<!--"):
                if line.startswith("-"):
                    continue
                return line[:80]

        return "Module directory"
    except Exception:
        return "Module directory"


def collect_top_symbols(
    child_dirs: list[Path],
    output_file: str = "README_AI.md",
    limit: int = 15,
) -> list[tuple[str, str, str]]:
    """Collect top symbols from child READMEs.

    Returns list of (name, kind, module) tuples.
    """
    symbols: list[tuple[str, str, str]] = []
    for child in child_dirs:
        for readme in child.rglob(output_file):
            try:
                content = readme.read_text(encoding="utf-8", errors="replace")
                module = readme.parent.name
                for m in re.finditer(
                    r'\*\*(class|function)\*\*\s+`(?:\w+\s+)?(\w+)`', content
                ):
                    kind, name = m.group(1), m.group(2)
                    symbols.append((name, kind, module))
            except Exception:
                pass

    # Deduplicate, return top N
    seen: set[str] = set()
    result: list[tuple[str, str, str]] = []
    for name, kind, module in symbols:
        if name not in seen:
            seen.add(name)
            result.append((name, kind, module))
        if len(result) >= limit:
            break
    return result


def group_files(
    results: list[ParseResult], config: IndexingConfig
) -> dict[str, list[ParseResult]]:
    """Group files by suffix pattern."""
    if not config.grouping.enabled:
        return {"_ungrouped": results}

    grouped = defaultdict(list)
    ungrouped = []

    for result in results:
        filename = result.path.stem  # Without extension
        matched = False

        for pattern in config.grouping.patterns.keys():
            if filename.endswith(pattern):
                grouped[pattern].append(result)
                matched = True
                break

        if not matched:
            ungrouped.append(result)

    # Sort groups by pattern order, add ungrouped at end
    ordered = {}
    for pattern in config.grouping.patterns.keys():
        if pattern in grouped:
            ordered[pattern] = grouped[pattern]

    if ungrouped:
        ordered["_ungrouped"] = ungrouped

    return ordered


def filter_symbols(
    symbols: list[Symbol], config: IndexingConfig
) -> list[Symbol]:
    """Filter symbols based on visibility and exclusion patterns."""
    filtered = []

    for symbol in symbols:
        # Check exclusion patterns
        name = symbol.name.split("::")[-1].split(".")[-1]
        excluded = False
        for pattern in config.symbols.exclude_patterns:
            if fnmatch(name, pattern):
                excluded = True
                break

        if excluded:
            continue

        # Check visibility (from signature)
        sig_lower = symbol.signature.lower()
        if config.symbols.include_visibility:
            # If visibility config exists, check it
            has_visibility = any(
                v in sig_lower for v in ["public", "private", "protected"]
            )
            if has_visibility:
                visible = any(
                    v in sig_lower for v in config.symbols.include_visibility
                )
                if not visible:
                    continue

        filtered.append(symbol)

    return filtered


def get_key_symbols(symbols: list[Symbol]) -> list[Symbol]:
    """Get key symbols (classes and main functions) from a file."""
    key = []

    # Add all classes
    for s in symbols:
        if s.kind == "class":
            key.append(s)

    # Add public functions/methods
    for s in symbols:
        if s.kind in ("function", "method"):
            sig_lower = s.signature.lower()
            if "public" in sig_lower or s.kind == "function":
                key.append(s)

    return key[:5]  # Limit to 5 key symbols


def format_route_table(
    routes: list[RouteInfo], framework: str = "thinkphp"
) -> list[str]:
    """Format route information as Markdown table with line numbers.

    Args:
        routes: List of RouteInfo objects
        framework: Framework name for title (e.g., "thinkphp", "laravel")

    Returns:
        List of markdown lines for the route table
    """
    if not routes:
        return []

    # Format framework name with proper casing
    framework_display = {
        "thinkphp": "ThinkPHP",
        "laravel": "Laravel",
        "django": "Django",
        "fastapi": "FastAPI",
    }.get(framework.lower(), framework.title())

    lines = [
        f"## Routes ({framework_display})",
        "",
        "| URL | Controller | Action | Location | Description |",
        "|-----|------------|--------|----------|-------------|",
    ]

    # Display up to 30 routes
    for route in routes[:30]:
        # Use route.location property (handles file:line format)
        location = f"`{route.location}`" if route.location else ""

        # Get description (already truncated to 60 chars in extractor)
        description = route.description if route.description else ""

        lines.append(
            f"| `{route.url}` | {route.controller} | "
            f"{route.action} | {location} | {description} |"
        )

    # Show "more" indicator if there are additional routes
    if len(routes) > 30:
        remaining = len(routes) - 30
        lines.append(f"| ... | _{remaining} more routes_ | | | |")

    lines.extend(["", ""])
    return lines


def truncate_content(content: str, max_size: int) -> tuple[str, bool]:
    """Truncate content to fit within size limit."""
    content_bytes = content.encode('utf-8')
    if len(content_bytes) <= max_size:
        return content, False

    # Find a good truncation point
    truncated = content_bytes[:max_size - 200].decode('utf-8', errors='ignore')

    # Try to truncate at a section boundary
    last_section = truncated.rfind("\n## ")
    if last_section > len(truncated) // 2:
        truncated = truncated[:last_section]

    # Add truncation notice
    truncated += (
        "\n\n---\n"
        "_Content truncated due to size limit. "
        "See individual module README files for details._\n"
    )

    return truncated, True
