#!/usr/bin/env python3
"""验证PHP项目的符号提取效果

用于测试和对比改进前后的效果
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codeindex.parser import parse_file
from codeindex.symbol_scorer import SymbolImportanceScorer, ScoringContext


def analyze_file(file_path: Path, scorer=None):
    """分析单个PHP文件的符号提取情况"""
    print(f"\n{'='*80}")
    print(f"文件: {file_path.name}")
    print(f"路径: {file_path}")

    # 读取文件
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        lines = content.count('\n') + 1
        print(f"行数: {lines:,}")
    except Exception as e:
        print(f"❌ 读取失败: {e}")
        return None

    # 解析符号
    result = parse_file(file_path)

    if result.error:
        print(f"❌ 解析错误: {result.error}")
        return None

    print(f"\n符号总数: {len(result.symbols)}")

    if not result.symbols:
        print("⚠️  未找到任何符号")
        return None

    # 按类型统计
    by_kind = {}
    for sym in result.symbols:
        by_kind[sym.kind] = by_kind.get(sym.kind, 0) + 1

    print("\n符号类型分布:")
    for kind, count in sorted(by_kind.items()):
        print(f"  {kind}: {count}")

    # 如果有评分器，对符号评分
    if scorer:
        print("\n符号评分 (Top 20):")
        scored_symbols = []
        for sym in result.symbols:
            score = scorer.score(sym)
            scored_symbols.append((sym, score))

        # 按分数排序
        scored_symbols.sort(key=lambda x: x[1], reverse=True)

        for i, (sym, score) in enumerate(scored_symbols[:20], 1):
            visibility = "public" if "public" in sym.signature.lower() else \
                        "protected" if "protected" in sym.signature.lower() else \
                        "private" if "private" in sym.signature.lower() else "?"

            # 截断长签名
            sig = sym.signature[:60] + "..." if len(sym.signature) > 60 else sym.signature

            print(f"  {i:2d}. [{score:5.1f}] {visibility:9s} {sym.kind:8s} {sym.name:30s}")
            if i <= 5:  # 前5个显示完整签名
                print(f"      {sym.signature}")

    return result


def main():
    """主函数"""
    php_project = Path.home() / "Projects/php_admin-main-c59644bb607125803a5d14400b64be9068b82488"

    if not php_project.exists():
        print(f"❌ PHP项目不存在: {php_project}")
        return 1

    print("=" * 80)
    print("PHP项目符号提取验证")
    print("=" * 80)
    print(f"\n项目路径: {php_project}")

    # 创建评分器（只有基础评分，未来会增加更多维度）
    scorer = SymbolImportanceScorer()
    print(f"\n评分器: SymbolImportanceScorer")
    print(f"  - 可见性评分: ✅")
    print(f"  - 语义评分: ✅")
    print(f"  - 文档评分: ⏳ (未实现)")
    print(f"  - 复杂度评分: ⏳ (未实现)")
    print(f"  - 命名模式评分: ⏳ (未实现)")

    # 测试几个大文件
    test_files = [
        "Application/Common/Business/OperateGoods.class.php",  # 8891 lines
        "Application/Api/Controller/InventoryController.class.php",  # 7923 lines
        "Application/Retail/Business/PrepareOrder.class.php",  # 4887 lines
        "Application/Cashier/Business/PlaceOrder.class.php",  # 3520 lines - 支付相关
    ]

    results = []
    for rel_path in test_files:
        file_path = php_project / rel_path
        if file_path.exists():
            result = analyze_file(file_path, scorer)
            if result:
                results.append((rel_path, result))
        else:
            print(f"\n⚠️  文件不存在: {rel_path}")

    # 总结
    print("\n" + "=" * 80)
    print("总结")
    print("=" * 80)
    print(f"\n测试文件数: {len(results)}")

    total_symbols = sum(len(r[1].symbols) for r in results)
    print(f"提取符号总数: {total_symbols}")

    print("\n当前限制:")
    print(f"  - 每个文件最多15个符号 (max_per_file: 15)")
    print(f"  - 对于8891行的文件，15个符号仅覆盖 0.17% 的代码")
    print(f"  - 对于7923行的文件，15个符号仅覆盖 0.19% 的代码")

    print("\n改进目标 (Phase 1):")
    print(f"  - 自适应符号数量: 大文件可提取 80-120 个符号")
    print(f"  - 智能评分选择: 优先选择重要的业务方法")
    print(f"  - 预期改进: +433%-700% 的信息完整度")

    print("\n💡 建议:")
    print("  1. 继续开发 Story 1.1.4-1.1.6 (文档、复杂度、命名模式评分)")
    print("  2. 完成 Epic 2 (自适应符号提取)")
    print("  3. 在此项目上验证最终效果")

    return 0


if __name__ == "__main__":
    sys.exit(main())
