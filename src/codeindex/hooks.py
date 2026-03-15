"""
Legacy hooks module.

CLAUDE.md management has been moved to claude_md.py (v0.24.0+).
This module is kept for backward compatibility of imports only.
"""

# Re-export from new module for any external imports
from .claude_md import (  # noqa: F401
    check_outdated,
    extract_version,
    inject,
)
