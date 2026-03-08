"""Import extraction for PHP parser.

This module provides functions to extract import/use statements and
require/include statements from PHP source code using tree-sitter.
"""

from tree_sitter import Tree

from ...parser import Import
from ..utils import get_node_text


def extract_imports(tree: Tree, source_bytes: bytes) -> list:
    """Extract import/use statements from the parse tree.

    Args:
        tree: The tree-sitter parse tree
        source_bytes: The source code as bytes

    Returns:
        List of Import objects
    """
    imports = []
    root = tree.root_node

    for child in root.children:
        if child.type == "namespace_use_declaration":
            php_imports = _parse_use(child, source_bytes)
            imports.extend(php_imports)
        elif child.type in ("include_expression", "require_expression"):
            php_import = _parse_include(child, source_bytes)
            if php_import:
                imports.append(php_import)

    return imports


def _parse_use(node, source_bytes: bytes) -> list[Import]:
    """Parse PHP use statement.

    Epic 10, Story 10.2.2: Updated to store alias in alias field (not names field)
    for consistency with Python import handling and LoomGraph integration.

    Handles:
    - use App\\Service\\UserService;
    - use App\\Model\\User as UserModel;
    - use App\\Repository\\{UserRepository, OrderRepository};

    Returns:
        List of Import objects with:
        - names: always empty [] (PHP use imports entire class, not specific members)
        - alias: the alias if present (e.g., "UserModel"), None otherwise
    """
    imports = []
    base_namespace = ""

    for child in node.children:
        if child.type == "namespace_name":
            # Group import base: use App\Repository\{...}
            base_namespace = get_node_text(child, source_bytes)

        elif child.type == "namespace_use_clause":
            # Single import
            module = ""
            alias = ""

            for clause_child in child.children:
                if clause_child.type == "qualified_name":
                    module = get_node_text(clause_child, source_bytes)
                elif clause_child.type == "name" and module:
                    # This is the alias (after 'as')
                    alias = get_node_text(clause_child, source_bytes)

            if module:
                # If there's a base namespace (group import), prepend it
                if base_namespace:
                    module = f"{base_namespace}\\{module}"

                # Epic 10, Story 10.2.2: alias now in alias field, names always empty
                imports.append(
                    Import(
                        module=module,
                        names=[],  # PHP use imports whole class, not specific members
                        is_from=True,  # PHP use is similar to Python's from...import
                        alias=alias if alias else None,
                    )
                )

        elif child.type == "namespace_use_group":
            # Group import: {UserRepository, OrderRepository}
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
                        # Epic 10, Story 10.2.2: alias now in alias field
                        imports.append(
                            Import(
                                module=full_module,
                                names=[],  # PHP use imports whole class
                                is_from=True,
                                alias=alias if alias else None,
                            )
                        )

    return imports


def _parse_include(node, source_bytes: bytes) -> Import | None:
    """Parse PHP include/require statements."""
    if node.type == "include_expression" or node.type == "require_expression":
        for child in node.children:
            if child.type == "string":
                module = get_node_text(child, source_bytes)
                # Remove quotes
                module = module.strip('\'"')
                return Import(module=module, names=[], is_from=False)
    return None
