"""Call extraction for Java parser.

This module provides functions to extract method calls, constructor calls,
and call relationships from Java source code using tree-sitter.
"""

from typing import Optional

from tree_sitter import Node, Tree

from ...parser import Call, CallType, Import, Inheritance
from ..utils import get_node_text
from .imports import build_import_map, build_static_import_map, resolve_static_import
from .inheritance import extract_inheritances


def extract_calls(
    tree: Tree,
    source_bytes: bytes,
    symbols: list,
    imports: list[Import],
    namespace: str = "",
    import_map: dict[str, str] | None = None
) -> list[Call]:
    """Extract function/method call relationships from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes
        symbols: Previously extracted symbols
        imports: Previously extracted imports
        namespace: Package namespace (optional)
        import_map: Mapping of short class names to full qualified names

    Returns:
        List of Call objects
    """
    root = tree.root_node

    if import_map is None:
        import_map = build_import_map(root, source_bytes)

    # Extract inheritances for parent resolution
    inheritances = extract_inheritances(tree, source_bytes, namespace, import_map)

    # Extract calls
    return _extract_calls_from_tree(
        tree, source_bytes, inheritances, namespace, import_map
    )


# ==================== Private Helper Functions ====================


def _parse_method_call(
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
            static_resolved = resolve_static_import(callee_raw, static_import_map)
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


def _parse_constructor_call(
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


def _extract_calls_recursive(
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
        call = _parse_method_call(
            node, source_bytes, caller, import_map,
            static_import_map, namespace, parent_map
        )
        if call:
            calls.append(call)

    elif node.type == "object_creation_expression":
        call = _parse_constructor_call(
            node, source_bytes, caller, import_map, namespace
        )
        if call:
            calls.append(call)

    for child in node.children:
        calls.extend(
            _extract_calls_recursive(
                child, source_bytes, caller, import_map,
                static_import_map, namespace, parent_map
            )
        )

    return calls


def _extract_calls_from_tree(
    tree: Tree,
    source_bytes: bytes,
    inheritances: list[Inheritance],
    namespace: str,
    import_map: dict[str, str]
) -> list[Call]:
    """Extract all Java call relationships from parse tree."""
    root = tree.root_node
    static_import_map = build_static_import_map(root, source_bytes)

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
                            _extract_calls_recursive(
                                method_node, source_bytes, caller,
                                import_map, static_import_map, namespace, parent_map
                            )
                        )

                elif method_node.type == "constructor_declaration":
                    caller = f"{full_class_name}.<init>"
                    calls.extend(
                        _extract_calls_recursive(
                            method_node, source_bytes, caller,
                            import_map, static_import_map, namespace, parent_map
                        )
                    )

    return calls
