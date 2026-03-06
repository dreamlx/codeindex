"""Inheritance extraction for PHP parser.

This module provides functions to extract class inheritance relationships
(extends and implements) from PHP source code using tree-sitter.
"""

from tree_sitter import Tree

from ...parser import Import, Inheritance
from ..utils import get_node_text


def extract_inheritances(tree: Tree, source_bytes: bytes) -> list:
    """Extract class inheritance relationships from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        List of Inheritance objects
    """
    inheritances = []
    namespace = ""
    use_map = {}

    root = tree.root_node

    # First pass: Extract namespace and use statements
    for child in root.children:
        if child.type == "namespace_definition":
            namespace = _parse_namespace(child, source_bytes)
        elif child.type == "namespace_use_declaration":
            php_imports = _parse_use_for_map(child, source_bytes)
            for imp in php_imports:
                if imp.alias:
                    use_map[imp.alias] = imp.module
                else:
                    short_name = imp.module.split("\\")[-1]
                    use_map[short_name] = imp.module

    # Second pass: Extract inheritances from classes
    for child in root.children:
        if child.type == "class_declaration":
            _parse_class_inheritances(child, source_bytes, namespace, use_map, inheritances)

    return inheritances


def _parse_namespace(node, source_bytes: bytes) -> str:
    """Parse PHP namespace definition."""
    for child in node.children:
        if child.type == "namespace_name":
            return get_node_text(child, source_bytes)
    return ""


def _parse_use_for_map(node, source_bytes: bytes) -> list[Import]:
    """Parse PHP use statement for building use_map.

    Returns minimal Import objects needed for name resolution.
    """
    imports = []
    base_namespace = ""

    for child in node.children:
        if child.type == "namespace_name":
            base_namespace = get_node_text(child, source_bytes)

        elif child.type == "namespace_use_clause":
            module = ""
            alias = ""

            for clause_child in child.children:
                if clause_child.type == "qualified_name":
                    module = get_node_text(clause_child, source_bytes)
                elif clause_child.type == "name" and module:
                    alias = get_node_text(clause_child, source_bytes)

            if module:
                if base_namespace:
                    module = f"{base_namespace}\\{module}"
                imports.append(
                    Import(module=module, names=[], is_from=True, alias=alias if alias else None)
                )

        elif child.type == "namespace_use_group":
            for group_child in child.children:
                if group_child.type == "namespace_use_clause":
                    name = ""
                    alias = ""
                    for clause_child in group_child.children:
                        if clause_child.type == "qualified_name":
                            name = get_node_text(clause_child, source_bytes)
                        elif clause_child.type == "name":
                            if not name:
                                name = get_node_text(clause_child, source_bytes)
                            else:
                                alias = get_node_text(clause_child, source_bytes)

                    if name:
                        full_module = f"{base_namespace}\\{name}" if base_namespace else name
                        imports.append(
                            Import(module=full_module, names=[], is_from=True, alias=alias if alias else None)
                        )

    return imports


def _parse_class_inheritances(
    node,
    source_bytes: bytes,
    namespace: str,
    use_map: dict[str, str],
    inheritances: list[Inheritance]
) -> None:
    """Parse class inheritance relationships from class_declaration node.

    Extracts extends and implements relationships and appends them to inheritances list.

    Args:
        node: class_declaration node
        source_bytes: Source code bytes
        namespace: Current namespace
        use_map: Use statement mapping
        inheritances: List to append Inheritance objects to
    """
    class_name = ""
    extends = ""
    implements = []

    for child in node.children:
        if child.type == "name":
            class_name = get_node_text(child, source_bytes)
        elif child.type == "base_clause":
            # extends BaseClass
            for bc_child in child.children:
                if bc_child.type == "name":
                    extends = get_node_text(bc_child, source_bytes)
        elif child.type == "class_interface_clause":
            # implements Interface1, Interface2
            for ic_child in child.children:
                if ic_child.type == "name":
                    implements.append(get_node_text(ic_child, source_bytes))

    # Build full class name with namespace
    full_class_name = f"{namespace}\\{class_name}" if namespace else class_name

    # Create Inheritance objects
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
