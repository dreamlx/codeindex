"""Call relationship extraction for Python parser.

This module provides functions to extract function/method call relationships
from Python source code using tree-sitter (Epic 11, Story 11.1).
"""

from typing import Optional

from tree_sitter import Node, Tree

from ...parser import Call, CallType, Import, Inheritance
from ..utils import count_arguments, get_node_text


def extract_calls(
    tree: Tree, source_bytes: bytes, symbols: list, imports: list, inheritances: list
) -> list:
    """Extract function/method call relationships from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes
        symbols: Previously extracted symbols (unused currently)
        imports: Previously extracted imports (for alias resolution)
        inheritances: Previously extracted inheritances (for super() resolution)

    Returns:
        List of Call objects
    """
    # Extract call relationships
    calls = _extract_python_calls_from_tree(tree, source_bytes, imports, inheritances)

    return calls


def _build_alias_map(imports: list[Import]) -> dict[str, str]:
    """Build alias-to-module mapping from imports (Epic 11, Story 11.1).

    Examples:
        >>> imports = [
        ...     Import(module="pandas", alias="pd"),
        ...     Import(module="numpy", alias="np"),
        ...     Import(module="numpy", names=["array"], is_from=True, alias="np_array"),
        ... ]
        >>> _build_alias_map(imports)
        {'pd': 'pandas', 'np': 'numpy', 'np_array': 'numpy.array'}

    Args:
        imports: List of Import objects

    Returns:
        Dictionary mapping alias to full module path
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


def _resolve_alias(callee: str, alias_map: dict[str, str]) -> str:
    """Resolve import alias in callee name (Epic 11, Story 11.1).

    Examples:
        >>> _resolve_alias("pd.read_csv", {"pd": "pandas"})
        'pandas.read_csv'

        >>> _resolve_alias("np_array", {"np_array": "numpy.array"})
        'numpy.array'

        >>> _resolve_alias("helper", {})
        'helper'

    Args:
        callee: Callee name (possibly with alias)
        alias_map: Alias-to-module mapping

    Returns:
        Resolved callee name
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


def _determine_python_call_type(func_node: Node, source_bytes: bytes) -> CallType:
    """Determine Python call type from function node.

    Rules:
        - Constructor: Identifier starts with uppercase → CONSTRUCTOR
        - Dynamic: getattr/setattr/eval/exec/__import__ → DYNAMIC
        - Static method: ClassName.method() → STATIC_METHOD
        - Instance method: obj.method() → METHOD
        - Simple call: func() → FUNCTION

    Args:
        func_node: Tree-sitter function node
        source_bytes: Source code bytes

    Returns:
        CallType enum value
    """
    if func_node.type == "identifier":
        name = get_node_text(func_node, source_bytes)
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
            attr_name = get_node_text(attr_node, source_bytes)
            # Constructor: Outer.Inner() → Inner starts with uppercase
            if attr_name and attr_name[0].isupper():
                return CallType.CONSTRUCTOR

        # Check the object part
        obj_node = func_node.child_by_field_name("object")
        if obj_node and obj_node.type == "identifier":
            obj_name = get_node_text(obj_node, source_bytes)
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

    Args:
        func_node: Tree-sitter function node
        source_bytes: Source code bytes

    Returns:
        Extracted callee name
    """
    if func_node.type == "identifier":
        return get_node_text(func_node, source_bytes)

    elif func_node.type == "attribute":
        # Build full attribute path: obj.attr1.attr2...
        parts = []
        current = func_node

        while current:
            if current.type == "attribute":
                # Get the attribute name
                attr_node = current.child_by_field_name("attribute")
                if attr_node:
                    parts.insert(0, get_node_text(attr_node, source_bytes))
                # Move to object
                current = current.child_by_field_name("object")
            elif current.type == "identifier":
                parts.insert(0, get_node_text(current, source_bytes))
                break
            elif current.type == "call":
                # Special case: super().method() → extract as "super.method"
                func_child = current.child_by_field_name("function")
                if func_child and func_child.type == "identifier":
                    func_name = get_node_text(func_child, source_bytes)
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
    callee = _resolve_alias(callee_raw, alias_map)

    # Determine call type
    call_type = _determine_python_call_type(func_node, source_bytes)

    # Constructor: format as Class.__init__
    if call_type == CallType.CONSTRUCTOR:
        callee = f"{callee}.__init__"

    # Extract arguments count (best-effort)
    args_node = node.child_by_field_name("arguments")
    args_count = count_arguments(args_node) if args_node else None

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
        calls.extend(
            _extract_python_calls(child, source_bytes, context, alias_map, parent_map)
        )

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

    Args:
        decorator_node: Tree-sitter decorator node

    Returns:
        True if simple decorator, False otherwise
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

    Args:
        decorator_node: Tree-sitter decorator node
        source_bytes: Source code bytes

    Returns:
        Decorator name
    """
    for child in decorator_node.children:
        if child.type == "identifier":
            return get_node_text(child, source_bytes)
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
    tree: Tree,
    source_bytes: bytes,
    imports: list[Import],
    inheritances: list[Inheritance],
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
    alias_map = _build_alias_map(imports)

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
                    func_name = get_node_text(node, source_bytes)
                    break

            # Extract calls within function
            if func_name:
                calls.extend(
                    _extract_python_calls(
                        child, source_bytes, func_name, alias_map, parent_map
                    )
                )

        elif child.type == "class_definition":
            # Extract class name
            class_name = ""
            for node in child.children:
                if node.type == "identifier":
                    class_name = get_node_text(node, source_bytes)
                    break

            if class_name:
                # Extract decorator calls (AC5: decorator calls)
                calls.extend(_extract_decorator_calls(child, source_bytes, "<module>"))

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
                                    method_name = get_node_text(node, source_bytes)
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
                                        method_node,
                                        source_bytes,
                                        context,
                                        alias_map,
                                        parent_map,
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
                                                    line_number=dec_node.start_point[0]
                                                    + 1,
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
                                            method_name = get_node_text(node, source_bytes)
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
                            func_name = get_node_text(node, source_bytes)
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
                            class_name = get_node_text(node, source_bytes)
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
                                            method_name = get_node_text(node, source_bytes)
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
