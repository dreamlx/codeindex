"""CLI entry point for codeindex."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .config import DEFAULT_CONFIG_NAME, Config
from .directory_tree import DirectoryTree
from .incremental import (
    UpdateLevel,
    analyze_changes,
    get_dirs_to_update,
    should_update_project_index,
)
from .invoker import (
    clean_ai_output,
    format_prompt,
    invoke_ai_cli,
    validate_markdown_output,
)
from .parallel import parse_files_parallel
from .scanner import find_all_directories, scan_directory
from .smart_writer import SmartWriter
from .symbol_index import GlobalSymbolIndex
from .symbol_scorer import ScoringContext, SymbolImportanceScorer
from .tech_debt import TechDebtDetector, TechDebtReport, TechDebtReporter
from .tech_debt_formatters import ConsoleFormatter, JSONFormatter, MarkdownFormatter
from .writer import (
    format_files_for_prompt,
    format_imports_for_prompt,
    format_symbols_for_prompt,
    generate_fallback_readme,
    write_readme,
)

console = Console()


@click.group()
@click.version_option()
def main():
    """codeindex - AI-native code indexing tool for large codebases."""
    pass


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Show what would be done without executing")
@click.option("--fallback", is_flag=True, help="Generate basic README without AI")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
@click.option("--timeout", default=120, help="AI CLI timeout in seconds")
@click.option("--parallel", "-p", type=int, help="Override parallel workers (from config)")
@click.option(
    "--strategy",
    type=click.Choice(["auto", "standard", "multi_turn"]),
    default="auto",
    help="AI enhancement strategy (auto=detect, standard=single prompt, "
    "multi_turn=3-round dialogue)",
)
def scan(
    path: Path,
    dry_run: bool,
    fallback: bool,
    quiet: bool,
    timeout: int,
    parallel: int | None,
    strategy: str,
):
    """
    Scan a directory and generate README_AI.md.

    PATH is the directory to scan.
    """
    path = path.resolve()

    # Load config
    config = Config.load()

    # Override parallel workers if specified
    if parallel is not None:
        config.parallel_workers = parallel

    if not quiet:
        console.print(f"[bold]Scanning:[/bold] {path}")

    # Scan directory
    if not quiet:
        console.print("  [dim]→ Scanning directory...[/dim]")
    result = scan_directory(path, config, path.parent)

    if not result.files:
        if not quiet:
            console.print(f"[yellow]No indexable files found in {path}[/yellow]")
        return

    if not quiet:
        console.print(f"  [dim]→ Found {len(result.files)} files[/dim]")

    # Parse files
    if not quiet:
        console.print("  [dim]→ Parsing with tree-sitter...[/dim]")
    parse_results = parse_files_parallel(result.files, config, quiet)
    total_symbols = sum(len(r.symbols) for r in parse_results)
    if not quiet:
        console.print(f"  [dim]→ Extracted {total_symbols} symbols[/dim]")

    # Detect if super large file and select strategy (Epic 3.2)
    actual_strategy = strategy
    if strategy == "auto" and not fallback:
        from codeindex.ai_enhancement import is_super_large_file

        # Aggregate all parse results into single ParseResult for detection
        all_symbols = []
        total_lines = 0
        for pr in parse_results:
            all_symbols.extend(pr.symbols)
            total_lines += pr.file_lines

        # Create aggregated parse result for detection
        from codeindex.parser import ParseResult

        aggregated = ParseResult(path=path, file_lines=total_lines, symbols=all_symbols)

        detection = is_super_large_file(aggregated, config)
        if detection.is_super_large:
            actual_strategy = "multi_turn"
            if not quiet:
                console.print(
                    f"  [yellow]⚠ Super large file detected: {detection.reason}[/yellow]"
                )
                console.print("  [dim]→ Using multi-turn dialogue strategy...[/dim]")

    # Execute multi-turn dialogue if strategy selected (Epic 3.2)
    if actual_strategy == "multi_turn" and not fallback:
        from codeindex.ai_enhancement import multi_turn_ai_enhancement

        # Create aggregated parse result for multi-turn dialogue
        all_symbols = []
        total_lines = 0
        for pr in parse_results:
            all_symbols.extend(pr.symbols)
            total_lines += pr.file_lines

        from codeindex.parser import ParseResult

        aggregated = ParseResult(path=path, file_lines=total_lines, symbols=all_symbols)

        if not quiet:
            console.print("  [bold cyan]→ Starting multi-turn dialogue...[/bold cyan]")

        result_mt = multi_turn_ai_enhancement(
            parse_result=aggregated,
            config=config,
            ai_command=config.ai_command,
            timeout_per_round=timeout,
        )

        if result_mt.success:
            # Write final README from Round 3
            if not quiet:
                console.print("  [dim]→ Writing README_AI.md...[/dim]")
            write_result = write_readme(path, result_mt.final_readme, config.output_file)

            if write_result.success:
                if not quiet:
                    duration_msg = f"{result_mt.total_time:.1f}s"
                    console.print(
                        f"[green]✓ Multi-turn complete ({duration_msg}):[/green] "
                        f"{write_result.path}"
                    )
                else:
                    print(write_result.path)
            else:
                console.print(f"[red]✗ Write error:[/red] {write_result.error}")
            return
        else:
            # Multi-turn failed, fall back to standard enhancement
            if not quiet:
                console.print(
                    f"[yellow]⚠ Multi-turn failed: {result_mt.error}[/yellow]"
                )
                console.print("  [dim]→ Falling back to standard enhancement...[/dim]")
            # Continue to standard enhancement below

    # Format for prompt
    if not quiet:
        console.print("  [dim]→ Formatting prompt...[/dim]")
    files_info = format_files_for_prompt(parse_results)
    symbols_info = format_symbols_for_prompt(parse_results)
    imports_info = format_imports_for_prompt(parse_results)

    if fallback:
        # Generate smart README without AI
        if not quiet:
            console.print("  [dim]→ Writing smart README...[/dim]")

        # For single directory scan, always use detailed level
        # (overview/navigation only make sense in hierarchical mode)
        level = "detailed"

        writer = SmartWriter(config.indexing)
        write_result = writer.write_readme(
            dir_path=path,
            parse_results=parse_results,
            level=level,
            child_dirs=[],
            output_file=config.output_file,
        )

        if write_result.success:
            size_kb = write_result.size_bytes / 1024
            truncated_msg = " [truncated]" if write_result.truncated else ""
            msg = f"[green]✓ Created ({level}, {size_kb:.1f}KB{truncated_msg}):[/green]"
            console.print(f"{msg} {write_result.path}")
        else:
            console.print(f"[red]✗ Error:[/red] {write_result.error}")
        return

    # Format prompt
    prompt = format_prompt(path, files_info, symbols_info, imports_info)

    if dry_run:
        console.print("\n[dim]Prompt preview:[/dim]")
        console.print(prompt[:500] + "..." if len(prompt) > 500 else prompt)
        console.print(f"\n[dim]Total prompt length: {len(prompt)} chars[/dim]")
        return

    # Invoke AI CLI
    if not quiet:
        console.print(f"  [dim]→ Invoking AI CLI (timeout: {timeout}s)...[/dim]")
        console.print(f"  [dim]  Command: {config.ai_command[:50]}...[/dim]")

    invoke_result = invoke_ai_cli(config.ai_command, prompt, timeout=timeout)

    if not invoke_result.success:
        console.print(f"[red]✗ AI CLI error:[/red] {invoke_result.error}")
        console.print("[yellow]Tip: Use --fallback to generate basic README without AI[/yellow]")
        return

    if not quiet:
        console.print(f"  [dim]→ AI responded ({len(invoke_result.output)} chars)[/dim]")

    # Clean and validate AI output
    cleaned_output = clean_ai_output(invoke_result.output)

    if not validate_markdown_output(cleaned_output):
        console.print("[yellow]⚠ AI output validation failed, using fallback[/yellow]")
        write_result = generate_fallback_readme(path, parse_results, config.output_file)
        if write_result.success:
            console.print(f"[green]✓ Created (fallback):[/green] {write_result.path}")
        else:
            console.print(f"[red]✗ Error:[/red] {write_result.error}")
        return

    # Write output
    if not quiet:
        console.print("  [dim]→ Writing README_AI.md...[/dim]")
    write_result = write_readme(path, cleaned_output, config.output_file)

    if write_result.success:
        if not quiet:
            console.print(f"[green]✓ Created:[/green] {write_result.path}")
        else:
            print(write_result.path)
    else:
        console.print(f"[red]✗ Write error:[/red] {write_result.error}")


@main.command()
@click.option("--force", "-f", is_flag=True, help="Overwrite existing config")
def init(force: bool):
    """Initialize .codeindex.yaml configuration file."""
    config_path = Path.cwd() / DEFAULT_CONFIG_NAME

    if config_path.exists() and not force:
        console.print(f"[yellow]Config already exists:[/yellow] {config_path}")
        console.print("Use --force to overwrite")
        return

    created_path = Config.create_default()
    console.print(f"[green]Created:[/green] {created_path}")
    console.print("\nEdit this file to configure:")
    console.print("  - ai_command: Your AI CLI command")
    console.print("  - include/exclude: Directories to scan")


@main.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
@click.option("--parallel", "-p", type=int, help="Override parallel workers")
@click.option("--timeout", default=120, help="Timeout per directory in seconds")
@click.option("--no-ai", is_flag=True, help="Disable AI enhancement, use SmartWriter only")
@click.option("--fallback", is_flag=True, help="Alias for --no-ai (deprecated)")
@click.option(
    "--ai-all",
    is_flag=True,
    help="Enhance ALL directories with AI (overrides config strategy)",
)
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
@click.option("--hierarchical", "-h", is_flag=True, help="Use hierarchical processing (bottom-up)")
def scan_all(
    root: Path | None,
    parallel: int | None,
    timeout: int,
    no_ai: bool,
    fallback: bool,
    ai_all: bool,
    quiet: bool,
    hierarchical: bool
):
    """Scan all project directories for README_AI.md generation.

    Two-phase processing:
    1. SmartWriter generates all READMEs in parallel
    2. AI enhances overview dirs + oversize files (parallel with rate limiting)

    Strategy:
    - Default: Use selective strategy from config
    - --ai-all: Enhance ALL directories with AI
    - --no-ai: Disable AI, use SmartWriter for all directories
    """
    import concurrent.futures
    import threading
    import time

    config = Config.load()

    # --fallback is alias for --no-ai
    use_ai = not (no_ai or fallback)

    # Override parallel workers if specified
    if parallel is not None:
        config.parallel_workers = parallel

    # Use hierarchical processing if requested
    if hierarchical:
        # Get current directory
        root = Path.cwd() if root is None else root

        if not quiet:
            console.print("[bold]🎯 Using hierarchical processing (bottom-up)[/bold]")

        # Import hierarchical processor
        from .hierarchical import scan_directories_hierarchical

        success = scan_directories_hierarchical(
            root,
            config,
            config.parallel_workers,
            not use_ai,  # fallback parameter
            quiet,
            timeout
        )

        return

    # Get current directory
    root = Path.cwd() if root is None else root

    # Build directory tree (first pass)
    if not quiet:
        console.print("[bold]🌳 Building directory tree...[/bold]")

    tree = DirectoryTree(root, config)
    stats = tree.get_stats()

    if stats["total_directories"] == 0:
        if not quiet:
            console.print("[yellow]No indexable directories found[/yellow]")
        return

    if not quiet:
        console.print(f"[green]✓ Found {stats['total_directories']} directories[/green]")
        console.print(f"  [dim]├── {stats['with_children']} with children (navigation)[/dim]")
        console.print(f"  [dim]├── {stats['leaf_directories']} leaf directories (detailed)[/dim]")
        console.print(f"  [dim]└── Max depth: {stats['max_depth']}[/dim]")

    # Get processing order (bottom-up: deepest first)
    dirs = tree.get_processing_order()

    # ========== Phase 1: SmartWriter parallel generation ==========
    if not quiet:
        console.print("\n[bold]📝 Phase 1: Generating READMEs (SmartWriter)...[/bold]")
        console.print(f"[dim]→ Processing with {config.parallel_workers} parallel workers...[/dim]")

    def process_with_smartwriter(dir_path: Path) -> tuple[Path, bool, str, int]:
        """Process a single directory with SmartWriter. Returns (path, success, msg, size_bytes)."""
        try:
            level = tree.get_level(dir_path)
            child_dirs = tree.get_children(dir_path)

            # Scan directory (non-recursive for overview to avoid huge file lists)
            scan_recursive = level != "overview"
            result = scan_directory(dir_path, config, recursive=scan_recursive)

            # Parse files (if any)
            parse_results = []
            if result.files:
                parse_results = parse_files_parallel(result.files, config, quiet=True)

            # Use SmartWriter
            writer = SmartWriter(config.indexing)
            write_result = writer.write_readme(
                dir_path=dir_path,
                parse_results=parse_results,
                level=level,
                child_dirs=child_dirs,
                output_file=config.output_file,
            )

            if write_result.success:
                size_kb = write_result.size_bytes / 1024
                truncated = " [truncated]" if write_result.truncated else ""
                status_msg = f"[{level}] {size_kb:.1f}KB{truncated}"
                return dir_path, True, status_msg, write_result.size_bytes
            else:
                return dir_path, False, write_result.error, 0

        except Exception as e:
            return dir_path, False, str(e), 0

    # Phase 1: Parallel SmartWriter processing
    phase1_results = {}  # dir_path -> (success, msg, size_bytes)
    success_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.parallel_workers) as executor:
        futures = {executor.submit(process_with_smartwriter, d): d for d in dirs}

        for future in concurrent.futures.as_completed(futures):
            dir_path, success, msg, size_bytes = future.result()
            phase1_results[dir_path] = (success, msg, size_bytes)
            if success:
                success_count += 1
                if not quiet:
                    console.print(f"[green]✓[/green] {dir_path.name} ({msg})")
            else:
                if not quiet:
                    console.print(f"[red]✗[/red] {dir_path.name}: {msg}")

    if not quiet:
        console.print(f"[dim]→ Phase 1 complete: {success_count}/{len(dirs)} directories[/dim]")

    # ========== Collect AI Enhancement Checklist ==========
    if not use_ai:
        if not quiet:
            console.print(f"\n[bold]Completed: {success_count}/{len(dirs)} directories[/bold]")
        return

    # Determine strategy
    if ai_all:
        strategy = "all"
    elif config.ai_enhancement.enabled:
        strategy = config.ai_enhancement.strategy
    else:
        strategy = "none"

    if strategy == "none":
        if not quiet:
            msg = f"Completed: {success_count}/{len(dirs)} directories (AI disabled)"
            console.print(f"\n[bold]{msg}[/bold]")
        return

    ai_checklist = []
    threshold = config.ai_enhancement.size_threshold

    for dir_path in dirs:
        level = tree.get_level(dir_path)
        success, msg, size_bytes = phase1_results.get(dir_path, (False, "", 0))

        if not success:
            continue

        # Strategy: all
        if strategy == "all":
            ai_checklist.append((dir_path, f"[{level}]"))
        # Strategy: selective
        elif strategy == "selective":
            # Condition 1: overview level (always enhance)
            if level == "overview":
                ai_checklist.append((dir_path, "overview"))
            # Condition 2: oversize files
            elif size_bytes > threshold:
                reason = f"oversize ({size_bytes / 1024:.1f}KB > {threshold / 1024:.0f}KB)"
                ai_checklist.append((dir_path, reason))

    if not ai_checklist:
        if not quiet:
            msg = f"Completed: {success_count}/{len(dirs)} directories"
            console.print(f"\n[bold]{msg} (no AI enhancement needed)[/bold]")
        return

    # ========== Phase 2: AI Enhancement (parallel with rate limiting) ==========
    if not quiet:
        overview_count = sum(1 for _, reason in ai_checklist if reason == "overview")
        oversize_count = sum(1 for _, reason in ai_checklist if reason.startswith("oversize"))
        level_count = len(ai_checklist) - overview_count - oversize_count

        if strategy == "all":
            console.print("\n[bold]🤖 Phase 2: AI Enhancement (--ai-all)...[/bold]")
            console.print(f"[dim]→ Enhancing ALL directories: {len(ai_checklist)} total[/dim]")
        else:
            console.print("\n[bold]🤖 Phase 2: AI Enhancement...[/bold]")
            checklist_msg = (
                f"→ Checklist: {len(ai_checklist)} directories "
                f"({overview_count} overview, {oversize_count} oversize, {level_count} other)"
            )
            console.print(f"[dim]{checklist_msg}[/dim]")

        rate_msg = (
            f"→ Max concurrent: {config.ai_enhancement.max_concurrent}, "
            f"delay: {config.ai_enhancement.rate_limit_delay}s"
        )
        console.print(f"[dim]{rate_msg}[/dim]")

    # Rate limiting state
    semaphore = threading.Semaphore(config.ai_enhancement.max_concurrent)
    last_call_time = [0.0]
    rate_lock = threading.Lock()

    def enhance_with_ai(dir_path: Path, reason: str) -> tuple[Path, bool, str]:
        """Enhance a single directory with AI. Includes rate limiting."""
        with semaphore:
            # Rate limiting
            with rate_lock:
                elapsed = time.time() - last_call_time[0]
                if elapsed < config.ai_enhancement.rate_limit_delay:
                    time.sleep(config.ai_enhancement.rate_limit_delay - elapsed)
                last_call_time[0] = time.time()

            try:
                level = tree.get_level(dir_path)

                # Re-scan directory (non-recursive for overview)
                scan_recursive = level != "overview"
                result = scan_directory(dir_path, config, recursive=scan_recursive)

                # Parse files
                parse_results = []
                if result.files:
                    parse_results = parse_files_parallel(result.files, config, quiet=True)

                # Detect if super large file and use multi-turn dialogue (Epic 3.2)
                if parse_results:
                    from codeindex.ai_enhancement import is_super_large_file
                    from codeindex.parser import ParseResult

                    # Aggregate parse results
                    all_symbols = []
                    total_lines = 0
                    for pr in parse_results:
                        all_symbols.extend(pr.symbols)
                        total_lines += pr.file_lines

                    aggregated = ParseResult(
                        path=dir_path, file_lines=total_lines, symbols=all_symbols
                    )

                    detection = is_super_large_file(aggregated, config)
                    if detection.is_super_large:
                        # Use multi-turn dialogue for super large files
                        from codeindex.ai_enhancement import multi_turn_ai_enhancement

                        result_mt = multi_turn_ai_enhancement(
                            parse_result=aggregated,
                            config=config,
                            ai_command=config.ai_command,
                            timeout_per_round=timeout,
                        )

                        if result_mt.success:
                            write_result = write_readme(
                                dir_path, result_mt.final_readme, config.output_file
                            )
                            if write_result.success:
                                new_size = write_result.path.stat().st_size
                                old_size = phase1_results[dir_path][2]
                                time_str = f"{result_mt.total_time:.1f}s"
                                msg = (
                                    f"Multi-turn ({old_size / 1024:.0f}KB → "
                                    f"{new_size / 1024:.0f}KB, {time_str})"
                                )
                                return dir_path, True, msg
                        # If multi-turn fails, fall through to standard enhancement

                # Format prompt
                files_info = format_files_for_prompt(parse_results)
                symbols_info = format_symbols_for_prompt(parse_results)
                imports_info = format_imports_for_prompt(parse_results)
                prompt = format_prompt(dir_path, files_info, symbols_info, imports_info)

                # Invoke AI CLI
                invoke_result = invoke_ai_cli(config.ai_command, prompt, timeout=timeout)

                if invoke_result.success:
                    cleaned_output = clean_ai_output(invoke_result.output)
                    if validate_markdown_output(cleaned_output):
                        write_result = write_readme(dir_path, cleaned_output, config.output_file)
                        if write_result.success:
                            new_size = write_result.path.stat().st_size
                            old_size = phase1_results[dir_path][2]
                            msg = f"AI enhanced ({old_size / 1024:.0f}KB → {new_size / 1024:.0f}KB)"
                            return dir_path, True, msg

                return dir_path, False, "AI failed, keeping SmartWriter version"

            except Exception as e:
                return dir_path, False, f"AI error: {str(e)[:50]}"

    # Phase 2: Parallel AI enhancement with rate limiting
    ai_success_count = 0

    max_workers = config.ai_enhancement.max_concurrent
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(enhance_with_ai, d, r): (d, r) for d, r in ai_checklist}

        for future in concurrent.futures.as_completed(futures):
            dir_path, success, msg = future.result()
            if success:
                ai_success_count += 1
                if not quiet:
                    console.print(f"[green]✓[/green] {dir_path.name}: {msg}")
            else:
                if not quiet:
                    console.print(f"[yellow]![/yellow] {dir_path.name}: {msg}")

    if not quiet:
        msg = (
            f"Completed: {success_count}/{len(dirs)} directories, "
            f"{ai_success_count}/{len(ai_checklist)} AI enhanced"
        )
        console.print(f"\n[bold]{msg}[/bold]")


@main.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
def status(root: Path):
    """Show indexing status for the project."""
    root = root.resolve()
    config = Config.load()

    console.print(f"[bold]Project:[/bold] {root}")
    console.print(f"[bold]Config:[/bold] {DEFAULT_CONFIG_NAME}")

    # Find all directories that should be indexed
    dirs = find_all_directories(root, config)

    if not dirs:
        console.print("[yellow]No indexable directories found[/yellow]")
        return

    # Check which have README_AI.md
    indexed = []
    not_indexed = []

    for d in dirs:
        readme_path = d / config.output_file
        if readme_path.exists():
            indexed.append(d)
        else:
            not_indexed.append(d)

    # Display table
    table = Table(title="Indexing Status")
    table.add_column("Status", style="bold")
    table.add_column("Count")
    table.add_column("Percentage")

    total = len(dirs)
    indexed_count = len(indexed)
    coverage = (indexed_count / total * 100) if total > 0 else 0

    table.add_row("[green]Indexed[/green]", str(indexed_count), f"{coverage:.1f}%")
    table.add_row("[yellow]Not indexed[/yellow]", str(len(not_indexed)), f"{100-coverage:.1f}%")
    table.add_row("Total", str(total), "100%")

    console.print(table)

    if not_indexed and len(not_indexed) <= 10:
        console.print("\n[dim]Not indexed:[/dim]")
        for d in not_indexed[:10]:
            rel = d.relative_to(root)
            console.print(f"  {rel}")


@main.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
def list_dirs(root: Path):
    """List all directories that would be indexed."""
    root = root.resolve()
    config = Config.load()

    dirs = find_all_directories(root, config)

    for d in dirs:
        rel = d.relative_to(root)
        print(rel)


@main.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
@click.option("--output", "-o", default="PROJECT_INDEX.md", help="Output filename")
def index(root: Path, output: str):
    """Generate PROJECT_INDEX.md - a lightweight project overview."""
    from datetime import datetime

    root = root.resolve()
    config = Config.load()

    console.print(f"[bold]Generating project index:[/bold] {root}")

    # Find all indexed directories (those with README_AI.md)
    dirs = find_all_directories(root, config)
    indexed_dirs = [d for d in dirs if (d / config.output_file).exists()]

    if not indexed_dirs:
        console.print("[yellow]No indexed directories found.[/yellow]")
        console.print("Run 'codeindex scan' first to generate README_AI.md files.")
        return

    # Try to get project name from pyproject.toml or directory name
    project_name = root.name
    description = ""
    entry_points = []

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        with open(pyproject, "rb") as f:
            data = tomllib.load(f)
            project = data.get("project", {})
            project_name = project.get("name", project_name)
            description = project.get("description", "")
            scripts = project.get("scripts", {})
            entry_points = [f"- `{k}`: `{v}`" for k, v in scripts.items()]

    # Build module table
    modules = []
    for d in sorted(indexed_dirs):
        rel_path = d.relative_to(root)
        readme_path = d / config.output_file

        # Try to extract purpose from README_AI.md (first paragraph after heading)
        purpose = ""
        try:
            content = readme_path.read_text()
            lines = content.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("## Purpose") or line.startswith("## 目的"):
                    # Get next non-empty line
                    for j in range(i + 1, min(i + 5, len(lines))):
                        if lines[j].strip() and not lines[j].startswith("#"):
                            full_purpose = lines[j].strip()
                            if len(full_purpose) <= 80:
                                purpose = full_purpose
                            else:
                                # Smart truncate at word boundary
                                truncated = full_purpose[:80]
                                last_space = truncated.rfind(" ")
                                if last_space > 40:
                                    purpose = truncated[:last_space] + "..."
                                else:
                                    purpose = truncated + "..."
                            break
                    break
        except Exception:
            pass

        if not purpose:
            purpose = f"{rel_path.name} module"

        modules.append(f"| `{rel_path}/` | {purpose} |")

    # Generate PROJECT_INDEX.md
    timestamp = datetime.now().strftime("%Y-%m-%d")
    content = f"""# Project Index: {project_name}

> Generated: {timestamp}
> {description}

## Modules

| Path | Purpose |
|------|---------|
{chr(10).join(modules)}

## Entry Points

{chr(10).join(entry_points) if entry_points else "_No CLI entry points defined_"}

---
*Generated by codeindex. See each directory's README_AI.md for details.*
"""

    # Write file
    output_path = root / output
    output_path.write_text(content)
    console.print(f"[green]✓ Created:[/green] {output_path}")
    console.print(f"[dim]Indexed {len(indexed_dirs)} modules[/dim]")


@main.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
@click.option("--output", "-o", default="PROJECT_SYMBOLS.md", help="Output filename")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
def symbols(root: Path, output: str, quiet: bool):
    """Generate PROJECT_SYMBOLS.md - a global symbol index for all classes."""
    root = root.resolve()
    config = Config.load()

    if not quiet:
        console.print(f"[bold]Generating global symbol index:[/bold] {root}")
        console.print("[dim]→ Scanning all directories...[/dim]")

    indexer = GlobalSymbolIndex(root, config)
    stats = indexer.collect_symbols(quiet=quiet)

    if not quiet:
        console.print(f"[dim]→ Found {stats['symbols']} symbols in {stats['files']} files[/dim]")

    if stats["symbols"] == 0:
        console.print("[yellow]No symbols found. Run 'codeindex scan' first.[/yellow]")
        return

    if not quiet:
        console.print("[dim]→ Generating index...[/dim]")

    output_path = indexer.generate_index(output)

    console.print(f"[green]✓ Created:[/green] {output_path}")
    index_msg = f"Indexed {stats['symbols']} symbols from {stats['directories']} directories"
    console.print(f"[dim]{index_msg}[/dim]")


@main.command()
@click.option("--since", default="HEAD~1", help="Starting commit reference")
@click.option("--until", default="HEAD", help="Ending commit reference")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def affected(since: str, until: str, as_json: bool):
    """Analyze git changes and show affected directories.

    Shows which directories need README_AI.md updates based on code changes.
    """
    import json

    config = Config.load()
    root = Path.cwd().resolve()

    if not as_json:
        console.print(f"[bold]Analyzing changes:[/bold] {since}..{until}")

    # Analyze changes
    analysis = analyze_changes(config, since, until, root)

    if as_json:
        # JSON output for scripting
        print(json.dumps(analysis.to_dict(), indent=2))
        return

    # Human-readable output
    if analysis.level == UpdateLevel.SKIP:
        console.print(f"[green]✓ {analysis.message}[/green]")
        return

    # Show statistics
    table = Table(title="Change Analysis")
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    table.add_row("Files changed", str(len(analysis.files)))
    table.add_row("Lines added", f"+{analysis.total_additions}")
    table.add_row("Lines deleted", f"-{analysis.total_deletions}")
    table.add_row("Total changes", str(analysis.total_lines))
    table.add_row("Update level", analysis.level.value.upper())

    console.print(table)

    # Show affected directories
    dirs_to_update = get_dirs_to_update(analysis, config)
    if dirs_to_update:
        console.print("\n[bold]Directories to update:[/bold]")
        for d in dirs_to_update:
            rel = d.relative_to(root) if d.is_absolute() else d
            readme_exists = (root / rel / config.output_file).exists()
            status = "[green]✓[/green]" if readme_exists else "[yellow]⚠[/yellow]"
            console.print(f"  {status} {rel}/")

    # Show recommendation
    console.print(f"\n[dim]{analysis.message}[/dim]")

    if should_update_project_index(analysis, config):
        console.print("[yellow]→ Consider updating PROJECT_INDEX.md[/yellow]")

    # Show suggested command
    if dirs_to_update:
        console.print("\n[bold]Suggested command:[/bold]")
        if len(dirs_to_update) == 1:
            console.print(f"  codeindex scan {dirs_to_update[0]}")
        else:
            console.print("  codeindex list-dirs | xargs -P 4 -I {} codeindex scan {}")


def _find_source_files(
    path: Path, recursive: bool, languages: list[str] | None = None
) -> list[Path]:
    """Find source files in the given directory based on language configuration.

    Args:
        path: Directory path to search
        recursive: If True, search subdirectories recursively
        languages: List of languages to include (optional, uses config if None)

    Returns:
        List of source file paths
    """
    # Load languages from config if not provided
    if languages is None:
        config = Config.load()
        languages = config.languages

    # Map languages to file extensions
    extensions = {
        'python': '*.py',
        'php': '*.php',
        'javascript': '*.js',
        'typescript': '*.ts',
        'java': '*.java',
        'go': '*.go',
        'rust': '*.rs',
        'cpp': '*.cpp',
        'c': '*.c',
    }

    files = []
    for lang in languages:
        ext = extensions.get(lang)
        if ext:
            if recursive:
                files.extend([f for f in path.rglob(ext) if f.is_file()])
            else:
                files.extend([f for f in path.glob(ext) if f.is_file()])

    return files


def _analyze_files(
    files: list[Path],
    detector: TechDebtDetector,
    reporter: TechDebtReporter,
    show_progress: bool,
) -> None:
    """Analyze files and add results to reporter.

    Args:
        files: List of source files to analyze
        detector: Technical debt detector instance
        reporter: Reporter to collect results
        show_progress: Whether to show progress messages
    """
    from .parser import parse_file

    for file_path in files:
        try:
            # Parse file
            parse_result = parse_file(file_path)

            if parse_result.error:
                if show_progress:
                    console.print(
                        f"[yellow]⚠ Skipping {file_path.name}: {parse_result.error}[/yellow]"
                    )
                continue

            # Determine file type based on extension
            file_ext = file_path.suffix.lower()
            if file_ext == '.py':
                file_type = 'python'
            elif file_ext == '.php':
                file_type = 'php'
            elif file_ext == '.js':
                file_type = 'javascript'
            elif file_ext == '.ts':
                file_type = 'typescript'
            else:
                file_type = file_ext[1:] if file_ext else 'unknown'

            # Create scorer context
            scoring_context = ScoringContext(
                framework=None,
                file_type=file_type,
                total_symbols=len(parse_result.symbols),
            )
            scorer = SymbolImportanceScorer(scoring_context)

            # Detect technical debt
            debt_analysis = detector.analyze_file(parse_result, scorer)

            # Analyze symbol overload
            symbol_issues, symbol_analysis = detector.analyze_symbol_overload(
                parse_result, scorer
            )

            # Merge symbol overload issues into debt analysis
            debt_analysis.issues.extend(symbol_issues)

            # Add to reporter
            reporter.add_file_result(
                file_path=file_path,
                debt_analysis=debt_analysis,
                symbol_analysis=symbol_analysis,
            )

        except Exception as e:
            if show_progress:
                console.print(f"[red]✗ Error analyzing {file_path.name}: {e}[/red]")
            continue


def _format_and_output(
    report: TechDebtReport,
    format: str,
    output: Path | None,
    quiet: bool,
) -> None:
    """Format and output the technical debt report.

    Args:
        report: Technical debt report to format
        format: Output format (console, markdown, or json)
        output: Optional output file path
        quiet: Whether to suppress status messages
    """
    # Select formatter
    if format == "console":
        formatter = ConsoleFormatter()
    elif format == "markdown":
        formatter = MarkdownFormatter()
    else:  # json
        formatter = JSONFormatter()

    formatted_output = formatter.format(report)

    # Write output
    if output:
        output.write_text(formatted_output)
        if not quiet:
            console.print(f"[green]✓ Report written to {output}[/green]")
    else:
        # Print to stdout
        print(formatted_output)


@main.command()
@click.argument("path", type=click.Path(exists=True, file_okay=False, path_type=Path))
@click.option(
    "--format",
    type=click.Choice(["console", "markdown", "json"], case_sensitive=False),
    default="console",
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(path_type=Path),
    help="Write output to file instead of stdout",
)
@click.option(
    "--recursive",
    "-r",
    is_flag=True,
    help="Recursively scan subdirectories",
)
@click.option(
    "--quiet",
    "-q",
    is_flag=True,
    help="Minimal output",
)
def tech_debt(path: Path, format: str, output: Path | None, recursive: bool, quiet: bool):
    """Analyze technical debt in a directory.

    Scans source files for technical debt issues including:
    - Super large files (>5000 lines)
    - Large files (>2000 lines)
    - God Classes (>50 methods)
    - Massive symbol count (>100 symbols)
    - High noise ratio (>50% low-quality symbols)

    Results can be output in console, markdown, or JSON format.
    """
    try:
        # Load config
        config = Config.load()

        # Initialize detector and reporter
        detector = TechDebtDetector(config)
        reporter = TechDebtReporter()

        # Find all source files to analyze
        files_to_analyze = _find_source_files(path, recursive)

        # Handle empty directory
        if not files_to_analyze:
            report = reporter.generate_report()
            _format_and_output(report, format, output, quiet)
            return

        # Only show progress if not JSON to stdout (JSON needs clean output)
        show_progress = not quiet and not (format == "json" and output is None)

        if show_progress:
            console.print(f"[dim]Analyzing {len(files_to_analyze)} source files...[/dim]")

        # Parse and analyze each file
        _analyze_files(files_to_analyze, detector, reporter, show_progress)

        # Generate and output report
        report = reporter.generate_report()
        _format_and_output(report, format, output, quiet)

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/red]")
        raise click.Abort()


if __name__ == "__main__":
    main()
