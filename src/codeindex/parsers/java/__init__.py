"""Java language parser.

This module provides the JavaParser class that implements Java-specific
symbol extraction, import resolution, inheritance extraction, and call
relationship analysis using tree-sitter.

The parser is organized into focused submodules:
- symbols: Symbol extraction (classes, interfaces, enums, records, methods, fields)
- imports: Import statement extraction
- inheritance: Class inheritance relationship extraction (extends/implements)
- calls: Function/method call relationship extraction
"""

from pathlib import Path

from tree_sitter import Tree

from ..base import BaseLanguageParser
from .calls import extract_calls
from .imports import build_import_map, extract_imports
from .inheritance import extract_inheritances, extract_package
from .symbols import extract_module_docstring, extract_symbols

__all__ = ["JavaParser"]


class JavaParser(BaseLanguageParser):
    """Java language parser.

    Extracts symbols, imports, calls, and inheritances from Java source code.
    Supports Java classes, interfaces, enums, records, methods, fields,
    constructors, annotations, and generics.

    This class serves as a facade that delegates to specialized extraction
    functions in submodules.
    """

    def extract_symbols(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract symbols (classes, interfaces, methods, fields) from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Symbol objects
        """
        root = tree.root_node
        namespace = extract_package(tree, source_bytes)
        import_map = build_import_map(root, source_bytes)
        inheritances = []

        return extract_symbols(tree, source_bytes, namespace, import_map, inheritances)

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
        root = tree.root_node
        namespace = extract_package(tree, source_bytes)
        import_map = build_import_map(root, source_bytes)

        return extract_calls(
            tree, source_bytes, symbols, imports, namespace, import_map
        )

    def extract_inheritances(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract class inheritance relationships from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Inheritance objects
        """
        namespace = extract_package(tree, source_bytes)
        import_map = build_import_map(tree.root_node, source_bytes)

        return extract_inheritances(tree, source_bytes, namespace, import_map)

    def parse(self, path: Path):
        """Parse a Java source file.

        Overrides BaseLanguageParser.parse() to add module_docstring extraction.

        Args:
            path: Path to the source file

        Returns:
            ParseResult containing symbols, imports, calls, inheritances, and module_docstring
        """
        from ...parser import ParseResult

        try:
            source_bytes = Path(path).read_bytes()
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
            symbols = self.extract_symbols(tree, source_bytes)
            imports = self.extract_imports(tree, source_bytes)
            inheritances = self.extract_inheritances(tree, source_bytes)
            calls = self.extract_calls(tree, source_bytes, symbols, imports)

            # Extract module docstring (Java)
            module_docstring = extract_module_docstring(tree, source_bytes)

            # Extract package namespace
            namespace = extract_package(tree, source_bytes)

            return ParseResult(
                path=path,
                symbols=symbols,
                imports=imports,
                inheritances=inheritances,
                calls=calls,
                file_lines=file_lines,
                module_docstring=module_docstring,
                namespace=namespace,
            )
        except Exception as e:
            # Return partial result with error
            return ParseResult(
                path=path,
                error=f"Parse error: {str(e)}",
                file_lines=file_lines,
            )


# ==================== Backward Compatibility Functions ====================


def is_java_file(path: str) -> bool:
    """Check if file is a Java source file."""
    return path.endswith('.java')


def get_java_parser():
    """Get the Java parser instance (lazy loading)."""
    from ...parser import _get_parser
    return _get_parser("java")


def parse_java_file(file_path: str, content: str):
    """Parse a Java source file.

    Args:
        file_path: Path to the Java file (for error reporting)
        content: Java source code content

    Returns:
        ParseResult containing symbols, imports, and docstrings
    """
    import os
    import tempfile

    from ...parser import parse_file

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
