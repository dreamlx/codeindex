"""
Print system environment information.

This example demonstrates how codeindex parses Python files
and extracts symbols, imports, and docstrings.
"""

import os
import platform
import sys
from datetime import datetime


def get_python_info() -> dict:
    """Get Python interpreter information."""
    return {
        "version": sys.version,
        "executable": sys.executable,
        "platform": sys.platform,
    }


def get_os_info() -> dict:
    """Get operating system information."""
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
    }


def get_env_vars(prefix: str = "") -> dict:
    """
    Get environment variables.

    Args:
        prefix: Only return vars starting with this prefix

    Returns:
        Dictionary of environment variables
    """
    if prefix:
        return {k: v for k, v in os.environ.items() if k.startswith(prefix)}
    return dict(os.environ)


class SystemReporter:
    """Generate system environment reports."""

    def __init__(self, include_env: bool = False):
        """
        Initialize reporter.

        Args:
            include_env: Whether to include environment variables
        """
        self.include_env = include_env
        self.timestamp = datetime.now()

    def generate_report(self) -> str:
        """Generate a formatted system report."""
        lines = [
            "=" * 50,
            "System Environment Report",
            f"Generated: {self.timestamp.isoformat()}",
            "=" * 50,
            "",
            "## Python",
        ]

        for k, v in get_python_info().items():
            lines.append(f"  {k}: {v}")

        lines.extend(["", "## Operating System"])
        for k, v in get_os_info().items():
            lines.append(f"  {k}: {v}")

        if self.include_env:
            lines.extend(["", "## Environment Variables"])
            for k, v in sorted(get_env_vars().items()):
                lines.append(f"  {k}={v[:50]}...")

        return "\n".join(lines)


if __name__ == "__main__":
    reporter = SystemReporter(include_env=False)
    # Note: Use logging instead of print in production
    import logging
    logging.basicConfig(level=logging.INFO)
    logging.info("\n" + reporter.generate_report())
