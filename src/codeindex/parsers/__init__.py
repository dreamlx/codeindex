"""Language-specific parser modules.

This package contains modular parsers for different programming languages.
Each language has its own parser module that implements the BaseLanguageParser interface.
"""

from .base import BaseLanguageParser
from .java import JavaParser
from .objc import ObjCParser
from .php import PhpParser
from .python import PythonParser
from .swift import SwiftParser
from .typescript import TypeScriptParser
from .utils import count_arguments, get_node_text

__all__ = [
    "BaseLanguageParser",
    "PythonParser",
    "PhpParser",
    "JavaParser",
    "TypeScriptParser",
    "SwiftParser",
    "ObjCParser",
    "get_node_text",
    "count_arguments",
]
