#!/usr/bin/env python3
"""Debug script to test adaptive configuration loading."""

from pathlib import Path

from src.codeindex.adaptive_selector import AdaptiveSymbolSelector
from src.codeindex.config import Config

# 加载 PHP 项目的配置
config_path = Path(
    "/Users/dreamlinx/Projects/php_admin-main-c59644bb607125803a5d14400b64be9068b82488/.codeindex.yaml"
)
config = Config.load(config_path)

print("=== 配置加载结果 ===")
print(f"max_per_file: {config.indexing.symbols.max_per_file}")
print(f"adaptive enabled: {config.indexing.symbols.adaptive_symbols.enabled}")
print(f"adaptive limits: {config.indexing.symbols.adaptive_symbols.limits}")
print(f"adaptive thresholds: {config.indexing.symbols.adaptive_symbols.thresholds}")

# 测试自适应选择器
selector = AdaptiveSymbolSelector(config.indexing.symbols.adaptive_symbols)
limit_8891 = selector.calculate_limit(8891, 56)  # 8891行，56个符号
limit_500 = selector.calculate_limit(500, 80)  # 500行，80个符号

print("\n=== 自适应计算结果 ===")
print("文件1: 8891行，56个符号")
print(f"  计算的limit: {limit_8891}")
print(f"  文件分类: {selector._determine_size_category(8891)}")
print("  期望: 56 (全部显示，因为 56 < 150)")

print("\n文件2: 500行，80个符号")
print(f"  计算的limit: {limit_500}")
print(f"  文件分类: {selector._determine_size_category(500)}")
print("  期望: 50 (large类别限制)")
