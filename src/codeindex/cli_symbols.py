"""CLI commands for symbol indexing and dependency analysis.

This module provides commands for generating project-wide indices
and analyzing code dependencies and affected directories.
"""

import json
from datetime import datetime
from pathlib import Path

import click
from rich.table import Table

from .cli_common import console
from .config import Config
from .incremental import (
    UpdateLevel,
    analyze_changes,
    get_dirs_to_update,
    should_update_project_index,
)
from .scanner import find_all_directories
from .semantic_extractor import DirectoryContext, SemanticExtractor
from .symbol_index import GlobalSymbolIndex


def extract_module_purpose(
    dir_path: Path,
    config: Config,
    output_file: str = "README_AI.md"
) -> str:
    """
    Extract module purpose/description from directory.

    Args:
        dir_path: Path to the directory
        config: Configuration object
        output_file: README filename to check

    Returns:
        Module purpose/description string
    """
    # Strategy:
    # 1. If semantic extraction enabled, use SemanticExtractor
    # 2. Otherwise, try to extract from README_AI.md "Purpose" section
    # 3. Fallback to generic description

    # Check if semantic extraction is enabled
    if config.indexing.semantic.enabled:
        try:
            # Initialize semantic extractor
            extractor = SemanticExtractor(
                use_ai=config.indexing.semantic.use_ai,
                ai_command=config.ai_command if config.indexing.semantic.use_ai else None
            )

            # Build DirectoryContext
            files = []
            subdirs = []
            if dir_path.is_dir():
                files = [f.name for f in dir_path.iterdir() if f.is_file()]
                subdirs = [d.name for d in dir_path.iterdir() if d.is_dir()]

            # Try to get symbols from README_AI.md or scan directory
            # For now, we'll use a simplified approach without full parsing
            symbols = []
            imports = []

            # Quick symbol extraction from filenames
            for f in files:
                if f.endswith(('.py', '.php', '.java', '.ts', '.js')):
                    # Extract class/file name without extension
                    name = f.rsplit('.', 1)[0]
                    symbols.append(name)

            context = DirectoryContext(
                path=str(dir_path),
                files=files,
                subdirs=subdirs,
                symbols=symbols,
                imports=imports
            )

            # Extract semantic
            semantic = extractor.extract_directory_semantic(context)
            return semantic.description

        except Exception:
            # Fall through to README extraction
            pass

    # Try to extract from README_AI.md
    readme_path = dir_path / output_file
    if readme_path.exists():
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
                                return full_purpose
                            else:
                                # Smart truncate at word boundary
                                truncated = full_purpose[:80]
                                last_space = truncated.rfind(" ")
                                if last_space > 40:
                                    return truncated[:last_space] + "..."
                                else:
                                    return truncated + "..."
                    break
        except Exception:
            pass

    # Fallback to generic description
    return f"{dir_path.name} module"


@click.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
@click.option("--output", "-o", default="PROJECT_INDEX.md", help="Output filename")
def index(root: Path, output: str):
    """Generate PROJECT_INDEX.md - a lightweight project overview."""
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

        # Extract purpose using semantic extraction or README fallback
        purpose = extract_module_purpose(d, config, config.output_file)

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


@click.command()
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


@click.command()
@click.option("--since", default="HEAD~1", help="Starting commit reference")
@click.option("--until", default="HEAD", help="Ending commit reference")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def affected(since: str, until: str, as_json: bool):
    """Analyze git changes and show affected directories.

    Shows which directories need README_AI.md updates based on code changes.
    """
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
