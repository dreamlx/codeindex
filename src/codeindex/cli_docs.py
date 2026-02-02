"""Documentation CLI commands for codeindex."""

from pathlib import Path

import click

from .cli_common import console


@click.group()
def docs():
    """Show codeindex documentation."""
    pass


@docs.command()
def show_ai_guide():
    """
    Show AI integration guide for Git Hooks.

    This command outputs the complete guide that AI Code tools can read
    to understand codeindex Git Hooks and update user project documentation.

    Usage:
        codeindex docs show-ai-guide
    """
    # Get the installed package location
    package_dir = Path(__file__).parent.parent.parent
    guide_path = package_dir / "examples" / "ai-integration-guide.md"

    if not guide_path.exists():
        console.print(
            "[red]Error:[/red] AI integration guide not found.\n"
            f"Expected at: {guide_path}\n\n"
            "Please reinstall codeindex or check installation.",
            style="red",
        )
        raise click.Abort()

    # Read and output the guide
    content = guide_path.read_text()

    console.print(
        "\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]"
    )
    console.print(
        "[bold cyan]  AI Integration Guide: codeindex Git Hooks[/bold cyan]"
    )
    console.print(
        "[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n"
    )

    console.print(content)

    console.print(
        "\n[bold cyan]═══════════════════════════════════════════════════[/bold cyan]"
    )
    console.print(
        "[dim]Tip: Your AI Code can read this output to understand Git Hooks[/dim]"
    )
    console.print(
        "[dim]Run: codeindex docs show-ai-guide > guide.md (to save to file)[/dim]"
    )
    console.print(
        "[bold cyan]═══════════════════════════════════════════════════[/bold cyan]\n"
    )
