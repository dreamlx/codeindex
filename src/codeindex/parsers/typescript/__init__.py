"""TypeScript/JavaScript language parser.

This module provides parsing for TypeScript (.ts), TSX (.tsx),
JavaScript (.js), and JSX (.jsx) files using tree-sitter.

A single TypeScriptParser class handles all 4 file types with 3 grammar variants:
- .ts  → tree-sitter-typescript (language_typescript)
- .tsx → tree-sitter-typescript (language_tsx)
- .js/.jsx → tree-sitter-javascript (language)

The parser is organized into focused submodules:
- symbols: Symbol extraction (classes, functions, methods, interfaces, enums, types)
- imports: Import statement extraction (ES6/CommonJS)
- inheritance: Class/interface inheritance relationship extraction
- calls: Function/method call relationship extraction
"""

from pathlib import Path

from tree_sitter import Language, Parser, Tree

from ..base import BaseLanguageParser
from .calls import extract_calls
from .imports import extract_imports
from .inheritance import extract_inheritances
from .symbols import extract_module_docstring, extract_symbols

__all__ = ["TypeScriptParser", "is_typescript_file", "get_typescript_parser"]


class TypeScriptParser(BaseLanguageParser):
    """TypeScript/JavaScript language parser.

    Handles .ts, .tsx, .js, .jsx files using the appropriate tree-sitter grammar.
    Extracts symbols, imports, calls, and inheritances.

    This class serves as a facade that delegates to specialized extraction
    functions in submodules.
    """

    # Grammar routing: extension → (grammar_name, grammar_loader)
    GRAMMAR_MAP = {
        ".ts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "javascript",
    }

    def __init__(self, parser: Parser, grammar_name: str = "typescript"):
        """Initialize the TypeScript parser.

        Args:
            parser: A configured tree-sitter Parser
            grammar_name: One of 'typescript', 'tsx', 'javascript'
        """
        super().__init__(parser)
        self.grammar_name = grammar_name

    @staticmethod
    def create_for_file(file_path: Path) -> "TypeScriptParser":
        """Create a TypeScriptParser configured for the given file extension.

        Args:
            file_path: Path to the source file

        Returns:
            TypeScriptParser with correct grammar loaded
        """
        ext = file_path.suffix.lower()
        grammar_name = TypeScriptParser.GRAMMAR_MAP.get(ext, "typescript")

        if grammar_name == "typescript":
            import tree_sitter_typescript as ts_ts
            lang = Language(ts_ts.language_typescript())
        elif grammar_name == "tsx":
            import tree_sitter_typescript as ts_ts
            lang = Language(ts_ts.language_tsx())
        elif grammar_name == "javascript":
            import tree_sitter_javascript as ts_js
            lang = Language(ts_js.language())
        else:
            raise ValueError(f"Unknown grammar: {grammar_name}")

        parser = Parser(lang)
        return TypeScriptParser(parser, grammar_name)

    def extract_symbols(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract symbols (classes, functions, methods, etc.) from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Symbol objects
        """
        return extract_symbols(tree, source_bytes)

    def extract_imports(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract import/export-from statements from the parse tree.

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
        """Extract class/interface inheritance relationships from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Inheritance objects
        """
        return extract_inheritances(tree, source_bytes)

    def parse(self, path: Path):
        """Parse a TypeScript/JavaScript source file.

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

        file_lines = source_bytes.count(b"\n") + (
            1 if source_bytes and not source_bytes.endswith(b"\n") else 0
        )

        if not source_bytes.strip():
            return ParseResult(path=path, file_lines=file_lines)

        tree = self.parser.parse(source_bytes)

        if tree.root_node.has_error:
            return ParseResult(
                path=path,
                error="Syntax error in source file",
                file_lines=file_lines,
            )

        try:
            symbols = self.extract_symbols(tree, source_bytes)
            imports = self.extract_imports(tree, source_bytes)
            inheritances = self.extract_inheritances(tree, source_bytes)
            calls = self.extract_calls(tree, source_bytes, symbols, imports)
            module_docstring = extract_module_docstring(tree, source_bytes)

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
            return ParseResult(
                path=path,
                error=f"Parse error: {str(e)}",
                file_lines=file_lines,
            )


# ==================== Backward Compatibility Functions ====================


def is_typescript_file(path: str) -> bool:
    """Check if file is a TypeScript/JavaScript source file.

    Args:
        path: Path to the file

    Returns:
        True if file has .ts, .tsx, .js, or .jsx extension
    """
    return any(path.endswith(ext) for ext in (".ts", ".tsx", ".js", ".jsx"))


def get_typescript_parser():
    """Get the TypeScript parser instance (lazy loading).

    Returns:
        TypeScriptParser instance
    """
    from ...parser import _get_parser
    return _get_parser("typescript")
