"""Objective-C language parser.

This module provides the ObjCParser class that implements Objective-C-specific
symbol extraction, import resolution, inheritance extraction, and call
relationship analysis using tree-sitter.

Supports:
- @interface declarations (headers)
- @implementation (implementation files)
- @protocol declarations
- Instance methods (-)
- Class methods (+)
- Properties (@property)
- Import statements (#import)
- Inheritance relationships

The parser is organized into focused submodules:
- symbols: Symbol extraction (classes, methods, properties, protocols)
- imports: Import statement extraction (#import)
- inheritance: Class inheritance and protocol conformance extraction
- calls: Function/method call relationship extraction (planned)

Epic: #23
Story: 3.1
"""

import re
from pathlib import Path

from tree_sitter import Tree

from ..base import BaseLanguageParser
from .calls import extract_calls
from .imports import extract_imports
from .inheritance import extract_inheritances
from .symbols import extract_symbols

__all__ = ["ObjCParser"]


class ObjCParser(BaseLanguageParser):
    """Objective-C language parser.

    Extracts symbols, imports, calls, and inheritances from Objective-C source code.
    Supports both header files (.h) and implementation files (.m).
    Parses @interface, @implementation, and @protocol declarations.

    This class serves as a facade that delegates to specialized extraction
    functions in submodules.
    """

    def _preprocess_source(self, source_bytes: bytes) -> bytes:
        """Preprocess Objective-C source to handle unsupported macros.

        tree-sitter-objc doesn't support some Apple framework macros like:
        - NS_ASSUME_NONNULL_BEGIN/END
        - NS_SWIFT_NAME()
        - __attribute__()

        We replace these with comments to preserve line numbers for symbol locations.

        Args:
            source_bytes: Original source code

        Returns:
            Preprocessed source code with macros commented out
        """
        source = source_bytes.decode('utf-8', errors='replace')

        # Replace nullability macros with comments (preserve line numbers)
        source = re.sub(r'\bNS_ASSUME_NONNULL_BEGIN\b', '// NS_ASSUME_NONNULL_BEGIN', source)
        source = re.sub(r'\bNS_ASSUME_NONNULL_END\b', '// NS_ASSUME_NONNULL_END', source)

        # Comment out NS_SWIFT_NAME() - keep on same line
        source = re.sub(r'\bNS_SWIFT_NAME\([^)]*\)', '', source)

        # Comment out common attributes that cause issues
        source = re.sub(r'__attribute__\s*\([^)]*\)', '', source)
        source = re.sub(r'\b__deprecated\b', '', source)

        return source.encode('utf-8')

    def parse(self, path: Path):
        """Parse Objective-C source file with preprocessing.

        Override base parse() to add preprocessing step for Apple framework macros.

        Args:
            path: Path to source file

        Returns:
            ParseResult with extracted symbols
        """
        # Import here to avoid circular dependency
        from ...parser import ParseResult

        try:
            source_bytes = path.read_bytes()
        except Exception as e:
            return ParseResult(path=path, error=str(e), file_lines=0)

        # Calculate file lines
        file_lines = source_bytes.count(b"\n") + (
            1 if source_bytes and not source_bytes.endswith(b"\n") else 0
        )

        # Preprocess source to handle unsupported macros
        preprocessed_bytes = self._preprocess_source(source_bytes)

        # Parse with tree-sitter
        tree = self.parser.parse(preprocessed_bytes)

        # Check for syntax errors
        if tree.root_node.has_error:
            return ParseResult(
                path=path,
                error="Syntax error in source file",
                file_lines=file_lines,
            )

        # Extract all information (use preprocessed bytes for extraction)
        try:
            symbols = self.extract_symbols(tree, preprocessed_bytes)
            imports = self.extract_imports(tree, preprocessed_bytes)
            inheritances = self.extract_inheritances(tree, preprocessed_bytes)
            calls = self.extract_calls(tree, preprocessed_bytes, symbols, imports)

            return ParseResult(
                path=path,
                symbols=symbols,
                imports=imports,
                inheritances=inheritances,
                calls=calls,
                file_lines=file_lines,
            )
        except Exception as e:
            # Return partial result with error
            return ParseResult(
                path=path,
                symbols=[],
                imports=[],
                inheritances=[],
                calls=[],
                error=f"Failed to extract symbols: {e}",
                file_lines=file_lines,
            )

    def extract_symbols(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract symbols (classes, methods, properties, protocols) from the parse tree.

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
        return extract_calls(tree, source_bytes, symbols, imports)

    def extract_inheritances(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract class inheritance relationships from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Inheritance objects
        """
        return extract_inheritances(tree, source_bytes)
