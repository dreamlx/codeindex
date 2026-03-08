"""Import extraction for Swift parser.

This module provides functions to extract import statements from Swift source code.
"""

from tree_sitter import Tree

from ...parser import Import


def extract_imports(tree: Tree, source_bytes: bytes) -> list:
    """Extract import statements from Swift source code.

    Args:
        tree: Tree-sitter parse tree
        source_bytes: Source code as bytes

    Returns:
        List of Import objects
    """
    imports: list[Import] = []
    root = tree.root_node

    for child in root.children:
        if child.type == "import_declaration":
            # Extract module name from import
            import_text = child.text.decode("utf-8", errors="replace")
            # Simple extraction: "import ModuleName" -> "ModuleName"
            parts = import_text.strip().split()
            if len(parts) >= 2:
                module_name = parts[1]
                imports.append(Import(module=module_name, names=[], is_from=False))

    return imports
