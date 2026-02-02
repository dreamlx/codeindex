#!/usr/bin/env python3
"""
AI Enhancement 失败诊断工具

用于分析为什么AI增强会失败，提供具体的改进建议。
"""

import sys
from pathlib import Path
from collections import defaultdict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codeindex.config import Config
from codeindex.scanner import scan_directory
from codeindex.parallel import parse_files_parallel
from codeindex.writer import (
    format_files_for_prompt,
    format_symbols_for_prompt,
    format_imports_for_prompt,
)
from codeindex.invoker import format_prompt
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()


def analyze_directory_prompt_size(dir_path: Path, config: Config) -> dict:
    """分析单个目录的prompt大小"""

    console.print(f"[dim]Analyzing {dir_path}...[/dim]")

    # Scan directory
    result = scan_directory(dir_path, config, recursive=True)

    if not result.files:
        return {
            "files": 0,
            "symbols": 0,
            "prompt_size": 0,
            "status": "empty",
        }

    # Parse files
    parse_results = parse_files_parallel(result.files, config, quiet=True)

    # Calculate sizes
    file_count = len(parse_results)
    symbol_count = sum(len(r.symbols) for r in parse_results)
    import_count = sum(len(r.imports) for r in parse_results)

    # Generate prompt components
    files_info = format_files_for_prompt(parse_results)
    symbols_info = format_symbols_for_prompt(parse_results)
    imports_info = format_imports_for_prompt(parse_results)
    prompt = format_prompt(dir_path, files_info, symbols_info, imports_info)

    prompt_size = len(prompt.encode("utf-8"))

    # Determine status
    if prompt_size > 200 * 1024:  # 200KB
        status = "too_large"
    elif prompt_size > 100 * 1024:  # 100KB
        status = "risky"
    elif prompt_size > 50 * 1024:  # 50KB
        status = "large"
    else:
        status = "ok"

    return {
        "files": file_count,
        "symbols": symbol_count,
        "imports": import_count,
        "files_info_size": len(files_info),
        "symbols_info_size": len(symbols_info),
        "imports_info_size": len(imports_info),
        "prompt_size": prompt_size,
        "status": status,
        "parse_results": parse_results,  # 用于详细分析
    }


def estimate_timeout_needed(analysis: dict) -> int:
    """估算需要的超时时间"""
    base_timeout = 60

    file_count = analysis["files"]
    symbol_count = analysis["symbols"]

    # 每10个文件+30秒
    file_factor = (file_count // 10) * 30

    # 每100个符号+20秒
    symbol_factor = (symbol_count // 100) * 20

    # 最大5分钟
    return min(base_timeout + file_factor + symbol_factor, 300)


def suggest_improvements(analysis: dict, timeout_config: int) -> list[str]:
    """根据分析结果提供改进建议"""
    suggestions = []

    # 检查prompt大小
    prompt_kb = analysis["prompt_size"] / 1024
    if analysis["status"] == "too_large":
        suggestions.append(
            f"🚨 CRITICAL: Prompt太大 ({prompt_kb:.0f}KB)，必须压缩：\n"
            f"   - 启用smart prompt compression（待实现）\n"
            f"   - 或者split目录为多个子目录"
        )
    elif analysis["status"] == "risky":
        suggestions.append(
            f"⚠️  Prompt较大 ({prompt_kb:.0f}KB)，可能不稳定：\n"
            f"   - 建议启用prompt compression\n"
            f"   - 增加timeout到 {estimate_timeout_needed(analysis)}秒"
        )
    elif analysis["status"] == "large":
        suggestions.append(
            f"ℹ️  Prompt中等 ({prompt_kb:.0f}KB)，但建议优化：\n"
            f"   - 考虑启用compression以提升速度"
        )

    # 检查超时配置
    estimated_timeout = estimate_timeout_needed(analysis)
    if estimated_timeout > timeout_config:
        suggestions.append(
            f"⏱  建议增加timeout：{timeout_config}秒 → {estimated_timeout}秒"
        )

    # 检查符号数量
    if analysis["symbols"] > 500:
        suggestions.append(
            f"📊 符号数量很大 ({analysis['symbols']}个)，建议：\n"
            f"   - 检查是否有大量get*/set*方法可以排除\n"
            f"   - 考虑使用符号分组摘要（待实现）"
        )

    # 检查文件数量
    if analysis["files"] > 50:
        suggestions.append(
            f"📁 文件数量很大 ({analysis['files']}个)，建议：\n"
            f"   - 考虑按子目录进一步组织代码\n"
            f"   - 或使用分批处理（待实现）"
        )

    return suggestions


def analyze_symbol_distribution(parse_results: list) -> dict:
    """分析符号分布，找出优化点"""
    symbol_patterns = defaultdict(int)
    large_files = []

    for result in parse_results:
        symbol_count = len(result.symbols)
        if symbol_count > 50:
            large_files.append((result.path.name, symbol_count))

        # 统计符号名称模式
        for symbol in result.symbols:
            name = symbol.name.lower()
            if name.startswith("get"):
                symbol_patterns["get*"] += 1
            elif name.startswith("set"):
                symbol_patterns["set*"] += 1
            elif name.startswith("is") or name.startswith("has"):
                symbol_patterns["is*/has*"] += 1
            elif symbol.kind == "class":
                symbol_patterns["classes"] += 1
            else:
                symbol_patterns["other"] += 1

    return {
        "patterns": dict(symbol_patterns),
        "large_files": sorted(large_files, key=lambda x: x[1], reverse=True)[:10],
    }


def main():
    """主函数"""
    console.print(Panel.fit(
        "[bold cyan]AI Enhancement 失败诊断工具[/bold cyan]\n"
        "[dim]分析prompt大小、估算超时、提供优化建议[/dim]",
        border_style="cyan"
    ))

    # 读取配置
    config = Config.load()
    timeout_config = 120  # 从cli参数读取，这里hardcode

    # 获取项目路径
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        project_root = Path.cwd()

    console.print(f"\n[bold]项目路径[/bold]: {project_root}")
    console.print(f"[bold]配置[/bold]:")
    console.print(f"  - max_concurrent: {config.ai_enhancement.max_concurrent}")
    console.print(f"  - rate_limit_delay: {config.ai_enhancement.rate_limit_delay}s")
    console.print(f"  - size_threshold: {config.ai_enhancement.size_threshold / 1024:.0f}KB")
    console.print(f"  - timeout: {timeout_config}s")

    # 查找所有可索引目录
    from codeindex.scanner import find_all_directories

    dirs = find_all_directories(project_root, config)
    console.print(f"\n[bold]找到 {len(dirs)} 个目录[/bold]\n")

    # 分析每个目录
    analyses = {}
    for i, dir_path in enumerate(dirs, 1):
        console.print(f"[dim]({i}/{len(dirs)})[/dim] ", end="")
        analysis = analyze_directory_prompt_size(dir_path, config)
        analyses[dir_path] = analysis

    # 生成报告
    console.print("\n" + "=" * 80)
    console.print("[bold cyan]诊断报告[/bold cyan]")
    console.print("=" * 80 + "\n")

    # 1. 总体统计
    console.print("[bold]1. 总体统计[/bold]\n")

    table = Table(title="Prompt大小分布")
    table.add_column("状态", style="cyan")
    table.add_column("数量", justify="right")
    table.add_column("百分比", justify="right")

    status_counts = defaultdict(int)
    for analysis in analyses.values():
        status_counts[analysis["status"]] += 1

    status_styles = {
        "ok": "green",
        "large": "yellow",
        "risky": "orange",
        "too_large": "red",
        "empty": "dim",
    }

    total = len(analyses)
    for status in ["ok", "large", "risky", "too_large", "empty"]:
        count = status_counts[status]
        pct = count / total * 100 if total > 0 else 0
        table.add_row(
            f"[{status_styles[status]}]{status}[/{status_styles[status]}]",
            str(count),
            f"{pct:.1f}%",
        )

    console.print(table)

    # 2. 问题目录详情
    console.print("\n[bold]2. 需要关注的目录[/bold]\n")

    problem_dirs = [
        (path, analysis)
        for path, analysis in analyses.items()
        if analysis["status"] in ["risky", "too_large"]
    ]

    if problem_dirs:
        detail_table = Table()
        detail_table.add_column("目录")
        detail_table.add_column("文件数", justify="right")
        detail_table.add_column("符号数", justify="right")
        detail_table.add_column("Prompt大小", justify="right")
        detail_table.add_column("状态")
        detail_table.add_column("建议超时", justify="right")

        for dir_path, analysis in sorted(
            problem_dirs, key=lambda x: x[1]["prompt_size"], reverse=True
        ):
            prompt_kb = analysis["prompt_size"] / 1024
            estimated_timeout = estimate_timeout_needed(analysis)

            status_style = status_styles[analysis["status"]]
            detail_table.add_row(
                dir_path.name,
                str(analysis["files"]),
                str(analysis["symbols"]),
                f"{prompt_kb:.1f}KB",
                f"[{status_style}]{analysis['status']}[/{status_style}]",
                f"{estimated_timeout}s",
            )

        console.print(detail_table)

        # 3. 每个问题目录的详细建议
        console.print("\n[bold]3. 改进建议[/bold]\n")

        for dir_path, analysis in problem_dirs[:5]:  # 只显示前5个
            console.print(f"\n[bold cyan]📁 {dir_path.name}[/bold cyan]")

            suggestions = suggest_improvements(analysis, timeout_config)
            for suggestion in suggestions:
                console.print(f"  {suggestion}")

            # 符号分布分析
            if "parse_results" in analysis:
                dist = analyze_symbol_distribution(analysis["parse_results"])
                if dist["patterns"]:
                    console.print(f"\n  [dim]符号分布：[/dim]")
                    for pattern, count in sorted(
                        dist["patterns"].items(), key=lambda x: x[1], reverse=True
                    ):
                        console.print(f"    - {pattern}: {count}个")

                if dist["large_files"]:
                    console.print(f"\n  [dim]最大的文件（符号数）：[/dim]")
                    for filename, count in dist["large_files"][:5]:
                        console.print(f"    - {filename}: {count}个符号")

    else:
        console.print("[green]✓ 所有目录的prompt大小都在安全范围内[/green]")

    # 4. 配置建议
    console.print("\n[bold]4. 配置优化建议[/bold]\n")

    # 计算平均prompt大小
    avg_prompt_size = sum(a["prompt_size"] for a in analyses.values()) / len(analyses)
    max_prompt_size = max(a["prompt_size"] for a in analyses.values())

    console.print(f"平均Prompt大小: {avg_prompt_size / 1024:.1f}KB")
    console.print(f"最大Prompt大小: {max_prompt_size / 1024:.1f}KB\n")

    config_suggestions = []

    # 并发建议
    risky_count = status_counts["risky"] + status_counts["too_large"]
    if risky_count > 0:
        config_suggestions.append(
            "🔧 max_concurrent: 降低到 2-4，避免同时处理多个大目录"
        )

    # 超时建议
    max_estimated_timeout = max(
        estimate_timeout_needed(a) for a in analyses.values()
    )
    if max_estimated_timeout > timeout_config:
        config_suggestions.append(
            f"⏱  timeout: 增加到 {max_estimated_timeout}秒（当前{timeout_config}秒）"
        )

    # rate limit建议
    if config.ai_enhancement.max_concurrent > 4:
        config_suggestions.append(
            "🚦 rate_limit_delay: 增加到 2.0秒，给API更多喘息时间"
        )

    if config_suggestions:
        console.print("[yellow]建议调整配置：[/yellow]\n")
        for suggestion in config_suggestions:
            console.print(f"  {suggestion}")
    else:
        console.print("[green]✓ 当前配置较为合理[/green]")

    # 5. 下一步行动
    console.print("\n[bold]5. 下一步行动[/bold]\n")

    actions = []

    if problem_dirs:
        actions.append("1. 对于risky/too_large的目录，手动调整timeout重试")
        actions.append("2. 考虑将大目录拆分为更小的子目录")
        actions.append("3. 启用exclude_patterns排除get*/set*方法")

    if risky_count > len(dirs) * 0.3:  # 超过30%的目录有问题
        actions.append("4. 等待Epic 3.1实施（prompt compression）")
        actions.append("5. 或者使用--no-ai暂时禁用AI增强")

    if not actions:
        actions.append("✓ 当前项目适合AI增强，可以正常运行scan-all")

    for action in actions:
        console.print(f"  {action}")

    console.print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
