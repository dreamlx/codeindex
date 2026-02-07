"""Multi-language AST parser using tree-sitter."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from tree_sitter import Language, Node, Parser


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


def _get_node_text(node, source_bytes: bytes) -> str:
    """Extract text from a tree-sitter node."""
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8")


def _extract_docstring(node, source_bytes: bytes) -> str:
    """Extract docstring from first child if it's a string."""
    if node.child_count == 0:
        return ""

    # Look for expression_statement containing string
    for child in node.children:
        if child.type == "block":
            for block_child in child.children:
                if block_child.type == "expression_statement":
                    for expr_child in block_child.children:
                        if expr_child.type == "string":
                            text = _get_node_text(expr_child, source_bytes)
                            # Remove quotes
                            if text.startswith('"""') or text.startswith("'''"):
                                return text[3:-3].strip()
                            elif text.startswith('"') or text.startswith("'"):
                                return text[1:-1].strip()
                    break
            break

    return ""


def _parse_function(
    node,
    source_bytes: bytes,
    class_name: str = "",
    decorators: list[str] | None = None
) -> Symbol:
    """Parse a function definition node."""
    name = ""
    signature_parts = []

    for child in node.children:
        if child.type == "identifier":  # function name is 'identifier', not 'name'
            name = _get_node_text(child, source_bytes)
        elif child.type == "parameters":
            signature_parts.append(_get_node_text(child, source_bytes))
        elif child.type == "type":
            signature_parts.append(f" -> {_get_node_text(child, source_bytes)}")

    kind = "method" if class_name else "function"
    full_name = f"{class_name}.{name}" if class_name else name
    signature = f"def {name}{''.join(signature_parts)}"
    docstring = _extract_docstring(node, source_bytes)

    return Symbol(
        name=full_name,
        kind=kind,
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_class(
    node, source_bytes: bytes, parent_class: str = "", inheritances: list[Inheritance] | None = None
) -> list[Symbol]:
    """Parse a class definition node and its methods.

    Args:
        node: Tree-sitter class_definition node
        source_bytes: Source code bytes
        parent_class: Parent class name for nested classes (e.g., "Outer" for Outer.Inner)
        inheritances: List to append Inheritance objects to (Epic 10, Story 10.1.1)

    Returns:
        List of Symbol objects (class + methods)
    """
    if inheritances is None:
        inheritances = []

    symbols = []
    class_name = ""
    bases = []

    for child in node.children:
        if child.type == "identifier":  # class name is 'identifier', not 'name'
            class_name = _get_node_text(child, source_bytes)
        elif child.type == "argument_list":
            # Extract base classes from argument_list
            # Format: (BaseA, BaseB, Generic[T])
            for arg_child in child.children:
                if arg_child.type in ("identifier", "attribute", "subscript"):
                    base_text = _get_node_text(arg_child, source_bytes)
                    # Remove generic type parameters: List[str] -> List
                    base_name = base_text.split("[")[0] if "[" in base_text else base_text
                    bases.append(base_name)

    # Build full class name (handle nested classes)
    full_class_name = f"{parent_class}.{class_name}" if parent_class else class_name

    signature = f"class {class_name}"
    if bases:
        signature += f"({', '.join(bases)})"

    docstring = _extract_docstring(node, source_bytes)

    symbols.append(
        Symbol(
            name=full_class_name,
            kind="class",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
    )

    # Create Inheritance objects (Epic 10, Story 10.1.1)
    for base in bases:
        inheritances.append(Inheritance(child=full_class_name, parent=base))

    # Parse methods and nested classes
    for child in node.children:
        if child.type == "block":
            for block_child in child.children:
                if block_child.type == "function_definition":
                    method = _parse_function(block_child, source_bytes, full_class_name)
                    symbols.append(method)
                elif block_child.type == "class_definition":
                    # Nested class (Epic 10, Story 10.1.1)
                    nested_symbols = _parse_class(
                        block_child, source_bytes, full_class_name, inheritances
                    )
                    symbols.extend(nested_symbols)

    return symbols


def _parse_import(node, source_bytes: bytes) -> list[Import]:
    """Parse an import statement.

    Returns a list of Import objects. For imports with different aliases,
    creates separate Import objects (Epic 10, Story 10.2.1).

    Examples:
        import numpy as np → [Import("numpy", [], False, alias="np")]
        from typing import Dict as D, List → [Import("typing", ["Dict"], True, alias="D"),
                                                Import("typing", ["List"], True, alias=None)]
    """
    imports = []

    if node.type == "import_statement":
        # import foo, bar as baz
        for child in node.children:
            if child.type == "dotted_name":
                # Simple import without alias
                module_name = _get_node_text(child, source_bytes)
                imports.append(Import(module=module_name, names=[], is_from=False, alias=None))
            elif child.type == "aliased_import":
                # import foo as bar
                module_name = ""
                alias = None
                for ac in child.children:
                    if ac.type == "dotted_name":
                        module_name = _get_node_text(ac, source_bytes)
                    elif ac.type == "identifier" and module_name:
                        # This is the alias (after 'as')
                        alias = _get_node_text(ac, source_bytes)
                if module_name:
                    imports.append(Import(module=module_name, names=[], is_from=False, alias=alias))

    elif node.type == "import_from_statement":
        # from foo import bar, baz as qux
        module = ""
        imported_items = []  # List of (name, alias) tuples
        found_module = False

        # Parse the import structure
        for child in node.children:
            if child.type == "dotted_name" and not found_module:
                # This is the module name
                module = _get_node_text(child, source_bytes)
                found_module = True
            elif child.type == "relative_import" and not found_module:
                module = _get_node_text(child, source_bytes)
                found_module = True
            elif found_module:
                # After module, collect imported items
                if child.type == "dotted_name":
                    # This could be wrongly parsed - skip if it's the module name itself
                    name = _get_node_text(child, source_bytes)
                    if name != module:  # Don't add module name as import
                        imported_items.append((name, None))
                elif child.type == "identifier":
                    # Single identifier: from foo import bar
                    name = _get_node_text(child, source_bytes)
                    if name not in ("import", "from", "*") and name != module:
                        imported_items.append((name, None))
                elif child.type == "aliased_import":
                    # from foo import bar as baz
                    name = ""
                    alias = None
                    for ac in child.children:
                        if ac.type in ("dotted_name", "identifier") and not name:
                            name = _get_node_text(ac, source_bytes)
                        elif ac.type == "identifier" and name:
                            # This is the alias (after 'as')
                            alias = _get_node_text(ac, source_bytes)
                    if name:
                        imported_items.append((name, alias))
                elif child.type == "wildcard_import":
                    # from foo import *
                    imported_items.append(("*", None))

        # Create Import objects
        if module and imported_items:
            # Create separate Import for each item
            for name, alias in imported_items:
                imports.append(Import(module=module, names=[name], is_from=True, alias=alias))

    return imports


def _extract_module_docstring(tree, source_bytes: bytes) -> str:
    """Extract module-level docstring."""
    root = tree.root_node
    for child in root.children:
        if child.type == "expression_statement":
            for expr_child in child.children:
                if expr_child.type == "string":
                    text = _get_node_text(expr_child, source_bytes)
                    if text.startswith('"""') or text.startswith("'''"):
                        return text[3:-3].strip()
                    elif text.startswith('"') or text.startswith("'"):
                        return text[1:-1].strip()
            break
        elif child.type not in ("comment",):
            break
    return ""


# ============================================================================
# Epic 11: Call Relationships Extraction (Story 11.1 - Python)
# ============================================================================


def build_alias_map(imports: list[Import]) -> dict[str, str]:
    """Build alias-to-module mapping from imports (Epic 11, Story 11.1).

    Examples:
        >>> imports = [
        ...     Import(module="pandas", alias="pd"),
        ...     Import(module="numpy", alias="np"),
        ...     Import(module="numpy", names=["array"], is_from=True, alias="np_array"),
        ... ]
        >>> build_alias_map(imports)
        {'pd': 'pandas', 'np': 'numpy', 'np_array': 'numpy.array'}
    """
    alias_map = {}
    for imp in imports:
        if imp.alias:
            # Handle from-import with alias: from numpy import array as np_array
            if imp.is_from and imp.names:
                # Map alias to module.name: np_array → numpy.array
                alias_map[imp.alias] = f"{imp.module}.{imp.names[0]}"
            else:
                # Regular import with alias: import pandas as pd
                alias_map[imp.alias] = imp.module
    return alias_map


def resolve_alias(callee: str, alias_map: dict[str, str]) -> str:
    """Resolve import alias in callee name (Epic 11, Story 11.1).

    Examples:
        >>> resolve_alias("pd.read_csv", {"pd": "pandas"})
        'pandas.read_csv'

        >>> resolve_alias("np_array", {"np_array": "numpy.array"})
        'numpy.array'

        >>> resolve_alias("helper", {})
        'helper'
    """
    if not callee:
        return callee

    # Direct match (for from-import aliases like np_array)
    if callee in alias_map:
        return alias_map[callee]

    # No dot, not in alias_map
    if "." not in callee:
        return callee

    # Split and check prefix (for module aliases like pd.read_csv)
    parts = callee.split(".", 1)
    prefix = parts[0]
    suffix = parts[1] if len(parts) > 1 else ""

    if prefix in alias_map:
        real_prefix = alias_map[prefix]
        return f"{real_prefix}.{suffix}" if suffix else real_prefix

    return callee


def _count_arguments(args_node: Node) -> Optional[int]:
    """Count arguments in argument_list node (best-effort).

    Args:
        args_node: Tree-sitter argument_list node

    Returns:
        Number of arguments, or None if cannot determine
    """
    if not args_node or args_node.type != "argument_list":
        return None

    count = 0
    for child in args_node.children:
        # Count actual argument nodes (skip parentheses and commas)
        if child.type not in ("(", ")", ","):
            count += 1

    return count


def _determine_python_call_type(func_node: Node, source_bytes: bytes) -> CallType:
    """Determine Python call type from function node.

    Rules:
        - Constructor: Identifier starts with uppercase → CONSTRUCTOR
        - Dynamic: getattr/setattr/eval/exec/__import__ → DYNAMIC
        - Static method: ClassName.method() → STATIC_METHOD
        - Instance method: obj.method() → METHOD
        - Simple call: func() → FUNCTION
    """
    if func_node.type == "identifier":
        name = _get_node_text(func_node, source_bytes)
        # Constructor: starts with uppercase
        if name and name[0].isupper():
            return CallType.CONSTRUCTOR
        # Dynamic calls
        if name in ("getattr", "setattr", "eval", "exec", "__import__"):
            return CallType.DYNAMIC
        return CallType.FUNCTION

    elif func_node.type == "attribute":
        # obj.method() or Class.method() or Outer.Inner() (nested class)
        # Check the attribute part (method/class name)
        attr_node = func_node.child_by_field_name("attribute")
        if attr_node:
            attr_name = _get_node_text(attr_node, source_bytes)
            # Constructor: Outer.Inner() → Inner starts with uppercase
            if attr_name and attr_name[0].isupper():
                return CallType.CONSTRUCTOR

        # Check the object part
        obj_node = func_node.child_by_field_name("object")
        if obj_node and obj_node.type == "identifier":
            obj_name = _get_node_text(obj_node, source_bytes)
            # Static method: ClassName.method()
            if obj_name and obj_name[0].isupper():
                return CallType.STATIC_METHOD

        return CallType.METHOD

    return CallType.FUNCTION


def _extract_call_name(func_node: Node, source_bytes: bytes) -> str:
    """Extract callee name from function node.

    Examples:
        - identifier: "helper" → "helper"
        - attribute: obj.method → "obj.method"
        - attribute: pd.read_csv → "pd.read_csv"
        - attribute: super().method → "super.method"
    """
    if func_node.type == "identifier":
        return _get_node_text(func_node, source_bytes)

    elif func_node.type == "attribute":
        # Build full attribute path: obj.attr1.attr2...
        parts = []
        current = func_node

        while current:
            if current.type == "attribute":
                # Get the attribute name
                attr_node = current.child_by_field_name("attribute")
                if attr_node:
                    parts.insert(0, _get_node_text(attr_node, source_bytes))
                # Move to object
                current = current.child_by_field_name("object")
            elif current.type == "identifier":
                parts.insert(0, _get_node_text(current, source_bytes))
                break
            elif current.type == "call":
                # Special case: super().method() → extract as "super.method"
                func_child = current.child_by_field_name("function")
                if func_child and func_child.type == "identifier":
                    func_name = _get_node_text(func_child, source_bytes)
                    if func_name == "super":
                        parts.insert(0, "super")
                        break
                # For other calls, just use generic name
                parts.insert(0, "<call>")
                break
            else:
                break

        return ".".join(parts)

    return ""


def _parse_python_call(
    node: Node,
    source_bytes: bytes,
    caller: str,
    alias_map: dict[str, str],
    parent_map: dict[str, str],
) -> Optional[Call]:
    """Parse a single Python call node.

    Args:
        node: Tree-sitter call node
        source_bytes: Source code bytes
        caller: Name of calling function/method (e.g., "Calculator.add" or "Child.method")
        alias_map: Import alias mapping
        parent_map: Parent class mapping (for super() resolution)

    Returns:
        Call object or None if cannot parse
    """
    # Extract function node
    func_node = node.child_by_field_name("function")
    if not func_node:
        return None

    # Extract callee name
    callee_raw = _extract_call_name(func_node, source_bytes)
    if not callee_raw:
        return None

    # Resolve self.method() to ClassName.method() (AC2: method call with self)
    if callee_raw.startswith("self.") and "." in caller:
        # Extract class name from caller (e.g., "Calculator.add" → "Calculator")
        class_name = caller.rsplit(".", 1)[0]
        # Replace self with class name
        callee_raw = callee_raw.replace("self.", f"{class_name}.", 1)

    # Resolve super().method() to Parent.method() (AC2: super method call)
    if callee_raw.startswith("super.") and "." in caller:
        # Extract class name from caller (e.g., "Child.method" → "Child")
        class_name = caller.rsplit(".", 1)[0]
        # Look up parent class
        if class_name in parent_map:
            parent_class = parent_map[class_name]
            # Replace super with parent class name
            callee_raw = callee_raw.replace("super.", f"{parent_class}.", 1)

    # Resolve alias (CRITICAL: Epic 11, Story 11.1, AC4)
    callee = resolve_alias(callee_raw, alias_map)

    # Determine call type
    call_type = _determine_python_call_type(func_node, source_bytes)

    # Constructor: format as Class.__init__
    if call_type == CallType.CONSTRUCTOR:
        callee = f"{callee}.__init__"

    # Extract arguments count (best-effort)
    args_node = node.child_by_field_name("arguments")
    args_count = _count_arguments(args_node) if args_node else None

    return Call(
        caller=caller,
        callee=callee,
        line_number=node.start_point[0] + 1,
        call_type=call_type,
        arguments_count=args_count,
    )


def _extract_python_calls(
    node: Node,
    source_bytes: bytes,
    context: str,
    alias_map: dict[str, str],
    parent_map: dict[str, str],
) -> list[Call]:
    """Extract Python call relationships (Epic 11, Story 11.1).

    Recursively traverses AST to extract function/method calls.

    Args:
        node: Tree-sitter AST node
        source_bytes: Source code bytes
        context: Current context (function/method/class name, e.g., "Child.method")
        alias_map: Import alias mapping
        parent_map: Parent class mapping (for super() resolution)

    Returns:
        List of Call objects
    """
    calls = []

    # Process call nodes
    if node.type == "call":
        call = _parse_python_call(node, source_bytes, context, alias_map, parent_map)
        if call:
            calls.append(call)

    # Recurse into children
    for child in node.children:
        calls.extend(_extract_python_calls(child, source_bytes, context, alias_map, parent_map))

    return calls


def _is_simple_decorator(decorator_node: Node) -> bool:
    """Check if decorator is simple (Phase 1 support).

    Simple decorators (Phase 1):
        @decorator         ✅
        @module.decorator  ✅

    Complex decorators (Phase 2, not supported yet):
        @decorator(arg1, arg2)  ❌
        @decorator()            ❌
        @outer(@inner)          ❌
    """
    # Decorator node should only have identifier or attribute children (no call)
    for child in decorator_node.children:
        if child.type == "call":  # Has call means it's complex
            return False
    return True


def _extract_decorator_name(decorator_node: Node, source_bytes: bytes) -> str:
    """Extract decorator name from decorator node.

    Examples:
        @decorator → "decorator"
        @module.decorator → "module.decorator"
    """
    for child in decorator_node.children:
        if child.type == "identifier":
            return _get_node_text(child, source_bytes)
        elif child.type == "attribute":
            return _extract_call_name(child, source_bytes)
    return ""


def _extract_decorator_calls(
    node: Node, source_bytes: bytes, context: str
) -> list[Call]:
    """Extract decorator calls from function/class definition (Phase 1).

    Args:
        node: function_definition or class_definition node
        source_bytes: Source code bytes
        context: Context (function/class name or module)

    Returns:
        List of Call objects for decorators
    """
    calls = []

    # Only handle function_definition and class_definition
    if node.type not in ("function_definition", "class_definition"):
        return calls

    # Find decorator nodes
    for child in node.children:
        if child.type == "decorator":
            # Phase 1: Only simple decorators
            if _is_simple_decorator(child):
                decorator_name = _extract_decorator_name(child, source_bytes)

                if decorator_name:
                    calls.append(
                        Call(
                            caller=context,
                            callee=decorator_name,
                            line_number=child.start_point[0] + 1,
                            call_type=CallType.FUNCTION,
                            arguments_count=1,  # Decorator receives 1 arg (decorated object)
                        )
                    )

    return calls


def _extract_python_calls_from_tree(
    tree, source_bytes: bytes, imports: list[Import], inheritances: list[Inheritance]
) -> list[Call]:
    """Extract all Python calls from parse tree.

    Args:
        tree: Tree-sitter parse tree
        source_bytes: Source code bytes
        imports: Import list (for alias resolution)
        inheritances: Inheritance list (for super() resolution)

    Returns:
        List of Call objects
    """
    # Build alias map from imports (Epic 11, AC4)
    alias_map = build_alias_map(imports)

    # Build parent map for super() resolution (child → parent)
    parent_map = {}
    for inh in inheritances:
        parent_map[inh.child] = inh.parent

    calls = []
    root = tree.root_node

    # Traverse top-level definitions
    for child in root.children:
        if child.type == "function_definition":
            # Extract function name
            func_name = ""
            for node in child.children:
                if node.type == "identifier":
                    func_name = _get_node_text(node, source_bytes)
                    break

            # Extract calls within function
            if func_name:
                calls.extend(
                    _extract_python_calls(child, source_bytes, func_name, alias_map, parent_map)
                )

        elif child.type == "class_definition":
            # Extract class name
            class_name = ""
            for node in child.children:
                if node.type == "identifier":
                    class_name = _get_node_text(node, source_bytes)
                    break

            if class_name:
                # Extract decorator calls (AC5: decorator calls)
                calls.extend(
                    _extract_decorator_calls(child, source_bytes, "<module>")
                )

                # Find class body
                body_node = None
                for node in child.children:
                    if node.type == "block":
                        body_node = node
                        break

                if body_node:
                    # Extract calls from methods
                    for method_node in body_node.children:
                        if method_node.type == "function_definition":
                            # Extract method name
                            method_name = ""
                            for node in method_node.children:
                                if node.type == "identifier":
                                    method_name = _get_node_text(node, source_bytes)
                                    break

                            if method_name:
                                context = f"{class_name}.{method_name}"

                                # Extract decorator calls for method
                                calls.extend(
                                    _extract_decorator_calls(
                                        method_node, source_bytes, class_name
                                    )
                                )

                                # Extract calls within method
                                calls.extend(
                                    _extract_python_calls(
                                        method_node, source_bytes, context, alias_map, parent_map
                                    )
                                )

                        elif method_node.type == "decorated_definition":
                            # Handle decorated methods
                            # First extract decorators
                            for dec_node in method_node.children:
                                if dec_node.type == "decorator":
                                    if _is_simple_decorator(dec_node):
                                        decorator_name = _extract_decorator_name(
                                            dec_node, source_bytes
                                        )
                                        if decorator_name:
                                            calls.append(
                                                Call(
                                                    caller=class_name,
                                                    callee=decorator_name,
                                                    line_number=dec_node.start_point[0] + 1,
                                                    call_type=CallType.FUNCTION,
                                                    arguments_count=1,
                                                )
                                            )

                            # Then process the function itself
                            for dec_child in method_node.children:
                                if dec_child.type == "function_definition":
                                    method_name = ""
                                    for node in dec_child.children:
                                        if node.type == "identifier":
                                            method_name = _get_node_text(node, source_bytes)
                                            break
                                    if method_name:
                                        context = f"{class_name}.{method_name}"
                                        calls.extend(
                                            _extract_python_calls(
                                                dec_child,
                                                source_bytes,
                                                context,
                                                alias_map,
                                                parent_map,
                                            )
                                        )

        elif child.type == "decorated_definition":
            # Handle decorated functions/classes
            # decorated_definition contains: decorator* + (function_definition | class_definition)

            # First, extract decorators from decorated_definition node itself
            for dec_node in child.children:
                if dec_node.type == "decorator":
                    if _is_simple_decorator(dec_node):
                        decorator_name = _extract_decorator_name(dec_node, source_bytes)
                        if decorator_name:
                            calls.append(
                                Call(
                                    caller="<module>",
                                    callee=decorator_name,
                                    line_number=dec_node.start_point[0] + 1,
                                    call_type=CallType.FUNCTION,
                                    arguments_count=1,
                                )
                            )

            # Then, handle the decorated function/class
            for dec_child in child.children:
                if dec_child.type == "function_definition":
                    func_name = ""
                    for node in dec_child.children:
                        if node.type == "identifier":
                            func_name = _get_node_text(node, source_bytes)
                            break
                    if func_name:
                        # Extract calls within function
                        calls.extend(
                            _extract_python_calls(
                                dec_child, source_bytes, func_name, alias_map, parent_map
                            )
                        )
                elif dec_child.type == "class_definition":
                    class_name = ""
                    for node in dec_child.children:
                        if node.type == "identifier":
                            class_name = _get_node_text(node, source_bytes)
                            break
                    if class_name:
                        # For decorated classes, process methods
                        body_node = None
                        for node in dec_child.children:
                            if node.type == "block":
                                body_node = node
                                break

                        if body_node:
                            for method_node in body_node.children:
                                if method_node.type == "function_definition":
                                    method_name = ""
                                    for node in method_node.children:
                                        if node.type == "identifier":
                                            method_name = _get_node_text(node, source_bytes)
                                            break
                                    if method_name:
                                        context = f"{class_name}.{method_name}"
                                        calls.extend(
                                            _extract_decorator_calls(
                                                method_node, source_bytes, class_name
                                            )
                                        )
                                        calls.extend(
                                            _extract_python_calls(
                                                method_node,
                                                source_bytes,
                                                context,
                                                alias_map,
                                                parent_map,
                                            )
                                        )

    return calls


def parse_file(path: Path, language: str | None = None) -> ParseResult:
    """
    Parse a source file (Python or PHP) and extract symbols and imports.

    Args:
        path: Path to the source file
        language: Optional language override ("python" or "php").
                  If None, language is detected from file extension.

    Returns:
        ParseResult containing symbols, imports, and docstrings
    """
    try:
        source_bytes = path.read_bytes()
    except Exception as e:
        return ParseResult(path=path, error=str(e), file_lines=0)

    # Calculate file lines
    file_lines = source_bytes.count(b"\n") + (
        1 if source_bytes and not source_bytes.endswith(b"\n") else 0
    )

    # Determine language
    if language is None:
        language = _get_language(path)
    if not language:
        return ParseResult(
            path=path, error=f"Unsupported file type: {path.suffix}", file_lines=file_lines
        )

    # Get appropriate parser (lazy loading)
    try:
        parser = _get_parser(language)
    except ImportError as e:
        return ParseResult(
            path=path, error=str(e), file_lines=file_lines
        )

    if not parser:
        return ParseResult(
            path=path, error=f"Unsupported language: {language}", file_lines=file_lines
        )

    try:
        tree = parser.parse(source_bytes)
    except Exception as e:
        return ParseResult(path=path, error=f"Parse error: {e}", file_lines=file_lines)

    # Check for syntax errors
    if tree.root_node.has_error:
        return ParseResult(
            path=path,
            error="Syntax error in file (tree-sitter parse failure)",
            file_lines=file_lines,
        )

    symbols: list[Symbol] = []
    imports: list[Import] = []
    inheritances: list[Inheritance] = []  # Epic 10, Story 10.1.1
    calls: list[Call] = []  # Epic 11, Story 11.1
    module_docstring = ""

    # Language-specific parsing
    if language == "python":
        module_docstring = _extract_module_docstring(tree, source_bytes)
        root = tree.root_node
        for child in root.children:
            if child.type == "function_definition":
                symbols.append(_parse_function(child, source_bytes))
            elif child.type == "class_definition":
                symbols.extend(_parse_class(child, source_bytes, "", inheritances))
            elif child.type == "decorated_definition":
                for dec_child in child.children:
                    if dec_child.type == "function_definition":
                        symbols.append(_parse_function(dec_child, source_bytes))
                    elif dec_child.type == "class_definition":
                        symbols.extend(_parse_class(dec_child, source_bytes, "", inheritances))
            elif child.type in ("import_statement", "import_from_statement"):
                # Epic 10, Story 10.2.1: _parse_import now returns list
                import_list = _parse_import(child, source_bytes)
                imports.extend(import_list)

        # Epic 11, Story 11.1: Extract call relationships
        calls = _extract_python_calls_from_tree(tree, source_bytes, imports, inheritances)

    elif language == "php":
        # PHP parsing (Epic 10, Story 10.1.2: inheritance extraction)
        root = tree.root_node
        namespace = ""
        inheritances: list[Inheritance] = []

        # First pass: collect namespace and build use_map for inheritance resolution
        use_map: dict[str, str] = {}  # {short_name: full_qualified_name}

        for child in root.children:
            if child.type == "namespace_definition":
                namespace = _parse_php_namespace(child, source_bytes)
            elif child.type == "namespace_use_declaration":
                use_imports = _parse_php_use(child, source_bytes)
                imports.extend(use_imports)
                # Build use_map for inheritance resolution
                # Epic 10, Story 10.2.2: Now using imp.alias field correctly
                for imp in use_imports:
                    # Extract class name from full path: App\Model\User -> User
                    short_name = imp.module.split("\\")[-1]
                    # If there's an alias, use it as the key; otherwise use short name
                    if imp.alias:
                        use_map[imp.alias] = imp.module
                    else:
                        use_map[short_name] = imp.module

        # Second pass: parse classes with use_map and inheritances
        for child in root.children:
            if child.type == "class_declaration":
                symbols.extend(
                    _parse_php_class(child, source_bytes, namespace, use_map, inheritances)
                )
            elif child.type == "function_definition":
                symbols.append(_parse_php_function(child, source_bytes))
            elif child.type in ("include_expression", "require_expression"):
                imp = _parse_php_include(child, source_bytes)
                if imp:
                    imports.append(imp)

        # Extract module docstring from PHP file comments
        module_docstring = ""
        for child in root.children:
            if child.type == "comment" and child.text.startswith(b"/**"):
                module_docstring = _extract_php_docstring(child, source_bytes)
                break

        return ParseResult(
            path=path,
            symbols=symbols,
            imports=imports,
            inheritances=inheritances,
            module_docstring=module_docstring,
            namespace=namespace,
            file_lines=file_lines,
        )

    elif language == "java":
        # Java parsing (Epic 10 Part 3: inheritance extraction)
        root = tree.root_node
        namespace = ""  # Java package name
        inheritances: list[Inheritance] = []

        # First pass: collect package name and build import_map
        import_map: dict[str, str] = _build_java_import_map(root, source_bytes)

        for child in root.children:
            if child.type == "package_declaration":
                namespace = _parse_java_package(child, source_bytes)
            elif child.type == "import_declaration":
                imp = _parse_java_import(child, source_bytes)
                if imp:
                    imports.append(imp)

        # Second pass: parse classes/interfaces with import_map and inheritances
        for child in root.children:
            if child.type == "class_declaration":
                symbols.extend(
                    _parse_java_class(child, source_bytes, namespace, import_map, inheritances)
                )
            elif child.type == "interface_declaration":
                symbols.extend(
                    _parse_java_interface(child, source_bytes, namespace, import_map, inheritances)
                )
            elif child.type == "enum_declaration":
                symbols.extend(_parse_java_enum(child, source_bytes))
            elif child.type == "record_declaration":
                symbols.extend(_parse_java_record(child, source_bytes))

        # Extract module docstring from first JavaDoc comment
        module_docstring = _extract_java_module_docstring(tree, source_bytes)

        # Epic 11, Story 11.2: Extract Java call relationships
        calls = _extract_java_calls_from_tree(
            tree, source_bytes, imports, inheritances, namespace, import_map
        )

        return ParseResult(
            path=path,
            symbols=symbols,
            imports=imports,
            inheritances=inheritances,
            calls=calls,  # Epic 11, Story 11.2
            module_docstring=module_docstring,
            namespace=namespace,
            file_lines=file_lines,
        )

    return ParseResult(
        path=path,
        symbols=symbols,
        imports=imports,
        inheritances=inheritances,
        calls=calls,  # Epic 11
        module_docstring=module_docstring,
        file_lines=file_lines,
    )


def parse_directory(paths: list[Path]) -> list[ParseResult]:
    """Parse multiple files."""
    return [parse_file(p) for p in paths]

def _get_language(file_path: Path) -> str:
    """Determine language from file extension."""
    suffix = file_path.suffix.lower()
    return FILE_EXTENSIONS.get(suffix)

def _extract_php_docstring(node, source_bytes: bytes) -> str:
    """
    Extract docstring from PHPDoc/DocComment or inline comments.

    For PHP, the comment is often a sibling node (previous sibling)
    rather than a child node.

    Supports:
    - PHPDoc blocks: /** ... */
    - Inline comments: // ...
    """
    # First check children (for class-level comments)
    for child in node.children:
        if child.type == "comment":
            text = _get_node_text(child, source_bytes)
            if text.startswith("/**"):
                return _parse_phpdoc_text(text)
            elif text.startswith("//"):
                # Inline comment: remove // and strip
                return text[2:].strip()

    # Check previous sibling (for method-level comments)
    if node.prev_sibling and node.prev_sibling.type == "comment":
        text = _get_node_text(node.prev_sibling, source_bytes)
        if text.startswith("/**"):
            return _parse_phpdoc_text(text)
        elif text.startswith("//"):
            # Inline comment: remove // and strip
            return text[2:].strip()

    return ""


def _parse_phpdoc_text(text: str) -> str:
    """
    Parse PHPDoc comment text and extract description.

    Extracts the first non-annotation line(s) from PHPDoc.
    Skips @param, @return, @throws, etc.

    Args:
        text: Raw PHPDoc comment text (/** ... */)

    Returns:
        Cleaned description text
    """
    # Handle single-line PHPDoc: /** Description */
    if "\n" not in text:
        # Remove /** and */
        content = text.strip()
        if content.startswith("/**"):
            content = content[3:]
        if content.endswith("*/"):
            content = content[:-2]
        content = content.strip()
        # Skip if it's only annotations
        if content.startswith("@"):
            return ""
        return content

    # Handle multi-line PHPDoc
    lines = text.split("\n")
    description_lines = []

    for line in lines[1:-1]:  # Skip first (/**) and last (*/) lines
        line = line.strip()
        # Remove leading * and whitespace
        if line.startswith("*"):
            line = line[1:].strip()

        # Skip empty lines
        if not line:
            continue

        # Skip annotation lines (@param, @return, etc.)
        if line.startswith("@"):
            break  # Stop at first annotation

        description_lines.append(line)

    return " ".join(description_lines)

def _parse_php_function(node, source_bytes: bytes, class_name: str = "") -> Symbol:
    """Parse a PHP function definition node (standalone function, not method)."""
    name = ""
    params = ""
    return_type = ""

    for child in node.children:
        if child.type == "name":
            name = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            return_type = _get_node_text(child, source_bytes)

    signature = f"function {name}{params}"
    if return_type:
        signature += f": {return_type}"

    docstring = _extract_php_docstring(node, source_bytes)

    return Symbol(
        name=name,
        kind="function",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_php_method(node, source_bytes: bytes, class_name: str) -> Symbol:
    """Parse a PHP method declaration node with visibility, static, and return type."""
    name = ""
    params = ""
    return_type = ""
    visibility = ""
    is_static = False

    for child in node.children:
        if child.type == "visibility_modifier":
            visibility = _get_node_text(child, source_bytes)
        elif child.type == "static_modifier":
            is_static = True
        elif child.type == "name":
            name = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            return_type = _get_node_text(child, source_bytes)

    # Build signature: [visibility] [static] function name(params)[: return_type]
    sig_parts = []
    if visibility:
        sig_parts.append(visibility)
    if is_static:
        sig_parts.append("static")
    sig_parts.append(f"function {name}{params}")
    signature = " ".join(sig_parts)
    if return_type:
        signature += f": {return_type}"

    docstring = _extract_php_docstring(node, source_bytes)
    full_name = f"{class_name}::{name}"

    return Symbol(
        name=full_name,
        kind="method",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_php_property(node, source_bytes: bytes, class_name: str) -> Symbol:
    """Parse a PHP property declaration node."""
    prop_name = ""
    visibility = ""
    is_static = False
    prop_type = ""

    for child in node.children:
        if child.type == "visibility_modifier":
            visibility = _get_node_text(child, source_bytes)
        elif child.type == "static_modifier":
            is_static = True
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            prop_type = _get_node_text(child, source_bytes)
        elif child.type == "property_element":
            for prop_child in child.children:
                if prop_child.type == "variable_name":
                    prop_name = _get_node_text(prop_child, source_bytes)

    # Build signature: [visibility] [static] [type] $name
    sig_parts = []
    if visibility:
        sig_parts.append(visibility)
    if is_static:
        sig_parts.append("static")
    if prop_type:
        sig_parts.append(prop_type)
    sig_parts.append(prop_name)
    signature = " ".join(sig_parts)

    full_name = f"{class_name}::{prop_name}"

    return Symbol(
        name=full_name,
        kind="property",
        signature=signature,
        docstring="",
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )

def _parse_php_class(
    node,
    source_bytes: bytes,
    namespace: str = "",
    use_map: dict[str, str] | None = None,
    inheritances: list[Inheritance] | None = None
) -> list[Symbol]:
    """Parse a PHP class definition node with extends, implements, properties and methods.

    Epic 10, Story 10.1.2: Added namespace, use_map, and inheritances parameters
    to support inheritance extraction for LoomGraph integration.

    Args:
        node: tree-sitter node for class_declaration
        source_bytes: Source code bytes
        namespace: Current namespace (e.g., "App\\Models")
        use_map: Mapping of short names to full qualified names from use statements
        inheritances: List to append Inheritance relationships to
    """
    if use_map is None:
        use_map = {}
    if inheritances is None:
        inheritances = []

    symbols = []
    class_name = ""
    extends = ""
    implements = []
    is_abstract = False
    is_final = False

    for child in node.children:
        if child.type == "name":
            class_name = _get_node_text(child, source_bytes)
        elif child.type == "abstract_modifier":
            is_abstract = True
        elif child.type == "final_modifier":
            is_final = True
        elif child.type == "base_clause":
            # extends BaseClass
            for bc_child in child.children:
                if bc_child.type == "name":
                    extends = _get_node_text(bc_child, source_bytes)
        elif child.type == "class_interface_clause":
            # implements Interface1, Interface2
            for ic_child in child.children:
                if ic_child.type == "name":
                    implements.append(_get_node_text(ic_child, source_bytes))

    # Build full class name with namespace
    full_class_name = f"{namespace}\\{class_name}" if namespace else class_name

    # Create Inheritance objects (Epic 10, Story 10.1.2)
    if extends:
        # Resolve parent class full name using use_map
        parent_full_name = use_map.get(extends, f"{namespace}\\{extends}" if namespace else extends)
        inheritances.append(Inheritance(child=full_class_name, parent=parent_full_name))

    for interface in implements:
        # Resolve interface full name using use_map
        interface_full_name = use_map.get(
            interface, f"{namespace}\\{interface}" if namespace else interface
        )
        inheritances.append(Inheritance(child=full_class_name, parent=interface_full_name))

    # Build signature: [abstract|final] class Name [extends Base] [implements I1, I2]
    sig_parts = []
    if is_abstract:
        sig_parts.append("abstract")
    elif is_final:
        sig_parts.append("final")
    sig_parts.append(f"class {class_name}")
    if extends:
        sig_parts.append(f"extends {extends}")
    if implements:
        sig_parts.append(f"implements {', '.join(implements)}")
    signature = " ".join(sig_parts)

    docstring = _extract_php_docstring(node, source_bytes)

    symbols.append(
        Symbol(
            name=class_name,
            kind="class",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
    )

    # Parse properties and methods from declaration_list
    for child in node.children:
        if child.type == "declaration_list":
            for decl in child.children:
                if decl.type == "property_declaration":
                    prop = _parse_php_property(decl, source_bytes, class_name)
                    symbols.append(prop)
                elif decl.type == "method_declaration":
                    method = _parse_php_method(decl, source_bytes, class_name)
                    symbols.append(method)

    return symbols

def _parse_php_include(node, source_bytes: bytes) -> Import | None:
    """Parse PHP include/require statements."""
    if node.type == "include_expression" or node.type == "require_expression":
        for child in node.children:
            if child.type == "string":
                module = _get_node_text(child, source_bytes)
                # Remove quotes
                module = module.strip('\'"')
                return Import(module=module, names=[], is_from=False)
    return None


def _parse_php_namespace(node, source_bytes: bytes) -> str:
    """Parse PHP namespace definition."""
    for child in node.children:
        if child.type == "namespace_name":
            return _get_node_text(child, source_bytes)
    return ""


def _parse_php_use(node, source_bytes: bytes) -> list[Import]:
    """Parse PHP use statement.

    Epic 10, Story 10.2.2: Updated to store alias in alias field (not names field)
    for consistency with Python import handling and LoomGraph integration.

    Handles:
    - use App\\Service\\UserService;
    - use App\\Model\\User as UserModel;
    - use App\\Repository\\{UserRepository, OrderRepository};

    Returns:
        List of Import objects with:
        - names: always empty [] (PHP use imports entire class, not specific members)
        - alias: the alias if present (e.g., "UserModel"), None otherwise
    """
    imports = []
    base_namespace = ""

    for child in node.children:
        if child.type == "namespace_name":
            # Group import base: use App\Repository\{...}
            base_namespace = _get_node_text(child, source_bytes)

        elif child.type == "namespace_use_clause":
            # Single import
            module = ""
            alias = ""

            for clause_child in child.children:
                if clause_child.type == "qualified_name":
                    module = _get_node_text(clause_child, source_bytes)
                elif clause_child.type == "name" and module:
                    # This is the alias (after 'as')
                    alias = _get_node_text(clause_child, source_bytes)

            if module:
                # If there's a base namespace (group import), prepend it
                if base_namespace:
                    module = f"{base_namespace}\\{module}"

                # Epic 10, Story 10.2.2: alias now in alias field, names always empty
                imports.append(
                    Import(
                        module=module,
                        names=[],  # PHP use imports whole class, not specific members
                        is_from=True,  # PHP use is similar to Python's from...import
                        alias=alias if alias else None,
                    )
                )

        elif child.type == "namespace_use_group":
            # Group import: {UserRepository, OrderRepository}
            for group_child in child.children:
                if group_child.type == "namespace_use_clause":
                    name = ""
                    alias = ""
                    for clause_child in group_child.children:
                        if clause_child.type == "qualified_name":
                            name = _get_node_text(clause_child, source_bytes)
                        elif clause_child.type == "name":
                            if not name:
                                name = _get_node_text(clause_child, source_bytes)
                            else:
                                alias = _get_node_text(clause_child, source_bytes)

                    if name:
                        full_module = f"{base_namespace}\\{name}" if base_namespace else name
                        # Epic 10, Story 10.2.2: alias now in alias field
                        imports.append(
                            Import(
                                module=full_module,
                                names=[],  # PHP use imports whole class
                                is_from=True,
                                alias=alias if alias else None,
                            )
                        )

    return imports


# ==================== Java Parser Functions ====================

# Java standard library classes (java.lang.* implicit imports)
JAVA_LANG_CLASSES = {
    "Object", "String", "Exception", "RuntimeException",
    "Throwable", "Error", "Class", "Number", "Integer",
    "Long", "Double", "Float", "Boolean", "Character",
    "Byte", "Short", "Void", "Math", "System",
    "Thread", "Runnable", "StringBuilder", "StringBuffer",
}


def _strip_generic_type(type_name: str) -> str:
    """
    Strip generic type parameters from a type name.

    Args:
        type_name: Type name that may contain generics (e.g., "ArrayList<String>")

    Returns:
        Type name without generics (e.g., "ArrayList")

    Examples:
        >>> _strip_generic_type("ArrayList<String>")
        'ArrayList'
        >>> _strip_generic_type("Map<K, V>")
        'Map'
        >>> _strip_generic_type("Comparable<T extends Number>")
        'Comparable'
        >>> _strip_generic_type("BaseClass")
        'BaseClass'
    """
    # Split on '<' and take first part
    return type_name.split('<')[0].strip()



def _extract_package_namespace(class_full_name: str) -> str:
    """
    Extract package namespace from a full class name.

    For nested classes like "com.example.Outer.Inner", extracts "com.example".
    For top-level classes like "com.example.User", extracts "com.example".

    Args:
        class_full_name: Full class name (e.g., "com.example.Outer.Inner")

    Returns:
        Package namespace (e.g., "com.example")

    Examples:
        >>> _extract_package_namespace("com.example.User")
        'com.example'
        >>> _extract_package_namespace("com.example.Outer.Inner")
        'com.example'
        >>> _extract_package_namespace("User")
        ''
        >>> _extract_package_namespace("Outer.Inner")
        ''
    """
    if not class_full_name or "." not in class_full_name:
        return ""

    parts = class_full_name.split(".")

    # Find the first part that starts with uppercase (class name)
    # Everything before it is the package namespace
    for i, part in enumerate(parts):
        if part and part[0].isupper():
            # Found first class name, return everything before it
            if i == 0:
                return ""  # No package, just class name
            return ".".join(parts[:i])

    # If no uppercase part found, assume all is package
    return class_full_name


def _resolve_java_type(
    short_name: str,
    namespace: str,
    import_map: dict[str, str]
) -> str:
    """
    Resolve a short type name to its full qualified name.

    Resolution priority:
    0. Already fully qualified (contains '.')
    1. java.lang.* (implicit imports)
    2. Explicit imports from import_map
    3. Same package (namespace)

    Args:
        short_name: Short type name (e.g., "BaseService")
        namespace: Current package name (e.g., "com.example.service")
        import_map: Mapping of short names to full qualified names

    Returns:
        Full qualified name (e.g., "com.example.base.BaseService")

    Examples:
        >>> _resolve_java_type("Exception", "com.example", {})
        'java.lang.Exception'
        >>> _resolve_java_type(
        ...     "BaseService",
        ...     "com.example.service",
        ...     {"BaseService": "com.example.base.BaseService"}
        ... )
        'com.example.base.BaseService'
        >>> _resolve_java_type("LocalClass", "com.example", {})
        'com.example.LocalClass'
        >>> _resolve_java_type("com.example.base.BaseUser", "com.example", {})
        'com.example.base.BaseUser'
    """
    # 0. Already fully qualified (contains '.')
    if "." in short_name:
        return short_name

    # 1. java.lang implicit imports
    if short_name in JAVA_LANG_CLASSES:
        return f"java.lang.{short_name}"

    # 2. Explicit imports
    if short_name in import_map:
        return import_map[short_name]

    # 3. Same package
    if namespace:
        return f"{namespace}.{short_name}"

    return short_name


def _build_java_import_map(root: Node, source_bytes: bytes) -> dict[str, str]:
    """
    Build a mapping of short class names to full qualified names from imports.

    Args:
        root: Tree-sitter root node
        source_bytes: Source code as bytes

    Returns:
        Dictionary mapping short names to full qualified names

    Examples:
        import com.example.base.BaseService;
        -> {"BaseService": "com.example.base.BaseService"}

        import java.util.ArrayList;
        -> {"ArrayList": "java.util.ArrayList"}
    """
    import_map = {}

    for child in root.children:
        if child.type == "import_declaration":
            # Extract import path
            for import_child in child.children:
                if import_child.type == "scoped_identifier":
                    full_name = _get_node_text(import_child, source_bytes)
                    # Extract short name (last part after '.')
                    short_name = full_name.split('.')[-1]
                    import_map[short_name] = full_name
                elif import_child.type == "identifier":
                    # Simple import (no dots)
                    short_name = _get_node_text(import_child, source_bytes)
                    import_map[short_name] = short_name

    return import_map


def _extract_java_modifiers(node: Node, source_bytes: bytes) -> list[str]:
    """
    Extract modifiers (public, private, static, etc.) from a Java node.

    Args:
        node: Tree-sitter node to extract modifiers from
        source_bytes: Source code as bytes

    Returns:
        List of modifier strings (e.g., ['public', 'static', 'final'])
    """
    modifiers = []
    for child in node.children:
        if child.type == "modifiers":
            for mod_child in child.children:
                modifiers.append(_get_node_text(mod_child, source_bytes))
    return modifiers


def _build_java_signature(modifiers: list[str], *parts: str) -> str:
    """
    Build a Java signature string from modifiers and parts.

    Args:
        modifiers: List of modifier strings (e.g., ['public', 'static'])
        *parts: Additional signature parts (e.g., return type, name, parameters)

    Returns:
        Complete signature string (e.g., "public static void main(String[] args)")
    """
    signature_parts = []

    # Add modifiers if present
    if modifiers:
        signature_parts.append(" ".join(modifiers))

    # Add remaining parts
    signature_parts.extend(parts)

    return " ".join(signature_parts)


def _extract_java_annotations(node: Node, source_bytes: bytes) -> list[Annotation]:
    """Extract annotations from a Java node.

    Story 7.1.2.1: Annotation Extraction
    Extracts annotations like @RestController, @GetMapping("/path"), etc.

    Args:
        node: Tree-sitter node to extract annotations from
        source_bytes: Source code as bytes

    Returns:
        List of Annotation objects
    """
    annotations = []

    for child in node.children:
        if child.type == "modifiers":
            for mod_child in child.children:
                if mod_child.type == "marker_annotation":
                    # Simple annotation without arguments: @Entity
                    name = ""
                    for name_child in mod_child.children:
                        if name_child.type in ("identifier", "scoped_identifier"):
                            name = _get_node_text(name_child, source_bytes)
                    if name:
                        annotations.append(Annotation(name=name, arguments={}))

                elif mod_child.type == "annotation":
                    # Annotation with arguments: @RequestMapping("/path")
                    name = ""
                    arguments = {}

                    for ann_child in mod_child.children:
                        if ann_child.type in ("identifier", "scoped_identifier"):
                            name = _get_node_text(ann_child, source_bytes)
                        elif ann_child.type == "annotation_argument_list":
                            arguments = _parse_annotation_arguments(ann_child, source_bytes)

                    if name:
                        annotations.append(Annotation(name=name, arguments=arguments))

    return annotations


def _parse_annotation_arguments(arg_list_node: Node, source_bytes: bytes) -> dict[str, str]:
    """Parse annotation arguments into a dictionary.

    Args:
        arg_list_node: annotation_argument_list node
        source_bytes: Source code as bytes

    Returns:
        Dictionary of argument name -> value
        For single value annotations like @GetMapping("/path"), returns {"value": "/path"}
    """
    arguments = {}

    for child in arg_list_node.children:
        if child.type == "element_value_pair":
            # Named argument: name = "value"
            key = ""
            value = ""
            for pair_child in child.children:
                if pair_child.type == "identifier":
                    key = _get_node_text(pair_child, source_bytes)
                elif pair_child.type == "string_literal":
                    value = _get_node_text(pair_child, source_bytes).strip('"')
                elif pair_child.type in ("decimal_integer_literal", "true", "false"):
                    value = _get_node_text(pair_child, source_bytes)
                elif pair_child.type == "element_value_array_initializer":
                    # Array value: {"/users", "/user"}
                    value = _get_node_text(pair_child, source_bytes)

            if key and value:
                arguments[key] = value

        elif child.type == "string_literal":
            # Single unnamed string argument: @GetMapping("/path")
            # Maps to "value" key by Java convention
            value = _get_node_text(child, source_bytes).strip('"')
            arguments["value"] = value
        elif child.type == "decimal_integer_literal":
            # Single unnamed integer argument
            value = _get_node_text(child, source_bytes)
            arguments["value"] = value

    return arguments


def _find_child_by_type(node: Node, type_name: str) -> Node | None:
    """
    Find first child node of a specific type.

    Args:
        node: Parent node to search in
        type_name: Type of child to find

    Returns:
        First matching child node, or None if not found
    """
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _extract_java_docstring(node: Node, source_bytes: bytes) -> str:
    """
    Extract JavaDoc comment from a node.

    JavaDoc comments are /** ... */ blocks that appear before declarations.
    They are typically previous siblings of the node.
    """
    # Check previous siblings for JavaDoc comments
    if (hasattr(node, 'prev_sibling') and node.prev_sibling and
            node.prev_sibling.type == "block_comment"):
        comment_text = _get_node_text(node.prev_sibling, source_bytes)
        if comment_text.startswith("/**"):
            # Remove /** and */ and clean up
            return comment_text[3:-2].strip()

    # Check children for comment (less common)
    for child in node.children:
        if child.type == "block_comment":
            comment_text = _get_node_text(child, source_bytes)
            if comment_text.startswith("/**"):
                return comment_text[3:-2].strip()

    return ""


def _parse_java_method(node: Node, source_bytes: bytes, class_name: str = "") -> Symbol:
    """Parse a Java method declaration."""
    name = ""
    params = ""
    return_type = ""
    type_params = ""  # Story 7.1.2.2: Method-level generic parameters
    throws_clause = ""  # Story 7.1.2.3: Throws declarations

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            name = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)
        elif child.type == "type_identifier" or child.type == "void_type":
            return_type = _get_node_text(child, source_bytes)
        elif child.type in ("generic_type", "array_type", "scoped_type_identifier"):
            return_type = _get_node_text(child, source_bytes)
        elif child.type == "type_parameters":  # Story 7.1.2.2: Capture method generics
            type_params = _get_node_text(child, source_bytes)
        elif child.type == "throws":  # Story 7.1.2.3: Capture throws clause
            throws_clause = _get_node_text(child, source_bytes)

    # Build signature using helper
    return_str = return_type if return_type else "void"
    full_name = f"{class_name}.{name}" if class_name else name
    # Include type parameters if present (e.g., <T extends Comparable<T>>)
    method_decl = f"{type_params} {return_str}" if type_params else return_str
    signature = _build_java_signature(modifiers, method_decl, f"{name}{params}")
    # Append throws clause if present (e.g., "throws IOException, SQLException")
    if throws_clause:
        signature += f" {throws_clause}"

    docstring = _extract_java_docstring(node, source_bytes)

    return Symbol(
        name=full_name,
        kind="method" if class_name else "function",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    )


def _parse_java_constructor(node: Node, source_bytes: bytes, class_name: str) -> Symbol:
    """Parse a Java constructor declaration."""
    name = ""
    params = ""
    throws_clause = ""  # Story 7.1.2.3: Throws declarations

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            name = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)
        elif child.type == "throws":  # Story 7.1.2.3: Capture throws clause
            throws_clause = _get_node_text(child, source_bytes)

    # Build signature using helper
    full_name = f"{class_name}.{name}"
    signature = _build_java_signature(modifiers, f"{name}{params}")
    # Append throws clause if present (e.g., "throws IOException, SQLException")
    if throws_clause:
        signature += f" {throws_clause}"

    docstring = _extract_java_docstring(node, source_bytes)

    return Symbol(
        name=full_name,
        kind="constructor",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    )


def _parse_java_field(node: Node, source_bytes: bytes, class_name: str = "") -> list[Symbol]:
    """Parse a Java field declaration."""
    type_name = ""
    field_names = []

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type in ("type_identifier", "generic_type", "array_type",
                          "integral_type", "floating_point_type", "boolean_type"):
            type_name = _get_node_text(child, source_bytes)
        elif child.type == "variable_declarator":
            for var_child in child.children:
                if var_child.type == "identifier":
                    field_names.append(_get_node_text(var_child, source_bytes))

    # Create symbols for each field
    symbols = []
    for field_name in field_names:
        full_name = f"{class_name}.{field_name}" if class_name else field_name

        # Build signature using helper
        signature = _build_java_signature(modifiers, type_name, field_name)

        symbols.append(Symbol(
            name=full_name,
            kind="field",
            signature=signature,
            docstring="",  # Fields typically don't have individual docstrings
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            annotations=annotations,  # Story 7.1.2.1
        ))

    return symbols


def _extract_java_inheritances(
    node: Node,
    source_bytes: bytes,
    child_name: str,
    package_namespace: str,
    import_map: dict[str, str]
) -> list[Inheritance]:
    """
    Extract inheritance relationships from a Java class or interface declaration.

    Args:
        node: Tree-sitter node for class_declaration or interface_declaration
        source_bytes: Source code as bytes
        child_name: Full name of child class (e.g., "com.example.Outer.Inner")
        package_namespace: Package name for type resolution (e.g., "com.example")
        import_map: Mapping of short names to full qualified names

    Returns:
        List of Inheritance objects

    Example:
        class UserService extends BaseService implements Loggable
        -> [
            Inheritance(child="UserService", parent="BaseService"),
            Inheritance(child="UserService", parent="Loggable")
        ]
    """
    inheritances = []

    # Extract superclass (extends) - this is a named field
    superclass_node = node.child_by_field_name("superclass")
    if superclass_node:
        parent_name = _extract_type_from_node(superclass_node, source_bytes)
        if parent_name:
            # Strip generics and resolve full name
            parent_name = _strip_generic_type(parent_name)
            parent_full = _resolve_java_type(parent_name, package_namespace, import_map)
            inheritances.append(Inheritance(child=child_name, parent=parent_full))

    # Extract super_interfaces and extends_interfaces by traversing children
    # These are NOT named fields, just child nodes with specific types
    for child in node.children:
        # Handle super_interfaces (implements for classes)
        if child.type == "super_interfaces":
            # Find type_list child (super_interfaces = implements + type_list)
            type_list = None
            for subchild in child.children:
                if subchild.type == "type_list":
                    type_list = subchild
                    break

            if type_list:
                # Extract only type nodes from type_list (skip commas)
                for type_node in type_list.children:
                    if type_node.type in (
                        "type_identifier",
                        "generic_type",
                        "scoped_type_identifier"
                    ):
                        interface_name = _extract_type_from_node(type_node, source_bytes)
                        if interface_name:
                            # Strip generics and resolve full name
                            interface_name = _strip_generic_type(interface_name)
                            interface_full = _resolve_java_type(
                                interface_name, package_namespace, import_map
                            )
                            inheritances.append(
                                Inheritance(child=child_name, parent=interface_full)
                            )

        # Handle extends_interfaces (extends for interfaces)
        elif child.type == "extends_interfaces":
            # Find type_list child (extends_interfaces = extends + type_list)
            type_list = None
            for subchild in child.children:
                if subchild.type == "type_list":
                    type_list = subchild
                    break

            if type_list:
                # Extract only type nodes from type_list (skip commas)
                for type_node in type_list.children:
                    if type_node.type in (
                        "type_identifier",
                        "generic_type",
                        "scoped_type_identifier"
                    ):
                        extended_interface = _extract_type_from_node(type_node, source_bytes)
                        if extended_interface:
                            # Strip generics and resolve full name
                            extended_interface = _strip_generic_type(extended_interface)
                            extended_full = _resolve_java_type(
                                extended_interface, package_namespace, import_map
                            )
                            inheritances.append(
                                Inheritance(child=child_name, parent=extended_full)
                            )

    return inheritances


def _extract_type_from_node(node: Node, source_bytes: bytes) -> str:
    """
    Extract type name from a tree-sitter node.

    Handles both simple type_identifier and complex generic_type nodes.
    For nodes like superclass or super_interfaces, traverses children to find the actual type.

    Args:
        node: Tree-sitter node
        source_bytes: Source code as bytes

    Returns:
        Type name string (may include generics)

    Examples:
        type_identifier "BaseUser" -> "BaseUser"
        generic_type "ArrayList<String>" -> "ArrayList<String>"
        superclass node -> "BaseUser" (extracts from children)
    """
    # If the node itself is a type_identifier or generic_type, return its text
    if node.type == "type_identifier":
        return _get_node_text(node, source_bytes)
    elif node.type == "generic_type":
        # Get full text including generics
        return _get_node_text(node, source_bytes)
    elif node.type == "scoped_type_identifier":
        # For fully qualified names like com.example.BaseClass
        return _get_node_text(node, source_bytes)

    # For container nodes (like superclass, super_interfaces), traverse children
    for child in node.children:
        if child.type in ("type_identifier", "generic_type", "scoped_type_identifier"):
            return _extract_type_from_node(child, source_bytes)

    # Fallback: return empty string if no type found
    return ""


def _parse_java_class(
    node: Node,
    source_bytes: bytes,
    namespace: str = "",
    import_map: dict[str, str] | None = None,
    inheritances: list[Inheritance] | None = None
) -> list[Symbol]:
    """Parse a Java class declaration.

    Args:
        node: Tree-sitter node for class_declaration
        source_bytes: Source code as bytes
        namespace: Current package name (e.g., "com.example.service")
        import_map: Mapping of short names to full qualified names
        inheritances: List to collect inheritance relationships (mutated in-place)

    Returns:
        List of Symbol objects for the class and its members
    """
    symbols = []
    class_name = ""
    type_params = ""
    superclass = ""
    interfaces = []

    if import_map is None:
        import_map = {}
    if inheritances is None:
        inheritances = []

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            class_name = _get_node_text(child, source_bytes)
        elif child.type == "type_parameters":
            type_params = _get_node_text(child, source_bytes)
        elif child.type == "superclass":
            for super_child in child.children:
                if super_child.type == "type_identifier":
                    superclass = _get_node_text(super_child, source_bytes)
        elif child.type == "super_interfaces":
            for interface_child in child.children:
                if interface_child.type == "type_list":
                    for type_child in interface_child.children:
                        if type_child.type == "type_identifier":
                            interfaces.append(_get_node_text(type_child, source_bytes))

    # Epic 10 Part 3: Extract inheritance relationships
    if class_name:
        # Construct full class name
        full_class_name = f"{namespace}.{class_name}" if namespace else class_name
        # Extract package namespace (for nested classes, removes outer class part)
        package_namespace = _extract_package_namespace(full_class_name)
        # Extract inheritances
        class_inheritances = _extract_java_inheritances(
            node, source_bytes, full_class_name, package_namespace, import_map
        )
        inheritances.extend(class_inheritances)

    # Build class signature using helper
    class_decl = class_name + type_params if type_params else class_name
    signature_parts = ["class", class_decl]
    if superclass:
        signature_parts.append(f"extends {superclass}")
    if interfaces:
        signature_parts.append(f"implements {', '.join(interfaces)}")

    signature = _build_java_signature(modifiers, *signature_parts)
    docstring = _extract_java_docstring(node, source_bytes)

    # Add class symbol
    symbols.append(Symbol(
        name=class_name,
        kind="class",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    ))

    # Parse class body (methods, fields, constructors)
    for child in node.children:
        if child.type == "class_body":
            for body_child in child.children:
                if body_child.type == "method_declaration":
                    method = _parse_java_method(body_child, source_bytes, class_name)
                    symbols.append(method)
                elif body_child.type == "constructor_declaration":
                    constructor = _parse_java_constructor(body_child, source_bytes, class_name)
                    symbols.append(constructor)
                elif body_child.type == "field_declaration":
                    fields = _parse_java_field(body_child, source_bytes, class_name)
                    symbols.extend(fields)
                elif body_child.type == "class_declaration":
                    # Nested class - use parent class name as namespace for nested class
                    nested_namespace = f"{namespace}.{class_name}" if namespace else class_name
                    nested_symbols = _parse_java_class(
                        body_child, source_bytes, nested_namespace, import_map, inheritances
                    )
                    symbols.extend(nested_symbols)

    return symbols


def _parse_java_interface(
    node: Node,
    source_bytes: bytes,
    namespace: str = "",
    import_map: dict[str, str] | None = None,
    inheritances: list[Inheritance] | None = None
) -> list[Symbol]:
    """Parse a Java interface declaration.

    Args:
        node: Tree-sitter node for interface_declaration
        source_bytes: Source code as bytes
        namespace: Current package name
        import_map: Mapping of short names to full qualified names
        inheritances: List to collect inheritance relationships

    Returns:
        List of Symbol objects for the interface and its members
    """
    symbols = []
    interface_name = ""
    type_params = ""
    extends = []

    if import_map is None:
        import_map = {}
    if inheritances is None:
        inheritances = []

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            interface_name = _get_node_text(child, source_bytes)
        elif child.type == "type_parameters":
            type_params = _get_node_text(child, source_bytes)
        elif child.type == "extends_interfaces":
            for ext_child in child.children:
                if ext_child.type == "type_list":
                    for type_child in ext_child.children:
                        if type_child.type in (
                            "type_identifier",
                            "generic_type",
                            "scoped_type_identifier",
                        ):
                            extends.append(_get_node_text(type_child, source_bytes))

    # Build interface signature using helper
    interface_decl = interface_name + type_params if type_params else interface_name
    signature_parts = ["interface", interface_decl]
    if extends:
        signature_parts.append(f"extends {', '.join(extends)}")

    signature = _build_java_signature(modifiers, *signature_parts)
    docstring = _extract_java_docstring(node, source_bytes)

    # Add interface symbol
    symbols.append(Symbol(
        name=interface_name,
        kind="interface",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    ))

    # Epic 10 Part 3: Extract inheritance relationships for interface
    if interface_name:
        # Construct full interface name
        full_interface_name = f"{namespace}.{interface_name}" if namespace else interface_name
        # Extract package namespace (for nested interfaces, removes outer class part)
        package_namespace = _extract_package_namespace(full_interface_name)
        # Extract inheritances (interface extends other interfaces)
        interface_inheritances = _extract_java_inheritances(
            node, source_bytes, full_interface_name, package_namespace, import_map
        )
        inheritances.extend(interface_inheritances)

    # Parse interface body (method declarations)
    for child in node.children:
        if child.type == "interface_body":
            for body_child in child.children:
                if body_child.type == "method_declaration":
                    method = _parse_java_method(body_child, source_bytes, interface_name)
                    symbols.append(method)

    return symbols


def _parse_java_enum(node: Node, source_bytes: bytes) -> list[Symbol]:
    """Parse a Java enum declaration."""
    symbols = []
    enum_name = ""

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            enum_name = _get_node_text(child, source_bytes)

    # Build enum signature using helper
    signature = _build_java_signature(modifiers, "enum", enum_name)
    docstring = _extract_java_docstring(node, source_bytes)

    # Add enum symbol
    symbols.append(Symbol(
        name=enum_name,
        kind="enum",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    ))

    # Parse enum body (constants, methods)
    for child in node.children:
        if child.type == "enum_body":
            for body_child in child.children:
                if body_child.type == "method_declaration":
                    method = _parse_java_method(body_child, source_bytes, enum_name)
                    symbols.append(method)
                elif body_child.type == "constructor_declaration":
                    constructor = _parse_java_constructor(body_child, source_bytes, enum_name)
                    symbols.append(constructor)

    return symbols


def _parse_java_record(node: Node, source_bytes: bytes) -> list[Symbol]:
    """Parse a Java record declaration (Java 14+)."""
    symbols = []
    record_name = ""
    type_params = ""
    params = ""

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            record_name = _get_node_text(child, source_bytes)
        elif child.type == "type_parameters":
            type_params = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)

    # Build record signature using helper
    name_part = record_name + type_params if type_params else record_name
    signature = _build_java_signature(modifiers, "record", f"{name_part}{params}")
    docstring = _extract_java_docstring(node, source_bytes)

    # Add record symbol
    symbols.append(Symbol(
        name=record_name,
        kind="record",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    ))

    # Parse record body (methods)
    for child in node.children:
        if child.type == "class_body":  # Records use class_body too
            for body_child in child.children:
                if body_child.type == "method_declaration":
                    method = _parse_java_method(body_child, source_bytes, record_name)
                    symbols.append(method)

    return symbols


def _parse_java_import(node: Node, source_bytes: bytes) -> Import | None:
    """Parse a Java import statement."""
    module = ""
    is_static = False
    is_wildcard = False

    for child in node.children:
        if child.type == "scoped_identifier" or child.type == "identifier":
            module = _get_node_text(child, source_bytes)
        elif child.type == "asterisk":
            is_wildcard = True
        elif child.type == "static":
            is_static = True

    if module:
        # Handle wildcard imports
        if is_wildcard:
            module = module + ".*"

        return Import(
            module=module,
            names=[],  # Java imports don't have "as" aliases like Python
            is_from=is_static,  # Use is_from to indicate static imports
        )

    return None


def _extract_java_module_docstring(tree, source_bytes: bytes) -> str:
    """Extract module-level JavaDoc comment."""
    root = tree.root_node

    # Look for first block comment (/** ... */)
    for child in root.children:
        if child.type == "block_comment":
            comment_text = _get_node_text(child, source_bytes)
            if comment_text.startswith("/**"):
                return comment_text[3:-2].strip()
        elif child.type in ("class_declaration", "interface_declaration",
                           "enum_declaration", "record_declaration"):
            # Found a declaration, extract its docstring as module docstring
            return _extract_java_docstring(child, source_bytes)

    return ""


def _parse_java_package(node: Node, source_bytes: bytes) -> str:
    """Extract Java package declaration."""
    for child in node.children:
        if child.type == "scoped_identifier" or child.type == "identifier":
            return _get_node_text(child, source_bytes)
    return ""


# ============================================================================
# Epic 11, Story 11.2: Java Call Extraction
# ============================================================================


def _build_java_static_import_map(root: Node, source_bytes: bytes) -> dict[str, str]:
    """Build mapping of statically imported method names to full qualified names.

    Args:
        root: Tree-sitter root node
        source_bytes: Source code bytes

    Returns:
        Dictionary mapping method names to full qualified names

    Examples:
        import static java.util.Collections.sort;
        -> {"sort": "java.util.Collections.sort"}

        import static java.lang.Math.*;
        -> Will need runtime resolution based on actual usage
    """
    static_import_map = {}

    for child in root.children:
        if child.type == "import_declaration":
            # Check if it's a static import
            is_static = False
            import_path = ""

            for import_child in child.children:
                if import_child.type == "static":
                    is_static = True
                elif import_child.type == "scoped_identifier":
                    import_path = _get_node_text(import_child, source_bytes)
                elif import_child.type == "asterisk_import":
                    # Wildcard static import: import static java.lang.Math.*;
                    # We'll mark this package for later resolution
                    if is_static and import_path:
                        static_import_map[f"_wildcard_{import_path}"] = import_path

            # Handle specific static import: import static pkg.Class.method;
            if is_static and import_path and "." in import_path:
                method_name = import_path.split(".")[-1]
                static_import_map[method_name] = import_path

    return static_import_map


def _resolve_java_static_import(
    method_name: str,
    static_import_map: dict[str, str]
) -> str | None:
    """Resolve statically imported method name to full qualified name.

    Args:
        method_name: Method name to resolve
        static_import_map: Static import mapping

    Returns:
        Full qualified name or None if not found
    """
    # Direct match
    if method_name in static_import_map:
        return static_import_map[method_name]

    # Check wildcard imports
    for key, package in static_import_map.items():
        if key.startswith("_wildcard_"):
            # For wildcard, assume method belongs to this package
            # This is best-effort; actual resolution would need type analysis
            return f"{package}.{method_name}"

    return None


def _parse_java_method_call(
    node: Node,
    source_bytes: bytes,
    caller: str,
    import_map: dict[str, str],
    static_import_map: dict[str, str],
    namespace: str,
    parent_map: dict[str, str]
) -> Optional[Call]:
    """Parse a Java method invocation node.

    Args:
        node: method_invocation node
        source_bytes: Source code bytes
        caller: Calling method name (e.g., "UserService.createUser")
        import_map: Regular import mapping
        static_import_map: Static import mapping
        namespace: Current package namespace
        parent_map: Parent class mapping for super() resolution

    Returns:
        Call object or None
    """
    # Collect all identifiers in order
    # For "user.save()", we get: ["user", "save"]
    # For "method()", we get: ["method"]
    # For chained calls "obj.m1().m2()", process only the outermost level
    identifiers = []
    has_super = False
    object_expr = None  # Track the object part for chained calls

    for child in node.children:
        if child.type == "identifier":
            identifiers.append(_get_node_text(child, source_bytes))
        elif child.type == "super":
            has_super = True
        elif child.type == "field_access":
            # field_access contains object.field structure
            for field_child in child.children:
                if field_child.type == "identifier":
                    identifiers.append(_get_node_text(field_child, source_bytes))
        elif child.type == "method_invocation":
            # Nested method call (chained): obj.m1().m2()
            # The nested invocation will be processed recursively
            # For this level, we just note that the object part is a method call
            object_expr = child

    if not identifiers and not object_expr:
        return None

    # Build callee_raw
    callee_raw = ""

    if has_super and identifiers:
        # super.method() - resolve to parent class
        method_name = identifiers[-1]  # Last identifier is method name
        if "." in caller:
            class_name = caller.rsplit(".", 1)[0]
            if class_name in parent_map:
                parent_class = parent_map[class_name]
                callee_raw = f"{parent_class}.{method_name}"
        if not callee_raw:
            # Fallback: use namespace
            callee_raw = f"{namespace}.Parent.{method_name}"

    elif object_expr and identifiers:
        # Chained call: obj.m1().m2()
        # object_expr is the nested method_invocation (m1())
        # identifiers contains the method name for current level (m2)
        # We need to infer the type from the chain
        # Simple heuristic: extract the first object from the nested chain
        def get_chain_object(node):
            """Extract the base object from a method chain."""
            for child in node.children:
                if child.type == "identifier":
                    return _get_node_text(child, source_bytes)
                elif child.type == "method_invocation":
                    # Recursively get from nested chain
                    return get_chain_object(child)
            return None

        base_obj = get_chain_object(object_expr)
        if base_obj and identifiers:
            method_name = identifiers[-1]
            callee_raw = f"{base_obj}.{method_name}"
        elif identifiers:
            # Fallback: just use method name
            callee_raw = identifiers[-1]

    elif len(identifiers) == 1:
        # Simple method call: method()
        callee_raw = identifiers[0]

    elif len(identifiers) >= 2:
        # obj.method() or Class.method()
        # First identifier is object/class, last is method
        obj_name = identifiers[0]
        method_name = identifiers[-1]
        callee_raw = f"{obj_name}.{method_name}"

    if not callee_raw:
        return None

    # Resolve callee to full qualified name
    callee = callee_raw

    # Case 1: Static import resolution
    if "." not in callee_raw:
        static_resolved = _resolve_java_static_import(callee_raw, static_import_map)
        if static_resolved:
            callee = static_resolved
        else:
            # Assume it's in same package
            callee = f"{namespace}.{callee_raw}"

    # Case 2: Class.method() or obj.method() - resolve class via import_map
    elif "." in callee_raw:
        parts = callee_raw.split(".")
        class_part = parts[0]
        method_part = ".".join(parts[1:])

        if class_part in import_map:
            # Resolve via import_map
            full_class = import_map[class_part]
            callee = f"{full_class}.{method_part}"
        elif class_part[0].isupper():
            # Uppercase - assume it's in same package
            callee = f"{namespace}.{callee_raw}"
        else:
            # Lowercase - try capitalizing (simple type inference heuristic)
            # E.g., "user.save()" → try "User.save()"
            capitalized = class_part.capitalize()
            if capitalized in import_map:
                full_class = import_map[capitalized]
                callee = f"{full_class}.{method_part}"
            else:
                # Assume capitalized class in same package
                callee = f"{namespace}.{capitalized}.{method_part}"

    # Determine call type
    if "." in callee_raw:
        # Check if object part is uppercase (Class.method)
        first_part = callee_raw.split(".")[0]
        if first_part[0].isupper() or first_part == "super":
            call_type = CallType.STATIC_METHOD
        else:
            call_type = CallType.METHOD
    else:
        call_type = CallType.FUNCTION

    # Extract argument count
    args_count = None
    for child in node.children:
        if child.type == "argument_list":
            args_count = sum(
                1 for c in child.children
                if c.type not in (",", "(", ")")
            )

    return Call(
        caller=caller,
        callee=callee,
        line_number=node.start_point[0] + 1,
        call_type=call_type,
        arguments_count=args_count
    )


def _parse_java_constructor_call(
    node: Node,
    source_bytes: bytes,
    caller: str,
    import_map: dict[str, str],
    namespace: str
) -> Optional[Call]:
    """Parse a Java object creation expression (constructor call).

    Args:
        node: object_creation_expression node
        source_bytes: Source code bytes
        caller: Calling method name
        import_map: Import mapping
        namespace: Current package namespace

    Returns:
        Call object or None
    """
    # Extract type being instantiated
    type_name = ""

    for child in node.children:
        if child.type == "type_identifier":
            type_name = _get_node_text(child, source_bytes)
        elif child.type == "generic_type":
            # Handle generics: ArrayList<String> -> ArrayList
            for generic_child in child.children:
                if generic_child.type == "type_identifier":
                    type_name = _get_node_text(generic_child, source_bytes)
                    break
        elif child.type == "scoped_type_identifier":
            # Handle scoped types: java.util.ArrayList
            type_name = _get_node_text(child, source_bytes)

    if not type_name:
        return None

    # Resolve type to full qualified name
    if "." in type_name:
        # Already fully qualified
        full_type = type_name
    elif type_name in import_map:
        # Resolve via import_map
        full_type = import_map[type_name]
    else:
        # Assume same package
        full_type = f"{namespace}.{type_name}"

    # Format as constructor: ClassName.<init>
    callee = f"{full_type}.<init>"

    # Extract argument count
    args_count = None
    for child in node.children:
        if child.type == "argument_list":
            args_count = sum(
                1 for c in child.children
                if c.type not in (",", "(", ")")
            )

    return Call(
        caller=caller,
        callee=callee,
        line_number=node.start_point[0] + 1,
        call_type=CallType.CONSTRUCTOR,
        arguments_count=args_count
    )


def _extract_java_calls(
    node: Node,
    source_bytes: bytes,
    caller: str,
    import_map: dict[str, str],
    static_import_map: dict[str, str],
    namespace: str,
    parent_map: dict[str, str]
) -> list[Call]:
    """Recursively extract Java calls from AST node.

    Args:
        node: Current AST node
        source_bytes: Source code bytes
        caller: Current method context
        import_map: Import mapping
        static_import_map: Static import mapping
        namespace: Package namespace
        parent_map: Parent class mapping

    Returns:
        List of Call objects
    """
    calls = []

    # Extract calls from this node
    if node.type == "method_invocation":
        call = _parse_java_method_call(
            node, source_bytes, caller, import_map,
            static_import_map, namespace, parent_map
        )
        if call:
            calls.append(call)

    elif node.type == "object_creation_expression":
        call = _parse_java_constructor_call(
            node, source_bytes, caller, import_map, namespace
        )
        if call:
            calls.append(call)

    # Recursively process children
    for child in node.children:
        calls.extend(
            _extract_java_calls(
                child, source_bytes, caller, import_map,
                static_import_map, namespace, parent_map
            )
        )

    return calls


def _extract_java_calls_from_tree(
    tree,
    source_bytes: bytes,
    imports: list[Import],
    inheritances: list[Inheritance],
    namespace: str,
    import_map: dict[str, str]
) -> list[Call]:
    """Extract all Java call relationships from parse tree.

    Args:
        tree: Tree-sitter parse tree
        source_bytes: Source code bytes
        imports: Import list
        inheritances: Inheritance list
        namespace: Package namespace
        import_map: Import mapping (already built)

    Returns:
        List of Call objects
    """
    # Build static import map
    root = tree.root_node
    static_import_map = _build_java_static_import_map(root, source_bytes)

    # Build parent map for super() resolution
    parent_map = {}
    for inh in inheritances:
        parent_map[inh.child] = inh.parent

    calls = []

    # Traverse classes and methods
    for child in root.children:
        if child.type in ("class_declaration", "interface_declaration"):
            # Extract class name
            class_name = ""
            for node in child.children:
                if node.type == "identifier":
                    class_name = _get_node_text(node, source_bytes)
                    break

            if not class_name:
                continue

            # Full class name with namespace
            full_class_name = f"{namespace}.{class_name}" if namespace else class_name

            # Find class body
            body_node = None
            for node in child.children:
                if node.type in ("class_body", "interface_body"):
                    body_node = node
                    break

            if not body_node:
                continue

            # Process methods in class
            for method_node in body_node.children:
                if method_node.type == "method_declaration":
                    # Extract method name
                    method_name = ""
                    for node in method_node.children:
                        if node.type == "identifier":
                            method_name = _get_node_text(node, source_bytes)
                            break

                    if method_name:
                        caller = f"{full_class_name}.{method_name}"
                        # Extract calls from method body
                        calls.extend(
                            _extract_java_calls(
                                method_node, source_bytes, caller,
                                import_map, static_import_map, namespace, parent_map
                            )
                        )

                elif method_node.type == "constructor_declaration":
                    # Constructor
                    caller = f"{full_class_name}.<init>"
                    calls.extend(
                        _extract_java_calls(
                            method_node, source_bytes, caller,
                            import_map, static_import_map, namespace, parent_map
                        )
                    )

    return calls
