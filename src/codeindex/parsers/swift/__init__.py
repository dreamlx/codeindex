"""Swift language parser.

This module provides the SwiftParser class that implements Swift-specific
symbol extraction, import resolution, and inheritance relationship analysis
using tree-sitter.

The parser is organized into focused submodules:
- symbols: Symbol extraction (classes, structs, enums, protocols, functions, methods, properties)
- imports: Import statement extraction
- inheritance: Class/protocol inheritance and conformance extraction
- calls: Function/method call relationship extraction (TODO: Phase 3)

Current capabilities (v0.21.0):
- Basic symbol extraction (classes, structs, enums, protocols, functions)
- Property and method extraction
- Generic type parameters
- Access modifiers (public, private, internal, fileprivate)
- Protocol inheritance and conformance
- Extension support
- Docstring extraction (/// and /** */)
- Property wrappers (@Published, @State, etc.)

TODO (Phase 3):
- Call graph extraction
"""

from tree_sitter import Parser, Tree

from ..base import BaseLanguageParser
from .calls import extract_calls
from .imports import extract_imports
from .inheritance import extract_inheritances
from .symbols import extract_symbols

__all__ = ["SwiftParser"]


class SwiftParser(BaseLanguageParser):
    """Swift language parser.

    Extracts symbols (classes, structs, enums, protocols, functions, methods, properties),
    imports, inheritances, and call relationships from Swift source files.

    This class serves as a facade that delegates to specialized extraction
    functions in submodules.
    """

    def __init__(self, parser: Parser):
        """Initialize Swift parser.

        Args:
            parser: Tree-sitter parser configured for Swift
        """
        super().__init__(parser)

    def extract_symbols(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract symbols from Swift source code.

        Args:
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes

        Returns:
            List of Symbol objects
        """
        return extract_symbols(tree, source_bytes)

    def extract_imports(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract import statements from Swift source code.

        Args:
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes

        Returns:
            List of Import objects
        """
        return extract_imports(tree, source_bytes)

    def extract_calls(
        self, tree: Tree, source_bytes: bytes, symbols: list, imports: list
    ) -> list:
        """Extract call relationships from Swift source code.

        TODO: Phase 3 implementation.

        Args:
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes
            symbols: Previously extracted symbols
            imports: Previously extracted imports

        Returns:
            Empty list (not implemented in current version)
        """
        return extract_calls(tree, source_bytes, symbols, imports)

    def extract_inheritances(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract inheritance relationships from Swift source code.

        Args:
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes

        Returns:
            List of Inheritance objects
        """
        return extract_inheritances(tree, source_bytes)
