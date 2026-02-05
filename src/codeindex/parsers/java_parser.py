"""Java language parser module.

This module provides a convenient interface for parsing Java files.
The actual implementation is in codeindex.parser.
"""

import os
import tempfile
from pathlib import Path

from codeindex.parser import PARSERS, ParseResult, parse_file


def is_java_file(path: str) -> bool:
    """Check if file is a Java source file."""
    return path.endswith('.java')


def get_java_parser():
    """Get the Java parser instance."""
    return PARSERS.get("java")


def parse_java_file(file_path: str, content: str) -> ParseResult:
    """
    Parse a Java source file.

    Args:
        file_path: Path to the Java file (for error reporting)
        content: Java source code content

    Returns:
        ParseResult containing symbols, imports, and docstrings
    """
    # Create temporary file with Java content
    with tempfile.NamedTemporaryFile(mode='w', suffix='.java', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        # Parse using the main parser
        result = parse_file(Path(temp_path), language="java")
        # Update path to original file path
        result.path = Path(file_path)
        return result
    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
