"""Swift language parser - Proof of Concept.

This is a minimal POC demonstrating Swift parsing capability.
Full implementation will be done in phases following TDD approach.

Phase 1: Basic symbol extraction (classes, functions, methods)
Phase 2: Advanced features (extensions, protocols, generics)
Phase 3: Call graph and inheritance relationships

Issue: #23
ADR: docs/architecture/adr/003-add-swift-objc-support.md
"""

from tree_sitter import Parser, Tree

from ..parser import Import, Symbol
from .base import BaseLanguageParser


class SwiftParser(BaseLanguageParser):
    """Swift language parser (POC stage).

    Current capabilities:
    - Basic class/struct/enum detection
    - Simple method extraction
    - Import statements

    TODO (Phase 1):
    - Complete symbol extraction with proper signatures
    - Property/variable extraction
    - Protocol and inheritance support
    - Comprehensive docstring extraction

    TODO (Phase 2):
    - Extension support
    - Generic type handling
    - Property wrapper detection
    - Advanced protocol features

    TODO (Phase 3):
    - Call graph extraction
    - Inheritance relationship tracking
    """

    def __init__(self, parser: Parser):
        """Initialize Swift parser.

        Args:
            parser: Tree-sitter parser configured for Swift
        """
        super().__init__(parser)

    def extract_symbols(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract symbols from Swift source code.

        POC implementation - extracts basic symbols only.

        Args:
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes

        Returns:
            List of Symbol objects
        """
        symbols: list[Symbol] = []
        root = tree.root_node

        # Extract top-level declarations
        for child in root.children:
            # Classes
            if child.type == "class_declaration":
                symbols.extend(self._extract_class(child, source_bytes))

            # Structs (treat as classes for now)
            elif child.type == "struct_declaration":
                symbols.extend(self._extract_struct(child, source_bytes))

            # Enums (treat as classes for now)
            elif child.type == "enum_declaration":
                symbols.extend(self._extract_enum(child, source_bytes))

            # Top-level functions
            elif child.type == "function_declaration":
                symbol = self._extract_function(child, source_bytes)
                if symbol:
                    symbols.append(symbol)

        return symbols

    def extract_imports(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract import statements from Swift source code.

        POC implementation - basic import extraction.

        Args:
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes

        Returns:
            List of Import objects
        """
        imports: list[Import] = []
        root = tree.root_node

        for child in root.children:
            if child.type == "import_declaration":
                # Extract module name from import
                import_text = child.text.decode("utf-8", errors="replace")
                # Simple extraction: "import ModuleName" -> "ModuleName"
                parts = import_text.strip().split()
                if len(parts) >= 2:
                    module_name = parts[1]
                    imports.append(Import(module=module_name, names=[], is_from=False))

        return imports

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
            Empty list (not implemented in POC)
        """
        # Phase 3: Implement call graph extraction
        return []

    def extract_inheritances(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract inheritance relationships from Swift source code.

        TODO: Phase 3 implementation.

        Args:
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes

        Returns:
            Empty list (not implemented in POC)
        """
        # Phase 3: Implement inheritance extraction
        return []

    # ==================== Private Helper Methods ====================

    def _extract_class(self, node, source_bytes: bytes) -> list[Symbol]:
        """Extract class declaration and its members.

        Args:
            node: class_declaration node
            source_bytes: Source code bytes

        Returns:
            List of symbols (class + methods)
        """
        symbols: list[Symbol] = []

        # Get class name
        name_node = node.child_by_field_name("name")
        if not name_node:
            return symbols

        class_name = name_node.text.decode("utf-8", errors="replace")

        # Create class symbol (simplified signature)
        class_symbol = Symbol(
            name=class_name,
            kind="class",
            signature=f"class {class_name}",
            docstring="",  # TODO: Extract docstrings in Phase 1
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
        symbols.append(class_symbol)

        # Extract methods from class body
        body_node = node.child_by_field_name("body")
        if body_node:
            symbols.extend(self._extract_class_methods(class_name, body_node, source_bytes))

        return symbols

    def _extract_struct(self, node, source_bytes: bytes) -> list[Symbol]:
        """Extract struct declaration and its members.

        Args:
            node: struct_declaration node
            source_bytes: Source code bytes

        Returns:
            List of symbols (struct + methods)
        """
        symbols: list[Symbol] = []

        name_node = node.child_by_field_name("name")
        if not name_node:
            return symbols

        struct_name = name_node.text.decode("utf-8", errors="replace")

        # Treat struct as class kind
        struct_symbol = Symbol(
            name=struct_name,
            kind="class",
            signature=f"struct {struct_name}",
            docstring="",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
        symbols.append(struct_symbol)

        # Extract methods
        body_node = node.child_by_field_name("body")
        if body_node:
            symbols.extend(self._extract_class_methods(struct_name, body_node, source_bytes))

        return symbols

    def _extract_enum(self, node, source_bytes: bytes) -> list[Symbol]:
        """Extract enum declaration.

        Args:
            node: enum_declaration node
            source_bytes: Source code bytes

        Returns:
            List with single enum symbol
        """
        name_node = node.child_by_field_name("name")
        if not name_node:
            return []

        enum_name = name_node.text.decode("utf-8", errors="replace")

        enum_symbol = Symbol(
            name=enum_name,
            kind="class",  # Treat enum as class kind
            signature=f"enum {enum_name}",
            docstring="",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
        return [enum_symbol]

    def _extract_function(self, node, source_bytes: bytes) -> Symbol | None:
        """Extract top-level function declaration.

        Args:
            node: function_declaration node
            source_bytes: Source code bytes

        Returns:
            Function symbol or None
        """
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        func_name = name_node.text.decode("utf-8", errors="replace")

        # Simple signature extraction (first line of function)
        func_text = node.text.decode("utf-8", errors="replace")
        first_line = func_text.split("\n")[0].strip()

        return Symbol(
            name=func_name,
            kind="function",
            signature=first_line,
            docstring="",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    def _extract_class_methods(
        self, class_name: str, body_node, source_bytes: bytes
    ) -> list[Symbol]:
        """Extract methods from class/struct body.

        Args:
            class_name: Name of containing class/struct
            body_node: Body node containing method declarations
            source_bytes: Source code bytes

        Returns:
            List of method symbols
        """
        methods: list[Symbol] = []

        for child in body_node.children:
            if child.type == "function_declaration":
                name_node = child.child_by_field_name("name")
                if not name_node:
                    continue

                method_name = name_node.text.decode("utf-8", errors="replace")

                # Simple signature (first line)
                method_text = child.text.decode("utf-8", errors="replace")
                first_line = method_text.split("\n")[0].strip()

                method_symbol = Symbol(
                    name=f"{class_name}.{method_name}",
                    kind="method",
                    signature=first_line,
                    docstring="",
                    line_start=child.start_point[0] + 1,
                    line_end=child.end_point[0] + 1,
                )
                methods.append(method_symbol)

        return methods
