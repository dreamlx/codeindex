"""CLI commands for scanning directories and generating README files.

This module provides the core scanning functionality, including single directory
scans and bulk scanning of entire projects with parallel processing and AI enhancement.
"""

import concurrent.futures
from pathlib import Path

import click

from .cli_common import console
from .config import Config
from .directory_tree import DirectoryTree
from .docstring_processor import DocstringProcessor
from .invoker import (
    clean_ai_output,
    format_prompt,
    invoke_ai_cli,
    validate_markdown_output,
)
from .parallel import parse_files_parallel
from .scanner import scan_directory
from .smart_writer import SmartWriter
from .writer import (
    format_files_for_prompt,
    format_imports_for_prompt,
    format_symbols_for_prompt,
    generate_fallback_readme,
    write_readme,
)

# ========== Helper functions for scan (extracted for maintainability) ==========


def _validate_scan_args(fallback: bool, dry_run: bool, ai: bool, quiet: bool) -> None:
    """Validate scan command arguments.

    Args:
        fallback: Deprecated --fallback flag
        dry_run: --dry-run flag (requires --ai)
        ai: --ai flag
        quiet: --quiet flag

    Raises:
        SystemExit: If validation fails
    """
    # Handle deprecated --fallback flag
    if fallback:
        if not quiet:
            console.print(
                "[yellow]Warning: --fallback is deprecated. "
                "Structural mode is now the default. "
                "This flag will be removed in a future version.[/yellow]"
            )

    # --dry-run requires --ai (only meaningful for AI mode)
    if dry_run and not ai:
        console.print("[red]Error: --dry-run requires --ai flag.[/red]")
        console.print("  --dry-run previews the AI prompt, which requires AI mode.")
        console.print("  Usage: codeindex scan path/ --ai --dry-run")
        raise SystemExit(1)


def _validate_and_resolve_path(path: Path, output: str) -> Path:
    """Validate and resolve the target path.

    Args:
        path: Path to validate (may be relative)
        output: Output format (markdown or json)

    Returns:
        Resolved absolute path

    Raises:
        click.BadParameter: If path is invalid (markdown mode)
        SystemExit: If path is invalid (json mode)
    """
    # Check if path exists (handle JSON error output)
    if not path.exists():
        if output == "json":
            import json

            from .errors import ErrorCode, ErrorInfo, create_error_response

            error = ErrorInfo(
                code=ErrorCode.DIRECTORY_NOT_FOUND,
                message=f"Directory does not exist: {path}",
                detail=None,
            )
            click.echo(json.dumps(create_error_response(error), indent=2, ensure_ascii=False))
            raise SystemExit(1)
        else:
            # Keep original Click behavior for markdown mode
            raise click.BadParameter(f"Directory '{path}' does not exist.")

    # Check if it's a directory
    if not path.is_dir():
        if output == "json":
            import json

            from .errors import ErrorCode, ErrorInfo, create_error_response

            error = ErrorInfo(
                code=ErrorCode.INVALID_PATH,
                message=f"Path is not a directory: {path}",
                detail=None,
            )
            click.echo(json.dumps(create_error_response(error), indent=2, ensure_ascii=False))
            raise SystemExit(1)
        else:
            raise click.BadParameter(f"Path '{path}' is not a directory.")

    return path


def _load_and_prepare_config(
    ai: bool,
    parallel: int | None,
    docstring_mode: str | None,
) -> tuple[Config, DocstringProcessor | None]:
    """Load configuration and prepare docstring processor.

    Args:
        ai: Whether AI mode is enabled
        parallel: Override parallel workers (None = use config value)
        docstring_mode: Override docstring mode (None = use config value)

    Returns:
        Tuple of (config, docstring_processor)

    Raises:
        SystemExit: If AI mode is requested but ai_command is not configured
    """
    # Load config
    config = Config.load()

    # --ai requires ai_command in config
    if ai and not config.ai_command:
        console.print("[red]Error: --ai requires ai_command in .codeindex.yaml[/red]")
        console.print("  Add ai_command to your config, for example:")
        console.print('  ai_command: \'claude -p "{prompt}" --allowedTools "Read"\'')
        raise SystemExit(1)

    # Override parallel workers if specified
    if parallel is not None:
        config.parallel_workers = parallel

    # Determine docstring mode (CLI overrides config)
    effective_docstring_mode = (
        docstring_mode if docstring_mode is not None else config.docstrings.mode
    )

    # Create DocstringProcessor if needed
    docstring_processor = None
    if effective_docstring_mode != "off" and config.docstrings.ai_command:
        docstring_processor = DocstringProcessor(
            ai_command=config.docstrings.ai_command,
            mode=effective_docstring_mode,
        )

    return config, docstring_processor


def _scan_and_parse_directory(
    path: Path, config: Config, quiet: bool, output: str
) -> list | None:
    """Scan directory and parse files.

    Args:
        path: Directory to scan
        config: Configuration
        quiet: Suppress progress messages
        output: Output format

    Returns:
        List of ParseResult objects, or None if no files found
    """
    if not quiet:
        console.print("  [dim]→ Scanning directory...[/dim]")
    result = scan_directory(path, config, path.parent)

    if not result.files:
        if output == "json":
            import json

            # Output empty results JSON
            json_output = {
                "success": True,
                "results": [],
                "summary": {
                    "total_files": 0,
                    "total_symbols": 0,
                    "total_imports": 0,
                    "errors": 0,
                },
            }
            click.echo(json.dumps(json_output, indent=2, ensure_ascii=False))
        else:
            if not quiet:
                console.print(f"[yellow]No indexable files found in {path}[/yellow]")
        return None

    if not quiet:
        console.print(f"  [dim]→ Found {len(result.files)} files[/dim]")

    # Parse files
    if not quiet:
        console.print("  [dim]→ Parsing with tree-sitter...[/dim]")
    parse_results = parse_files_parallel(result.files, config, quiet)
    total_symbols = sum(len(r.symbols) for r in parse_results)
    if not quiet:
        console.print(f"  [dim]→ Extracted {total_symbols} symbols[/dim]")

    return parse_results


def _output_scan_json(parse_results: list) -> None:
    """Output scan results as JSON.

    Args:
        parse_results: List of ParseResult objects
    """
    import json

    # Build JSON output
    json_output = {
        "success": True,
        "results": [r.to_dict() for r in parse_results],
        "summary": {
            "total_files": len(parse_results),
            "total_symbols": sum(len(r.symbols) for r in parse_results),
            "total_imports": sum(len(r.imports) for r in parse_results),
            "errors": sum(1 for r in parse_results if r.error),
        },
    }

    # Output to stdout
    click.echo(json.dumps(json_output, indent=2, ensure_ascii=False))


def _generate_structural_readme(
    path: Path,
    parse_results: list,
    config: Config,
    docstring_processor: DocstringProcessor | None,
    quiet: bool,
    show_cost: bool,
) -> None:
    """Generate structural README without AI.

    Args:
        path: Directory path
        parse_results: List of ParseResult objects
        config: Configuration
        docstring_processor: Optional docstring processor
        quiet: Suppress progress messages
        show_cost: Show token cost information
    """
    # DEFAULT: Generate smart README without AI (structural mode)
    if not quiet:
        console.print("  [dim]→ Writing smart README...[/dim]")

    # For single directory scan, always use detailed level
    # (overview/navigation only make sense in hierarchical mode)
    level = "detailed"

    writer = SmartWriter(config.indexing, docstring_processor=docstring_processor)
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

        # Show cost information if requested
        if show_cost and docstring_processor:
            tokens = docstring_processor.total_tokens
            estimated_cost = (tokens / 1_000_000) * 3.0  # Rough estimate: $3 per 1M tokens
            console.print(
                f"  [dim]→ Docstring processing: {tokens} tokens "
                f"(~${estimated_cost:.4f})[/dim]"
            )
    else:
        console.print(f"[red]✗ Error:[/red] {write_result.error}")


def _generate_ai_readme(
    path: Path,
    parse_results: list,
    config: Config,
    dry_run: bool,
    quiet: bool,
    timeout: int,
) -> None:
    """Generate AI-enhanced README.

    Args:
        path: Directory path
        parse_results: List of ParseResult objects
        config: Configuration
        dry_run: Preview prompt without executing
        quiet: Suppress progress messages
        timeout: AI CLI timeout in seconds
    """
    # Format for prompt
    if not quiet:
        console.print("  [dim]→ Formatting prompt...[/dim]")
    files_info = format_files_for_prompt(parse_results)
    symbols_info = format_symbols_for_prompt(parse_results)
    imports_info = format_imports_for_prompt(parse_results)

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
        console.print("[yellow]Tip: Remove --ai to generate structural README without AI[/yellow]")
        return

    if not quiet:
        console.print(f"  [dim]→ AI responded ({len(invoke_result.output)} chars)[/dim]")

    # Clean and validate AI output
    cleaned_output = clean_ai_output(invoke_result.output)

    if not validate_markdown_output(cleaned_output):
        console.print("[yellow]⚠ AI output validation failed, using structural fallback[/yellow]")
        write_result = generate_fallback_readme(path, parse_results, config.output_file)
        if write_result.success:
            console.print(f"[green]✓ Created (structural fallback):[/green] {write_result.path}")
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


# ========== Helper functions for scan_all (validation and config) ==========


def _validate_scanall_args(fallback: bool, no_ai: bool, quiet: bool) -> None:
    """Validate scan_all command arguments.

    Args:
        fallback: Deprecated --fallback flag
        no_ai: Deprecated --no-ai flag
        quiet: --quiet flag
    """
    # Handle deprecated flags
    if fallback or no_ai:
        if not quiet:
            flag_name = "--fallback" if fallback else "--no-ai"
            console.print(
                f"[yellow]Warning: {flag_name} is deprecated. "
                "Structural mode is now the default. "
                "This flag will be removed in a future version.[/yellow]"
            )


def _load_scanall_config(
    root: Path,
    output: str,
    parallel: int | None,
    docstring_mode: str | None,
) -> tuple[Config, DocstringProcessor | None]:
    """Load configuration for scan_all.

    Args:
        root: Root directory path
        output: Output format
        parallel: Override parallel workers
        docstring_mode: Override docstring mode

    Returns:
        Tuple of (config, docstring_processor)

    Raises:
        SystemExit: If config file not found (JSON mode)
    """
    # Check if config file exists (for JSON mode)
    config_path = root / ".codeindex.yaml"
    if not config_path.exists():
        if output == "json":
            import json

            from .errors import ErrorCode, ErrorInfo, create_error_response

            error = ErrorInfo(
                code=ErrorCode.NO_CONFIG_FOUND,
                message=f"Configuration file not found: {config_path}",
                detail="Run 'codeindex init' to create .codeindex.yaml",
            )
            click.echo(json.dumps(create_error_response(error), indent=2, ensure_ascii=False))
            raise SystemExit(1)

    # Load config from root directory
    config = Config.load(config_path if config_path.exists() else None)

    # Override parallel workers if specified
    if parallel is not None:
        config.parallel_workers = parallel

    # Determine docstring mode (CLI overrides config)
    effective_docstring_mode = (
        docstring_mode if docstring_mode is not None else config.docstrings.mode
    )

    # Create DocstringProcessor if needed
    docstring_processor = None
    if effective_docstring_mode != "off" and config.docstrings.ai_command:
        docstring_processor = DocstringProcessor(
            ai_command=config.docstrings.ai_command,
            mode=effective_docstring_mode,
        )

    return config, docstring_processor


def _output_scanall_json(root: Path, config: Config) -> None:
    """Output scan_all results as JSON.

    Args:
        root: Root directory path
        config: Configuration
    """
    import json

    # Build directory tree
    tree = DirectoryTree(root, config)
    dirs = tree.get_processing_order()

    if not dirs:
        # Empty output
        json_output = {
            "success": True,
            "results": [],
            "summary": {
                "total_files": 0,
                "total_symbols": 0,
                "total_imports": 0,
                "errors": 0,
            },
        }
        click.echo(json.dumps(json_output, indent=2, ensure_ascii=False))
        return

    # Scan and parse all directories
    all_parse_results = []

    for dir_path in dirs:
        # Scan directory (non-recursive for overview, recursive for detailed)
        level = tree.get_level(dir_path)
        scan_recursive = level != "overview"
        scan_result = scan_directory(dir_path, config, base_path=root, recursive=scan_recursive)

        if scan_result.files:
            # Parse files
            parse_results = parse_files_parallel(scan_result.files, config, quiet=True)
            all_parse_results.extend(parse_results)

    # Build JSON output
    json_output = {
        "success": True,
        "results": [r.to_dict() for r in all_parse_results],
        "summary": {
            "total_files": len(all_parse_results),
            "total_symbols": sum(len(r.symbols) for r in all_parse_results),
            "total_imports": sum(len(r.imports) for r in all_parse_results),
            "errors": sum(1 for r in all_parse_results if r.error),
        },
    }

    # Output to stdout
    click.echo(json.dumps(json_output, indent=2, ensure_ascii=False))


def _build_and_print_tree(root: Path, config: Config, quiet: bool) -> DirectoryTree:
    """Build directory tree and print statistics.

    Args:
        root: Root directory path
        config: Configuration
        quiet: Suppress progress messages

    Returns:
        DirectoryTree instance
    """
    # Build directory tree (first pass)
    if not quiet:
        console.print("[bold]🌳 Building directory tree...[/bold]")

    tree = DirectoryTree(root, config)
    stats = tree.get_stats()

    if stats["total_directories"] == 0:
        if not quiet:
            console.print("[yellow]No indexable directories found[/yellow]")
        return tree

    if not quiet:
        console.print(f"[green]✓ Found {stats['total_directories']} directories[/green]")
        console.print(f"  [dim]├── {stats['with_children']} with children (navigation)[/dim]")
        console.print(f"  [dim]├── {stats['leaf_directories']} leaf directories (detailed)[/dim]")
        console.print(f"  [dim]└── Max depth: {stats['max_depth']}[/dim]")

    return tree


def _process_directories_parallel(
    dirs: list[Path],
    tree: DirectoryTree,
    config: Config,
    docstring_processor: DocstringProcessor | None,
    quiet: bool,
    show_cost: bool,
) -> None:
    """Process directories in parallel using SmartWriter.

    Args:
        dirs: List of directories to process
        tree: DirectoryTree for level information
        config: Configuration
        docstring_processor: Optional docstring processor
        quiet: Suppress progress messages
        show_cost: Show token cost information
    """
    # ========== Phase 1: SmartWriter parallel generation ==========
    if not quiet:
        console.print("\n[bold]📝 Phase 1: Generating READMEs (SmartWriter)...[/bold]")
        console.print(f"[dim]→ Processing with {config.parallel_workers} parallel workers...[/dim]")

    # Phase 1: Parallel SmartWriter processing
    phase1_results = {}  # dir_path -> (success, msg, size_bytes)
    success_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=config.parallel_workers) as executor:
        futures = {
            executor.submit(
                _process_directory_with_smartwriter, d, tree, config, docstring_processor
            ): d
            for d in dirs
        }

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

    # Phase 1 complete - show summary
    if not quiet:
        msg = f"Completed: {success_count}/{len(dirs)} directories"
        console.print(f"\n[bold]{msg}[/bold]")

        # Show cost information if requested
        if show_cost and docstring_processor:
            tokens = docstring_processor.total_tokens
            estimated_cost = (tokens / 1_000_000) * 3.0
            console.print(
                f"  [dim]→ Docstring processing: {tokens} tokens "
                f"(~${estimated_cost:.4f})[/dim]"
            )


# ========== Helper functions for scan_all (extracted from nested functions) ==========


def _process_directory_with_smartwriter(
    dir_path: Path,
    tree: DirectoryTree,
    config: Config,
    docstring_processor=None,
) -> tuple[Path, bool, str, int]:
    """Process a single directory with SmartWriter.

    Args:
        dir_path: Directory to process
        tree: DirectoryTree for level and child information
        config: Configuration
        docstring_processor: Optional DocstringProcessor for AI docstring extraction

    Returns:
        Tuple of (path, success, status_message, size_bytes)
    """
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

        # Use SmartWriter with docstring processor
        writer = SmartWriter(config.indexing, docstring_processor=docstring_processor)
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


# ========== CLI Commands ==========


@click.command()
@click.argument("path", type=click.Path(exists=False, file_okay=False, path_type=Path))
@click.option("--ai", is_flag=True, help="Enable AI-enhanced documentation (requires ai_command in config)")
@click.option("--dry-run", is_flag=True, help="Preview AI prompt without executing (requires --ai)")
@click.option("--fallback", is_flag=True, hidden=True, help="[Deprecated] Structural mode is now the default")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
@click.option("--timeout", default=120, help="AI CLI timeout in seconds")
@click.option("--parallel", "-p", type=int, help="Override parallel workers (from config)")
@click.option(
    "--docstring-mode",
    type=click.Choice(["off", "hybrid", "all-ai"]),
    default=None,
    help="Docstring extraction mode (off=disabled, hybrid=selective AI, "
    "all-ai=maximum quality). Overrides config value.",
)
@click.option(
    "--show-cost",
    is_flag=True,
    help="Display AI token usage and estimated cost for docstring processing",
)
@click.option(
    "--output",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Output format (markdown writes README_AI.md, json prints to stdout)",
)
def scan(
    path: Path,
    ai: bool,
    dry_run: bool,
    fallback: bool,
    quiet: bool,
    timeout: int,
    parallel: int | None,
    docstring_mode: str | None,
    show_cost: bool,
    output: str,
):
    """
    Scan a directory and generate README_AI.md.

    By default, generates structural documentation without AI.
    Use --ai to enable AI-enhanced documentation.

    PATH is the directory to scan.
    """
    path = path.resolve()

    # Validate arguments
    _validate_scan_args(fallback, dry_run, ai, quiet)

    # Force quiet mode when outputting JSON (stdout must be clean)
    if output == "json":
        quiet = True

    # Validate and resolve path
    path = _validate_and_resolve_path(path, output)

    # Load configuration and prepare docstring processor
    config, docstring_processor = _load_and_prepare_config(ai, parallel, docstring_mode)

    if not quiet:
        console.print(f"[bold]Scanning:[/bold] {path}")

    # Scan and parse directory
    parse_results = _scan_and_parse_directory(path, config, quiet, output)
    if parse_results is None:
        return

    # Handle JSON output mode
    if output == "json":
        _output_scan_json(parse_results)
        return

    # Generate README (structural or AI-enhanced)
    if not ai:
        _generate_structural_readme(path, parse_results, config, docstring_processor, quiet, show_cost)
    else:
        _generate_ai_readme(path, parse_results, config, dry_run, quiet, timeout)


@click.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
@click.option("--parallel", "-p", type=int, help="Override parallel workers")
@click.option("--timeout", default=120, help="Timeout per directory in seconds")
@click.option("--ai", is_flag=True, help="Enable AI-enhanced documentation (requires ai_command in config)")
@click.option("--no-ai", is_flag=True, hidden=True, help="[Deprecated] Structural mode is now the default")
@click.option("--fallback", is_flag=True, hidden=True, help="[Deprecated] Structural mode is now the default")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
@click.option("--hierarchical", "-h", is_flag=True, help="Use hierarchical processing (bottom-up)")
@click.option(
    "--docstring-mode",
    type=click.Choice(["off", "hybrid", "all-ai"]),
    default=None,
    help="Docstring extraction mode (off=disabled, hybrid=selective AI, "
    "all-ai=maximum quality). Overrides config value.",
)
@click.option(
    "--show-cost",
    is_flag=True,
    help="Display AI token usage and estimated cost for docstring processing",
)
@click.option(
    "--output",
    type=click.Choice(["markdown", "json"]),
    default="markdown",
    help="Output format (markdown writes README_AI.md files, json prints to stdout)",
)
def scan_all(
    root: Path | None,
    parallel: int | None,
    timeout: int,
    ai: bool,
    no_ai: bool,
    fallback: bool,
    quiet: bool,
    hierarchical: bool,
    docstring_mode: str | None,
    show_cost: bool,
    output: str,
):
    """Scan all project directories for README_AI.md generation.

    By default, generates structural documentation without AI.
    Use --ai to enable AI-enhanced documentation.
    """
    # Determine root path first (needed for config loading)
    root = Path.cwd() if root is None else root

    # Validate arguments
    _validate_scanall_args(fallback, no_ai, quiet)

    # Load configuration
    config, docstring_processor = _load_scanall_config(root, output, parallel, docstring_mode)

    # Use hierarchical processing if requested
    if hierarchical:
        if not quiet:
            console.print("[bold]🎯 Using hierarchical processing (bottom-up)[/bold]")

        # Import hierarchical processor
        from .hierarchical import scan_directories_hierarchical

        scan_directories_hierarchical(
            root,
            config,
            config.parallel_workers,
            not ai,  # fallback parameter
            quiet,
            timeout
        )
        return

    # Handle JSON output mode
    if output == "json":
        _output_scanall_json(root, config)
        return

    # Build directory tree and get processing order
    tree = _build_and_print_tree(root, config, quiet)
    if tree.get_stats()["total_directories"] == 0:
        return

    dirs = tree.get_processing_order()

    # Process directories in parallel
    _process_directories_parallel(dirs, tree, config, docstring_processor, quiet, show_cost)
