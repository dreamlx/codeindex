"""Call extraction for TypeScript/JavaScript parser.

This module provides functions to extract function and method call relationships
from TypeScript/JavaScript source code using tree-sitter.
"""

from tree_sitter import Node, Tree

from ...parser import Call, CallType
from ..utils import get_node_text


def extract_calls(
    tree: Tree, source_bytes: bytes, symbols: list, imports: list
) -> list:
    """Extract function/method call relationships.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes
        symbols: Previously extracted symbols
        imports: Previously extracted imports

    Returns:
        List of Call objects
    """
    calls = []
    root = tree.root_node

    # Build symbol context for caller resolution
    for child in root.children:
        _extract_calls_from_node(child, source_bytes, "", calls)

    return calls


def _extract_calls_from_node(
    node: Node, source_bytes: bytes, caller: str, calls: list[Call]
):
    """Recursively extract calls from AST nodes.

    Args:
        node: The node to extract from
        source_bytes: The source code as bytes
        caller: Current caller context
        calls: List to accumulate Call objects
    """
    # Determine caller context
    current_caller = caller

    if node.type == "function_declaration" or node.type == "generator_function_declaration":
        for child in node.children:
            if child.type == "identifier":
                current_caller = get_node_text(child, source_bytes)
                break

    elif node.type in ("class_declaration", "abstract_class_declaration"):
        class_name = ""
        for child in node.children:
            if child.type in ("type_identifier", "identifier"):
                class_name = get_node_text(child, source_bytes)
                break
        if class_name:
            # Process class body methods
            for child in node.children:
                if child.type == "class_body":
                    for body_child in child.children:
                        if body_child.type == "method_definition":
                            method_name = ""
                            for mc in body_child.children:
                                if mc.type == "property_identifier":
                                    method_name = get_node_text(mc, source_bytes)
                                    break
                            if method_name:
                                method_caller = f"{class_name}.{method_name}"
                                _extract_calls_from_node(
                                    body_child, source_bytes, method_caller, calls
                                )
            return

    elif node.type == "export_statement":
        for child in node.children:
            _extract_calls_from_node(child, source_bytes, caller, calls)
        return

    # Extract call from current node
    if node.type == "call_expression":
        call = _parse_call_expression(node, source_bytes, current_caller)
        if call:
            calls.append(call)

    elif node.type == "new_expression":
        call = _parse_new_expression(node, source_bytes, current_caller)
        if call:
            calls.append(call)

    # Recurse into children
    for child in node.children:
        if child.type not in ("class_declaration", "abstract_class_declaration",
                              "function_declaration", "generator_function_declaration"):
            _extract_calls_from_node(child, source_bytes, current_caller, calls)


def _parse_call_expression(
    node: Node, source_bytes: bytes, caller: str
) -> Call | None:
    """Parse a call_expression node.

    Args:
        node: The call_expression node
        source_bytes: The source code as bytes
        caller: Current caller context

    Returns:
        Call object or None
    """
    callee_text = ""
    call_type = CallType.FUNCTION

    first_child = node.children[0] if node.children else None
    if not first_child:
        return None

    if first_child.type == "identifier":
        callee_text = get_node_text(first_child, source_bytes)
        # Skip require() calls (handled as imports)
        if callee_text == "require":
            return None
        call_type = CallType.FUNCTION

    elif first_child.type == "member_expression":
        callee_text = get_node_text(first_child, source_bytes)
        # Determine if static or instance method
        object_node = None
        for child in first_child.children:
            if child.type in ("identifier", "this"):
                object_node = child
                break
            elif child.type == "member_expression":
                object_node = child
                break

        if object_node:
            obj_text = get_node_text(object_node, source_bytes)
            if obj_text == "this":
                call_type = CallType.METHOD
            elif obj_text and obj_text[0].isupper():
                call_type = CallType.STATIC_METHOD
            else:
                call_type = CallType.METHOD

    else:
        # Complex expression (e.g., IIFE, chained calls)
        callee_text = get_node_text(first_child, source_bytes)
        if len(callee_text) > 80:
            callee_text = callee_text[:77] + "..."
        call_type = CallType.METHOD

    if not callee_text:
        return None

    # Count arguments
    args_count = None
    for child in node.children:
        if child.type == "arguments":
            args_count = sum(
                1 for c in child.children
                if c.type not in ("(", ")", ",")
            )

    return Call(
        caller=caller,
        callee=callee_text,
        line_number=node.start_point[0] + 1,
        call_type=call_type,
        arguments_count=args_count,
    )


def _parse_new_expression(
    node: Node, source_bytes: bytes, caller: str
) -> Call | None:
    """Parse a new_expression (constructor call).

    Args:
        node: The new_expression node
        source_bytes: The source code as bytes
        caller: Current caller context

    Returns:
        Call object or None
    """
    type_name = ""

    for child in node.children:
        if child.type in ("identifier", "type_identifier"):
            type_name = get_node_text(child, source_bytes)
            break
        elif child.type == "member_expression":
            type_name = get_node_text(child, source_bytes)
            break

    if not type_name:
        return None

    args_count = None
    for child in node.children:
        if child.type == "arguments":
            args_count = sum(
                1 for c in child.children
                if c.type not in ("(", ")", ",")
            )

    return Call(
        caller=caller,
        callee=f"{type_name}.<init>",
        line_number=node.start_point[0] + 1,
        call_type=CallType.CONSTRUCTOR,
        arguments_count=args_count,
    )
