#!/usr/bin/env python3
"""Debug OperateGoods.class.php symbol filtering."""

from pathlib import Path

from src.codeindex.config import Config
from src.codeindex.parser import parse_file
from src.codeindex.smart_writer import SmartWriter

# Parse the file
file_path = Path(
    "/Users/dreamlinx/Projects/php_admin-main-c59644bb607125803a5d14400b64be9068b82488"
    "/Application/Common/Business/OperateGoods.class.php"
)

print(f"=== Parsing {file_path.name} ===")
result = parse_file(file_path)

print(f"File lines: {result.file_lines}")
print(f"Total symbols parsed: {len(result.symbols)}")
print(f"Namespace: {result.namespace}")

# Load config
config_path = Path(
    "/Users/dreamlinx/Projects/php_admin-main-c59644bb607125803a5d14400b64be9068b82488/.codeindex.yaml"
)
config = Config.load(config_path)

# Create SmartWriter and test filtering
writer = SmartWriter(config.indexing)
filtered_symbols = writer._filter_symbols(result.symbols)

print("\n=== After filtering ===")
print(f"Filtered symbols count: {len(filtered_symbols)}")
print(f"Adaptive enabled: {config.indexing.symbols.adaptive_symbols.enabled}")

# Calculate limit
if config.indexing.symbols.adaptive_symbols.enabled:
    limit = writer.adaptive_selector.calculate_limit(
        result.file_lines, len(filtered_symbols)
    )
    print(f"Adaptive limit: {limit}")
else:
    limit = config.indexing.symbols.max_per_file
    print(f"Fixed limit: {limit}")

print("\n=== Final display ===")
print(f"Will display: {min(limit, len(filtered_symbols))} symbols")
print(f"Will truncate: {max(0, len(filtered_symbols) - limit)} symbols")

# Show first few filtered symbols
print("\n=== First 5 filtered symbols ===")
for i, sym in enumerate(filtered_symbols[:5]):
    print(f"{i+1}. {sym.name} ({sym.kind})")
