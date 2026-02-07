"""Language-specific parser modules.

This package contains modular parsers for different programming languages.
Each language has its own parser module that implements the BaseLanguageParser interface.
"""

from .base import BaseLanguageParser
from .java_parser import JavaParser
from .php_parser import PhpParser
from .python_parser import PythonParser
from .utils import count_arguments, get_node_text

__all__ = [
    "BaseLanguageParser",
    "PythonParser",
    "PhpParser",
    "JavaParser",
    "get_node_text",
    "count_arguments",
]
