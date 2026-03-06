"""Import extraction for Python parser.

This module provides functions to extract import statements from Python source code
using tree-sitter.
"""

from tree_sitter import Node, Tree

from ...parser import Import
from ..utils import get_node_text


def extract_imports(tree: Tree, source_bytes: bytes) -> list:
    """Extract import statements from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        List of Import objects
    """
    imports: list[Import] = []
    root = tree.root_node

    for child in root.children:
        if child.type in ("import_statement", "import_from_statement"):
            import_list = _parse_import(child, source_bytes)
            imports.extend(import_list)

    return imports


def _parse_import(node: Node, source_bytes: bytes) -> list[Import]:
    """Parse an import statement.

    Returns a list of Import objects. For imports with different aliases,
    creates separate Import objects (Epic 10, Story 10.2.1).

    Examples:
        import numpy as np → [Import("numpy", [], False, alias="np")]
        from typing import Dict as D, List → [Import("typing", ["Dict"], True, alias="D"),
                                                Import("typing", ["List"], True, alias=None)]

    Args:
        node: Tree-sitter import statement node
        source_bytes: Source code bytes

    Returns:
        List of Import objects
    """
    imports = []

    if node.type == "import_statement":
        # import foo, bar as baz
        for child in node.children:
            if child.type == "dotted_name":
                # Simple import without alias
                module_name = get_node_text(child, source_bytes)
                imports.append(
                    Import(module=module_name, names=[], is_from=False, alias=None)
                )
            elif child.type == "aliased_import":
                # import foo as bar
                module_name = ""
                alias = None
                for ac in child.children:
                    if ac.type == "dotted_name":
                        module_name = get_node_text(ac, source_bytes)
                    elif ac.type == "identifier" and module_name:
                        # This is the alias (after 'as')
                        alias = get_node_text(ac, source_bytes)
                if module_name:
                    imports.append(
                        Import(module=module_name, names=[], is_from=False, alias=alias)
                    )

    elif node.type == "import_from_statement":
        # from foo import bar, baz as qux
        module = ""
        imported_items = []  # List of (name, alias) tuples
        found_module = False

        # Parse the import structure
        for child in node.children:
            if child.type == "dotted_name" and not found_module:
                # This is the module name
                module = get_node_text(child, source_bytes)
                found_module = True
            elif child.type == "relative_import" and not found_module:
                module = get_node_text(child, source_bytes)
                found_module = True
            elif found_module:
                # After module, collect imported items
                if child.type == "dotted_name":
                    # This could be wrongly parsed - skip if it's the module name itself
                    name = get_node_text(child, source_bytes)
                    if name != module:  # Don't add module name as import
                        imported_items.append((name, None))
                elif child.type == "identifier":
                    # Single identifier: from foo import bar
                    name = get_node_text(child, source_bytes)
                    if name not in ("import", "from", "*") and name != module:
                        imported_items.append((name, None))
                elif child.type == "aliased_import":
                    # from foo import bar as baz
                    name = ""
                    alias = None
                    for ac in child.children:
                        if ac.type in ("dotted_name", "identifier") and not name:
                            name = get_node_text(ac, source_bytes)
                        elif ac.type == "identifier" and name:
                            # This is the alias (after 'as')
                            alias = get_node_text(ac, source_bytes)
                    if name:
                        imported_items.append((name, alias))
                elif child.type == "wildcard_import":
                    # from foo import *
                    imported_items.append(("*", None))

        # Create Import objects
        if module and imported_items:
            # Create separate Import for each item
            for name, alias in imported_items:
                imports.append(
                    Import(module=module, names=[name], is_from=True, alias=alias)
                )

    return imports
