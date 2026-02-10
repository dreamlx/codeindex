"""CLI commands for configuration and project status.

This module provides commands for initializing configuration files,
checking indexing status, and listing indexable directories.
"""

from pathlib import Path

import click
from rich.table import Table

from .cli_common import console
from .config import DEFAULT_CONFIG_NAME, Config
from .init_wizard import (
    create_codeindex_md,
    generate_config_yaml,
    run_interactive_wizard,
)
from .scanner import find_all_directories


@click.command()
@click.option("--force", "-f", is_flag=True, help="Overwrite existing config")
@click.option("--yes", "-y", is_flag=True, help="Non-interactive mode with defaults")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output (for CI/CD)")
@click.option("--help-config", is_flag=True, help="Show complete configuration reference")
def init(force: bool, yes: bool, quiet: bool, help_config: bool):
    """Initialize .codeindex.yaml configuration file.

    Interactive wizard guides you through setup with smart defaults.
    Use --yes for non-interactive mode (suitable for automation).
    """
    # Show configuration help if requested
    if help_config:
        from .config_help import show_full_config_help

        show_full_config_help()
        return
    config_path = Path.cwd() / DEFAULT_CONFIG_NAME

    if config_path.exists() and not force:
        if not quiet:
            console.print(f"[yellow]Config already exists:[/yellow] {config_path}")
            console.print("Use --force to overwrite")
        return

    project_dir = Path.cwd()

    # Non-interactive mode
    if yes:
        from .init_wizard import (
            calculate_batch_size,
            calculate_parallel_workers,
            count_files,
            detect_frameworks,
            detect_languages,
            infer_exclude_patterns,
            infer_include_patterns,
        )

        # Auto-detect everything
        detected_languages = detect_languages(project_dir)
        detected_frameworks = detect_frameworks(project_dir, detected_languages)
        include_patterns = infer_include_patterns(project_dir)
        exclude_patterns = infer_exclude_patterns(project_dir)

        file_count = count_files(project_dir, include_patterns)
        parallel_workers = calculate_parallel_workers(file_count)
        batch_size = calculate_batch_size(file_count)

        # Create minimal result
        from .init_wizard import WizardResult

        result = WizardResult(
            detected_languages=detected_languages,
            suggested_patterns={"include": include_patterns, "exclude": exclude_patterns},
            detected_frameworks=detected_frameworks,
            parallel_workers=parallel_workers,
            batch_size=batch_size,
            enable_hooks=False,  # Conservative default for non-interactive
            create_codeindex_md=True,  # Helpful for AI agents
            configure_ai=False,  # Skip in non-interactive
        )

        # Generate config
        yaml_content = generate_config_yaml(result, project_dir)
        config_path.write_text(yaml_content)

        # Create CODEINDEX.md
        if result.create_codeindex_md:
            create_codeindex_md(project_dir)

        if not quiet:
            console.print(f"[green]✓ Created:[/green] {config_path}")
            if result.create_codeindex_md:
                console.print("[green]✓ Created:[/green] CODEINDEX.md")

        return

    # Interactive mode (original behavior enhanced with wizard)
    result = run_interactive_wizard(project_dir)

    # Generate and write configuration
    yaml_content = generate_config_yaml(result, project_dir)
    config_path.write_text(yaml_content)
    result.config_created = True

    # Create CODEINDEX.md if requested
    if result.create_codeindex_md:
        codeindex_path = create_codeindex_md(project_dir)
        result.codeindex_md_created = True
        console.print(f"\n[green]✓ Created:[/green] {codeindex_path}")

    # Install Git Hooks if requested
    if result.enable_hooks:
        try:
            from .hooks import install_hooks

            install_hooks()
            result.hooks_installed = True
            console.print("[green]✓ Git Hooks installed[/green]")
        except Exception as e:
            console.print(f"[yellow]Warning:[/yellow] Could not install hooks: {e}")

    # Success summary
    console.print("\n[green]✓ Setup complete![/green]")
    console.print(f"\n[bold]Created:[/bold] {config_path}")
    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Run [cyan]codeindex scan-all[/cyan] to generate documentation")
    console.print("  2. Check [cyan]codeindex status[/cyan] to see coverage")

    return result


@click.command()
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


@click.command()
@click.option("--root", type=click.Path(exists=True, file_okay=False, path_type=Path), default=".")
def list_dirs(root: Path):
    """List all directories that would be indexed."""
    root = root.resolve()
    config = Config.load()

    dirs = find_all_directories(root, config)

    for d in dirs:
        rel = d.relative_to(root)
        print(rel)
