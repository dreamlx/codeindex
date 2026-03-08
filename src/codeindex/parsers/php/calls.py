"""Call extraction for PHP parser.

This module provides functions to extract function/method call relationships
from PHP source code using tree-sitter.
"""

from typing import Optional

from tree_sitter import Node, Tree

from ...parser import Call, CallType, Import
from ..utils import get_node_text


def extract_calls(
    tree: Tree, source_bytes: bytes, symbols: list, imports: list
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
    # First extract namespace and use statements
    namespace = ""
    use_map = {}
    inheritances = []

    root = tree.root_node

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

    # Extract inheritances for parent:: resolution
    for child in root.children:
        if child.type == "class_declaration":
            _extract_class_inheritances(child, source_bytes, namespace, use_map, inheritances)

    # Extract calls
    return _extract_calls_from_tree(
        tree, source_bytes, imports, inheritances, namespace, use_map
    )


def _parse_namespace(node, source_bytes: bytes) -> str:
    """Parse PHP namespace definition."""
    for child in node.children:
        if child.type == "namespace_name":
            return get_node_text(child, source_bytes)
    return ""


def _parse_use_for_map(node, source_bytes: bytes) -> list[Import]:
    """Parse PHP use statement for building use_map."""
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


def _extract_class_inheritances(
    node,
    source_bytes: bytes,
    namespace: str,
    use_map: dict[str, str],
    inheritances: list
) -> None:
    """Extract inheritance relationships from class node for parent:: resolution."""
    from ...parser import Inheritance

    class_name = ""
    extends = ""
    implements = []

    for child in node.children:
        if child.type == "name":
            class_name = get_node_text(child, source_bytes)
        elif child.type == "base_clause":
            for bc_child in child.children:
                if bc_child.type == "name":
                    extends = get_node_text(bc_child, source_bytes)
        elif child.type == "class_interface_clause":
            for ic_child in child.children:
                if ic_child.type == "name":
                    implements.append(get_node_text(ic_child, source_bytes))

    # Build full class name with namespace
    full_class_name = f"{namespace}\\{class_name}" if namespace else class_name

    # Create Inheritance objects
    if extends:
        parent_full_name = use_map.get(extends, f"{namespace}\\{extends}" if namespace else extends)
        inheritances.append(Inheritance(child=full_class_name, parent=parent_full_name))

    for interface in implements:
        interface_full_name = use_map.get(
            interface, f"{namespace}\\{interface}" if namespace else interface
        )
        inheritances.append(Inheritance(child=full_class_name, parent=interface_full_name))


def _extract_calls_from_tree(
    tree,
    source_bytes: bytes,
    imports: list[Import],
    inheritances: list,
    namespace: str,
    use_map: dict[str, str]
) -> list[Call]:
    """Extract all PHP call relationships from parse tree.

    Args:
        tree: Tree-sitter parse tree
        source_bytes: Source code bytes
        imports: Import list
        inheritances: Inheritance list
        namespace: PHP namespace
        use_map: Use statement mapping

    Returns:
        List of Call objects
    """
    # Build parent map for parent:: resolution
    parent_map = {}
    for inh in inheritances:
        parent_map[inh.child] = inh.parent

    calls = []
    root = tree.root_node

    # Process top-level functions
    for child in root.children:
        if child.type == "function_definition":
            # Extract function name
            func_name = ""
            for node in child.children:
                if node.type == "name":
                    func_name = get_node_text(node, source_bytes)
                    break

            if func_name:
                caller = f"{namespace}\\{func_name}" if namespace else func_name
                # Extract calls from function body
                calls.extend(
                    _extract_calls_from_node(
                        child, source_bytes, caller,
                        use_map, namespace, parent_map, current_class=""
                    )
                )

        elif child.type == "class_declaration":
            # Extract class name
            class_name = ""
            for node in child.children:
                if node.type == "name":
                    class_name = get_node_text(node, source_bytes)
                    break

            if not class_name:
                continue

            # Full class name with namespace
            full_class_name = f"{namespace}\\{class_name}" if namespace else class_name

            # Find class body
            body_node = None
            for node in child.children:
                if node.type == "declaration_list":
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
                        if node.type == "name":
                            method_name = get_node_text(node, source_bytes)
                            break

                    if method_name:
                        caller = f"{full_class_name}::{method_name}"
                        # Extract calls from method body
                        calls.extend(
                            _extract_calls_from_node(
                                method_node, source_bytes, caller,
                                use_map, namespace, parent_map, full_class_name
                            )
                        )

    return calls


def _extract_calls_from_node(
    node: Node,
    source_bytes: bytes,
    caller: str,
    use_map: dict[str, str],
    namespace: str,
    parent_map: dict[str, str],
    current_class: str
) -> list[Call]:
    """Extract PHP calls from a function/method body.

    Args:
        node: Function or method node
        source_bytes: Source code bytes
        caller: Calling function/method name
        use_map: Use statement mapping
        namespace: Current namespace
        parent_map: Parent class mapping
        current_class: Current class name (for $this resolution)

    Returns:
        List of Call objects
    """
    calls = []

    # Recursively find all call nodes
    def traverse(n):
        # Function call
        if n.type == "function_call_expression":
            call = _parse_function_call(
                n, source_bytes, caller, use_map, namespace
            )
            if call:
                calls.append(call)

        # Member call expression ($obj->method())
        elif n.type == "member_call_expression":
            call = _parse_member_call(
                n, source_bytes, caller, use_map, namespace, current_class
            )
            if call:
                calls.append(call)

        # Scoped call expression (Class::method())
        elif n.type == "scoped_call_expression":
            call = _parse_scoped_call(
                n, source_bytes, caller, use_map, namespace, parent_map, current_class
            )
            if call:
                calls.append(call)

        # Object creation (new Class())
        elif n.type == "object_creation_expression":
            call = _parse_object_creation(
                n, source_bytes, caller, use_map, namespace
            )
            if call:
                calls.append(call)

        # Recurse into children
        for child in n.children:
            traverse(child)

    traverse(node)
    return calls


def _parse_function_call(
    node: Node,
    source_bytes: bytes,
    caller: str,
    use_map: dict[str, str],
    namespace: str
) -> Optional[Call]:
    """Parse PHP function call expression.

    Args:
        node: function_call_expression node
        source_bytes: Source code bytes
        caller: Calling function/method name
        use_map: Use statement mapping
        namespace: Current namespace

    Returns:
        Call object or None
    """
    # Extract function name
    func_name = None
    args_count = None

    for child in node.children:
        if child.type in ("name", "qualified_name"):
            func_name = get_node_text(child, source_bytes)
        elif child.type == "arguments":
            # Count arguments
            args_count = sum(
                1 for c in child.children
                if c.type not in (",", "(", ")")
            )

    if not func_name:
        return None

    # Resolve function name via use_map if needed
    callee = func_name

    # Check if it's a namespaced function
    if "\\" in func_name:
        # Already qualified, keep as is
        # Remove leading backslash if present
        callee = func_name.lstrip("\\")
    elif func_name in use_map:
        # Resolve via use_map
        callee = use_map[func_name]
    else:
        # Assume it's in current namespace or global
        # For now, keep simple name (don't add namespace for built-in functions)
        callee = func_name

    return Call(
        caller=caller,
        callee=callee,
        line_number=node.start_point[0] + 1,
        call_type=CallType.FUNCTION,
        arguments_count=args_count
    )


def _parse_member_call(
    node: Node,
    source_bytes: bytes,
    caller: str,
    use_map: dict[str, str],
    namespace: str,
    current_class: str
) -> Optional[Call]:
    """Parse PHP member call expression ($obj->method()).

    Args:
        node: member_call_expression node
        source_bytes: Source code bytes
        caller: Calling function/method name
        use_map: Use statement mapping
        namespace: Current namespace
        current_class: Current class name

    Returns:
        Call object or None
    """
    # Extract object and method name
    object_name = None
    method_name = None
    args_count = None

    for child in node.children:
        if child.type == "variable_name" and not object_name:
            # This is the object ($this, $user, etc.)
            object_name = get_node_text(child, source_bytes)
        elif child.type == "name":
            # This is the method name
            method_name = get_node_text(child, source_bytes)
        elif child.type == "arguments":
            # Count arguments
            args_count = sum(
                1 for c in child.children
                if c.type not in (",", "(", ")")
            )

    if not method_name:
        return None

    # Determine the class
    if object_name == "$this" and current_class:
        # $this->method() in current class
        callee = f"{current_class}::{method_name}"
        call_type = CallType.METHOD
    else:
        # Try to infer class from variable name
        # For now, capitalize variable name as heuristic
        if object_name and object_name.startswith("$"):
            var_name = object_name[1:]  # Remove $
            # Capitalize first letter as class name heuristic
            class_name = var_name.capitalize()

            # Check if this class is in use_map
            if class_name in use_map:
                full_class = use_map[class_name]
                callee = f"{full_class}::{method_name}"
            else:
                # Assume it's in current namespace
                callee = f"{class_name}::{method_name}"

            call_type = CallType.METHOD
        else:
            # Can't determine class, use dynamic
            return Call(
                caller=caller,
                callee=None,
                line_number=node.start_point[0] + 1,
                call_type=CallType.DYNAMIC,
                arguments_count=args_count
            )

    return Call(
        caller=caller,
        callee=callee,
        line_number=node.start_point[0] + 1,
        call_type=call_type,
        arguments_count=args_count
    )


def _parse_scoped_call(
    node: Node,
    source_bytes: bytes,
    caller: str,
    use_map: dict[str, str],
    namespace: str,
    parent_map: dict[str, str],
    current_class: str
) -> Optional[Call]:
    """Parse PHP scoped call expression (Class::method() or parent::method()).

    Args:
        node: scoped_call_expression node
        source_bytes: Source code bytes
        caller: Calling function/method name
        use_map: Use statement mapping
        namespace: Current namespace
        parent_map: Parent class mapping
        current_class: Current class name

    Returns:
        Call object or None
    """
    # Extract scope and method name
    scope_name = None
    method_name = None
    args_count = None

    for child in node.children:
        if child.type in ("name", "qualified_name", "relative_scope") and not scope_name:
            # This is the class/scope name
            scope_name = get_node_text(child, source_bytes)
        elif child.type == "name" and scope_name:
            # This is the method name (second name node)
            method_name = get_node_text(child, source_bytes)
        elif child.type == "arguments":
            # Count arguments
            args_count = sum(
                1 for c in child.children
                if c.type not in (",", "(", ")")
            )

    if not method_name:
        return None

    # Resolve scope
    if scope_name == "parent" and current_class:
        # parent::method() - resolve to parent class
        if current_class in parent_map:
            parent_class = parent_map[current_class]
            callee = f"{parent_class}::{method_name}"
        else:
            # Can't resolve parent, use as-is
            callee = f"parent::{method_name}"
    elif scope_name == "self" and current_class:
        # self::method() - same as current class
        callee = f"{current_class}::{method_name}"
    elif scope_name == "static" and current_class:
        # static::method() - late static binding, use current class
        callee = f"{current_class}::{method_name}"
    elif scope_name:
        # Regular class name
        # Check if starts with backslash (fully qualified)
        if scope_name.startswith("\\"):
            # Extract without backslash (Python 3.10 compatible)
            clean_scope = scope_name.lstrip("\\")
            callee = f"{clean_scope}::{method_name}"
        elif scope_name in use_map:
            # Resolve via use_map
            full_class = use_map[scope_name]
            callee = f"{full_class}::{method_name}"
        elif namespace:
            # Assume it's in current namespace
            callee = f"{namespace}\\{scope_name}::{method_name}"
        else:
            callee = f"{scope_name}::{method_name}"
    else:
        return None

    return Call(
        caller=caller,
        callee=callee,
        line_number=node.start_point[0] + 1,
        call_type=CallType.STATIC_METHOD,
        arguments_count=args_count
    )


def _parse_object_creation(
    node: Node,
    source_bytes: bytes,
    caller: str,
    use_map: dict[str, str],
    namespace: str
) -> Optional[Call]:
    """Parse PHP object creation expression (new Class()).

    Args:
        node: object_creation_expression node
        source_bytes: Source code bytes
        caller: Calling function/method name
        use_map: Use statement mapping
        namespace: Current namespace

    Returns:
        Call object or None
    """
    # Extract class name and arguments
    class_name = None
    args_count = None

    for child in node.children:
        if child.type in ("name", "qualified_name"):
            class_name = get_node_text(child, source_bytes)
        elif child.type == "arguments":
            # Count arguments
            args_count = sum(
                1 for c in child.children
                if c.type not in (",", "(", ")")
            )

    if not class_name:
        return None

    # Skip anonymous classes
    if class_name == "class":
        return None

    # Resolve class name
    if class_name.startswith("\\"):
        # Fully qualified name
        full_class = class_name.lstrip("\\")
    elif class_name in use_map:
        # Resolve via use_map
        full_class = use_map[class_name]
    elif namespace:
        # Assume it's in current namespace
        full_class = f"{namespace}\\{class_name}"
    else:
        full_class = class_name

    # Constructor call
    callee = f"{full_class}::__construct"

    return Call(
        caller=caller,
        callee=callee,
        line_number=node.start_point[0] + 1,
        call_type=CallType.CONSTRUCTOR,
        arguments_count=args_count
    )
