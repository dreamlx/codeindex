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
        """Extract symbols from Swift source code (Story 1.4: with docstrings).

        Args:
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes

        Returns:
            List of Symbol objects
        """
        symbols: list[Symbol] = []
        root = tree.root_node

        # Build docstring map: node index -> docstring text (Story 1.4)
        docstring_map = self._build_docstring_map(root, source_bytes)

        # Extract top-level declarations
        for i, child in enumerate(root.children):
            # Get docstring for this node if exists
            docstring = docstring_map.get(i, "")

            # Classes (but check if it's actually an extension)
            if child.type == "class_declaration":
                # Swift tree-sitter uses class_declaration for both classes and extensions
                # Check the text to distinguish (may have access modifiers)
                node_text = child.text.decode('utf-8', errors='replace').strip()
                # Check for 'extension' keyword (with or without access modifier)
                if ' extension ' in node_text or node_text.startswith('extension '):
                    # This is actually an extension
                    symbols.extend(self._extract_extension(child, source_bytes, docstring))
                else:
                    # This is a real class
                    symbols.extend(self._extract_class(child, source_bytes, docstring))

            # Structs (treat as classes for now)
            elif child.type == "struct_declaration":
                symbols.extend(self._extract_struct(child, source_bytes, docstring))

            # Enums (treat as classes for now)
            elif child.type == "enum_declaration":
                symbols.extend(self._extract_enum(child, source_bytes, docstring))

            # Protocols (Story 1.2)
            elif child.type == "protocol_declaration":
                symbols.extend(self._extract_protocol(child, source_bytes, docstring))

            # Top-level functions
            elif child.type == "function_declaration":
                symbol = self._extract_function(child, source_bytes, docstring)
                if symbol:
                    symbols.append(symbol)

            # Extensions (Story 2.1)
            elif child.type == "extension_declaration":
                symbols.extend(self._extract_extension(child, source_bytes, docstring))

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
            if child.type == "class_declaration":
                # Check if it's actually an extension (may have access modifier)
                node_text = child.text.decode('utf-8', errors='replace').strip()
                if ' extension ' in node_text or node_text.startswith('extension '):
                    # This is an extension
                    inheritances.extend(self._extract_extension_inheritances(child, source_bytes))
                else:
                    # Regular class
                    inheritances.extend(self._extract_type_inheritances(child, source_bytes))
            elif child.type in ["struct_declaration", "protocol_declaration"]:
                inheritances.extend(self._extract_type_inheritances(child, source_bytes))
            # Fallback for actual extension_declaration nodes (if they exist)
            elif child.type == "extension_declaration":
                inheritances.extend(self._extract_extension_inheritances(child, source_bytes))

        return inheritances

    # ==================== Private Helper Methods ====================

    def _extract_class(
        self, node, source_bytes: bytes, docstring: str = ""
    ) -> list[Symbol]:
        """Extract class declaration and its members.

        Args:
            node: class_declaration node
            source_bytes: Source code bytes
            docstring: Docstring for this class (Story 1.4)

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

        # Extract generic parameters (Story 1.5)
        generics = self._extract_generic_parameters(node)

        # Extract access modifier (Story 1.5)
        access_modifier = self._extract_access_modifier(node)

        # Create class symbol with docstring (Story 1.4)
        class_symbol = Symbol(
            name=class_name,
            kind="class",
            signature=f"{access_modifier}class {class_name}{generics}",
            docstring=docstring,
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

    def _extract_struct(
        self, node, source_bytes: bytes, docstring: str = ""
    ) -> list[Symbol]:
        """Extract struct declaration and its members.

        Args:
            node: struct_declaration node
            source_bytes: Source code bytes
            docstring: Docstring for this struct (Story 1.4)

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

        # Extract generic parameters (Story 1.5)
        generics = self._extract_generic_parameters(node)

        # Extract access modifier (Story 1.5)
        access_modifier = self._extract_access_modifier(node)

        # Treat struct as class kind, with docstring (Story 1.4)
        struct_symbol = Symbol(
            name=struct_name,
            kind="class",
            signature=f"{access_modifier}struct {struct_name}{generics}",
            docstring=docstring,
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

    def _extract_enum(
        self, node, source_bytes: bytes, docstring: str = ""
    ) -> list[Symbol]:
        """Extract enum declaration.

        Args:
            node: enum_declaration node
            source_bytes: Source code bytes
            docstring: Docstring for this enum (Story 1.4)

        Returns:
            List with single enum symbol
        """
        name_node = node.child_by_field_name("name")
        if not name_node:
            return []

        enum_name = name_node.text.decode("utf-8", errors="replace")

        # Extract generic parameters (Story 1.5)
        generics = self._extract_generic_parameters(node)

        # Extract access modifier (Story 1.5)
        access_modifier = self._extract_access_modifier(node)

        enum_symbol = Symbol(
            name=enum_name,
            kind="class",  # Treat enum as class kind
            signature=f"{access_modifier}enum {enum_name}{generics}",
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
        return [enum_symbol]

    def _extract_function(
        self, node, source_bytes: bytes, docstring: str = ""
    ) -> Symbol | None:
        """Extract top-level function declaration.

        Args:
            node: function_declaration node
            source_bytes: Source code bytes
            docstring: Docstring for this function (Story 1.4)

        Returns:
            Function symbol or None
        """
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        func_name = name_node.text.decode("utf-8", errors="replace")

        # Enhanced signature extraction (Story 2.2: include where clauses)
        signature = self._extract_function_signature(node, source_bytes)

        return Symbol(
            name=func_name,
            kind="function",
            signature=signature,
            docstring=docstring,
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
            # Extract methods (both regular and protocol methods)
            if child.type in ["function_declaration", "protocol_function_declaration"]:
                # Try field-based extraction first
                name_node = child.child_by_field_name("name")
                if not name_node:
                    # Fallback: find simple_identifier for protocol methods
                    for subchild in child.children:
                        if subchild.type == "simple_identifier":
                            name_node = subchild
                            break

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

            # Extract properties (Story 1.1, also works for protocols)
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

    def _extract_protocol(
        self, node, source_bytes: bytes, docstring: str = ""
    ) -> list[Symbol]:
        """Extract protocol declaration and its members (Story 1.2).

        Args:
            node: protocol_declaration node
            source_bytes: Source code bytes
            docstring: Docstring for this protocol (Story 1.4)

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

        # Extract access modifier (Story 1.5)
        access_modifier = self._extract_access_modifier(node)

        # Create protocol symbol with docstring (Story 1.4)
        protocol_symbol = Symbol(
            name=protocol_name,
            kind="class",
            signature=f"{access_modifier}protocol {protocol_name}",
            docstring=docstring,
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

        # Find inheritance_specifier nodes (Swift AST uses this, not type_inheritance_clause)
        for child in node.children:
            if child.type == "inheritance_specifier":
                # Extract parent type from this specifier
                parent_type = self._extract_parent_type_from_specifier(
                    child, source_bytes
                )
                if parent_type:
                    inheritance = Inheritance(
                        child=type_name,
                        parent=parent_type,
                    )
                    inheritances.append(inheritance)

        return inheritances

    def _extract_parent_type_from_specifier(
        self, node, source_bytes: bytes
    ) -> str | None:
        """Extract parent type name from inheritance_specifier node.

        Args:
            node: inheritance_specifier node
            source_bytes: Source code bytes

        Returns:
            Parent type name or None
        """
        # Look for type_identifier in user_type structure
        for child in node.children:
            if child.type == "user_type":
                for subchild in child.children:
                    if subchild.type == "type_identifier":
                        return subchild.text.decode("utf-8", errors="replace")
            # Direct type_identifier
            elif child.type == "type_identifier":
                return child.text.decode("utf-8", errors="replace")

        return None

    def _build_docstring_map(self, node, source_bytes: bytes) -> dict[int, str]:
        """Build map of node indices to their preceding docstrings (Story 1.4).

        Args:
            node: Parent node to search (usually root)
            source_bytes: Source code bytes

        Returns:
            Dictionary mapping child index to docstring text
        """
        docstring_map: dict[int, str] = {}
        prev_comment = None

        for i, child in enumerate(node.children):
            # Check for both comment types (/// and /** */)
            if child.type in ["comment", "multiline_comment"]:
                # Check if it's a doc comment
                comment_text = child.text.decode("utf-8", errors="replace")
                if self._is_doc_comment(comment_text):
                    prev_comment = self._clean_docstring(comment_text)
            else:
                # Non-comment node - associate prev_comment if exists
                if prev_comment:
                    docstring_map[i] = prev_comment
                    prev_comment = None

        return docstring_map

    def _is_doc_comment(self, comment_text: str) -> bool:
        """Check if comment is a documentation comment (Story 1.4).

        Args:
            comment_text: Raw comment text

        Returns:
            True if it's a doc comment (/// or /** */)
        """
        stripped = comment_text.strip()
        return stripped.startswith("///") or stripped.startswith("/**")

    def _clean_docstring(self, comment_text: str) -> str:
        """Clean and format docstring text (Story 1.4).

        Args:
            comment_text: Raw comment text

        Returns:
            Cleaned docstring
        """
        lines = comment_text.split("\n")
        cleaned_lines = []

        for line in lines:
            # Remove /// prefix
            if "///" in line:
                line = line.split("///", 1)[1]
            # Remove /** and */ delimiters
            line = line.replace("/**", "").replace("*/", "")
            # Remove leading * in multi-line comments
            line = line.lstrip(" *")

            cleaned_lines.append(line.strip())

        # Join and clean up
        result = " ".join(cleaned_lines).strip()
        return result

    def _extract_generic_parameters(self, node) -> str:
        """Extract generic type parameters from a node (Story 1.5).

        Args:
            node: AST node that may contain type_parameters

        Returns:
            Generic parameters string (e.g., "<T>", "<K, V>", "<T: Comparable>")
            or empty string if no generics
        """
        for child in node.children:
            if child.type == "type_parameters":
                # Extract the full generic parameter text
                generic_text = child.text.decode("utf-8", errors="replace")
                return generic_text

        return ""

    def _extract_access_modifier(self, node) -> str:
        """Extract access modifier from a node (Story 1.5).

        Args:
            node: AST node that may have modifiers

        Returns:
            Access modifier string (e.g., "public", "private", "internal", "fileprivate")
            or empty string if no access modifier
        """
        for child in node.children:
            if child.type == "modifiers":
                # Extract all modifiers
                modifier_text = child.text.decode("utf-8", errors="replace")
                return modifier_text + " "

        return ""

    def _extract_extension(
        self, node, source_bytes: bytes, docstring: str = ""
    ) -> list[Symbol]:
        """Extract extension declaration and its members (Story 2.1).

        Args:
            node: extension_declaration node
            source_bytes: Source code bytes
            docstring: Docstring for this extension

        Returns:
            List of symbols (extension + methods + properties)
        """
        symbols: list[Symbol] = []

        # Get extended type name
        extended_type = None
        for child in node.children:
            if child.type in ("type_identifier", "simple_identifier", "user_type"):
                extended_type = child.text.decode("utf-8", errors="replace")
                break

        if not extended_type:
            return symbols

        # Extract access modifier
        access_modifier = self._extract_access_modifier(node)

        # Check for protocol conformance in extension
        # Look for inheritance_specifier (protocol conformance)
        protocols = []
        for child in node.children:
            if child.type == "inheritance_specifier":
                # Direct inheritance_specifier node (tree-sitter-swift structure)
                protocol_name = child.text.decode("utf-8", errors="replace")
                protocols.append(protocol_name)
            elif child.type == "type_inheritance_clause":
                # Fallback: nested structure
                protocols.extend(self._extract_parent_types(child, source_bytes))

        # Build extension signature
        if protocols:
            protocol_list = ", ".join(protocols)
            signature = f"{access_modifier}extension {extended_type}: {protocol_list}"
        else:
            signature = f"{access_modifier}extension {extended_type}"

        # Create extension symbol
        extension_symbol = Symbol(
            name=f"{extended_type}+Extension",
            kind="class",  # Treat extension as class kind
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
        symbols.append(extension_symbol)

        # Extract methods and properties from extension body
        body_node = None
        for child in node.children:
            # Extension uses class_body, not extension_body
            if child.type == "class_body":
                body_node = child
                break

        if body_node:
            # Use existing method to extract members
            # Extensions are like classes, use same extraction logic
            symbols.extend(
                self._extract_class_methods(extended_type, body_node, source_bytes)
            )

        return symbols

    def _extract_parent_types(self, node, source_bytes: bytes) -> list[str]:
        """Extract parent type names from type_inheritance_clause.

        Args:
            node: type_inheritance_clause node
            source_bytes: Source code bytes

        Returns:
            List of parent type names
        """
        parent_types = []

        for child in node.children:
            if child.type == "type_identifier":
                parent_type = child.text.decode("utf-8", errors="replace")
                parent_types.append(parent_type)

        return parent_types

    def _extract_extension_inheritances(self, node, source_bytes: bytes) -> list:
        """Extract inheritance relationships from extension declarations (Story 2.1).

        Extensions can add protocol conformance to existing types.

        Args:
            node: extension_declaration node
            source_bytes: Source code bytes

        Returns:
            List of Inheritance objects
        """
        from ..parser import Inheritance

        inheritances: list[Inheritance] = []

        # Get extended type name
        extended_type = None
        for child in node.children:
            if child.type in ("type_identifier", "simple_identifier", "user_type"):
                extended_type = child.text.decode("utf-8", errors="replace")
                break

        if not extended_type:
            return inheritances

        # Check for protocol conformance
        for child in node.children:
            if child.type == "inheritance_specifier":
                # Direct inheritance_specifier node
                protocol_name = child.text.decode("utf-8", errors="replace")
                inheritance = Inheritance(child=extended_type, parent=protocol_name)
                inheritances.append(inheritance)
            elif child.type == "type_inheritance_clause":
                # Fallback: nested structure
                parent_types = self._extract_parent_types(child, source_bytes)

                # Create Inheritance objects for each protocol
                for parent_type in parent_types:
                    inheritance = Inheritance(child=extended_type, parent=parent_type)
                    inheritances.append(inheritance)

        return inheritances

    def _extract_function_signature(self, node, source_bytes: bytes) -> str:
        """Extract complete function signature including where clauses (Story 2.2).

        Args:
            node: function_declaration node
            source_bytes: Source code bytes

        Returns:
            Complete function signature string
        """
        # Start with basic signature (function declaration up to body)
        func_text = node.text.decode("utf-8", errors="replace")

        # Find the opening brace of function body
        brace_index = func_text.find("{")
        if brace_index != -1:
            # Extract signature up to the opening brace
            signature = func_text[:brace_index].strip()
        else:
            # No body (e.g., protocol method), use first line
            signature = func_text.split("\n")[0].strip()

        return signature
