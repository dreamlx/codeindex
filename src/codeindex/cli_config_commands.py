"""CLI commands for configuration help and explanation (Epic 15 Story 15.3).

This module provides commands for:
- Explaining individual configuration parameters
- Showing configuration documentation
- Context-aware help
"""

import os

import click

from .config_help import explain_parameter, get_current_config_value


@click.group()
def config():
    """Configuration help and explanation commands."""
    pass


@config.command()
@click.argument("parameter")
def explain(parameter: str):
    """Explain a specific configuration parameter.

    Examples:
        codeindex config explain parallel_workers
        codeindex config explain batch_size
        codeindex config explain hooks.post_commit.mode
    """
    # Try to get current value from config
    current_value = None
    try:
        current_value = get_current_config_value(parameter)
    except Exception:
        pass  # Config file doesn't exist or parameter not found

    # Get system info for validation
    cpu_count = os.cpu_count()

    # Display explanation
    exit_code = explain_parameter(parameter, current_value=current_value, cpu_count=cpu_count)

    if exit_code != 0:
        raise click.ClickException(f"Unknown parameter: {parameter}")
