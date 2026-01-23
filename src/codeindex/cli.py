"""CLI entry point for codeindex."""

from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from .config import DEFAULT_CONFIG_NAME, Config
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
from .writer import (
    format_files_for_prompt,
    format_imports_for_prompt,
    format_symbols_for_prompt,
    generate_fallback_readme,
    write_readme,
)
from .smart_writer import SmartWriter, determine_level

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
def scan(
    path: Path,
    dry_run: bool,
    fallback: bool,
    quiet: bool,
    timeout: int,
    parallel: int | None
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
            console.print(f"[green]✓ Created ({level}, {size_kb:.1f}KB{truncated_msg}):[/green] {write_result.path}")
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
@click.option("--fallback", is_flag=True, help="Use fallback mode for all directories")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
@click.option("--hierarchical", "-h", is_flag=True, help="Use hierarchical processing (bottom-up)")
def scan_all(
    root: Path | None,
    parallel: int | None,
    timeout: int,
    fallback: bool,
    quiet: bool,
    hierarchical: bool
):
    """Scan all project directories for README_AI.md generation."""
    import subprocess
    import sys

    config = Config.load()

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
            fallback,
            quiet,
            timeout
        )

        return

    # Get current directory
    root = Path.cwd() if root is None else root

    # Find all directories to scan
    dirs = find_all_directories(root, config)

    if not dirs:
        if not quiet:
            console.print("[yellow]No indexable directories found[/yellow]")
        return

    if not quiet:
        console.print(f"[green]Found {len(dirs)} directories to process[/green]")

    # Build commands for each directory
    commands = []
    for dir_path in dirs:
        cmd = [sys.executable, "-m", "codeindex.cli", "scan", str(dir_path)]
        if fallback:
            cmd.append("--fallback")
        if quiet:
            cmd.append("--quiet")
        cmd.extend(["--timeout", str(timeout)])
        commands.append(cmd)

    # Execute in batches using xargs for true parallelism
    batch_size = config.parallel_workers * 2  # Process in batches

    if not quiet:
        console.print(f"[dim]→ Processing with {config.parallel_workers} parallel workers...[/dim]")

    for i in range(0, len(commands), batch_size):
        batch = commands[i:i + batch_size]

        # Use xargs to run in parallel
        cmd_list = []
        for cmd in batch:
            # Join command parts and escape quotes
            cmd_str = ' '.join(f'"{c}"' if ' ' in c else c for c in cmd[2:])  # Skip python and -m
            cmd_list.append(cmd_str)

        # Create xargs command
        xargs_template = (
            "echo '{cmds}' | xargs -P {workers} -I {{}} "
            "{python} -m codeindex.cli {{}} "
        )
        xargs_cmd = xargs_template.format(
            cmds=chr(10).join(cmd_list),
            workers=config.parallel_workers,
            python=sys.executable
        )

        batch_num = i // batch_size + 1
        total_batches = (len(commands) - 1) // batch_size + 1

        if not quiet and i == 0:
            console.print(
                f"[dim]→ Executing batch {batch_num}/{total_batches}...[/dim]"
            )

        # Execute
        result = subprocess.run(xargs_cmd, shell=True, capture_output=True, text=True)

        if result.returncode != 0 and not quiet:
            console.print(f"[yellow]⚠ Batch {batch_num} completed with issues[/yellow]")


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


if __name__ == "__main__":
    main()