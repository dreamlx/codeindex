#!/usr/bin/env python3
"""Simple test for hierarchical processing."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup basic directories
here = Path(__file__).parent
test_dir = here / "test_hierarchical_test"

# Create test structure
print(f"Creating test structure in: {test_dir}")

# Clean up first
import shutil  # noqa: E402

if test_dir.exists():
    shutil.rmtree(test_dir)

# Create directory structure
(test_dir / "level1").mkdir(parents=True)
(test_dir / "level1" / "level2a").mkdir()
(test_dir / "level1" / "level2b").mkdir()
(test_dir / "level1" / "level2a" / "level3").mkdir()

# Create test files
(test_dir / "level1" / "file1.py").write_text("def func1(): pass")
(test_dir / "level1" / "level2a" / "file2.py").write_text("def func2(): pass")
(test_dir / "level1" / "level2b" / "file3.py").write_text("def func3(): pass")
(test_dir / "level1" / "level2a" / "level3" / "file4.py").write_text("def func4(): pass")

# Create config
(test_dir / ".codeindex.yaml").write_text("""
version: 1
ai_command: 'echo "test"'
languages:
  - python
parallel_workers: 4
""")

print("✅ Test structure created")

# Now test
from codeindex.config import Config  # noqa: E402
from codeindex.hierarchical import (  # noqa: E402
    build_directory_hierarchy,
    create_processing_batches,
)
from codeindex.scanner import find_all_directories  # noqa: E402

config = Config()
config.languages = ["python"]

print("\n=== Finding directories ===")
dirs = find_all_directories(test_dir, config)
for d in dirs:
    print(f"  {d.relative_to(test_dir)}")

print("\n=== Building hierarchy ===")
dir_info, roots = build_directory_hierarchy(dirs)

for path, info in dir_info.items():
    print(f"  {path.relative_to(test_dir)}: level {info.level} has {len(info.children)} children")

print("\n=== Creating batches ===")
batches = create_processing_batches(dir_info, 2)
for i, batch in enumerate(batches):
    print(f"  Batch {i+1}: {[b.name for b in batch]}")

print("\n✅ Test completed successfully")
