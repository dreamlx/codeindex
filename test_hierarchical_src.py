#!/usr/bin/env python3
"""Test hierarchical processing on current codeindex project with proper config."""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codeindex.config import Config
from codeindex.scanner import find_all_directories, scan_directory
from codeindex.hierarchical import build_directory_hierarchy, create_processing_batches
from rich.console import Console

console = Console()

def test_codeindex_with_subdirs():
    """Test on codeindex project but look at subdirectories."""
    here = Path(__file__).parent

    # Load config
    config = Config.load()  # Load actual config from .codeindex.yaml

    console.print("[bold]🔍 Testing on codeindex project with subdirectories[/bold]")
    console.print(f"Root: {here}")
    console.print(f"Include patterns: {config.include}")

    # Only check src/ directory for more realistic hierarchy
    src_dir = here / "src" / "codeindex"

    if not src_dir.exists():
        console.print(f"[red]❌ {src_dir} not found[/red]")
        return

    console.print(f"\n📂 Analyzing src/codeindex...")

    # Create a temporary config that includes all subdirs
    temp_config = Config()
    temp_config.languages = ["python"]
    temp_config.include = ["*"]  # Include everything under src/codeindex
    temp_config.exclude = ["**/__pycache__/**", "**/venv/**", "**/.git/**"]

    # Find directories with Python files in src/codeindex
    directories = find_all_directories(src_dir, temp_config)

    console.print(f"\n📊 Found {len(directories)} directories with Python files:")
    for d in directories:
        rel = d.relative_to(src_dir)
        scan_result = scan_directory(d, temp_config, d.parent, recursive=False)
        console.print(f"  - {rel}: {len(scan_result.files)} files")

    # Build hierarchy
    if directories:
        console.print("\n[bold]🏗️ Building hierarchy...[/bold]")
        dir_info, roots = build_directory_hierarchy(directories)

        # Show levels
        level_counts = {}
        for info in dir_info.values():
            level_counts[info.level] = level_counts.get(info.level, 0) + 1

        console.print(f"[green]✓ Hierarchy built:[/green]")
        console.print(f"  Total directories: {len(dir_info)}")
        console.print(f"  Root directories: {len(roots)}")
        console.print(f"  Levels range from {min(level_counts.keys())} to {max(level_counts.keys())}")

        # Show hierarchy
        console.print("\n[bold]📝 Directory tree:[/bold]")
        for root in roots:
            def print_tree(path, level=0):
                info = dir_info[path]
                indent = "  " * level
                if level == 0:
                    console.print(f"{info.path.name}/ (level {info.level})")
                else:
                    prefix = "└── " if level > 0 else ""
                    console.print(f"{indent}{prefix}{info.path.name}/ (level {info.level}, {len(info.children)} children)")

                for child in sorted(info.children, key=lambda p: p.name):
                    if len(info.children) <= 10 or level == 0:  # Limit output
                        print_tree(child, level + 1)

            print_tree(root)

        # Create batches
        console.print("\n[bold]📦 Creating processing batches...[/bold]")
        batches = create_processing_batches(dir_info, max_workers=4)

        console.print(f"[green]✓ {len(batches)} batches:[/green]")
        for i, batch in enumerate(batches[:5]):  # Show first 5 batches
            level = dir_info[batch[0]].level if batch else "N/A"
            console.print(f"  Batch {i+1} (level {level}): {len(batch)} directories")
            if len(batch) <= 3:
                for d in batch:
                    rel = d.relative_to(src_dir)
                    console.print(f"    - {rel}")

def test_full_hierarchical_scan():
    """Test full hierarchical scan."""
    here = Path(__file__).parent

    console.print("\n[bold]🚀 Testing full hierarchical scan on src/codeindex...[/bold]")

    from codeindex.hierarchical import scan_directories_hierarchical

    src_dir = here / "src" / "codeindex"
    if not src_dir.exists():
        console.print(f"[red]❌ {src_dir} not found[/red]")
        return

    # Configure for this directory
    config = Config()
    config.languages = ["python"]
    config.include = ["*"]
    config.exclude = ["**/__pycache__/**"]
    config.parallel_workers = 4

    success = scan_directories_hierarchical(
        src_dir,
        config,
        max_workers=4,
        use_fallback=True,
        quiet=False,
        timeout=60
    )

    console.print(f"\n[{'✓' if success else '✗'} Hierarchical scan {'completed successfully' if success else 'failed'}")

if __name__ == "__main__":
    test_codeindex_with_subdirs()
    test_full_hierarchical_scan()