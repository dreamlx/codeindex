"""Import extraction for TypeScript/JavaScript parser.

This module provides functions to extract import/export statements
from TypeScript/JavaScript source code using tree-sitter.
"""

from tree_sitter import Node, Tree

from ...parser import Import
from ..utils import get_node_text


def extract_imports(tree: Tree, source_bytes: bytes) -> list:
    """Extract import/export-from statements.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        List of Import objects
    """
    imports = []
    root = tree.root_node

    for child in root.children:
        if child.type == "import_statement":
            imports.extend(_parse_import_statement(child, source_bytes))
        elif child.type == "export_statement":
            imports.extend(_parse_export_as_import(child, source_bytes))
        elif child.type == "lexical_declaration":
            # CommonJS require
            imp = _parse_require(child, source_bytes)
            if imp:
                imports.append(imp)

    return imports


def _parse_import_statement(
    node: Node, source_bytes: bytes
) -> list[Import]:
    """Parse an import statement node.

    Args:
        node: The import_statement node
        source_bytes: The source code as bytes

    Returns:
        List of Import objects
    """
    imports = []
    module = ""
    import_clause = None

    for child in node.children:
        if child.type == "string":
            module = _extract_string_content(child, source_bytes)
        elif child.type == "import_clause":
            import_clause = child

    if not module:
        return imports

    if import_clause is None:
        # Side-effect import: import 'module'
        imports.append(Import(module=module, names=[], is_from=False))
        return imports

    # Parse import clause
    for child in import_clause.children:
        if child.type == "identifier":
            # Default import: import X from 'module'
            default_name = get_node_text(child, source_bytes)
            imports.append(Import(
                module=module,
                names=[default_name],
                is_from=True,
                alias=default_name,
            ))
        elif child.type == "named_imports":
            # Named imports: import { A, B } from 'module'
            names = []
            for spec in child.children:
                if spec.type == "import_specifier":
                    spec_name = ""
                    for spec_child in spec.children:
                        if spec_child.type == "identifier":
                            spec_name = get_node_text(spec_child, source_bytes)
                            break
                    if spec_name:
                        names.append(spec_name)
            if names:
                imports.append(Import(
                    module=module,
                    names=names,
                    is_from=True,
                ))
        elif child.type == "namespace_import":
            # Namespace import: import * as X from 'module'
            alias = ""
            for ns_child in child.children:
                if ns_child.type == "identifier":
                    alias = get_node_text(ns_child, source_bytes)
            imports.append(Import(
                module=module,
                names=["*"],
                is_from=True,
                alias=alias,
            ))

    return imports


def _parse_export_as_import(
    node: Node, source_bytes: bytes
) -> list[Import]:
    """Parse export statements that re-export from another module.

    Args:
        node: The export_statement node
        source_bytes: The source code as bytes

    Returns:
        List of Import objects
    """
    imports = []
    module = ""
    has_from = False
    names = []
    is_wildcard = False

    for child in node.children:
        if child.type == "string":
            module = _extract_string_content(child, source_bytes)
        elif child.type == "from":
            has_from = True
        elif child.type == "export_clause":
            for spec in child.children:
                if spec.type == "export_specifier":
                    for spec_child in spec.children:
                        if spec_child.type == "identifier":
                            names.append(get_node_text(spec_child, source_bytes))
                            break
        elif child.type == "*":
            is_wildcard = True

    if module and has_from:
        if is_wildcard:
            imports.append(Import(module=module, names=["*"], is_from=True))
        elif names:
            imports.append(Import(module=module, names=names, is_from=True))

    return imports


def _parse_require(
    node: Node, source_bytes: bytes
) -> Import | None:
    """Parse CommonJS require: const X = require('module').

    Args:
        node: The lexical_declaration node
        source_bytes: The source code as bytes

    Returns:
        Import object or None
    """
    for child in node.children:
        if child.type == "variable_declarator":
            var_name = ""
            req_module = ""

            for var_child in child.children:
                if var_child.type == "identifier":
                    var_name = get_node_text(var_child, source_bytes)
                elif var_child.type == "call_expression":
                    callee = ""
                    for call_child in var_child.children:
                        if call_child.type == "identifier":
                            callee = get_node_text(call_child, source_bytes)
                        elif call_child.type == "arguments":
                            for arg_child in call_child.children:
                                if arg_child.type == "string":
                                    req_module = _extract_string_content(
                                        arg_child, source_bytes
                                    )

                    if callee == "require" and req_module:
                        return Import(
                            module=req_module,
                            names=[var_name] if var_name else [],
                            is_from=False,
                            alias=var_name if var_name else None,
                        )

    return None


def _extract_string_content(node: Node, source_bytes: bytes) -> str:
    """Extract string content from a string node (strip quotes).

    Args:
        node: The string node
        source_bytes: The source code as bytes

    Returns:
        String content without quotes
    """
    for child in node.children:
        if child.type == "string_fragment":
            return get_node_text(child, source_bytes)
    # Fallback: strip quotes manually
    text = get_node_text(node, source_bytes)
    if len(text) >= 2 and text[0] in ("'", '"', '`') and text[-1] in ("'", '"', '`'):
        return text[1:-1]
    return text
