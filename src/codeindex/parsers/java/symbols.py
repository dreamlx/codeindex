"""Symbol extraction for Java parser.

This module provides functions to extract symbols (classes, interfaces, enums,
records, methods, fields, constructors) from Java source code using tree-sitter.
"""

from typing import Optional

from tree_sitter import Node, Tree

from ...parser import Annotation, Inheritance, Symbol
from ..utils import get_node_text

# Java standard library classes (java.lang.* implicit imports)
JAVA_LANG_CLASSES = {
    "Object", "String", "Exception", "RuntimeException",
    "Throwable", "Error", "Class", "Number", "Integer",
    "Long", "Double", "Float", "Boolean", "Character",
    "Byte", "Short", "Void", "Math", "System",
    "Thread", "Runnable", "StringBuilder", "StringBuffer",
}


def extract_symbols(
    tree: Tree,
    source_bytes: bytes,
    namespace: str = "",
    import_map: Optional[dict[str, str]] = None,
    inheritances: Optional[list[Inheritance]] = None
) -> list[Symbol]:
    """Extract symbols (classes, interfaces, methods, fields) from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes
        namespace: Package namespace (optional)
        import_map: Mapping of short class names to full qualified names
        inheritances: List to collect inheritance relationships

    Returns:
        List of Symbol objects
    """
    symbols = []
    root = tree.root_node

    if import_map is None:
        import_map = {}
    if inheritances is None:
        inheritances = []

    # Extract type declarations
    for child in root.children:
        if child.type == "class_declaration":
            class_symbols = _parse_java_class(
                child, source_bytes, namespace, import_map, inheritances
            )
            symbols.extend(class_symbols)
        elif child.type == "interface_declaration":
            interface_symbols = _parse_java_interface(
                child, source_bytes, namespace, import_map, inheritances
            )
            symbols.extend(interface_symbols)
        elif child.type == "enum_declaration":
            enum_symbols = _parse_java_enum(child, source_bytes)
            symbols.extend(enum_symbols)
        elif child.type == "record_declaration":
            record_symbols = _parse_java_record(child, source_bytes)
            symbols.extend(record_symbols)

    return symbols


def extract_module_docstring(tree: Tree, source_bytes: bytes) -> str:
    """Extract module-level JavaDoc comment.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        Module docstring or empty string
    """
    root = tree.root_node

    for child in root.children:
        if child.type == "block_comment":
            comment_text = get_node_text(child, source_bytes)
            if comment_text.startswith("/**"):
                return comment_text[3:-2].strip()
        elif child.type in ("class_declaration", "interface_declaration",
                           "enum_declaration", "record_declaration"):
            return _extract_java_docstring(child, source_bytes)

    return ""


# ==================== Private Helper Functions ====================


def _strip_generic_type(type_name: str) -> str:
    """Strip generic type parameters from a type name."""
    return type_name.split('<')[0].strip()


def _extract_package_namespace(class_full_name: str) -> str:
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


def _extract_java_modifiers(node: Node, source_bytes: bytes) -> list[str]:
    """Extract modifiers from a Java node."""
    modifiers = []
    for child in node.children:
        if child.type == "modifiers":
            for mod_child in child.children:
                modifiers.append(get_node_text(mod_child, source_bytes))
    return modifiers


def _build_java_signature(modifiers: list[str], *parts: str) -> str:
    """Build a Java signature string from modifiers and parts."""
    signature_parts = []

    if modifiers:
        signature_parts.append(" ".join(modifiers))

    signature_parts.extend(parts)

    return " ".join(signature_parts)


def _extract_java_annotations(node: Node, source_bytes: bytes) -> list[Annotation]:
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
                            arguments = _parse_annotation_arguments(ann_child, source_bytes)

                    if name:
                        annotations.append(Annotation(name=name, arguments=arguments))

    return annotations


def _parse_annotation_arguments(arg_list_node: Node, source_bytes: bytes) -> dict[str, str]:
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


def _find_child_by_type(node: Node, type_name: str) -> Node | None:
    """Find first child node of a specific type."""
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _extract_java_docstring(node: Node, source_bytes: bytes) -> str:
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


def _parse_java_method(node: Node, source_bytes: bytes, class_name: str = "") -> Symbol:
    """Parse a Java method declaration."""
    name = ""
    params = ""
    return_type = ""
    type_params = ""
    throws_clause = ""

    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)

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
    signature = _build_java_signature(modifiers, method_decl, f"{name}{params}")
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
        annotations=annotations,
    )


def _parse_java_constructor(node: Node, source_bytes: bytes, class_name: str) -> Symbol:
    """Parse a Java constructor declaration."""
    name = ""
    params = ""
    throws_clause = ""

    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)

    for child in node.children:
        if child.type == "identifier":
            name = get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = get_node_text(child, source_bytes)
        elif child.type == "throws":
            throws_clause = get_node_text(child, source_bytes)

    full_name = f"{class_name}.{name}"
    signature = _build_java_signature(modifiers, f"{name}{params}")
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
        annotations=annotations,
    )


def _parse_java_field(node: Node, source_bytes: bytes, class_name: str = "") -> list[Symbol]:
    """Parse a Java field declaration."""
    type_name = ""
    field_names = []

    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)

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
        signature = _build_java_signature(modifiers, type_name, field_name)

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
        parent_name = _extract_type_from_node(superclass_node, source_bytes)
        if parent_name:
            parent_name = _strip_generic_type(parent_name)
            parent_full = _resolve_java_type(parent_name, package_namespace, import_map)
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
                        interface_name = _extract_type_from_node(type_node, source_bytes)
                        if interface_name:
                            interface_name = _strip_generic_type(interface_name)
                            interface_full = _resolve_java_type(
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
                        extended_interface = _extract_type_from_node(type_node, source_bytes)
                        if extended_interface:
                            extended_interface = _strip_generic_type(extended_interface)
                            extended_full = _resolve_java_type(
                                extended_interface, package_namespace, import_map
                            )
                            inheritances.append(
                                Inheritance(child=child_name, parent=extended_full)
                            )

    return inheritances


def _extract_type_from_node(node: Node, source_bytes: bytes) -> str:
    """Extract type name from a tree-sitter node."""
    if node.type == "type_identifier":
        return get_node_text(node, source_bytes)
    elif node.type == "generic_type":
        return get_node_text(node, source_bytes)
    elif node.type == "scoped_type_identifier":
        return get_node_text(node, source_bytes)

    for child in node.children:
        if child.type in ("type_identifier", "generic_type", "scoped_type_identifier"):
            return _extract_type_from_node(child, source_bytes)

    return ""


def _parse_java_class(
    node: Node,
    source_bytes: bytes,
    namespace: str = "",
    import_map: Optional[dict[str, str]] = None,
    inheritances: Optional[list[Inheritance]] = None
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

    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)

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
        package_namespace = _extract_package_namespace(full_class_name)
        class_inheritances = _extract_java_inheritances(
            node, source_bytes, full_class_name, package_namespace, import_map
        )
        inheritances.extend(class_inheritances)

    class_decl = class_name + type_params if type_params else class_name
    signature_parts = ["class", class_decl]
    if superclass:
        signature_parts.append(f"extends {superclass}")
    if interfaces:
        signature_parts.append(f"implements {', '.join(interfaces)}")

    signature = _build_java_signature(modifiers, *signature_parts)
    docstring = _extract_java_docstring(node, source_bytes)

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
                    method = _parse_java_method(body_child, source_bytes, class_name)
                    symbols.append(method)
                elif body_child.type == "constructor_declaration":
                    constructor = _parse_java_constructor(body_child, source_bytes, class_name)
                    symbols.append(constructor)
                elif body_child.type == "field_declaration":
                    fields = _parse_java_field(body_child, source_bytes, class_name)
                    symbols.extend(fields)
                elif body_child.type == "class_declaration":
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
    import_map: Optional[dict[str, str]] = None,
    inheritances: Optional[list[Inheritance]] = None
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

    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)

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

    signature = _build_java_signature(modifiers, *signature_parts)
    docstring = _extract_java_docstring(node, source_bytes)

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
        package_namespace = _extract_package_namespace(full_interface_name)
        interface_inheritances = _extract_java_inheritances(
            node, source_bytes, full_interface_name, package_namespace, import_map
        )
        inheritances.extend(interface_inheritances)

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

    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)

    for child in node.children:
        if child.type == "identifier":
            enum_name = get_node_text(child, source_bytes)

    signature = _build_java_signature(modifiers, "enum", enum_name)
    docstring = _extract_java_docstring(node, source_bytes)

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

    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)

    for child in node.children:
        if child.type == "identifier":
            record_name = get_node_text(child, source_bytes)
        elif child.type == "type_parameters":
            type_params = get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = get_node_text(child, source_bytes)

    name_part = record_name + type_params if type_params else record_name
    signature = _build_java_signature(modifiers, "record", f"{name_part}{params}")
    docstring = _extract_java_docstring(node, source_bytes)

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
                    method = _parse_java_method(body_child, source_bytes, record_name)
                    symbols.append(method)

    return symbols
