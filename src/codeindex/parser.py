"""Multi-language AST parser using tree-sitter.

Epic 13: Parser Modularization - Phase 3
This module serves as the unified entry point for all language parsers.
Language-specific logic has been extracted to modular parser classes.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from tree_sitter import Language, Parser


class CallType(Enum):
    """Call type enumeration (Epic 11).

    Distinguishes between different types of function/method calls
    for knowledge graph construction.
    """

    FUNCTION = "function"  # Function call: calculate()
    METHOD = "method"  # Instance method: obj.method()
    STATIC_METHOD = "static_method"  # Static method: Class.method()
    CONSTRUCTOR = "constructor"  # Constructor: new Class() / __init__
    DYNAMIC = "dynamic"  # Dynamic call: getattr(obj, name)()


@dataclass
class Call:
    """Function/method call relationship (Epic 11).

    Represents caller → callee relationships for knowledge graph construction.
    Used by LoomGraph to build CALLS relations.

    Attributes:
        caller: Full name of calling function/method (with namespace)
            Examples:
            - "myproject.service.UserService.create_user"
            - "com.example.UserController.handleRequest"

        callee: Full name of called function/method (with namespace), None for dynamic
            Examples:
            - "pandas.read_csv" (alias resolved)
            - "com.example.User.<init>" (constructor)
            - None (unresolvable dynamic call)

        line_number: Line number where call occurs (1-based)

        call_type: Type of call (CallType enum)

        arguments_count: Number of arguments (best-effort, None if uncertain)

    Added in v0.13.0 for LoomGraph integration (Epic 11, Story 11.1).
    """

    caller: str
    callee: Optional[str]
    line_number: int
    call_type: CallType
    arguments_count: Optional[int] = None

    @property
    def is_dynamic(self) -> bool:
        """Whether this is a dynamic call (callee unknown)."""
        return self.call_type == CallType.DYNAMIC

    @property
    def is_resolved(self) -> bool:
        """Whether the callee was successfully resolved."""
        return self.callee is not None

    def to_dict(self) -> dict:
        """Convert Call to JSON-serializable dict."""
        return {
            "caller": self.caller,
            "callee": self.callee,
            "line_number": self.line_number,
            "call_type": self.call_type.value,
            "arguments_count": self.arguments_count,
        }

    @staticmethod
    def from_dict(data: dict) -> "Call":
        """Create Call from JSON dict."""
        return Call(
            caller=data["caller"],
            callee=data.get("callee"),
            line_number=data["line_number"],
            call_type=CallType(data["call_type"]),
            arguments_count=data.get("arguments_count"),
        )


@dataclass
class Symbol:
    """Represents a code symbol (class, function, etc.)."""

    name: str
    kind: str  # class, function, method
    signature: str = ""
    docstring: str = ""
    line_start: int = 0
    line_end: int = 0
    annotations: list["Annotation"] = field(default_factory=list)  # Story 7.1.2.1

    def to_dict(self) -> dict:
        """Convert Symbol to JSON-serializable dict."""
        return {
            "name": self.name,
            "kind": self.kind,
            "signature": self.signature,
            "docstring": self.docstring,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "annotations": [a.to_dict() for a in self.annotations],
        }


@dataclass
class Import:
    """Represents an import statement (extended for LoomGraph).

    Attributes:
        module: Module name (e.g., "numpy", "os.path")
        names: Imported names (e.g., ["join", "exists"])
        is_from: Whether it's a "from X import Y" statement
        alias: Import alias (e.g., "np" in "import numpy as np")
                Added in v0.9.0 for LoomGraph integration

    Examples:
        import numpy as np → Import("numpy", [], False, alias="np")
        from typing import Dict as DictType → Import("typing", ["Dict"], True, alias="DictType")
        import os → Import("os", [], False, alias=None)
    """

    module: str
    names: list[str] = field(default_factory=list)
    is_from: bool = False
    alias: str | None = None  # Added in v0.9.0 for LoomGraph integration

    def to_dict(self) -> dict:
        """Convert Import to JSON-serializable dict."""
        return {
            "module": self.module,
            "names": self.names,
            "is_from": self.is_from,
            "alias": self.alias,
        }


@dataclass
class Inheritance:
    """Class inheritance information for knowledge graph construction.

    Represents parent-child relationships between classes/interfaces.
    Used by LoomGraph to build INHERITS relations in knowledge graph.

    Attributes:
        child: Child class name (e.g., "AdminUser")
        parent: Parent class/interface name (e.g., "BaseUser")

    Examples:
        Python: class AdminUser(BaseUser) → Inheritance("AdminUser", "BaseUser")
        PHP: class AdminUser extends BaseUser → Inheritance("AdminUser", "BaseUser")
        Java: class AdminUser extends BaseUser → Inheritance("AdminUser", "BaseUser")

    Added in v0.9.0 for LoomGraph integration (Epic 10, Story 10.3).
    """

    child: str
    parent: str

    def to_dict(self) -> dict:
        """Convert Inheritance to JSON-serializable dict."""
        return {
            "child": self.child,
            "parent": self.parent,
        }


@dataclass
class Annotation:
    """Represents a code annotation/decorator (e.g., Java @RestController).

    Story 7.1.2.1: Annotation Extraction
    Supports extraction of annotations from Java classes, methods, and fields.
    """

    name: str
    arguments: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert Annotation to JSON-serializable dict."""
        return {
            "name": self.name,
            "arguments": self.arguments,
        }


@dataclass
class ParseResult:
    """Result of parsing a file (extended for LoomGraph).

    Attributes:
        path: File path
        symbols: Extracted symbols (classes, functions, methods, etc.)
        imports: Import statements
        inheritances: Class inheritance relationships (added in v0.9.0)
        calls: Function/method call relationships (added in v0.13.0, Epic 11)
        module_docstring: Module-level docstring
        namespace: Namespace (PHP only)
        error: Parse error message if any
        file_lines: Number of lines in the file
    """

    path: Path
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[Import] = field(default_factory=list)
    inheritances: list[Inheritance] = field(default_factory=list)  # Added in v0.9.0
    calls: list[Call] = field(default_factory=list)  # Added in v0.13.0 (Epic 11)
    module_docstring: str = ""
    namespace: str = ""  # PHP namespace
    error: str | None = None
    file_lines: int = 0  # Number of lines in the file

    def to_dict(self) -> dict:
        """Convert ParseResult to JSON-serializable dict."""
        return {
            "path": str(self.path),
            "symbols": [symbol.to_dict() for symbol in self.symbols],
            "imports": [imp.to_dict() for imp in self.imports],
            "inheritances": [inh.to_dict() for inh in self.inheritances],
            "calls": [call.to_dict() for call in self.calls],  # Epic 11
            "module_docstring": self.module_docstring,
            "namespace": self.namespace,
            "error": self.error,
            "file_lines": self.file_lines,
        }


# File extension to language mapping
FILE_EXTENSIONS: Dict[str, str] = {
    ".py": "python",
    ".php": "php",
    ".phtml": "php",
    ".java": "java",
}

# Parser cache for lazy loading (avoids re-initialization)
_PARSER_CACHE: Dict[str, Parser] = {}


def _get_parser(language: str) -> Parser | None:
    """Get or create a parser for the specified language (lazy loading).

    This function implements lazy loading to avoid importing all language
    parsers at module load time. Only the needed parser is imported and
    initialized when first used.

    Args:
        language: Language name ("python", "php", "java")

    Returns:
        Parser instance for the language, or None if unsupported

    Raises:
        ImportError: If the tree-sitter library for the language is not installed

    Example:
        parser = _get_parser("python")  # Only imports tree-sitter-python
    """
    # Return cached parser if available
    if language in _PARSER_CACHE:
        return _PARSER_CACHE[language]

    # Lazy import and initialize parser based on language
    try:
        if language == "python":
            import tree_sitter_python as tspython

            lang = Language(tspython.language())
        elif language == "php":
            import tree_sitter_php as tsphp

            lang = Language(tsphp.language_php())
        elif language == "java":
            import tree_sitter_java as tsjava

            lang = Language(tsjava.language())
        else:
            return None

        # Create and cache parser
        parser = Parser(lang)
        _PARSER_CACHE[language] = parser
        return parser

    except ImportError as e:
        # Provide helpful error message
        raise ImportError(
            f"tree-sitter-{language} is not installed. "
            f"Install it with: pip install tree-sitter-{language}"
        ) from e


def parse_file(path: Path, language: str | None = None) -> ParseResult:
    """Parse a source file (Python, PHP, or Java) and extract symbols and imports.

    Epic 13, Phase 3: Simplified entry point that delegates to language parsers.

    Args:
        path: Path to the source file
        language: Optional language override ("python", "php", "java").
                  If None, language is detected from file extension.

    Returns:
        ParseResult containing symbols, imports, calls, inheritances, and docstrings
    """
    # Determine language from file extension if not specified
    if language is None:
        language = _get_language(path)

    if not language:
        # Read file to get line count for error reporting
        try:
            file_lines = path.read_bytes().count(b"\n") + 1
        except Exception:
            file_lines = 0
        return ParseResult(
            path=path, error=f"Unsupported file type: {path.suffix}", file_lines=file_lines
        )

    # Get tree-sitter parser (lazy loading)
    try:
        parser = _get_parser(language)
    except ImportError as e:
        # Read file to get line count
        try:
            file_lines = path.read_bytes().count(b"\n") + 1
        except Exception:
            file_lines = 0
        return ParseResult(path=path, error=str(e), file_lines=file_lines)

    if not parser:
        return ParseResult(path=path, error=f"Unsupported language: {language}", file_lines=0)

    # Delegate to language-specific parser (Epic 13 refactoring)
    from .parsers import JavaParser, PhpParser, PythonParser

    if language == "python":
        lang_parser = PythonParser(parser)
    elif language == "php":
        lang_parser = PhpParser(parser)
    elif language == "java":
        lang_parser = JavaParser(parser)
    else:
        return ParseResult(path=path, error=f"Unsupported language: {language}", file_lines=0)

    # Use language parser's parse method
    return lang_parser.parse(path)


def parse_directory(paths: list[Path]) -> list[ParseResult]:
    """Parse multiple files."""
    return [parse_file(p) for p in paths]


def _get_language(file_path: Path) -> str:
    """Determine language from file extension."""
    suffix = file_path.suffix.lower()
    return FILE_EXTENSIONS.get(suffix)
