"""Java language parser (backward compatibility shim).

DEPRECATED: This module exists for backward compatibility only.
New code should import from codeindex.parsers.java instead.

The Java parser has been refactored into a modular structure:
- codeindex.parsers.java.symbols - Symbol extraction
- codeindex.parsers.java.imports - Import extraction
- codeindex.parsers.java.inheritance - Inheritance extraction
- codeindex.parsers.java.calls - Call extraction
"""

# Re-export everything from the new location
from .java import (
    JavaParser,
    get_java_parser,
    is_java_file,
    parse_java_file,
)

__all__ = [
    "JavaParser",
    "is_java_file",
    "get_java_parser",
    "parse_java_file",
]
