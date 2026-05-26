"""CLI commands for CLAUDE.md management."""

from pathlib import Path

import click
from rich.console import Console

from . import __version__
from .claude_md import check_outdated, extract_version, inject

console = Console()


@click.group("claude-md")
def claude_md():
    """Manage codeindex section in CLAUDE.md."""
    pass


@claude_md.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True, path_type=Path),
    default=".",
    help="Project root directory (default: current directory).",
)
def update(project_dir: Path):
    """Update codeindex section in project CLAUDE.md."""
    project_dir = project_dir.resolve()
    claude_md_path = project_dir / "CLAUDE.md"

    old_version = extract_version(claude_md_path)

    success = inject(claude_md_path, __version__)

    if success:
        if old_version:
            console.print(
                f"[green]✓[/green] Updated codeindex section: "
                f"v{old_version} → v{__version__}"
            )
        else:
            console.print(
                f"[green]✓[/green] Injected codeindex section (v{__version__}) "
                f"into {claude_md_path.name}"
            )
    else:
        console.print("[red]✗[/red] Failed to update CLAUDE.md")
        raise SystemExit(1)


@claude_md.command()
@click.option(
    "--project-dir",
    type=click.Path(exists=True, path_type=Path),
    default=".",
    help="Project root directory (default: current directory).",
)
def status(project_dir: Path):
    """Check if codeindex section in CLAUDE.md is up-to-date."""
    project_dir = project_dir.resolve()
    claude_md_path = project_dir / "CLAUDE.md"

    if not claude_md_path.exists():
        console.print("[yellow]No CLAUDE.md found.[/yellow] Run `codeindex claude-md update` to create one.")
        return

    injected_version = extract_version(claude_md_path)

    if injected_version is None:
        console.print("[yellow]No codeindex section found.[/yellow] Run `codeindex claude-md update` to inject.")
        return

    if injected_version == __version__:
        console.print(f"[green]✓[/green] CLAUDE.md is up-to-date (v{__version__})")
    else:
        console.print(
            f"[yellow]⚠[/yellow] CLAUDE.md has v{injected_version}, "
            f"current is v{__version__}. Run `codeindex claude-md update`."
        )


def print_outdated_warning():
    """Print a one-line warning if CLAUDE.md is outdated. Called on CLI startup."""
    outdated_version = check_outdated()
    if outdated_version:
        console.print(
            f"[dim yellow]hint: CLAUDE.md has codeindex v{outdated_version}, "
            f"current is v{__version__}. "
            f"Run `codeindex claude-md update` to refresh.[/dim yellow]"
        )
