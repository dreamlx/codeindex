#!/usr/bin/env python3
"""Test hierarchical processing on current codeindex project."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codeindex.config import Config
from codeindex.scanner import find_all_directories
from codeindex.hierarchical import build_directory_hierarchy, create_processing_batches
from rich.console import Console

console = Console()

def test_codeindex_hierarchy():
    """Test on actual codeindex project."""
    here = Path(__file__).parent

    # Load config
    config = Config()
    config.languages = ["python"]  # Only process Python files

    console.print("[bold]🔍 Testing on codeindex project[/bold]")
    console.print(f"Root: {here}")

    # Find all directories with Python files
    directories = find_all_directories(here, config)

    # Filter to a manageable subset for testing
    test_dirs = directories[:10]  # First 10 directories

    console.print(f"\n📊 Found {len(directories)} directories, testing with {len(test_dirs)}:")
    for d in test_dirs:
        rel = d.relative_to(here)
        console.print(f"  - {rel}")

    # Build hierarchy
    console.print("\n[bold]🏗️ Building hierarchy...[/bold]")
    dir_info, roots = build_directory_hierarchy(test_dirs)

    # Show results
    level_counts = {}
    for info in dir_info.values():
        level_counts[info.level] = level_counts.get(info.level, 0) + 1

    console.print(f"\n[green]✓ Hierarchy built:[/green]")
    console.print(f"  Total directories: {len(dir_info)}")
    console.print(f"  Root directories: {len(roots)}")
    console.print(f"  Levels: {sorted(level_counts.keys())}")

    # Show some directory hierarchies
    console.print("\n[bold]📝 Directory relationships:[/bold]")
    for root in roots[:3]:
        console.print(f"\n📁 {root.name} (level {dir_info[root].level})")

        def show_tree(path, indent=0):
            info = dir_info[path]
            prefix = "  " * indent + ("└── " if indent > 0 else "")
            console.print(f"{prefix}{path.name} (level {info.level}, {'✓files' if info.has_files else '✗empty'})")
            for child in sorted(info.children, key=lambda p: p.name):
                show_tree(child, indent + 1)

        for child in sorted(dir_info[root].children, key=lambda p: p.name)[:3]:
            show_tree(child, 1)
            if len(dir_info[root].children) > 3:
                console.print(f"  ... and {len(dir_info[root].children) - 3} more")
                break

    # Create batches
    console.print("\n[bold]📦 Creating processing batches...[/bold]")
    batches = create_processing_batches(dir_info, max_workers=4)

    console.print(f"[green]✓ {len(batches)} batches created:[/green]")
    for i, batch in enumerate(batches):
        level = dir_info[batch[0]].level if batch else 0
        rel_paths = [b.relative_to(here) for b in batch]
        console.print(f"  Batch {i+1} (level {level}): {len(batch)} dirs")
        if len(rel_paths) <= 3:
            for rp in rel_paths:
                console.print(f"    - {rp}")

if __name__ == "__main__":
    test_codeindex_hierarchy()