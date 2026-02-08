"""PHP language parser.

This module provides PHP-specific parsing functionality using tree-sitter.
"""

from typing import Optional

from tree_sitter import Node, Tree

from ..parser import Call, CallType, Import, Inheritance, Symbol
from .base import BaseLanguageParser
from .utils import get_node_text


class PhpParser(BaseLanguageParser):
    """PHP language parser.

    Extracts symbols, imports, calls, and inheritances from PHP source code.
    Supports PHP classes, methods, properties, functions, and namespace handling.
    """

    def parse(self, path):
        """Parse a PHP source file.

        Overrides BaseLanguageParser.parse() to add namespace extraction.

        Args:
            path: Path to the source file

        Returns:
            ParseResult containing symbols, imports, calls, inheritances, and namespace
        """
        from pathlib import Path

        from ..parser import ParseResult

        try:
            source_bytes = Path(path).read_bytes()
        except Exception as e:
            return ParseResult(path=path, error=str(e), file_lines=0)

        # Calculate file lines
        file_lines = source_bytes.count(b"\n") + (
            1 if source_bytes and not source_bytes.endswith(b"\n") else 0
        )

        # Parse with tree-sitter
        tree = self.parser.parse(source_bytes)

        # Extract all information
        try:
            symbols = self.extract_symbols(tree, source_bytes)
            imports = self.extract_imports(tree, source_bytes)
            inheritances = self.extract_inheritances(tree, source_bytes)
            calls = self.extract_calls(tree, source_bytes, symbols, imports)

            # Extract namespace (PHP)
            namespace = ""
            root = tree.root_node
            for child in root.children:
                if child.type == "namespace_definition":
                    namespace = self._parse_php_namespace(child, source_bytes)
                    break

            return ParseResult(
                path=path,
                symbols=symbols,
                imports=imports,
                inheritances=inheritances,
                calls=calls,
                file_lines=file_lines,
                namespace=namespace,
            )
        except Exception as e:
            # Return partial result with error
            return ParseResult(
                path=path,
                error=f"Parse error: {str(e)}",
                file_lines=file_lines,
            )

    def extract_symbols(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract symbols (classes, functions, methods, properties) from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Symbol objects
        """
        symbols = []
        namespace = ""
        use_map = {}  # For tracking use statements
        inheritances = []  # For tracking inheritance relationships

        root = tree.root_node

        # First pass: Extract namespace and use statements
        for child in root.children:
            if child.type == "namespace_definition":
                namespace = self._parse_php_namespace(child, source_bytes)
            elif child.type == "namespace_use_declaration":
                imports = self._parse_php_use(child, source_bytes)
                # Build use map for class resolution
                for imp in imports:
                    if imp.alias:
                        use_map[imp.alias] = imp.module
                    else:
                        # Extract short name from module
                        short_name = imp.module.split("\\")[-1]
                        use_map[short_name] = imp.module

        # Second pass: Extract functions and classes
        for child in root.children:
            if child.type == "function_definition":
                symbol = self._parse_php_function(child, source_bytes)
                symbols.append(symbol)
            elif child.type == "class_declaration":
                # Pass namespace, use_map, and inheritances for inheritance extraction
                class_symbols = self._parse_php_class(
                    child, source_bytes, namespace, use_map, inheritances
                )
                symbols.extend(class_symbols)

        return symbols

    def extract_imports(self, tree: Tree, source_bytes: bytes) -> list:
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
                php_imports = self._parse_php_use(child, source_bytes)
                imports.extend(php_imports)
            elif child.type in ("include_expression", "require_expression"):
                php_import = self._parse_php_include(child, source_bytes)
                if php_import:
                    imports.append(php_import)

        return imports

    def extract_calls(
        self, tree: Tree, source_bytes: bytes, symbols: list, imports: list
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
                namespace = self._parse_php_namespace(child, source_bytes)
            elif child.type == "namespace_use_declaration":
                php_imports = self._parse_php_use(child, source_bytes)
                for imp in php_imports:
                    if imp.alias:
                        use_map[imp.alias] = imp.module
                    else:
                        short_name = imp.module.split("\\")[-1]
                        use_map[short_name] = imp.module

        # Extract inheritances for parent:: resolution
        for child in root.children:
            if child.type == "class_declaration":
                self._parse_php_class(child, source_bytes, namespace, use_map, inheritances)

        # Extract calls
        return self._extract_php_calls_from_tree(
            tree, source_bytes, imports, inheritances, namespace, use_map
        )

    def extract_inheritances(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract class inheritance relationships from the parse tree.

        Args:
            tree: The tree-sitter parse tree
            source_bytes: The source code as bytes

        Returns:
            List of Inheritance objects
        """
        inheritances = []
        namespace = ""
        use_map = {}

        root = tree.root_node

        # First pass: Extract namespace and use statements
        for child in root.children:
            if child.type == "namespace_definition":
                namespace = self._parse_php_namespace(child, source_bytes)
            elif child.type == "namespace_use_declaration":
                php_imports = self._parse_php_use(child, source_bytes)
                for imp in php_imports:
                    if imp.alias:
                        use_map[imp.alias] = imp.module
                    else:
                        short_name = imp.module.split("\\")[-1]
                        use_map[short_name] = imp.module

        # Second pass: Extract inheritances from classes
        for child in root.children:
            if child.type == "class_declaration":
                self._parse_php_class(child, source_bytes, namespace, use_map, inheritances)

        return inheritances

    # ==================== Private Helper Methods ====================

    def _extract_php_docstring(self, node, source_bytes: bytes) -> str:
        """Extract docstring from PHPDoc/DocComment or inline comments.

        For PHP, the comment is often a sibling node (previous sibling)
        rather than a child node.

        Supports:
        - PHPDoc blocks: /** ... */
        - Inline comments: // ...
        """
        # First check children (for class-level comments)
        for child in node.children:
            if child.type == "comment":
                text = get_node_text(child, source_bytes)
                if text.startswith("/**"):
                    return self._parse_phpdoc_text(text)
                elif text.startswith("//"):
                    # Inline comment: remove // and strip
                    return text[2:].strip()

        # Check previous sibling (for method-level comments)
        if node.prev_sibling and node.prev_sibling.type == "comment":
            text = get_node_text(node.prev_sibling, source_bytes)
            if text.startswith("/**"):
                return self._parse_phpdoc_text(text)
            elif text.startswith("//"):
                # Inline comment: remove // and strip
                return text[2:].strip()

        return ""

    def _parse_phpdoc_text(self, text: str) -> str:
        """Parse PHPDoc comment text and extract description.

        Extracts the first non-annotation line(s) from PHPDoc.
        Skips @param, @return, @throws, etc.

        Args:
            text: Raw PHPDoc comment text (/** ... */)

        Returns:
            Cleaned description text
        """
        # Handle single-line PHPDoc: /** Description */
        if "\n" not in text:
            # Remove /** and */
            content = text.strip()
            if content.startswith("/**"):
                content = content[3:]
            if content.endswith("*/"):
                content = content[:-2]
            content = content.strip()
            # Skip if it's only annotations
            if content.startswith("@"):
                return ""
            return content

        # Handle multi-line PHPDoc
        lines = text.split("\n")
        description_lines = []

        for line in lines[1:-1]:  # Skip first (/**) and last (*/) lines
            line = line.strip()
            # Remove leading * and whitespace
            if line.startswith("*"):
                line = line[1:].strip()

            # Skip empty lines
            if not line:
                continue

            # Skip annotation lines (@param, @return, etc.)
            if line.startswith("@"):
                break  # Stop at first annotation

            description_lines.append(line)

        return " ".join(description_lines)

    def _parse_php_function(self, node, source_bytes: bytes, class_name: str = "") -> Symbol:
        """Parse a PHP function definition node (standalone function, not method)."""
        name = ""
        params = ""
        return_type = ""

        for child in node.children:
            if child.type == "name":
                name = get_node_text(child, source_bytes)
            elif child.type == "formal_parameters":
                params = get_node_text(child, source_bytes)
            elif child.type in ("named_type", "primitive_type", "optional_type"):
                return_type = get_node_text(child, source_bytes)

        signature = f"function {name}{params}"
        if return_type:
            signature += f": {return_type}"

        docstring = self._extract_php_docstring(node, source_bytes)

        return Symbol(
            name=name,
            kind="function",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    def _parse_php_method(self, node, source_bytes: bytes, class_name: str) -> Symbol:
        """Parse a PHP method declaration node with visibility, static, and return type."""
        name = ""
        params = ""
        return_type = ""
        visibility = ""
        is_static = False

        for child in node.children:
            if child.type == "visibility_modifier":
                visibility = get_node_text(child, source_bytes)
            elif child.type == "static_modifier":
                is_static = True
            elif child.type == "name":
                name = get_node_text(child, source_bytes)
            elif child.type == "formal_parameters":
                params = get_node_text(child, source_bytes)
            elif child.type in ("named_type", "primitive_type", "optional_type"):
                return_type = get_node_text(child, source_bytes)

        # Build signature: [visibility] [static] function name(params)[: return_type]
        sig_parts = []
        if visibility:
            sig_parts.append(visibility)
        if is_static:
            sig_parts.append("static")
        sig_parts.append(f"function {name}{params}")
        signature = " ".join(sig_parts)
        if return_type:
            signature += f": {return_type}"

        docstring = self._extract_php_docstring(node, source_bytes)
        full_name = f"{class_name}::{name}"

        return Symbol(
            name=full_name,
            kind="method",
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    def _parse_php_property(self, node, source_bytes: bytes, class_name: str) -> Symbol:
        """Parse a PHP property declaration node."""
        prop_name = ""
        visibility = ""
        is_static = False
        prop_type = ""

        for child in node.children:
            if child.type == "visibility_modifier":
                visibility = get_node_text(child, source_bytes)
            elif child.type == "static_modifier":
                is_static = True
            elif child.type in ("named_type", "primitive_type", "optional_type"):
                prop_type = get_node_text(child, source_bytes)
            elif child.type == "property_element":
                for prop_child in child.children:
                    if prop_child.type == "variable_name":
                        prop_name = get_node_text(prop_child, source_bytes)

        # Build signature: [visibility] [static] [type] $name
        sig_parts = []
        if visibility:
            sig_parts.append(visibility)
        if is_static:
            sig_parts.append("static")
        if prop_type:
            sig_parts.append(prop_type)
        sig_parts.append(prop_name)
        signature = " ".join(sig_parts)

        full_name = f"{class_name}::{prop_name}"

        return Symbol(
            name=full_name,
            kind="property",
            signature=signature,
            docstring="",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    def _parse_php_class(
        self,
        node,
        source_bytes: bytes,
        namespace: str = "",
        use_map: dict[str, str] | None = None,
        inheritances: list[Inheritance] | None = None
    ) -> list[Symbol]:
        """Parse a PHP class definition node with extends, implements, properties and methods.

        Epic 10, Story 10.1.2: Added namespace, use_map, and inheritances parameters
        to support inheritance extraction for LoomGraph integration.

        Args:
            node: tree-sitter node for class_declaration
            source_bytes: Source code bytes
            namespace: Current namespace (e.g., "App\\Models")
            use_map: Mapping of short names to full qualified names from use statements
            inheritances: List to append Inheritance relationships to
        """
        if use_map is None:
            use_map = {}
        if inheritances is None:
            inheritances = []

        symbols = []
        class_name = ""
        extends = ""
        implements = []
        is_abstract = False
        is_final = False

        for child in node.children:
            if child.type == "name":
                class_name = get_node_text(child, source_bytes)
            elif child.type == "abstract_modifier":
                is_abstract = True
            elif child.type == "final_modifier":
                is_final = True
            elif child.type == "base_clause":
                # extends BaseClass
                for bc_child in child.children:
                    if bc_child.type == "name":
                        extends = get_node_text(bc_child, source_bytes)
            elif child.type == "class_interface_clause":
                # implements Interface1, Interface2
                for ic_child in child.children:
                    if ic_child.type == "name":
                        implements.append(get_node_text(ic_child, source_bytes))

        # Build full class name with namespace
        full_class_name = f"{namespace}\\{class_name}" if namespace else class_name

        # Create Inheritance objects (Epic 10, Story 10.1.2)
        if extends:
            # Resolve parent class full name using use_map
            parent_full_name = use_map.get(extends, f"{namespace}\\{extends}" if namespace else extends)
            inheritances.append(Inheritance(child=full_class_name, parent=parent_full_name))

        for interface in implements:
            # Resolve interface full name using use_map
            interface_full_name = use_map.get(
                interface, f"{namespace}\\{interface}" if namespace else interface
            )
            inheritances.append(Inheritance(child=full_class_name, parent=interface_full_name))

        # Build signature: [abstract|final] class Name [extends Base] [implements I1, I2]
        sig_parts = []
        if is_abstract:
            sig_parts.append("abstract")
        elif is_final:
            sig_parts.append("final")
        sig_parts.append(f"class {class_name}")
        if extends:
            sig_parts.append(f"extends {extends}")
        if implements:
            sig_parts.append(f"implements {', '.join(implements)}")
        signature = " ".join(sig_parts)

        docstring = self._extract_php_docstring(node, source_bytes)

        symbols.append(
            Symbol(
                name=class_name,
                kind="class",
                signature=signature,
                docstring=docstring,
                line_start=node.start_point[0] + 1,
                line_end=node.end_point[0] + 1,
            )
        )

        # Parse properties and methods from declaration_list
        for child in node.children:
            if child.type == "declaration_list":
                for decl in child.children:
                    if decl.type == "property_declaration":
                        prop = self._parse_php_property(decl, source_bytes, class_name)
                        symbols.append(prop)
                    elif decl.type == "method_declaration":
                        method = self._parse_php_method(decl, source_bytes, class_name)
                        symbols.append(method)

        return symbols

    def _parse_php_include(self, node, source_bytes: bytes) -> Import | None:
        """Parse PHP include/require statements."""
        if node.type == "include_expression" or node.type == "require_expression":
            for child in node.children:
                if child.type == "string":
                    module = get_node_text(child, source_bytes)
                    # Remove quotes
                    module = module.strip('\'"')
                    return Import(module=module, names=[], is_from=False)
        return None

    def _parse_php_namespace(self, node, source_bytes: bytes) -> str:
        """Parse PHP namespace definition."""
        for child in node.children:
            if child.type == "namespace_name":
                return get_node_text(child, source_bytes)
        return ""

    def _parse_php_use(self, node, source_bytes: bytes) -> list[Import]:
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

    # ==================== Call Extraction Methods ====================

    def _extract_php_calls_from_tree(
        self,
        tree,
        source_bytes: bytes,
        imports: list[Import],
        inheritances: list[Inheritance],
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
                        self._extract_php_calls(
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
                                self._extract_php_calls(
                                    method_node, source_bytes, caller,
                                    use_map, namespace, parent_map, full_class_name
                                )
                            )

        return calls

    def _extract_php_calls(
        self,
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
                call = self._parse_php_function_call(
                    n, source_bytes, caller, use_map, namespace
                )
                if call:
                    calls.append(call)

            # Member call expression ($obj->method())
            elif n.type == "member_call_expression":
                call = self._parse_php_member_call(
                    n, source_bytes, caller, use_map, namespace, current_class
                )
                if call:
                    calls.append(call)

            # Scoped call expression (Class::method())
            elif n.type == "scoped_call_expression":
                call = self._parse_php_scoped_call(
                    n, source_bytes, caller, use_map, namespace, parent_map, current_class
                )
                if call:
                    calls.append(call)

            # Object creation (new Class())
            elif n.type == "object_creation_expression":
                call = self._parse_php_object_creation(
                    n, source_bytes, caller, use_map, namespace
                )
                if call:
                    calls.append(call)

            # Recurse into children
            for child in n.children:
                traverse(child)

        traverse(node)
        return calls

    def _parse_php_function_call(
        self,
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

    def _parse_php_member_call(
        self,
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

    def _parse_php_scoped_call(
        self,
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

    def _parse_php_object_creation(
        self,
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
