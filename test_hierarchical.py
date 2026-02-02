#!/usr/bin/env python3
"""Test hierarchical processing."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from codeindex.hierarchical import scan_directories_hierarchical, build_directory_hierarchy
from codeindex.config import Config
from rich.console import Console

console = Console()

def test_hierarchy():
    """Test directory hierarchy building."""

    # Test with PHP project
    php_root = Path("/Users/dreamlinx/Projects/php_admin-main-c59644bb607125803a5d14400b64be9068b82488")
    config = Config()

    print("=== Test: Directory Hierarchy ===")

    # Import find_all_directories
    from codeindex.scanner import find_all_directories

    # Find directories
    directories = find_all_directories(php_root, config)

    # Take first 10 for testing
    test_dirs = directories[:10]

    print(f"Testing with {len(test_dirs)} directories...")

    # Build hierarchy
    dir_info, roots = build_directory_hierarchy(test_dirs)

    print(f"\n📊 Results:")
    print(f"  Total directories: {len(dir_info)}")
    print(f"  Root directories: {len(roots)}")

    # Show levels
    level_counts = {}
    for info in dir_info.values():
        level_counts[info.level] = level_counts.get(info.level, 0) + 1

    print(f"\n📏 Levels found:")
    for level in sorted(level_counts.keys()):
        print(f"  Level {level}: {level_counts[level]} directories")

    # Show some examples
    print(f"\n📝 Example hierarchy:")
    for root in roots[:3]:
        print(f"\nRoot: {root.name}")
        for child in dir_info[root].children:
            print(f"  └── {child.name} (level {dir_info[child].level})")
            for grandchild in dir_info[child].children:
                print(f"      └── {grandchild.name} (level {dir_info[grandchild].level})")

def test_full_hierarchical():
    """Test full hierarchical processing."""

    php_root = Path("/Users/dreamlinx/Projects/php_admin-main-c59644bb607125803a5d14400b64be9068b82488")
    if not php_root.exists():
        print("❌ PHP project not found")
        return

    print("\n=== Test: Full Hierarchical Processing ===")

    config = Config()
    success = scan_directories_hierarchical(
        php_root,
        config,
        max_workers=4,
        use_fallback=True,
        quiet=False,
        timeout=60
    )

    print(f"\n✅ Processing {'succeeded' if success else 'failed'}")

if __name__ == "__main__":
    test_hierarchy()
    test_full_hierarchical()