"""Common utilities for CLI modules.

This module provides shared resources used across all CLI command modules,
such as the Rich console instance for formatted output.
"""

from rich.console import Console

# Shared console instance for all CLI commands
console = Console()
