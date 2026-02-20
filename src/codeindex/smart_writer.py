"""Smart README writer — backward-compatibility shim.

All implementation has moved to the writers/ package.
This module re-exports the public API so existing imports continue to work:
    from codeindex.smart_writer import SmartWriter, determine_level
"""

from .writers import LevelType, SmartWriter, WriteResult, determine_level

__all__ = ["SmartWriter", "WriteResult", "LevelType", "determine_level"]
