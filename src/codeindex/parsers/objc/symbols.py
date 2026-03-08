"""Symbol extraction for Objective-C parser.

This module provides functions to extract symbols from Objective-C source code:
- @interface declarations (classes)
- @implementation (class implementations)
- @protocol declarations
- Instance methods (-)
- Class methods (+)
- Properties (@property)
"""

from tree_sitter import Tree

from ...parser import Symbol
from ..utils import get_node_text


def extract_symbols(tree: Tree, source_bytes: bytes) -> list:
    """Extract symbols from Objective-C source code.

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
        # @interface declarations (usually in .h files)
        if child.type == "class_interface":
            symbols.extend(_extract_interface(child, source_bytes))

        # @implementation (usually in .m files)
        elif child.type == "class_implementation":
            symbols.extend(_extract_implementation(child, source_bytes))

        # @protocol declarations
        elif child.type == "protocol_declaration":
            symbols.extend(_extract_protocol(child, source_bytes))

    return symbols


def _extract_interface(node, source_bytes: bytes) -> list[Symbol]:
    """Extract symbols from @interface declaration.

    Args:
        node: class_interface node
        source_bytes: Source code bytes

    Returns:
        List of symbols (class + methods + properties)
    """
    symbols = []

    # Get class name
    class_name = None
    for child in node.children:
        if child.type == "identifier":
            class_name = get_node_text(child, source_bytes)
            break

    if not class_name:
        return symbols

    # Add class symbol
    signature = _build_interface_signature(node, source_bytes, class_name)
    symbols.append(
        Symbol(
            name=class_name,
            kind="class",
            signature=signature,
            docstring="",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
    )

    # Extract methods and properties from interface
    for child in node.children:
        if child.type == "property_declaration":
            prop_sym = _extract_property(child, source_bytes, class_name)
            if prop_sym:
                symbols.append(prop_sym)
        elif child.type == "method_declaration":
            method_sym = _extract_method(child, source_bytes, class_name)
            if method_sym:
                symbols.append(method_sym)
        elif child.type == "declaration_list":
            symbols.extend(
                _extract_declarations(child, source_bytes, class_name)
            )

    return symbols


def _extract_implementation(node, source_bytes: bytes) -> list[Symbol]:
    """Extract symbols from @implementation.

    Args:
        node: class_implementation node
        source_bytes: Source code bytes

    Returns:
        List of symbols (class + methods)
    """
    symbols = []

    # Get class name
    class_name = None
    for child in node.children:
        if child.type == "identifier":
            class_name = get_node_text(child, source_bytes)
            break

    if not class_name:
        return symbols

    # Add class symbol
    symbols.append(
        Symbol(
            name=class_name,
            kind="class",
            signature=f"@implementation {class_name}",
            docstring="",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
    )

    # Extract method implementations
    for child in node.children:
        if child.type == "implementation_definition":
            # Methods are inside implementation_definition
            for subchild in child.children:
                if subchild.type == "method_definition":
                    method_sym = _extract_method(subchild, source_bytes, class_name)
                    if method_sym:
                        symbols.append(method_sym)
        elif child.type in ("method_definition", "function_definition"):
            # Fallback for direct children
            method_sym = _extract_method(child, source_bytes, class_name)
            if method_sym:
                symbols.append(method_sym)

    return symbols


def _extract_protocol(node, source_bytes: bytes) -> list[Symbol]:
    """Extract symbols from @protocol declaration.

    Args:
        node: protocol_declaration node
        source_bytes: Source code bytes

    Returns:
        List of symbols (protocol + methods + properties)
    """
    symbols = []

    # Get protocol name
    protocol_name = None
    for child in node.children:
        if child.type == "identifier":
            protocol_name = get_node_text(child, source_bytes)
            break

    if not protocol_name:
        return symbols

    # Check for protocol inheritance (protocol_reference_list)
    parent_protocols = []
    for child in node.children:
        if child.type == "protocol_reference_list":
            for subchild in child.children:
                if subchild.type == "identifier":
                    parent_protocols.append(get_node_text(subchild, source_bytes))

    # Build protocol signature
    signature = f"@protocol {protocol_name}"
    if parent_protocols:
        signature += " <" + ", ".join(parent_protocols) + ">"

    # Add protocol symbol (using "interface" kind for compatibility)
    symbols.append(
        Symbol(
            name=protocol_name,
            kind="interface",  # Protocols are like interfaces
            signature=signature,
            docstring="",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )
    )

    # Extract methods and properties from protocol
    for child in node.children:
        if child.type == "method_declaration":
            method_sym = _extract_method(child, source_bytes, protocol_name)
            if method_sym:
                symbols.append(method_sym)
        elif child.type == "property_declaration":
            prop_sym = _extract_property(child, source_bytes, protocol_name)
            if prop_sym:
                symbols.append(prop_sym)
        elif child.type == "qualified_protocol_interface_declaration":
            # Handle @required/@optional sections
            for subchild in child.children:
                if subchild.type == "method_declaration":
                    method_sym = _extract_method(subchild, source_bytes, protocol_name)
                    if method_sym:
                        symbols.append(method_sym)
                elif subchild.type == "property_declaration":
                    prop_sym = _extract_property(subchild, source_bytes, protocol_name)
                    if prop_sym:
                        symbols.append(prop_sym)

    return symbols


def _extract_declarations(
    decl_list_node, source_bytes: bytes, class_name: str
) -> list[Symbol]:
    """Extract methods and properties from declaration list.

    Args:
        decl_list_node: declaration_list node
        source_bytes: Source code bytes
        class_name: Name of the containing class

    Returns:
        List of method and property symbols
    """
    symbols = []

    for child in decl_list_node.children:
        if child.type == "method_declaration":
            method_sym = _extract_method(child, source_bytes, class_name)
            if method_sym:
                symbols.append(method_sym)

        elif child.type == "property_declaration":
            prop_sym = _extract_property(child, source_bytes, class_name)
            if prop_sym:
                symbols.append(prop_sym)

    return symbols


def _extract_method(
    node, source_bytes: bytes, class_name: str
) -> Symbol | None:
    """Extract method symbol.

    Args:
        node: method_declaration or method_definition node
        source_bytes: Source code bytes
        class_name: Name of the containing class

    Returns:
        Method symbol or None
    """
    # Get method selector (name) by collecting identifier nodes
    method_parts = []
    is_class_method = False

    for child in node.children:
        # Check if class method (+) or instance method (-)
        if child.type == "+" or get_node_text(child, source_bytes) == "+":
            is_class_method = True
        elif child.type == "-" or get_node_text(child, source_bytes) == "-":
            is_class_method = False

        # Collect method name parts (identifiers outside method_parameter)
        if child.type == "identifier":
            method_parts.append(get_node_text(child, source_bytes))
        elif child.type == "method_parameter":
            # Add colon for parameter
            method_parts.append(":")

    if not method_parts:
        return None

    # Build method selector (e.g., "add:to:" or "reset")
    method_name = "".join(method_parts)

    # Build signature
    signature = _build_method_signature(node, source_bytes, is_class_method)

    # Full qualified name
    full_name = f"{class_name}.{method_name}"

    return Symbol(
        name=full_name,
        kind="method",
        signature=signature,
        docstring="",
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _extract_property(
    node, source_bytes: bytes, class_name: str
) -> Symbol | None:
    """Extract property symbol.

    Args:
        node: property_declaration node
        source_bytes: Source code bytes
        class_name: Name of the containing class

    Returns:
        Property symbol or None
    """
    # Find property name in struct_declarator
    prop_name = None

    def find_property_name(n):
        """Recursively find property name in struct_declarator."""
        if n.type == "identifier" and n.parent and n.parent.type in (
            "struct_declarator", "pointer_declarator"
        ):
            return get_node_text(n, source_bytes)
        for child in n.children:
            result = find_property_name(child)
            if result:
                return result
        return None

    prop_name = find_property_name(node)

    if not prop_name:
        return None

    # Build signature from full declaration
    signature = get_node_text(node, source_bytes).strip()

    # Full qualified name
    full_name = f"{class_name}.{prop_name}"

    return Symbol(
        name=full_name,
        kind="property",
        signature=signature,
        docstring="",
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _build_interface_signature(
    node, source_bytes: bytes, class_name: str
) -> str:
    """Build signature for @interface declaration.

    Args:
        node: class_interface node
        source_bytes: Source code bytes
        class_name: Class name

    Returns:
        Signature string
    """
    # Look for superclass (second identifier after ':')
    superclass = None
    protocols = []

    found_colon = False
    for child in node.children:
        if child.type == ":":
            found_colon = True
        elif found_colon and child.type == "identifier":
            superclass = get_node_text(child, source_bytes)
            break

    # Extract protocols from parameterized_arguments
    for child in node.children:
        if child.type == "parameterized_arguments":
            for subchild in child.children:
                if subchild.type == "type_name":
                    for type_child in subchild.children:
                        if type_child.type == "type_identifier":
                            protocols.append(get_node_text(type_child, source_bytes))
                            break

    # Build signature
    sig = f"@interface {class_name}"
    if superclass:
        sig += f" : {superclass}"
    if protocols:
        sig += " <" + ", ".join(protocols) + ">"

    return sig


def _build_method_signature(
    node, source_bytes: bytes, is_class_method: bool
) -> str:
    """Build method signature.

    Args:
        node: method_declaration or method_definition node
        source_bytes: Source code bytes
        is_class_method: True if class method (+)

    Returns:
        Method signature string
    """
    # Extract signature from source (first line)
    method_text = get_node_text(node, source_bytes)
    lines = method_text.split("\n")
    first_line = lines[0].strip()

    # For method definitions, stop at opening brace
    if "{" in first_line:
        first_line = first_line[:first_line.index("{")].strip()

    return first_line
