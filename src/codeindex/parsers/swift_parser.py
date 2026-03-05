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

            # Protocols (Story 1.2)
            elif child.type == "protocol_declaration":
                symbols.extend(self._extract_protocol(child, source_bytes))

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
        """Extract inheritance relationships from Swift source code (Story 1.2).

        Extracts:
        - Class inheritance relationships
        - Protocol inheritance relationships
        - Class/struct conformance to protocols

        Args:
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes

        Returns:
            List of Inheritance objects
        """
        from ..parser import Inheritance

        inheritances: list[Inheritance] = []
        root = tree.root_node

        # Process all top-level declarations
        for child in root.children:
            if child.type in [
                "class_declaration",
                "struct_declaration",
                "protocol_declaration",
            ]:
                inheritances.extend(self._extract_type_inheritances(child, source_bytes))

        return inheritances

    # ==================== Private Helper Methods ====================

    def _extract_class(self, node, source_bytes: bytes) -> list[Symbol]:
        """Extract class declaration and its members.

        Args:
            node: class_declaration node
            source_bytes: Source code bytes

        Returns:
            List of symbols (class + properties + methods)
        """
        symbols: list[Symbol] = []

        # Get class name from type_identifier child
        class_name = None
        for child in node.children:
            if child.type == "type_identifier":
                class_name = child.text.decode("utf-8", errors="replace")
                break

        if not class_name:
            return symbols

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

        # Extract methods and properties from class body
        body_node = None
        for child in node.children:
            if child.type == "class_body":
                body_node = child
                break

        if body_node:
            symbols.extend(self._extract_class_methods(class_name, body_node, source_bytes))

        return symbols

    def _extract_struct(self, node, source_bytes: bytes) -> list[Symbol]:
        """Extract struct declaration and its members.

        Args:
            node: struct_declaration node
            source_bytes: Source code bytes

        Returns:
            List of symbols (struct + properties + methods)
        """
        symbols: list[Symbol] = []

        # Get struct name from type_identifier child
        struct_name = None
        for child in node.children:
            if child.type == "type_identifier":
                struct_name = child.text.decode("utf-8", errors="replace")
                break

        if not struct_name:
            return symbols

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

        # Extract methods and properties from struct body
        body_node = None
        for child in node.children:
            if child.type == "class_body":  # Swift uses class_body for struct too
                body_node = child
                break

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
        """Extract methods and properties from class/struct body.

        Args:
            class_name: Name of containing class/struct
            body_node: Body node containing method and property declarations
            source_bytes: Source code bytes

        Returns:
            List of method and property symbols
        """
        symbols: list[Symbol] = []

        for child in body_node.children:
            # Extract methods
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
                symbols.append(method_symbol)

            # Extract properties (Story 1.1)
            elif child.type == "property_declaration":
                prop = self._extract_property(class_name, child, source_bytes)
                if prop:
                    symbols.append(prop)

        return symbols

    def _extract_property(
        self, class_name: str, node, source_bytes: bytes
    ) -> Symbol | None:
        """Extract a single property declaration.

        Handles:
        - Stored properties (var/let)
        - Computed properties (get/set)
        - Property wrappers (@Published, @State, etc.)
        - Lazy properties
        - Static/class properties
        - Visibility modifiers (private, public, etc.)

        Args:
            class_name: Name of containing class/struct
            node: property_declaration node
            source_bytes: Source code bytes

        Returns:
            Property symbol or None
        """
        # Extract property name from pattern binding
        # Swift structure: property_declaration -> pattern_binding -> pattern -> identifier
        prop_name = self._find_property_name(node)
        if not prop_name:
            return None

        # Build signature from full property text
        prop_text = node.text.decode("utf-8", errors="replace")
        first_line = prop_text.split("\n")[0].strip()

        # Extract attributes (@Published, @State, etc.)
        attributes = []
        for child in node.children:
            if child.type == "attribute":
                attr_text = child.text.decode("utf-8", errors="replace")
                attributes.append(attr_text)

        # Extract modifiers (static, lazy, private, etc.)
        modifiers = []
        for child in node.children:
            if child.type == "modifiers":
                for mod_child in child.children:
                    if mod_child.type in [
                        "property_modifier",
                        "member_modifier",
                        "visibility_modifier",
                    ]:
                        mod_text = mod_child.text.decode("utf-8", errors="replace")
                        modifiers.append(mod_text)

        # Build complete signature
        signature_parts = []
        if attributes:
            signature_parts.extend(attributes)
        if modifiers:
            signature_parts.extend(modifiers)
        signature_parts.append(first_line)

        signature = " ".join(signature_parts)

        return Symbol(
            name=f"{class_name}.{prop_name}",
            kind="property",
            signature=signature,
            docstring="",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    def _find_property_name(self, node) -> str | None:
        """Find property name from property_declaration node.

        Swift AST structure:
        property_declaration -> pattern -> simple_identifier

        Args:
            node: property_declaration node

        Returns:
            Property name or None
        """
        # Look for pattern -> simple_identifier (direct children)
        for child in node.children:
            if child.type == "pattern":
                for identifier in child.children:
                    if identifier.type == "simple_identifier":
                        return identifier.text.decode("utf-8", errors="replace")

        # Fallback: search recursively for any simple_identifier
        for child in node.children:
            for subchild in child.children:
                if subchild.type == "simple_identifier":
                    return subchild.text.decode("utf-8", errors="replace")

        return None

    def _extract_protocol(self, node, source_bytes: bytes) -> list[Symbol]:
        """Extract protocol declaration and its members (Story 1.2).

        Args:
            node: protocol_declaration node
            source_bytes: Source code bytes

        Returns:
            List of symbols (protocol + methods + properties)
        """
        symbols: list[Symbol] = []

        # Get protocol name from type_identifier child
        protocol_name = None
        for child in node.children:
            if child.type == "type_identifier":
                protocol_name = child.text.decode("utf-8", errors="replace")
                break

        if not protocol_name:
            return symbols

        # Create protocol symbol (treat as class kind)
        protocol_symbol = Symbol(
            name=protocol_name,
            kind="class",
            signature=f"protocol {protocol_name}",
            docstring="",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
        symbols.append(protocol_symbol)

        # Extract methods and properties from protocol body
        body_node = None
        for child in node.children:
            if child.type == "protocol_body":
                body_node = child
                break

        if body_node:
            symbols.extend(
                self._extract_class_methods(protocol_name, body_node, source_bytes)
            )

        return symbols

    def _extract_type_inheritances(self, node, source_bytes: bytes) -> list:
        """Extract inheritance relationships from class/struct/protocol node (Story 1.2).

        Args:
            node: class_declaration/struct_declaration/protocol_declaration node
            source_bytes: Source code bytes

        Returns:
            List of Inheritance objects
        """
        from ..parser import Inheritance

        inheritances: list[Inheritance] = []

        # Get type name
        type_name = None
        for child in node.children:
            if child.type == "type_identifier":
                type_name = child.text.decode("utf-8", errors="replace")
                break

        if not type_name:
            return inheritances

        # Find type_inheritance_clause (e.g., ": ParentClass, Protocol1, Protocol2")
        for child in node.children:
            if child.type == "type_inheritance_clause":
                # Extract all parent types
                parent_types = self._extract_parent_types(child, source_bytes)
                for parent_type in parent_types:
                    inheritance = Inheritance(
                        child_name=type_name,
                        parent_name=parent_type,
                        inheritance_type="implementation",  # Swift uses inheritance for both
                    )
                    inheritances.append(inheritance)

        return inheritances

    def _extract_parent_types(self, node, source_bytes: bytes) -> list[str]:
        """Extract parent type names from type_inheritance_clause node.

        Args:
            node: type_inheritance_clause node
            source_bytes: Source code bytes

        Returns:
            List of parent type names
        """
        parent_types: list[str] = []

        # Look for type_identifier nodes in inheritance clause
        for child in node.children:
            if child.type == "type_identifier":
                parent_name = child.text.decode("utf-8", errors="replace")
                parent_types.append(parent_name)
            # Handle nested structures (e.g., user_type contains type_identifier)
            elif child.type == "user_type":
                for subchild in child.children:
                    if subchild.type == "type_identifier":
                        parent_name = subchild.text.decode("utf-8", errors="replace")
                        parent_types.append(parent_name)

        return parent_types
