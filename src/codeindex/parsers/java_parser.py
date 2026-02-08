"""Java language parser.

This module provides Java-specific parsing functionality using tree-sitter.
"""

from typing import Optional

from tree_sitter import Node, Tree

from ..parser import Annotation, Call, CallType, Import, Inheritance, Symbol
from .base import BaseLanguageParser
from .utils import get_node_text

# Java standard library classes (java.lang.* implicit imports)
JAVA_LANG_CLASSES = {
    "Object", "String", "Exception", "RuntimeException",
    "Throwable", "Error", "Class", "Number", "Integer",
    "Long", "Double", "Float", "Boolean", "Character",
    "Byte", "Short", "Void", "Math", "System",
    "Thread", "Runnable", "StringBuilder", "StringBuffer",
}


class JavaParser(BaseLanguageParser):
    """Java language parser.

    Extracts symbols, imports, calls, and inheritances from Java source code.
    Supports Java classes, interfaces, enums, records, methods, fields, constructors,
    annotations, and generics.
    """

    def extract_symbols(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract symbols (classes, interfaces, methods, fields) from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Symbol objects
        """
        symbols = []
        namespace = ""
        import_map = {}
        inheritances = []

        root = tree.root_node

        # First pass: Extract package and imports
        for child in root.children:
            if child.type == "package_declaration":
                namespace = self._parse_java_package(child, source_bytes)
            elif child.type == "import_declaration":
                import_map = self._build_java_import_map(root, source_bytes)
                break  # Import map built, no need to continue

        # Second pass: Extract type declarations
        for child in root.children:
            if child.type == "class_declaration":
                class_symbols = self._parse_java_class(
                    child, source_bytes, namespace, import_map, inheritances
                )
                symbols.extend(class_symbols)
            elif child.type == "interface_declaration":
                interface_symbols = self._parse_java_interface(
                    child, source_bytes, namespace, import_map, inheritances
                )
                symbols.extend(interface_symbols)
            elif child.type == "enum_declaration":
                enum_symbols = self._parse_java_enum(child, source_bytes)
                symbols.extend(enum_symbols)
            elif child.type == "record_declaration":
                record_symbols = self._parse_java_record(child, source_bytes)
                symbols.extend(record_symbols)

        return symbols

    def extract_imports(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract import statements from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Import objects
        """
        imports = []
        root = tree.root_node

        for child in root.children:
            if child.type == "import_declaration":
                java_import = self._parse_java_import(child, source_bytes)
                if java_import:
                    imports.append(java_import)

        return imports

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
        # Extract namespace and import map
        namespace = ""
        import_map = {}
        inheritances = []

        root = tree.root_node

        for child in root.children:
            if child.type == "package_declaration":
                namespace = self._parse_java_package(child, source_bytes)
            elif child.type == "import_declaration":
                import_map = self._build_java_import_map(root, source_bytes)
                break

        # Extract inheritances for parent resolution
        for child in root.children:
            if child.type in ("class_declaration", "interface_declaration"):
                # This will populate inheritances list
                if child.type == "class_declaration":
                    self._parse_java_class(child, source_bytes, namespace, import_map, inheritances)
                else:
                    self._parse_java_interface(child, source_bytes, namespace, import_map, inheritances)

        # Extract calls
        return self._extract_java_calls_from_tree(
            tree, source_bytes, imports, inheritances, namespace, import_map
        )

    def extract_inheritances(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract class inheritance relationships from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Inheritance objects
        """
        inheritances = []
        namespace = ""
        import_map = {}

        root = tree.root_node

        # First pass: Extract package and imports
        for child in root.children:
            if child.type == "package_declaration":
                namespace = self._parse_java_package(child, source_bytes)
            elif child.type == "import_declaration":
                import_map = self._build_java_import_map(root, source_bytes)
                break

        # Second pass: Extract inheritances from type declarations
        for child in root.children:
            if child.type == "class_declaration":
                self._parse_java_class(child, source_bytes, namespace, import_map, inheritances)
            elif child.type == "interface_declaration":
                self._parse_java_interface(child, source_bytes, namespace, import_map, inheritances)

        return inheritances

    def parse(self, path):
        """Parse a Java source file.

        Overrides BaseLanguageParser.parse() to add module_docstring extraction.

        Args:
            path: Path to the source file

        Returns:
            ParseResult containing symbols, imports, calls, inheritances, and module_docstring
        """
        from pathlib import Path

        from ..parser import ParseResult

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

        # Extract all information
        try:
            symbols = self.extract_symbols(tree, source_bytes)
            imports = self.extract_imports(tree, source_bytes)
            inheritances = self.extract_inheritances(tree, source_bytes)
            calls = self.extract_calls(tree, source_bytes, symbols, imports)

            # Extract module docstring (Java)
            module_docstring = self._extract_java_module_docstring(tree, source_bytes)

            # Extract package namespace
            namespace = ""
            root = tree.root_node
            for child in root.children:
                if child.type == "package_declaration":
                    namespace = self._parse_java_package(child, source_bytes)
                    break

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

    # ==================== Private Helper Methods ====================

    def _strip_generic_type(self, type_name: str) -> str:
        """Strip generic type parameters from a type name."""
        return type_name.split('<')[0].strip()

    def _extract_package_namespace(self, class_full_name: str) -> str:
        """Extract package namespace from a full class name."""
        if not class_full_name or "." not in class_full_name:
            return ""

        parts = class_full_name.split(".")

        for i, part in enumerate(parts):
            if part and part[0].isupper():
                if i == 0:
                    return ""
                return ".".join(parts[:i])

        return class_full_name

    def _resolve_java_type(
        self,
        short_name: str,
        namespace: str,
        import_map: dict[str, str]
    ) -> str:
        """Resolve a short type name to its full qualified name."""
        if "." in short_name:
            return short_name

        if short_name in JAVA_LANG_CLASSES:
            return f"java.lang.{short_name}"

        if short_name in import_map:
            return import_map[short_name]

        if namespace:
            return f"{namespace}.{short_name}"

        return short_name

    def _build_java_import_map(self, root: Node, source_bytes: bytes) -> dict[str, str]:
        """Build a mapping of short class names to full qualified names from imports."""
        import_map = {}

        for child in root.children:
            if child.type == "import_declaration":
                for import_child in child.children:
                    if import_child.type == "scoped_identifier":
                        full_name = get_node_text(import_child, source_bytes)
                        short_name = full_name.split('.')[-1]
                        import_map[short_name] = full_name
                    elif import_child.type == "identifier":
                        short_name = get_node_text(import_child, source_bytes)
                        import_map[short_name] = short_name

        return import_map

    def _extract_java_modifiers(self, node: Node, source_bytes: bytes) -> list[str]:
        """Extract modifiers from a Java node."""
        modifiers = []
        for child in node.children:
            if child.type == "modifiers":
                for mod_child in child.children:
                    modifiers.append(get_node_text(mod_child, source_bytes))
        return modifiers

    def _build_java_signature(self, modifiers: list[str], *parts: str) -> str:
        """Build a Java signature string from modifiers and parts."""
        signature_parts = []

        if modifiers:
            signature_parts.append(" ".join(modifiers))

        signature_parts.extend(parts)

        return " ".join(signature_parts)

    def _extract_java_annotations(self, node: Node, source_bytes: bytes) -> list[Annotation]:
        """Extract annotations from a Java node."""
        annotations = []

        for child in node.children:
            if child.type == "modifiers":
                for mod_child in child.children:
                    if mod_child.type == "marker_annotation":
                        name = ""
                        for name_child in mod_child.children:
                            if name_child.type in ("identifier", "scoped_identifier"):
                                name = get_node_text(name_child, source_bytes)
                        if name:
                            annotations.append(Annotation(name=name, arguments={}))

                    elif mod_child.type == "annotation":
                        name = ""
                        arguments = {}

                        for ann_child in mod_child.children:
                            if ann_child.type in ("identifier", "scoped_identifier"):
                                name = get_node_text(ann_child, source_bytes)
                            elif ann_child.type == "annotation_argument_list":
                                arguments = self._parse_annotation_arguments(ann_child, source_bytes)

                        if name:
                            annotations.append(Annotation(name=name, arguments=arguments))

        return annotations

    def _parse_annotation_arguments(self, arg_list_node: Node, source_bytes: bytes) -> dict[str, str]:
        """Parse annotation arguments into a dictionary."""
        arguments = {}

        for child in arg_list_node.children:
            if child.type == "element_value_pair":
                key = ""
                value = ""
                for pair_child in child.children:
                    if pair_child.type == "identifier":
                        key = get_node_text(pair_child, source_bytes)
                    elif pair_child.type == "string_literal":
                        value = get_node_text(pair_child, source_bytes).strip('"')
                    elif pair_child.type in ("decimal_integer_literal", "true", "false"):
                        value = get_node_text(pair_child, source_bytes)
                    elif pair_child.type == "element_value_array_initializer":
                        value = get_node_text(pair_child, source_bytes)

                if key and value:
                    arguments[key] = value

            elif child.type == "string_literal":
                value = get_node_text(child, source_bytes).strip('"')
                arguments["value"] = value
            elif child.type == "decimal_integer_literal":
                value = get_node_text(child, source_bytes)
                arguments["value"] = value

        return arguments

    def _find_child_by_type(self, node: Node, type_name: str) -> Node | None:
        """Find first child node of a specific type."""
        for child in node.children:
            if child.type == type_name:
                return child
        return None

    def _extract_java_docstring(self, node: Node, source_bytes: bytes) -> str:
        """Extract JavaDoc comment from a node."""
        if (hasattr(node, 'prev_sibling') and node.prev_sibling and
                node.prev_sibling.type == "block_comment"):
            comment_text = get_node_text(node.prev_sibling, source_bytes)
            if comment_text.startswith("/**"):
                return comment_text[3:-2].strip()

        for child in node.children:
            if child.type == "block_comment":
                comment_text = get_node_text(child, source_bytes)
                if comment_text.startswith("/**"):
                    return comment_text[3:-2].strip()

        return ""

    def _parse_java_method(self, node: Node, source_bytes: bytes, class_name: str = "") -> Symbol:
        """Parse a Java method declaration."""
        name = ""
        params = ""
        return_type = ""
        type_params = ""
        throws_clause = ""

        modifiers = self._extract_java_modifiers(node, source_bytes)
        annotations = self._extract_java_annotations(node, source_bytes)

        for child in node.children:
            if child.type == "identifier":
                name = get_node_text(child, source_bytes)
            elif child.type == "formal_parameters":
                params = get_node_text(child, source_bytes)
            elif child.type == "type_identifier" or child.type == "void_type":
                return_type = get_node_text(child, source_bytes)
            elif child.type in ("generic_type", "array_type", "scoped_type_identifier"):
                return_type = get_node_text(child, source_bytes)
            elif child.type == "type_parameters":
                type_params = get_node_text(child, source_bytes)
            elif child.type == "throws":
                throws_clause = get_node_text(child, source_bytes)

        return_str = return_type if return_type else "void"
        full_name = f"{class_name}.{name}" if class_name else name
        method_decl = f"{type_params} {return_str}" if type_params else return_str
        signature = self._build_java_signature(modifiers, method_decl, f"{name}{params}")
        if throws_clause:
            signature += f" {throws_clause}"

        docstring = self._extract_java_docstring(node, source_bytes)

        return Symbol(
            name=full_name,
            kind="method" if class_name else "function",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            annotations=annotations,
        )

    def _parse_java_constructor(self, node: Node, source_bytes: bytes, class_name: str) -> Symbol:
        """Parse a Java constructor declaration."""
        name = ""
        params = ""
        throws_clause = ""

        modifiers = self._extract_java_modifiers(node, source_bytes)
        annotations = self._extract_java_annotations(node, source_bytes)

        for child in node.children:
            if child.type == "identifier":
                name = get_node_text(child, source_bytes)
            elif child.type == "formal_parameters":
                params = get_node_text(child, source_bytes)
            elif child.type == "throws":
                throws_clause = get_node_text(child, source_bytes)

        full_name = f"{class_name}.{name}"
        signature = self._build_java_signature(modifiers, f"{name}{params}")
        if throws_clause:
            signature += f" {throws_clause}"

        docstring = self._extract_java_docstring(node, source_bytes)

        return Symbol(
            name=full_name,
            kind="constructor",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            annotations=annotations,
        )

    def _parse_java_field(self, node: Node, source_bytes: bytes, class_name: str = "") -> list[Symbol]:
        """Parse a Java field declaration."""
        type_name = ""
        field_names = []

        modifiers = self._extract_java_modifiers(node, source_bytes)
        annotations = self._extract_java_annotations(node, source_bytes)

        for child in node.children:
            if child.type in ("type_identifier", "generic_type", "array_type",
                              "integral_type", "floating_point_type", "boolean_type"):
                type_name = get_node_text(child, source_bytes)
            elif child.type == "variable_declarator":
                for var_child in child.children:
                    if var_child.type == "identifier":
                        field_names.append(get_node_text(var_child, source_bytes))

        symbols = []
        for field_name in field_names:
            full_name = f"{class_name}.{field_name}" if class_name else field_name
            signature = self._build_java_signature(modifiers, type_name, field_name)

            symbols.append(Symbol(
                name=full_name,
                kind="field",
                signature=signature,
                docstring="",
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
                annotations=annotations,
            ))

        return symbols

    def _extract_java_inheritances(
        self,
        node: Node,
        source_bytes: bytes,
        child_name: str,
        package_namespace: str,
        import_map: dict[str, str]
    ) -> list[Inheritance]:
        """Extract inheritance relationships from a Java class or interface declaration."""
        inheritances = []

        superclass_node = node.child_by_field_name("superclass")
        if superclass_node:
            parent_name = self._extract_type_from_node(superclass_node, source_bytes)
            if parent_name:
                parent_name = self._strip_generic_type(parent_name)
                parent_full = self._resolve_java_type(parent_name, package_namespace, import_map)
                inheritances.append(Inheritance(child=child_name, parent=parent_full))

        for child in node.children:
            if child.type == "super_interfaces":
                type_list = None
                for subchild in child.children:
                    if subchild.type == "type_list":
                        type_list = subchild
                        break

                if type_list:
                    for type_node in type_list.children:
                        if type_node.type in (
                            "type_identifier",
                            "generic_type",
                            "scoped_type_identifier"
                        ):
                            interface_name = self._extract_type_from_node(type_node, source_bytes)
                            if interface_name:
                                interface_name = self._strip_generic_type(interface_name)
                                interface_full = self._resolve_java_type(
                                    interface_name, package_namespace, import_map
                                )
                                inheritances.append(
                                    Inheritance(child=child_name, parent=interface_full)
                                )

            elif child.type == "extends_interfaces":
                type_list = None
                for subchild in child.children:
                    if subchild.type == "type_list":
                        type_list = subchild
                        break

                if type_list:
                    for type_node in type_list.children:
                        if type_node.type in (
                            "type_identifier",
                            "generic_type",
                            "scoped_type_identifier"
                        ):
                            extended_interface = self._extract_type_from_node(type_node, source_bytes)
                            if extended_interface:
                                extended_interface = self._strip_generic_type(extended_interface)
                                extended_full = self._resolve_java_type(
                                    extended_interface, package_namespace, import_map
                                )
                                inheritances.append(
                                    Inheritance(child=child_name, parent=extended_full)
                                )

        return inheritances

    def _extract_type_from_node(self, node: Node, source_bytes: bytes) -> str:
        """Extract type name from a tree-sitter node."""
        if node.type == "type_identifier":
            return get_node_text(node, source_bytes)
        elif node.type == "generic_type":
            return get_node_text(node, source_bytes)
        elif node.type == "scoped_type_identifier":
            return get_node_text(node, source_bytes)

        for child in node.children:
            if child.type in ("type_identifier", "generic_type", "scoped_type_identifier"):
                return self._extract_type_from_node(child, source_bytes)

        return ""

    def _parse_java_class(
        self,
        node: Node,
        source_bytes: bytes,
        namespace: str = "",
        import_map: dict[str, str] | None = None,
        inheritances: list[Inheritance] | None = None
    ) -> list[Symbol]:
        """Parse a Java class declaration."""
        symbols = []
        class_name = ""
        type_params = ""
        superclass = ""
        interfaces = []

        if import_map is None:
            import_map = {}
        if inheritances is None:
            inheritances = []

        modifiers = self._extract_java_modifiers(node, source_bytes)
        annotations = self._extract_java_annotations(node, source_bytes)

        for child in node.children:
            if child.type == "identifier":
                class_name = get_node_text(child, source_bytes)
            elif child.type == "type_parameters":
                type_params = get_node_text(child, source_bytes)
            elif child.type == "superclass":
                for super_child in child.children:
                    if super_child.type == "type_identifier":
                        superclass = get_node_text(super_child, source_bytes)
            elif child.type == "super_interfaces":
                for interface_child in child.children:
                    if interface_child.type == "type_list":
                        for type_child in interface_child.children:
                            if type_child.type == "type_identifier":
                                interfaces.append(get_node_text(type_child, source_bytes))

        if class_name:
            full_class_name = f"{namespace}.{class_name}" if namespace else class_name
            package_namespace = self._extract_package_namespace(full_class_name)
            class_inheritances = self._extract_java_inheritances(
                node, source_bytes, full_class_name, package_namespace, import_map
            )
            inheritances.extend(class_inheritances)

        class_decl = class_name + type_params if type_params else class_name
        signature_parts = ["class", class_decl]
        if superclass:
            signature_parts.append(f"extends {superclass}")
        if interfaces:
            signature_parts.append(f"implements {', '.join(interfaces)}")

        signature = self._build_java_signature(modifiers, *signature_parts)
        docstring = self._extract_java_docstring(node, source_bytes)

        symbols.append(Symbol(
            name=class_name,
            kind="class",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            annotations=annotations,
        ))

        for child in node.children:
            if child.type == "class_body":
                for body_child in child.children:
                    if body_child.type == "method_declaration":
                        method = self._parse_java_method(body_child, source_bytes, class_name)
                        symbols.append(method)
                    elif body_child.type == "constructor_declaration":
                        constructor = self._parse_java_constructor(body_child, source_bytes, class_name)
                        symbols.append(constructor)
                    elif body_child.type == "field_declaration":
                        fields = self._parse_java_field(body_child, source_bytes, class_name)
                        symbols.extend(fields)
                    elif body_child.type == "class_declaration":
                        nested_namespace = f"{namespace}.{class_name}" if namespace else class_name
                        nested_symbols = self._parse_java_class(
                            body_child, source_bytes, nested_namespace, import_map, inheritances
                        )
                        symbols.extend(nested_symbols)

        return symbols

    def _parse_java_interface(
        self,
        node: Node,
        source_bytes: bytes,
        namespace: str = "",
        import_map: dict[str, str] | None = None,
        inheritances: list[Inheritance] | None = None
    ) -> list[Symbol]:
        """Parse a Java interface declaration."""
        symbols = []
        interface_name = ""
        type_params = ""
        extends = []

        if import_map is None:
            import_map = {}
        if inheritances is None:
            inheritances = []

        modifiers = self._extract_java_modifiers(node, source_bytes)
        annotations = self._extract_java_annotations(node, source_bytes)

        for child in node.children:
            if child.type == "identifier":
                interface_name = get_node_text(child, source_bytes)
            elif child.type == "type_parameters":
                type_params = get_node_text(child, source_bytes)
            elif child.type == "extends_interfaces":
                for ext_child in child.children:
                    if ext_child.type == "type_list":
                        for type_child in ext_child.children:
                            if type_child.type in (
                                "type_identifier",
                                "generic_type",
                                "scoped_type_identifier",
                            ):
                                extends.append(get_node_text(type_child, source_bytes))

        interface_decl = interface_name + type_params if type_params else interface_name
        signature_parts = ["interface", interface_decl]
        if extends:
            signature_parts.append(f"extends {', '.join(extends)}")

        signature = self._build_java_signature(modifiers, *signature_parts)
        docstring = self._extract_java_docstring(node, source_bytes)

        symbols.append(Symbol(
            name=interface_name,
            kind="interface",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            annotations=annotations,
        ))

        if interface_name:
            full_interface_name = f"{namespace}.{interface_name}" if namespace else interface_name
            package_namespace = self._extract_package_namespace(full_interface_name)
            interface_inheritances = self._extract_java_inheritances(
                node, source_bytes, full_interface_name, package_namespace, import_map
            )
            inheritances.extend(interface_inheritances)

        for child in node.children:
            if child.type == "interface_body":
                for body_child in child.children:
                    if body_child.type == "method_declaration":
                        method = self._parse_java_method(body_child, source_bytes, interface_name)
                        symbols.append(method)

        return symbols

    def _parse_java_enum(self, node: Node, source_bytes: bytes) -> list[Symbol]:
        """Parse a Java enum declaration."""
        symbols = []
        enum_name = ""

        modifiers = self._extract_java_modifiers(node, source_bytes)
        annotations = self._extract_java_annotations(node, source_bytes)

        for child in node.children:
            if child.type == "identifier":
                enum_name = get_node_text(child, source_bytes)

        signature = self._build_java_signature(modifiers, "enum", enum_name)
        docstring = self._extract_java_docstring(node, source_bytes)

        symbols.append(Symbol(
            name=enum_name,
            kind="enum",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            annotations=annotations,
        ))

        for child in node.children:
            if child.type == "enum_body":
                for body_child in child.children:
                    if body_child.type == "method_declaration":
                        method = self._parse_java_method(body_child, source_bytes, enum_name)
                        symbols.append(method)
                    elif body_child.type == "constructor_declaration":
                        constructor = self._parse_java_constructor(body_child, source_bytes, enum_name)
                        symbols.append(constructor)

        return symbols

    def _parse_java_record(self, node: Node, source_bytes: bytes) -> list[Symbol]:
        """Parse a Java record declaration (Java 14+)."""
        symbols = []
        record_name = ""
        type_params = ""
        params = ""

        modifiers = self._extract_java_modifiers(node, source_bytes)
        annotations = self._extract_java_annotations(node, source_bytes)

        for child in node.children:
            if child.type == "identifier":
                record_name = get_node_text(child, source_bytes)
            elif child.type == "type_parameters":
                type_params = get_node_text(child, source_bytes)
            elif child.type == "formal_parameters":
                params = get_node_text(child, source_bytes)

        name_part = record_name + type_params if type_params else record_name
        signature = self._build_java_signature(modifiers, "record", f"{name_part}{params}")
        docstring = self._extract_java_docstring(node, source_bytes)

        symbols.append(Symbol(
            name=record_name,
            kind="record",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            annotations=annotations,
        ))

        for child in node.children:
            if child.type == "class_body":
                for body_child in child.children:
                    if body_child.type == "method_declaration":
                        method = self._parse_java_method(body_child, source_bytes, record_name)
                        symbols.append(method)

        return symbols

    def _parse_java_import(self, node: Node, source_bytes: bytes) -> Import | None:
        """Parse a Java import statement."""
        module = ""
        is_static = False
        is_wildcard = False

        for child in node.children:
            if child.type == "scoped_identifier" or child.type == "identifier":
                module = get_node_text(child, source_bytes)
            elif child.type == "asterisk":
                is_wildcard = True
            elif child.type == "static":
                is_static = True

        if module:
            if is_wildcard:
                module = module + ".*"

            return Import(
                module=module,
                names=[],
                is_from=is_static,
            )

        return None

    def _extract_java_module_docstring(self, tree, source_bytes: bytes) -> str:
        """Extract module-level JavaDoc comment."""
        root = tree.root_node

        for child in root.children:
            if child.type == "block_comment":
                comment_text = get_node_text(child, source_bytes)
                if comment_text.startswith("/**"):
                    return comment_text[3:-2].strip()
            elif child.type in ("class_declaration", "interface_declaration",
                               "enum_declaration", "record_declaration"):
                return self._extract_java_docstring(child, source_bytes)

        return ""

    def _parse_java_package(self, node: Node, source_bytes: bytes) -> str:
        """Extract Java package declaration."""
        for child in node.children:
            if child.type == "scoped_identifier" or child.type == "identifier":
                return get_node_text(child, source_bytes)
        return ""

    # ==================== Call Extraction Methods ====================

    def _build_java_static_import_map(self, root: Node, source_bytes: bytes) -> dict[str, str]:
        """Build mapping of statically imported method names to full qualified names."""
        static_import_map = {}

        for child in root.children:
            if child.type == "import_declaration":
                is_static = False
                import_path = ""
                has_wildcard = False

                for import_child in child.children:
                    if import_child.type == "static":
                        is_static = True
                    elif import_child.type == "scoped_identifier":
                        import_path = get_node_text(import_child, source_bytes)
                    elif import_child.type in ("asterisk", "asterisk_import"):
                        has_wildcard = True

                if is_static and import_path and has_wildcard:
                    static_import_map[f"_wildcard_{import_path}"] = import_path

                elif is_static and import_path and "." in import_path:
                    method_name = import_path.split(".")[-1]
                    if method_name not in static_import_map:
                        static_import_map[method_name] = import_path

        return static_import_map

    def _resolve_java_static_import(
        self,
        method_name: str,
        static_import_map: dict[str, str]
    ) -> str | None:
        """Resolve statically imported method name to full qualified name."""
        if method_name in static_import_map:
            return static_import_map[method_name]

        for key, package in static_import_map.items():
            if key.startswith("_wildcard_"):
                return f"{package}.{method_name}"

        return None

    def _parse_java_method_call(
        self,
        node: Node,
        source_bytes: bytes,
        caller: str,
        import_map: dict[str, str],
        static_import_map: dict[str, str],
        namespace: str,
        parent_map: dict[str, str]
    ) -> Optional[Call]:
        """Parse a Java method invocation node."""
        def extract_field_identifiers(field_node):
            ids = []
            for child in field_node.children:
                if child.type == "identifier":
                    ids.append(get_node_text(child, source_bytes))
                elif child.type == "field_access":
                    ids.extend(extract_field_identifiers(child))
            return ids

        identifiers = []
        has_super = False
        object_expr = None

        for child in node.children:
            if child.type == "identifier":
                identifiers.append(get_node_text(child, source_bytes))
            elif child.type == "super":
                has_super = True
            elif child.type == "field_access":
                identifiers.extend(extract_field_identifiers(child))
            elif child.type == "method_invocation":
                object_expr = child

        if not identifiers and not object_expr:
            return None

        callee_raw = ""
        skip_resolution = False

        if has_super and identifiers:
            method_name = identifiers[-1]
            if "." in caller:
                class_name = caller.rsplit(".", 1)[0]
                if class_name in parent_map:
                    parent_class = parent_map[class_name]
                    callee_raw = f"{parent_class}.{method_name}"
                    skip_resolution = True
            if not callee_raw:
                callee_raw = f"{namespace}.Parent.{method_name}"
                skip_resolution = True

        elif object_expr and identifiers:
            def get_chain_object(n):
                for c in n.children:
                    if c.type == "identifier":
                        return get_node_text(c, source_bytes)
                    elif c.type == "method_invocation":
                        return get_chain_object(c)
                return None

            base_obj = get_chain_object(object_expr)
            if base_obj and identifiers:
                method_name = identifiers[-1]
                callee_raw = f"{base_obj}.{method_name}"
            elif identifiers:
                callee_raw = identifiers[-1]

        elif len(identifiers) == 1:
            callee_raw = identifiers[0]

        elif len(identifiers) >= 2:
            callee_raw = ".".join(identifiers)

        if not callee_raw:
            return None

        if skip_resolution:
            callee = callee_raw
        else:
            callee = callee_raw

            if "." not in callee_raw:
                static_resolved = self._resolve_java_static_import(callee_raw, static_import_map)
                if static_resolved:
                    callee = static_resolved
                else:
                    callee = f"{namespace}.{callee_raw}"

            elif "." in callee_raw:
                parts = callee_raw.split(".")

                if len(parts) >= 3 and parts[0][0].islower():
                    callee = callee_raw
                else:
                    class_part = parts[0]
                    method_part = ".".join(parts[1:])

                    if class_part in import_map:
                        full_class = import_map[class_part]
                        callee = f"{full_class}.{method_part}"
                    elif class_part[0].isupper():
                        callee = f"{namespace}.{callee_raw}"
                    else:
                        capitalized = class_part.capitalize()
                        if capitalized in import_map:
                            full_class = import_map[capitalized]
                            callee = f"{full_class}.{method_part}"
                        else:
                            callee = f"{namespace}.{capitalized}.{method_part}"

        if "." in callee_raw:
            first_part = callee_raw.split(".")[0]
            if first_part[0].isupper() or first_part == "super":
                call_type = CallType.STATIC_METHOD
            else:
                call_type = CallType.METHOD
        else:
            call_type = CallType.FUNCTION

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
        self,
        node: Node,
        source_bytes: bytes,
        caller: str,
        import_map: dict[str, str],
        namespace: str
    ) -> Optional[Call]:
        """Parse a Java object creation expression (constructor call)."""
        type_name = ""

        for child in node.children:
            if child.type == "type_identifier":
                type_name = get_node_text(child, source_bytes)
            elif child.type == "generic_type":
                for generic_child in child.children:
                    if generic_child.type == "type_identifier":
                        type_name = get_node_text(generic_child, source_bytes)
                        break
            elif child.type == "scoped_type_identifier":
                type_name = get_node_text(child, source_bytes)

        if not type_name:
            return None

        if "." in type_name:
            full_type = type_name
        elif type_name in import_map:
            full_type = import_map[type_name]
        else:
            full_type = f"{namespace}.{type_name}"

        callee = f"{full_type}.<init>"

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
        self,
        node: Node,
        source_bytes: bytes,
        caller: str,
        import_map: dict[str, str],
        static_import_map: dict[str, str],
        namespace: str,
        parent_map: dict[str, str]
    ) -> list[Call]:
        """Recursively extract Java calls from AST node."""
        calls = []

        if node.type == "method_invocation":
            call = self._parse_java_method_call(
                node, source_bytes, caller, import_map,
                static_import_map, namespace, parent_map
            )
            if call:
                calls.append(call)

        elif node.type == "object_creation_expression":
            call = self._parse_java_constructor_call(
                node, source_bytes, caller, import_map, namespace
            )
            if call:
                calls.append(call)

        for child in node.children:
            calls.extend(
                self._extract_java_calls(
                    child, source_bytes, caller, import_map,
                    static_import_map, namespace, parent_map
                )
            )

        return calls

    def _extract_java_calls_from_tree(
        self,
        tree,
        source_bytes: bytes,
        imports: list[Import],
        inheritances: list[Inheritance],
        namespace: str,
        import_map: dict[str, str]
    ) -> list[Call]:
        """Extract all Java call relationships from parse tree."""
        root = tree.root_node
        static_import_map = self._build_java_static_import_map(root, source_bytes)

        parent_map = {}
        for inh in inheritances:
            parent_map[inh.child] = inh.parent

        calls = []

        for child in root.children:
            if child.type in ("class_declaration", "interface_declaration"):
                class_name = ""
                for node in child.children:
                    if node.type == "identifier":
                        class_name = get_node_text(node, source_bytes)
                        break

                if not class_name:
                    continue

                full_class_name = f"{namespace}.{class_name}" if namespace else class_name

                body_node = None
                for node in child.children:
                    if node.type in ("class_body", "interface_body"):
                        body_node = node
                        break

                if not body_node:
                    continue

                for method_node in body_node.children:
                    if method_node.type == "method_declaration":
                        method_name = ""
                        for node in method_node.children:
                            if node.type == "identifier":
                                method_name = get_node_text(node, source_bytes)
                                break

                        if method_name:
                            caller = f"{full_class_name}.{method_name}"
                            calls.extend(
                                self._extract_java_calls(
                                    method_node, source_bytes, caller,
                                    import_map, static_import_map, namespace, parent_map
                                )
                            )

                    elif method_node.type == "constructor_declaration":
                        caller = f"{full_class_name}.<init>"
                        calls.extend(
                            self._extract_java_calls(
                                method_node, source_bytes, caller,
                                import_map, static_import_map, namespace, parent_map
                            )
                        )

        return calls


# ==================== Backward Compatibility Functions ====================

def is_java_file(path: str) -> bool:
    """Check if file is a Java source file."""
    return path.endswith('.java')


def get_java_parser():
    """Get the Java parser instance (lazy loading)."""
    from ..parser import _get_parser
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
    from pathlib import Path

    from ..parser import parse_file

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
