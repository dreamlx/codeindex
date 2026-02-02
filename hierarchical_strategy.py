#!/usr/bin/env python3
"""Advanced parallel processing strategy for codeindex."""

from pathlib import Path
from typing import List, Dict, Set
from dataclasses import dataclass
from rich.console import Console

console = Console()


@dataclass
class DirectoryNode:
    """Represents a directory in the processing hierarchy."""
    path: Path
    level: int  # 0 = leaf (smallest), higher = parent directories
    children: List['DirectoryNode']
    parent: 'DirectoryNode' | None
    has_files: bool
    dependencies: Set[Path]  # Directories this one depends on


def build_directory_tree(
    directories: List[Path],
    config
) -> List[DirectoryNode]:
    """
    Build a hierarchical tree of directories.

    Leaf directories (with no subdirectories that also contain files) get priority.
    """
    # Sort directories by depth (deepest first)
    sorted_dirs = sorted(directories, key=lambda p: len(p.parts), reverse=True)

    # Track processed directories
    node_map: Dict[Path, DirectoryNode] = {}
    root_nodes: List[DirectoryNode] = []

    for dir_path in sorted_dirs:
        # Check if this directory has indexable files
        scan_result = scan_directory(dir_path, config)
        has_files = bool(scan_result.files)

        # Create node
        node = DirectoryNode(
            path=dir_path,
            level=0,  # Will be calculated
            children=[],
            parent=None,
            has_files=has_files,
            dependencies=set()
        )
        node_map[dir_path] = node

        # Find parent relationship
        parent_path = dir_path.parent
        if parent_path in node_map:
            node.parent = node_map[parent_path]
            node.parent.children.append(node)
            node.level = node.parent.level + 1
        else:
            root_nodes.append(node)

    # Calculate levels bottom-up
    def calculate_levels(node: DirectoryNode) -> int:
        if not node.children:
            return 0

        max_child_level = max(calculate_levels(child) for child in node.children)
        return max_child_level + 1

    for root in root_nodes:
        calculate_levels(root)

    return root_nodes


def detect_dependencies(
    nodes: List[DirectoryNode],
    config
) -> None:
    """
    Detect dependencies between directories based on imports/includes.

    A directory depends on another if it imports files from it.
    """
    for node in nodes:
        if not node.has_files:
            continue

        # Parse files in this directory
        scan_result = scan_directory(node.path, config)
        parse_results = [parse_file(f) for f in scan_result.files]

        # Extract import patterns
        imported_paths = set()
        for result in parse_results:
            for imp in result.imports:
                # Try to resolve import to a directory
                import_path = resolve_import_to_directory(imp.module, node.path)
                if import_path:
                    imported_paths.add(import_path)

        # Set dependencies
        node.dependencies = imported_paths


def create_processing_batches(
    nodes: List[DirectoryNode],
    max_parallel: int
) -> List[List[DirectoryNode]]:
    """
    Create batches for parallel processing respecting dependencies.

    Returns batches in order they should be processed.
    """
    # Group by level (same level = can be parallel)
    level_groups: Dict[int, List[DirectoryNode]] = {}

    def collect_by_level(node: DirectoryNode):
        if node.level not in level_groups:
            level_groups[node.level] = []
        level_groups[node.level].append(node)

        for child in node.children:
            collect_by_level(child)

    for root in nodes:
        collect_by_level(root)

    # Create sorted batches
    batches = []
    for level in sorted(level_groups.keys()):
        dirs_at_level = level_groups[level]

        # Create sub-batches of size max_parallel
        for i in range(0, len(dirs_at_level), max_parallel):
            batch = dirs_at_level[i:i + max_parallel]
            batches.append(batch)

    return batches


def hierarchical_scan(
    root_dir: Path,
    config,
    max_parallel: int = 8
):
    """
    Perform hierarchical parallel scan.

    1. Build directory tree
    2. Detect dependencies
    3. Create processing batches
    4. Execute in order
    """
    console.print("[bold]🔍 Building directory hierarchy...[/bold]")

    # Find all directories
    all_dirs = find_all_directories(root_dir, config)

    # Build tree structure
    tree_nodes = build_directory_tree(all_dirs, config)

    # Detect dependencies
    console.print("[bold]🔗 Analyzing dependencies...[/bold]")
    detect_dependencies(tree_nodes, config)

    # Create processing batches
    console.print("[bold]📦 Creating processing batches...[/bold]")
    batches = create_processing_batches(tree_nodes, max_parallel)

    # Print summary
    console.print(f"[green]✓ Found {len(all_dirs)} directories in {len(batches)} batches[/green]")

    for i, batch in enumerate(batches):
        level = batch[0].level if batch else 0
        console.print(f"  Batch {i+1}: Level {level}, {len(batch)} directories")

    return batches


def resolve_import_to_directory(import_module: str, current_dir: Path) -> Path | None:
    """
    Resolve an import statement to a directory path.

    This is a simplified version - real implementation would need
    language-specific import resolution logic.
    """
    # Simple heuristic: look for matching directories
    parts = import_module.strip().replace('\\', '/').split('/')

    # Walk up from current directory looking for matches
    search_dir = current_dir
    while search_dir != search_dir.parent:
        candidate = search_dir
        for part in parts:
            candidate = candidate / part

        if candidate.exists() and candidate.is_dir():
            return candidate

        search_dir = search_dir.parent

    return None