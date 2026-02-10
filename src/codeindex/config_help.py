"""Configuration help documentation for codeindex (Epic 15 Story 15.3).

This module provides comprehensive help documentation for all .codeindex.yaml
configuration parameters, including:
- Parameter descriptions
- Value ranges and defaults
- Performance tuning recommendations
- Examples and trade-offs
"""

from typing import Dict, Optional

from rich.console import Console

console = Console()


# ============================================================================
# Configuration Parameter Documentation
# ============================================================================

CONFIG_PARAMS: Dict[str, Dict[str, str]] = {
    "parallel_workers": {
        "name": "parallel_workers",
        "type": "int",
        "default": "CPU count (8)",
        "range": "1-32",
        "description": "Number of concurrent workers for scanning",
        "recommendations": """
  • Small projects (<100 files): 4
  • Medium projects (100-1000 files): 8
  • Large projects (>1000 files): 16
  • CI/CD: 4 (conservative)""",
        "trade_offs": "Higher values = faster scanning but more CPU/memory usage",
        "example": "parallel_workers: 8",
    },
    "batch_size": {
        "name": "batch_size",
        "type": "int",
        "default": "50",
        "range": "10-200",
        "description": "Files processed per batch",
        "recommendations": """
  • Normal: 50
  • Low memory: 20
  • High performance: 100""",
        "trade_offs": """
  • Larger = faster but more memory
  • Smaller = slower but less memory""",
        "example": "batch_size: 50",
    },
    "ai_command": {
        "name": "ai_command",
        "type": "string",
        "default": "(not set)",
        "description": "AI CLI command template for documentation generation",
        "examples": """
  • Claude: 'claude -p "{prompt}" --allowedTools "Read"'
  • ChatGPT: 'chatgpt "{prompt}"'
  • Custom: 'your-ai-cli "{prompt}"'""",
        "example": 'ai_command: \'claude -p "{prompt}" --allowedTools "Read"\'',
    },
    "languages": {
        "name": "languages",
        "type": "list[string]",
        "default": "(auto-detected)",
        "description": "Programming languages to index",
        "supported": "python, php, java, javascript, typescript, go, rust, ruby",
        "example": """languages:
  - python
  - php""",
    },
    "include": {
        "name": "include",
        "type": "list[string]",
        "default": "(auto-inferred)",
        "description": "Directory patterns to include in scanning",
        "example": """include:
  - src/
  - lib/""",
    },
    "exclude": {
        "name": "exclude",
        "type": "list[string]",
        "default": "(standard exclusions)",
        "description": "Directory patterns to exclude from scanning",
        "example": """exclude:
  - "**/__pycache__/**"
  - "**/node_modules/**"
  - "**/.git/**\"""",
    },
    "hooks.post_commit.enabled": {
        "name": "hooks.post_commit.enabled",
        "type": "bool",
        "default": "false",
        "description": "Enable/disable Git post-commit hook",
        "example": """hooks:
  post_commit:
    enabled: true""",
    },
    "hooks.post_commit.mode": {
        "name": "hooks.post_commit.mode",
        "type": "string",
        "default": "auto",
        "options": "auto, disabled, async, sync, prompt",
        "description": "Git Hooks execution mode",
        "mode_descriptions": """
  • auto: Smart mode based on change size
  • disabled: Skip all updates
  • async: Background updates (non-blocking)
  • sync: Wait for updates to complete
  • prompt: Ask user before running""",
        "example": """hooks:
  post_commit:
    mode: auto""",
    },
    "output_file": {
        "name": "output_file",
        "type": "string",
        "default": "README_AI.md",
        "description": "Name of generated documentation files",
        "example": "output_file: README_AI.md",
    },
}


# ============================================================================
# Help Display Functions
# ============================================================================


def show_full_config_help() -> None:
    """Display full configuration reference with all parameters."""
    console.print("\n[bold cyan]📖 codeindex Configuration Reference[/bold cyan]\n")

    console.print("[bold]Performance Settings[/bold] ⚡\n")
    _show_param_section("parallel_workers")
    _show_param_section("batch_size")

    console.print("\n[bold]AI Integration[/bold] 🤖\n")
    _show_param_section("ai_command")

    console.print("\n[bold]Project Structure[/bold] 📁\n")
    _show_param_section("languages")
    _show_param_section("include")
    _show_param_section("exclude")

    console.print("\n[bold]Git Hooks[/bold] 🔗\n")
    _show_param_section("hooks.post_commit.enabled")
    _show_param_section("hooks.post_commit.mode")

    console.print("\n[bold]Output[/bold] 📝\n")
    _show_param_section("output_file")

    console.print("\n[dim]💡 Tip: Use 'codeindex config explain <parameter>' for detailed help[/dim]\n")


def _show_param_section(param_name: str) -> None:
    """Show a single parameter section in config help.

    Args:
        param_name: Name of the parameter to display
    """
    param = CONFIG_PARAMS.get(param_name)
    if not param:
        return

    console.print(f"[bold]{param['name']}[/bold]: {param.get('default', 'N/A')}")
    console.print(f"  # {param['description']}")

    if "type" in param:
        console.print(f"  # Type: {param['type']}")

    if "range" in param:
        console.print(f"  # Range: {param['range']}")

    if "options" in param:
        console.print(f"  # Options: {param['options']}")

    if "recommendations" in param:
        console.print(f"  # Recommendation:{param['recommendations']}")

    if "trade_offs" in param:
        console.print(f"  # Trade-off:{param['trade_offs']}")

    console.print()


def explain_parameter(
    param_name: str, current_value: Optional[any] = None, cpu_count: Optional[int] = None
) -> int:
    """Explain a specific configuration parameter.

    Args:
        param_name: Name of the parameter to explain
        current_value: Current value from user's config (if exists)
        cpu_count: System CPU count for validation

    Returns:
        Exit code (0 for success, 1 for unknown parameter)
    """
    param = CONFIG_PARAMS.get(param_name)

    if not param:
        console.print(f"[red]✗ Unknown parameter:[/red] {param_name}")
        console.print("\n[dim]Available parameters:[/dim]")
        for name in sorted(CONFIG_PARAMS.keys()):
            console.print(f"  • {name}")
        return 1

    # Display parameter information
    console.print(f"\n[bold cyan]{param['name']}[/bold cyan]\n")
    console.print(f"[bold]Description:[/bold] {param['description']}")

    if "type" in param:
        console.print(f"[bold]Type:[/bold] {param['type']}")

    if "default" in param:
        console.print(f"[bold]Default:[/bold] {param['default']}")

    if "range" in param:
        console.print(f"[bold]Range:[/bold] {param['range']}")

    if "options" in param:
        console.print(f"[bold]Options:[/bold] {param['options']}")

    # Show current value if provided
    if current_value is not None:
        console.print(f"\n[bold]Current value:[/bold] {current_value}")

        # Validate and warn if needed
        if param_name == "parallel_workers" and cpu_count:
            if current_value > cpu_count:
                console.print(
                    f"[yellow]⚠ Warning:[/yellow] Value exceeds CPU count ({cpu_count}). "
                    f"May not improve performance."
                )

    # Show recommendations
    if "recommendations" in param:
        console.print(f"\n[bold]Recommendation:[/bold]{param['recommendations']}")

    # Show trade-offs
    if "trade_offs" in param:
        console.print(f"\n[bold]Trade-off:[/bold]{param['trade_offs']}")

    # Show mode descriptions (for hooks.post_commit.mode)
    if "mode_descriptions" in param:
        console.print(f"\n[bold]Modes:[/bold]{param['mode_descriptions']}")

    # Show examples
    if "example" in param:
        console.print(f"\n[bold]Example:[/bold]\n```yaml\n{param['example']}\n```")

    if "examples" in param:
        console.print(f"\n[bold]Examples:[/bold]{param['examples']}")

    console.print()
    return 0


def get_current_config_value(param_name: str, config_path: Optional[str] = None) -> Optional[any]:
    """Get current value of a parameter from config file.

    Args:
        param_name: Name of the parameter
        config_path: Path to .codeindex.yaml (default: current directory)

    Returns:
        Current value or None if not found
    """
    try:
        from pathlib import Path

        from .config import Config

        if config_path:
            config = Config.load(Path(config_path))
        else:
            config = Config.load()

        # Navigate nested attributes (e.g., hooks.post_commit.mode)
        parts = param_name.split(".")
        value = config

        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

        return value
    except Exception:
        return None
