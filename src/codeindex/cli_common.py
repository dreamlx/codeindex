"""Common utilities for CLI modules.

This module provides shared resources used across all CLI command modules,
such as the Rich console instance for formatted output.
"""

import os

from rich.console import Console

# Shared console instance for all CLI commands
console = Console()


def print_deprecation_notice(what: str, instead: str) -> None:
    """Print a one-line deprecation notice to stderr.

    Per ADR-006, CLAUDE.md upkeep and hook management are moving to the
    codeindex Claude Code plugin. These CLI subcommands stay functional
    through v0.x but are deprecated and will be removed in v1.0.

    Suppressed when ``CODEINDEX_NO_DEPRECATION_WARNINGS`` is set (the
    post-commit hook sets this so it never spams per-commit output).
    Written to stderr so it never pollutes stdout / JSON output.
    """
    if os.environ.get("CODEINDEX_NO_DEPRECATION_WARNINGS"):
        return
    Console(stderr=True).print(
        f"[dim yellow]ℹ {what} is deprecated and will be removed in v1.0. "
        f"{instead}[/dim yellow]"
    )
