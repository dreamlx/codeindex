"""Bottom-up hierarchical processing for codeindex."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Set, Tuple

from rich.console import Console

from .config import Config
from .scanner import find_all_directories, scan_directory
from .smart_writer import SmartWriter, determine_level

console = Console()


@dataclass
class DirectoryInfo:
    """Information about a directory in the hierarchy."""
    path: Path
    level: int  # 0 = deepest, numbers increase upward
    children: Set[Path]  # Directories directly contained
    parent: Path | None
    has_files: bool
    scan_result = None  # Will hold scan result
    readmes_below: Set[Path]  # README_AI.md files in subdirectories


def build_directory_hierarchy(
    directories: List[Path],
) -> Tuple[Dict[Path, DirectoryInfo], List[Path]]:
    """
    Build directory hierarchy from bottom up.

    Returns:
        - dict mapping paths to DirectoryInfo
        - list of root directories (top level)
    """
    # Sort by depth (deepest first)
    sorted_dirs = sorted(directories, key=lambda p: len(p.parts), reverse=True)

    dir_info = {}
    roots = []

    # First pass: create all nodes
    for dir_path in sorted_dirs:
        info = DirectoryInfo(
            path=dir_path,
            level=0,  # Will be calculated
            children=set(),
            parent=None,
            has_files=False,
            readmes_below=set()
        )
        dir_info[dir_path] = info

    # Second pass: establish relationships
    for dir_path, info in dir_info.items():
        # Find parent relationship
        parent_path = dir_path.parent
        if parent_path in dir_info:
            info.parent = parent_path
            dir_info[parent_path].children.add(dir_path)
        else:
            roots.append(dir_path)

    # Calculate levels bottom-up
    def calculate_level(path: Path) -> int:
        info = dir_info[path]
        if not info.children:
            info.level = 0
            return 0

        max_child_level = max(calculate_level(child) for child in info.children)
        info.level = max_child_level + 1
        return info.level

    for root in roots:
        calculate_level(root)

    return dir_info, roots


def create_processing_batches(
    dir_info: Dict[Path, DirectoryInfo], max_workers: int
) -> List[List[Path]]:
    """
    Create batches for parallel processing.

    All directories at the same level can be processed in parallel.
    """
    level_groups = defaultdict(list)

    for path, info in dir_info.items():
        if info.has_files:  # Only include directories that need processing
            level_groups[info.level].append(path)

    # Create batches from level groups (deeper levels first)
    batches = []
    for level in sorted(level_groups.keys()):
        dirs_at_level = level_groups[level]

        # Split into batches of max_workers
        for i in range(0, len(dirs_at_level), max_workers):
            batch = dirs_at_level[i:i + max_workers]
            batches.append(batch)

    return batches


def process_directory_batch(
    batch: List[Path],
    config: Config,
    use_fallback: bool = False,
    quiet: bool = False,
    timeout: int = 120,
    root_path: Path = None,
) -> Dict[Path, bool]:
    """
    Process a batch of directories in parallel.

    Returns dict mapping path to success boolean.
    """
    import concurrent.futures

    results = {}

    def process_single(path: Path) -> Tuple[Path, bool]:
        try:
            # Use smart processing with level detection
            return path, process_normal(path, config, use_fallback, quiet, timeout, root_path)
        except Exception as e:
            if not quiet:
                console.print(f"[yellow]⚠ Skipping {path.name}: {e}[/yellow]")
            return path, False

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as executor:
        futures = {executor.submit(process_single, path): path for path in batch}

        for future in concurrent.futures.as_completed(futures):
            path, success = future.result()
            results[path] = success

    return results


# Global variable to hold directory info (should be passed as parameter in real implementation)
dir_info = None


def process_normal(
    path: Path,
    config: Config,
    use_fallback: bool,
    quiet: bool,
    timeout: int,
    root_path: Path = None,
) -> bool:
    """Process a single directory with smart level detection."""
    # Scan directory
    if not quiet:
        console.print(f"  [dim]→ {path.name}: scanning...[/dim]")

    scan_result = scan_directory(path, config)

    # Parse files
    from .parallel import parse_files_parallel
    parse_results = []
    if scan_result.files:
        parse_results = parse_files_parallel(scan_result.files, config, quiet)

    # Check if this directory has README_AI.md from children
    child_dirs = []
    if path in dir_info and dir_info[path].readmes_below:
        child_dirs = list(dir_info[path].readmes_below)

    # Determine appropriate level
    has_children = bool(child_dirs)
    if root_path is None:
        root_path = path
    level = determine_level(path, root_path, has_children, config.indexing)

    if not quiet:
        console.print(
            f"  [dim]→ {path.name}: generating [{level}] README "
            f"with {len(child_dirs)} subdirs...[/dim]"
        )

    # Use smart writer
    writer = SmartWriter(config.indexing)
    write_result = writer.write_readme(
        dir_path=path,
        parse_results=parse_results,
        level=level,
        child_dirs=child_dirs,
        output_file=config.output_file,
    )

    if write_result.truncated and not quiet:
        size_kb = write_result.size_bytes // 1024
        console.print(
            f"  [yellow]⚠ {path.name}: README truncated to {size_kb}KB[/yellow]"
        )

    return write_result.success


def process_with_children(
    path: Path, config: Config, use_fallback: bool, quiet: bool, timeout: int
) -> bool:
    """Process a directory that has children, aggregating their information."""
    # This would be similar process_normal but with child aggregation
    return process_normal(path, config, use_fallback, quiet, timeout)


def scan_directories_hierarchical(
    root: Path,
    config: Config,
    max_workers: int = 8,
    use_fallback: bool = True,
    quiet: bool = False,
    timeout: int = 120
) -> bool:
    """
    Main function for hierarchical directory scanning.

    Returns True if processing was successful overall.
    """
    global dir_info

    # Step 1: Find all directories
    directories = find_all_directories(root, config)

    if not directories:
        if not quiet:
            console.print("[yellow]No directories to process[/yellow]")
        return True

    # Step 2: Scan files to determine which directories need processing
    if not quiet:
        console.print("[bold]🔍 Building directory hierarchy...[/bold]")

    for dir_path in directories:
        scan_result = scan_directory(dir_path, config)
        _ = bool(scan_result.files)  # Check if directory has files

        # Update dir_info after it's built
        # (This would need restructuring in real implementation)
        pass

    # Step 3: Build hierarchy
    dir_info, roots = build_directory_hierarchy(directories)

    # Mark directories that have files
    for dir_path in directories:
        scan_result = scan_directory(dir_path, config)
        if dir_path in dir_info:
            dir_info[dir_path].has_files = bool(scan_result.files)
            dir_info[dir_path].scan_result = scan_result

        # Update parent-child relationship for README tracking
        parent_path = dir_path.parent
        if parent_path in dir_info:
            dir_info[parent_path].readmes_below.add(dir_path)

    # Step 4: Create processing batches
    if not quiet:
        console.print("[bold]📦 Creating processing batches...[/bold]")

    batches = create_processing_batches(dir_info, max_workers)

    if not quiet:
        total_dirs = sum(len(batch) for batch in batches)
        console.print(f"[green]✓ {total_dirs} directories in {len(batches)} levels/batches[/green]")

    # Step 5: Process batches
    global_processed = 0
    for i, batch in enumerate(batches):
        if not quiet:
            level = dir_info[batch[0]].level if batch else 0
            console.print(f"\n[bold]Level {level} - Batch {i+1}/{len(batches)}[/bold]")

        results = process_directory_batch(
            batch, config, use_fallback, quiet, timeout, root_path=root
        )

        for path, success in results.items():
            if success:
                global_processed += 1
            elif not quiet:
                console.print(f"[yellow]⚠ Skipped: {path.name}[/yellow]")

    if not quiet:
        console.print(f"\n[green]✓ Processed {global_processed}/{total_dirs} directories[/green]")

    return global_processed > 0


def generate_enhanced_fallback_readme(
    dir_path: Path,
    parse_results: list,
    child_readmes: List[Path],
    output_file: str = "README_AI.md"
):
    """
    Generate enhanced fallback README that includes child directory summaries.
    """
    from datetime import datetime

    from .writer import format_imports_for_prompt, format_symbols_for_prompt

    output_path = dir_path / output_file

    # Basic directory info
    lines = [
        f"<!-- Generated by codeindex (hierarchical) at {datetime.now().isoformat()} -->",
        "",
        f"# {dir_path.name}",
        ""
    ]

    # File statistics
    files_count = len(parse_results)
    symbols_count = sum(len(r.symbols) for r in parse_results)

    lines.extend([
        "## Overview",
        f"- **Files**: {files_count}",
        f"- **Symbols**: {symbols_count}",
        f"- **Subdirectories**: {len(child_readmes)}",
        ""
    ])

    # Child directories section
    if child_readmes:
        lines.extend([
            "## Subdirectories",
            ""
        ])

        for child_path in sorted(child_readmes):
            child_name = child_path.name
            child_readme = child_path / output_file

            # Extract brief description from child README if it exists
            description = "Module directory"
            if child_readme.exists():
                try:
                    content = child_readme.read_text()
                    # Look for first non-heading line
                    for line in content.split('\n')[2:10]:  # Skip title and header
                        line = line.strip()
                        if line and not line.startswith('#'):
                            description = line[:100]
                            break
                except Exception:
                    pass

            lines.append(f"- **{child_name}** - {description}")

        lines.append("")

    # Local files and symbols
    if parse_results:
        lines.extend([
            "## Files",
            ""
        ])

        # Group by subdirectory
        files_by_subdir = defaultdict(list)
        for result in parse_results:
            if not result.error:
                rel_path = result.path.relative_to(dir_path)
                if rel_path.parent != Path('.'):
                    files_by_subdir[str(rel_path.parent)].append(result)
                else:
                    files_by_subdir['.'].append(result)

        for subdir in sorted(files_by_subdir.keys()):
            if subdir == '.':
                # Files in root
                for result in files_by_subdir[subdir]:
                    lines.append(f"- {result.path.name} ({len(result.symbols)} symbols)")
            else:
                # Files in subdirectory
                lines.append(f"- **{subdir}/**")
                for result in files_by_subdir[subdir]:
                    lines.append(f"  - {result.path.name} ({len(result.symbols)} symbols)")

        lines.extend([
            "",
            "## Symbols",
            ""
        ])

        # Add symbols
        lines.append(format_symbols_for_prompt(parse_results))

        # Add dependencies if any
        all_imports = []
        for result in parse_results:
            all_imports.extend(result.imports)

        if all_imports:
            lines.extend([
                "",
                "## Dependencies",
                ""
            ])
            lines.append(format_imports_for_prompt(parse_results))

    # Write file
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return type('WriteResult', (), {
            'path': output_path,
            'success': True,
            'error': ""
        })()
    except Exception as e:
        return type('WriteResult', (), {
            'path': output_path,
            'success': False,
            'error': str(e)
        })()
