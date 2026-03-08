"""Python language parser.

This module provides the PythonParser class that implements Python-specific
symbol extraction, import resolution, and call relationship analysis using tree-sitter.

The parser is organized into focused submodules:
- symbols: Symbol extraction (classes, functions, methods)
- imports: Import statement extraction
- inheritance: Class inheritance relationship extraction
- calls: Function/method call relationship extraction
"""

from pathlib import Path

from tree_sitter import Tree

from ..base import BaseLanguageParser
from .calls import extract_calls
from .imports import extract_imports
from .inheritance import extract_inheritances
from .symbols import extract_module_docstring, extract_symbols

__all__ = ["PythonParser"]


class PythonParser(BaseLanguageParser):
    """Python language parser.

    Extracts symbols (classes, functions, methods), imports, inheritances,
    and call relationships from Python source files.

    This class serves as a facade that delegates to specialized extraction
    functions in submodules.
    """

    def extract_symbols(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract symbols (classes, functions, methods) from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Symbol objects
        """
        return extract_symbols(tree, source_bytes)

    def extract_imports(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract import statements from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Import objects
        """
        return extract_imports(tree, source_bytes)

    def extract_calls(
        self, tree: Tree, source_bytes: bytes, symbols: list, imports: list
    ) -> list:
        """Extract function/method call relationships from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes
            symbols: Previously extracted symbols
            imports: Previously extracted imports

        Returns:
            List of Call objects
        """
        # Extract inheritances first (needed for super() resolution)
        inheritances = self.extract_inheritances(tree, source_bytes)

        # Extract call relationships
        calls = extract_calls(tree, source_bytes, symbols, imports, inheritances)

        return calls

    def extract_inheritances(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract class inheritance relationships from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Inheritance objects
        """
        return extract_inheritances(tree, source_bytes)

    def parse(self, path: Path):
        """Parse a Python source file.

        This overrides the base parse() method to add module docstring extraction.

        Args:
            path: Path to the source file

        Returns:
            ParseResult containing symbols, imports, calls, and inheritances
        """
        from ...parser import ParseResult

        try:
            source_bytes = path.read_bytes()
        except Exception as e:
            return ParseResult(path=path, error=str(e), file_lines=0)

        # Calculate file lines
        file_lines = source_bytes.count(b"\n") + (
            1 if source_bytes and not source_bytes.endswith(b"\n") else 0
        )

        # Parse with tree-sitter
        tree = self.parser.parse(source_bytes)

        # Check for syntax errors (tree-sitter doesn't throw exceptions)
        if tree.root_node.has_error:
            return ParseResult(
                path=path,
                error="Syntax error in source file",
                file_lines=file_lines,
            )

        # Extract all information
        try:
            # Extract module docstring first
            module_docstring = extract_module_docstring(tree, source_bytes)

            symbols = self.extract_symbols(tree, source_bytes)
            imports = self.extract_imports(tree, source_bytes)
            inheritances = self.extract_inheritances(tree, source_bytes)
            calls = self.extract_calls(tree, source_bytes, symbols, imports)

            return ParseResult(
                path=path,
                symbols=symbols,
                imports=imports,
                inheritances=inheritances,
                calls=calls,
                file_lines=file_lines,
                module_docstring=module_docstring,
            )
        except Exception as e:
            # Return partial result with error
            return ParseResult(
                path=path,
                error=f"Parse error: {str(e)}",
                file_lines=file_lines,
            )
