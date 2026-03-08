"""Import extraction for Objective-C parser.

This module provides functions to extract import statements from Objective-C:
- #import "LocalFile.h" (local imports)
- #import <Framework/Header.h> (system imports)
"""

from tree_sitter import Tree

from ...parser import Import
from ..utils import get_node_text


def extract_imports(tree: Tree, source_bytes: bytes) -> list:
    """Extract import statements from Objective-C code.

    Args:
        tree: Tree-sitter parse tree
        source_bytes: Source code as bytes

    Returns:
        List of Import objects
    """
    imports = []
    root = tree.root_node

    for child in root.children:
        if child.type == "preproc_include":
            import_obj = _extract_import(child, source_bytes)
            if import_obj:
                imports.append(import_obj)

    return imports


def _extract_import(node, source_bytes: bytes) -> Import | None:
    """Extract single import statement.

    Args:
        node: preproc_import node
        source_bytes: Source code bytes

    Returns:
        Import object or None
    """
    # Get imported module/header
    module_name = None

    for child in node.children:
        if child.type == "string_literal":
            # Local import: #import "MyClass.h"
            # Extract from string_content child if exists
            for subchild in child.children:
                if subchild.type == "string_content":
                    module_name = get_node_text(subchild, source_bytes)
                    break
            if not module_name:
                module_name = get_node_text(child, source_bytes).strip('"')
            break
        elif child.type == "system_lib_string":
            # System import: #import <Foundation/Foundation.h>
            module_name = get_node_text(child, source_bytes).strip("<>")
            break

    if not module_name:
        return None

    # Strip .h extension if present
    if module_name.endswith(".h"):
        module_name = module_name[:-2]

    return Import(module=module_name, names=[], is_from=False)
