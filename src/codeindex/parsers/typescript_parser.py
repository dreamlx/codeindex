"""TypeScript/JavaScript language parser.

This module provides parsing for TypeScript (.ts), TSX (.tsx),
JavaScript (.js), and JSX (.jsx) files using tree-sitter.

A single TypeScriptParser class handles all 4 file types with 3 grammar variants:
- .ts  → tree-sitter-typescript (language_typescript)
- .tsx → tree-sitter-typescript (language_tsx)
- .js/.jsx → tree-sitter-javascript (language)
"""

from pathlib import Path

from tree_sitter import Language, Node, Parser, Tree

from ..parser import Call, CallType, Import, Inheritance, Symbol
from .base import BaseLanguageParser
from .utils import get_node_text


class TypeScriptParser(BaseLanguageParser):
    """TypeScript/JavaScript language parser.

    Handles .ts, .tsx, .js, .jsx files using the appropriate tree-sitter grammar.
    Extracts symbols, imports, calls, and inheritances.
    """

    # Grammar routing: extension → (grammar_name, grammar_loader)
    GRAMMAR_MAP = {
        ".ts": "typescript",
        ".tsx": "tsx",
        ".js": "javascript",
        ".jsx": "javascript",
    }

    def __init__(self, parser: Parser, grammar_name: str = "typescript"):
        """Initialize the TypeScript parser.

        Args:
            parser: A configured tree-sitter Parser
            grammar_name: One of 'typescript', 'tsx', 'javascript'
        """
        super().__init__(parser)
        self.grammar_name = grammar_name

    @staticmethod
    def create_for_file(file_path: Path) -> "TypeScriptParser":
        """Create a TypeScriptParser configured for the given file extension.

        Args:
            file_path: Path to the source file

        Returns:
            TypeScriptParser with correct grammar loaded
        """
        ext = file_path.suffix.lower()
        grammar_name = TypeScriptParser.GRAMMAR_MAP.get(ext, "typescript")

        if grammar_name == "typescript":
            import tree_sitter_typescript as ts_ts
            lang = Language(ts_ts.language_typescript())
        elif grammar_name == "tsx":
            import tree_sitter_typescript as ts_ts
            lang = Language(ts_ts.language_tsx())
        elif grammar_name == "javascript":
            import tree_sitter_javascript as ts_js
            lang = Language(ts_js.language())
        else:
            raise ValueError(f"Unknown grammar: {grammar_name}")

        parser = Parser(lang)
        return TypeScriptParser(parser, grammar_name)

    def parse(self, path: Path):
        """Parse a TypeScript/JavaScript source file.

        Overrides BaseLanguageParser.parse() to add module_docstring extraction.
        """
        from ..parser import ParseResult

        try:
            source_bytes = Path(path).read_bytes()
        except Exception as e:
            return ParseResult(path=path, error=str(e), file_lines=0)

        file_lines = source_bytes.count(b"\n") + (
            1 if source_bytes and not source_bytes.endswith(b"\n") else 0
        )

        if not source_bytes.strip():
            return ParseResult(path=path, file_lines=file_lines)

        tree = self.parser.parse(source_bytes)

        if tree.root_node.has_error:
            return ParseResult(
                path=path,
                error="Syntax error in source file",
                file_lines=file_lines,
            )

        try:
            symbols = self.extract_symbols(tree, source_bytes)
            imports = self.extract_imports(tree, source_bytes)
            inheritances = self.extract_inheritances(tree, source_bytes)
            calls = self.extract_calls(tree, source_bytes, symbols, imports)
            module_docstring = self._extract_module_docstring(tree, source_bytes)

            return ParseResult(
                path=path,
                symbols=symbols,
                imports=imports,
                inheritances=inheritances,
                calls=calls,
                file_lines=file_lines,
                module_docstring=module_docstring,
            )
        except Exception as e:
            return ParseResult(
                path=path,
                error=f"Parse error: {str(e)}",
                file_lines=file_lines,
            )

    # ==================== Symbol Extraction ====================

    def extract_symbols(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract symbols from the parse tree."""
        symbols = []
        root = tree.root_node

        for child in root.children:
            symbols.extend(self._extract_node_symbols(child, source_bytes))

        return symbols

    def _extract_node_symbols(
        self, node: Node, source_bytes: bytes, class_name: str = ""
    ) -> list[Symbol]:
        """Extract symbols from a single AST node."""
        symbols = []

        if node.type == "function_declaration":
            sym = self._parse_function_declaration(node, source_bytes)
            if sym:
                symbols.append(sym)

        elif node.type == "generator_function_declaration":
            sym = self._parse_function_declaration(node, source_bytes)
            if sym:
                symbols.append(sym)

        elif node.type == "class_declaration":
            symbols.extend(self._parse_class_declaration(node, source_bytes))

        elif node.type == "abstract_class_declaration":
            symbols.extend(self._parse_class_declaration(node, source_bytes, abstract=True))

        elif node.type == "interface_declaration":
            sym = self._parse_interface_declaration(node, source_bytes)
            if sym:
                symbols.append(sym)

        elif node.type == "enum_declaration":
            sym = self._parse_enum_declaration(node, source_bytes)
            if sym:
                symbols.append(sym)

        elif node.type == "type_alias_declaration":
            sym = self._parse_type_alias(node, source_bytes)
            if sym:
                symbols.append(sym)

        elif node.type == "lexical_declaration":
            symbols.extend(self._parse_lexical_declaration(node, source_bytes))

        elif node.type == "export_statement":
            # Extract symbols from exported declarations
            for child in node.children:
                symbols.extend(self._extract_node_symbols(child, source_bytes, class_name))

        elif node.type == "module" and self.grammar_name != "javascript":
            # TypeScript namespace/module
            sym = self._parse_namespace(node, source_bytes)
            if sym:
                symbols.append(sym)

        elif node.type == "internal_module":
            sym = self._parse_namespace(node, source_bytes)
            if sym:
                symbols.append(sym)

        elif node.type == "expression_statement":
            # Namespace declarations are wrapped in expression_statement
            for child in node.children:
                symbols.extend(self._extract_node_symbols(child, source_bytes, class_name))

        return symbols

    def _parse_function_declaration(
        self, node: Node, source_bytes: bytes
    ) -> Symbol | None:
        """Parse a function declaration node."""
        name = ""
        params = ""
        is_async = False
        is_generator = False

        for child in node.children:
            if child.type == "identifier":
                name = get_node_text(child, source_bytes)
            elif child.type == "formal_parameters":
                params = get_node_text(child, source_bytes)
            elif child.type == "async":
                is_async = True
            elif child.type == "*":
                is_generator = True

        # Also detect generator from node type
        if node.type == "generator_function_declaration":
            is_generator = True

        if not name:
            return None

        sig_parts = []
        if is_async:
            sig_parts.append("async")
        sig_parts.append("function")
        if is_generator:
            sig_parts.append("*")
        sig_parts.append(f"{name}{params}")

        # Add return type if present
        return_type = self._find_type_annotation(node, source_bytes)
        if return_type:
            sig_parts.append(f": {return_type}")

        return Symbol(
            name=name,
            kind="function",
            signature=" ".join(sig_parts),
            docstring=self._extract_jsdoc(node, source_bytes),
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    def _parse_class_declaration(
        self, node: Node, source_bytes: bytes, abstract: bool = False
    ) -> list[Symbol]:
        """Parse a class declaration node."""
        symbols = []
        class_name = ""
        type_params = ""
        extends = ""
        implements_list = []

        for child in node.children:
            if child.type in ("type_identifier", "identifier"):
                class_name = get_node_text(child, source_bytes)
            elif child.type == "type_parameters":
                type_params = get_node_text(child, source_bytes)
            elif child.type == "class_heritage":
                extends, implements_list = self._parse_class_heritage(child, source_bytes)

        if not class_name:
            return symbols

        sig_parts = []
        if abstract:
            sig_parts.append("abstract")
        sig_parts.append("class")
        sig_parts.append(class_name + type_params if type_params else class_name)
        if extends:
            sig_parts.append(f"extends {extends}")
        if implements_list:
            sig_parts.append(f"implements {', '.join(implements_list)}")

        symbols.append(Symbol(
            name=class_name,
            kind="class",
            signature=" ".join(sig_parts),
            docstring=self._extract_jsdoc(node, source_bytes),
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        ))

        # Extract class body members
        for child in node.children:
            if child.type == "class_body":
                symbols.extend(self._parse_class_body(child, source_bytes, class_name))

        return symbols

    def _parse_class_heritage(
        self, node: Node, source_bytes: bytes
    ) -> tuple[str, list[str]]:
        """Parse class_heritage node to extract extends and implements."""
        extends = ""
        implements_list = []

        for child in node.children:
            if child.type == "extends_clause":
                for ext_child in child.children:
                    if ext_child.type in ("identifier", "type_identifier", "generic_type"):
                        extends = get_node_text(ext_child, source_bytes)
            elif child.type == "implements_clause":
                for impl_child in child.children:
                    if impl_child.type in ("type_identifier", "generic_type"):
                        implements_list.append(get_node_text(impl_child, source_bytes))

        return extends, implements_list

    def _parse_class_body(
        self, node: Node, source_bytes: bytes, class_name: str
    ) -> list[Symbol]:
        """Parse class body members."""
        symbols = []

        for child in node.children:
            if child.type == "method_definition":
                sym = self._parse_method_definition(child, source_bytes, class_name)
                if sym:
                    symbols.append(sym)
            elif child.type == "public_field_definition":
                sym = self._parse_field_definition(child, source_bytes, class_name)
                if sym:
                    symbols.append(sym)

        return symbols

    def _parse_method_definition(
        self, node: Node, source_bytes: bytes, class_name: str
    ) -> Symbol | None:
        """Parse a method definition node."""
        name = ""
        params = ""
        is_async = False
        is_static = False
        is_getter = False
        is_setter = False
        accessibility = ""

        for child in node.children:
            if child.type == "property_identifier":
                name = get_node_text(child, source_bytes)
            elif child.type == "formal_parameters":
                params = get_node_text(child, source_bytes)
            elif child.type == "async":
                is_async = True
            elif child.type == "static":
                is_static = True
            elif child.type == "get":
                is_getter = True
            elif child.type == "set":
                is_setter = True
            elif child.type == "accessibility_modifier":
                accessibility = get_node_text(child, source_bytes)

        if not name:
            return None

        # Determine kind
        if name == "constructor":
            kind = "constructor"
        else:
            kind = "method"

        full_name = f"{class_name}.{name}"

        # Build signature
        sig_parts = []
        if accessibility:
            sig_parts.append(accessibility)
        if is_static:
            sig_parts.append("static")
        if is_async:
            sig_parts.append("async")
        if is_getter:
            sig_parts.append("get")
        if is_setter:
            sig_parts.append("set")
        sig_parts.append(f"{name}{params}")

        return_type = self._find_type_annotation(node, source_bytes)
        if return_type:
            sig_parts.append(f": {return_type}")

        return Symbol(
            name=full_name,
            kind=kind,
            signature=" ".join(sig_parts),
            docstring=self._extract_jsdoc(node, source_bytes),
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    def _parse_field_definition(
        self, node: Node, source_bytes: bytes, class_name: str
    ) -> Symbol | None:
        """Parse a class field definition."""
        name = ""
        accessibility = ""

        for child in node.children:
            if child.type == "property_identifier":
                name = get_node_text(child, source_bytes)
            elif child.type == "accessibility_modifier":
                accessibility = get_node_text(child, source_bytes)

        if not name:
            return None

        full_name = f"{class_name}.{name}"

        sig_parts = []
        if accessibility:
            sig_parts.append(accessibility)
        sig_parts.append(name)

        type_ann = self._find_type_annotation(node, source_bytes)
        if type_ann:
            sig_parts.append(f": {type_ann}")

        return Symbol(
            name=full_name,
            kind="field",
            signature=" ".join(sig_parts),
            docstring="",
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    def _parse_interface_declaration(
        self, node: Node, source_bytes: bytes
    ) -> Symbol | None:
        """Parse an interface declaration."""
        name = ""
        type_params = ""
        extends_list = []

        for child in node.children:
            if child.type == "type_identifier":
                name = get_node_text(child, source_bytes)
            elif child.type == "type_parameters":
                type_params = get_node_text(child, source_bytes)
            elif child.type == "extends_type_clause":
                for ext_child in child.children:
                    if ext_child.type in ("type_identifier", "generic_type"):
                        extends_list.append(get_node_text(ext_child, source_bytes))

        if not name:
            return None

        sig_parts = ["interface"]
        sig_parts.append(name + type_params if type_params else name)
        if extends_list:
            sig_parts.append(f"extends {', '.join(extends_list)}")

        return Symbol(
            name=name,
            kind="interface",
            signature=" ".join(sig_parts),
            docstring=self._extract_jsdoc(node, source_bytes),
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    def _parse_enum_declaration(
        self, node: Node, source_bytes: bytes
    ) -> Symbol | None:
        """Parse an enum declaration."""
        name = ""
        is_const = False

        for child in node.children:
            if child.type == "identifier":
                name = get_node_text(child, source_bytes)
            elif child.type == "const":
                is_const = True

        if not name:
            return None

        sig_parts = []
        if is_const:
            sig_parts.append("const")
        sig_parts.append("enum")
        sig_parts.append(name)

        return Symbol(
            name=name,
            kind="enum",
            signature=" ".join(sig_parts),
            docstring=self._extract_jsdoc(node, source_bytes),
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    def _parse_type_alias(
        self, node: Node, source_bytes: bytes
    ) -> Symbol | None:
        """Parse a type alias declaration."""
        name = ""
        type_params = ""

        for child in node.children:
            if child.type == "type_identifier":
                name = get_node_text(child, source_bytes)
            elif child.type == "type_parameters":
                type_params = get_node_text(child, source_bytes)

        if not name:
            return None

        sig = f"type {name}{type_params}" if type_params else f"type {name}"

        return Symbol(
            name=name,
            kind="type_alias",
            signature=sig,
            docstring=self._extract_jsdoc(node, source_bytes),
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    def _parse_lexical_declaration(
        self, node: Node, source_bytes: bytes
    ) -> list[Symbol]:
        """Parse const/let/var declaration, distinguishing arrow functions from variables."""
        symbols = []
        decl_keyword = ""

        for child in node.children:
            if child.type in ("const", "let", "var"):
                decl_keyword = child.type
            elif child.type == "variable_declarator":
                sym = self._parse_variable_declarator(child, source_bytes, decl_keyword)
                if sym:
                    symbols.append(sym)

        return symbols

    def _parse_variable_declarator(
        self, node: Node, source_bytes: bytes, decl_keyword: str
    ) -> Symbol | None:
        """Parse a variable_declarator node."""
        name = ""
        value_node = None

        for child in node.children:
            if child.type == "identifier":
                name = get_node_text(child, source_bytes)
            elif child.type in ("arrow_function", "function"):
                value_node = child

        if not name:
            return None

        if value_node and value_node.type == "arrow_function":
            # Arrow function → function symbol
            params = ""
            is_async = False
            for child in value_node.children:
                if child.type == "formal_parameters":
                    params = get_node_text(child, source_bytes)
                elif child.type == "async":
                    is_async = True
                elif child.type == "identifier" and not params:
                    # Single param arrow: (x) => ... or x => ...
                    params = f"({get_node_text(child, source_bytes)})"

            sig_parts = [decl_keyword]
            if is_async:
                sig_parts.append("async")
            sig_parts.append(f"{name} = {params} =>")

            return_type = self._find_type_annotation(node, source_bytes)
            if return_type:
                sig_parts[-1] = f"{name}: {return_type} = {params} =>"

            return Symbol(
                name=name,
                kind="function",
                signature=" ".join(sig_parts),
                docstring=self._extract_jsdoc(node.parent, source_bytes) if node.parent else "",
                line_start=node.parent.start_point[0] + 1 if node.parent else node.start_point[0] + 1,
                line_end=node.parent.end_point[0] + 1 if node.parent else node.end_point[0] + 1,
            )
        else:
            # Regular variable
            sig_parts = [decl_keyword, name]
            type_ann = self._find_type_annotation(node, source_bytes)
            if type_ann:
                sig_parts.append(f": {type_ann}")

            return Symbol(
                name=name,
                kind="variable",
                signature=" ".join(sig_parts),
                docstring="",
                line_start=node.parent.start_point[0] + 1 if node.parent else node.start_point[0] + 1,
                line_end=node.parent.end_point[0] + 1 if node.parent else node.end_point[0] + 1,
            )

    def _parse_namespace(
        self, node: Node, source_bytes: bytes
    ) -> Symbol | None:
        """Parse a namespace/module declaration."""
        name = ""

        for child in node.children:
            if child.type == "identifier":
                name = get_node_text(child, source_bytes)

        if not name:
            return None

        return Symbol(
            name=name,
            kind="namespace",
            signature=f"namespace {name}",
            docstring=self._extract_jsdoc(node, source_bytes),
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
        )

    # ==================== Import Extraction ====================

    def extract_imports(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract import/export-from statements."""
        imports = []
        root = tree.root_node

        for child in root.children:
            if child.type == "import_statement":
                imports.extend(self._parse_import_statement(child, source_bytes))
            elif child.type == "export_statement":
                imports.extend(self._parse_export_as_import(child, source_bytes))
            elif child.type == "lexical_declaration":
                # CommonJS require
                imp = self._parse_require(child, source_bytes)
                if imp:
                    imports.append(imp)

        return imports

    def _parse_import_statement(
        self, node: Node, source_bytes: bytes
    ) -> list[Import]:
        """Parse an import statement node."""
        imports = []
        module = ""
        import_clause = None

        for child in node.children:
            if child.type == "string":
                module = self._extract_string_content(child, source_bytes)
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
        self, node: Node, source_bytes: bytes
    ) -> list[Import]:
        """Parse export statements that re-export from another module."""
        imports = []
        module = ""
        has_from = False
        names = []
        is_wildcard = False

        for child in node.children:
            if child.type == "string":
                module = self._extract_string_content(child, source_bytes)
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
        self, node: Node, source_bytes: bytes
    ) -> Import | None:
        """Parse CommonJS require: const X = require('module')."""
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
                                        req_module = self._extract_string_content(
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

    # ==================== Inheritance Extraction ====================

    def extract_inheritances(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract class/interface inheritance relationships."""
        inheritances = []
        root = tree.root_node

        for child in root.children:
            self._extract_inheritances_from_node(child, source_bytes, inheritances)

        return inheritances

    def _extract_inheritances_from_node(
        self, node: Node, source_bytes: bytes, inheritances: list[Inheritance]
    ):
        """Recursively extract inheritance from a node."""
        if node.type in ("class_declaration", "abstract_class_declaration"):
            class_name = ""
            for child in node.children:
                if child.type in ("type_identifier", "identifier"):
                    class_name = get_node_text(child, source_bytes)
                elif child.type == "class_heritage" and class_name:
                    extends, implements_list = self._parse_class_heritage(child, source_bytes)
                    if extends:
                        # Strip generic params for inheritance
                        parent = self._strip_generic_type(extends)
                        inheritances.append(Inheritance(child=class_name, parent=parent))
                    for impl in implements_list:
                        parent = self._strip_generic_type(impl)
                        inheritances.append(Inheritance(child=class_name, parent=parent))

        elif node.type == "interface_declaration":
            iface_name = ""
            for child in node.children:
                if child.type == "type_identifier":
                    iface_name = get_node_text(child, source_bytes)
                elif child.type == "extends_type_clause" and iface_name:
                    for ext_child in child.children:
                        if ext_child.type in ("type_identifier", "generic_type"):
                            parent = self._strip_generic_type(
                                get_node_text(ext_child, source_bytes)
                            )
                            inheritances.append(Inheritance(child=iface_name, parent=parent))

        elif node.type == "export_statement":
            for child in node.children:
                self._extract_inheritances_from_node(child, source_bytes, inheritances)

    # ==================== Import-Aware Call Resolution ====================

    def _build_import_map(self, imports: list[Import]) -> dict[str, str]:
        """Build local-name-to-module mapping from imports.

        Examples:
            import { X } from './module'       → { "X": "./module.X" }
            import X from './module'           → { "X": "./module" }  (default)
            import * as X from './module'      → { "X": "./module" }  (namespace)
            const { X } = require('./module')  → { "X": "./module.X" }
        """
        import_map: dict[str, str] = {}
        for imp in imports:
            if imp.is_from and imp.names:
                if imp.names == ["*"] and imp.alias:
                    # Namespace import: import * as X from './module'
                    import_map[imp.alias] = imp.module
                elif len(imp.names) == 1 and imp.alias == imp.names[0]:
                    # Default import: import X from './module'
                    import_map[imp.alias] = imp.module
                else:
                    # Named imports: import { A, B } from './module'
                    for name in imp.names:
                        import_map[name] = f"{imp.module}.{name}"
            elif not imp.is_from and imp.alias and imp.names:
                # CommonJS: const { X } = require('./module') or const X = require('./module')
                for name in imp.names:
                    import_map[name] = f"{imp.module}.{name}"
            elif not imp.is_from and imp.alias and not imp.names:
                # CommonJS whole module: const X = require('./module')
                import_map[imp.alias] = imp.module
        return import_map

    def _resolve_callee(self, callee: str, import_map: dict[str, str]) -> str:
        """Resolve callee name using import map.

        - Direct match: executeToolCall → ./tool-executor.executeToolCall
        - Prefix match: LLMClient.chat → ./llm-client.LLMClient.chat
        - Skip this.xxx / super.xxx (instance calls)
        """
        if not callee or not import_map:
            return callee

        # Skip this.xxx and super.xxx
        if callee.startswith(("this.", "super.")):
            return callee

        # Direct match
        if callee in import_map:
            return import_map[callee]

        # Prefix match: split on first dot
        if "." in callee:
            prefix, suffix = callee.split(".", 1)
            if prefix in import_map:
                resolved_prefix = import_map[prefix]
                return f"{resolved_prefix}.{suffix}"

        return callee

    # ==================== Call Extraction ====================

    def extract_calls(
        self, tree: Tree, source_bytes: bytes, symbols: list, imports: list
    ) -> list:
        """Extract function/method call relationships."""
        calls = []
        root = tree.root_node
        import_map = self._build_import_map(imports)

        for child in root.children:
            self._extract_calls_from_node(child, source_bytes, "", calls, import_map)

        return calls

    def _extract_calls_from_node(
        self, node: Node, source_bytes: bytes, caller: str, calls: list[Call],
        import_map: dict[str, str] | None = None,
    ):
        """Recursively extract calls from AST nodes."""
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
                                    self._extract_calls_from_node(
                                        body_child, source_bytes, method_caller, calls, import_map
                                    )
                return

        elif node.type == "export_statement":
            for child in node.children:
                self._extract_calls_from_node(child, source_bytes, caller, calls, import_map)
            return

        # Extract call from current node
        if node.type == "call_expression":
            call = self._parse_call_expression(node, source_bytes, current_caller, import_map)
            if call:
                calls.append(call)

        elif node.type == "new_expression":
            call = self._parse_new_expression(node, source_bytes, current_caller, import_map)
            if call:
                calls.append(call)

        # Recurse into children
        for child in node.children:
            if child.type not in ("class_declaration", "abstract_class_declaration",
                                  "function_declaration", "generator_function_declaration"):
                self._extract_calls_from_node(child, source_bytes, current_caller, calls, import_map)

    def _parse_call_expression(
        self, node: Node, source_bytes: bytes, caller: str,
        import_map: dict[str, str] | None = None,
    ) -> Call | None:
        """Parse a call_expression node."""
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

        # Resolve callee using import map
        if import_map:
            callee_text = self._resolve_callee(callee_text, import_map)

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
        self, node: Node, source_bytes: bytes, caller: str,
        import_map: dict[str, str] | None = None,
    ) -> Call | None:
        """Parse a new_expression (constructor call)."""
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

        # Resolve type name using import map
        if import_map:
            type_name = self._resolve_callee(type_name, import_map)

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

    # ==================== Helper Methods ====================

    def _strip_generic_type(self, type_name: str) -> str:
        """Strip generic type parameters: 'Map<string, User>' → 'Map'."""
        idx = type_name.find("<")
        if idx >= 0:
            return type_name[:idx].strip()
        return type_name

    def _extract_string_content(self, node: Node, source_bytes: bytes) -> str:
        """Extract string content from a string node (strip quotes)."""
        for child in node.children:
            if child.type == "string_fragment":
                return get_node_text(child, source_bytes)
        # Fallback: strip quotes manually
        text = get_node_text(node, source_bytes)
        if len(text) >= 2 and text[0] in ("'", '"', '`') and text[-1] in ("'", '"', '`'):
            return text[1:-1]
        return text

    def _find_type_annotation(self, node: Node, source_bytes: bytes) -> str:
        """Find type annotation child of a node."""
        for child in node.children:
            if child.type == "type_annotation":
                # Extract the type part (skip the colon)
                for type_child in child.children:
                    if type_child.type != ":":
                        return get_node_text(type_child, source_bytes)
        return ""

    def _extract_jsdoc(self, node: Node, source_bytes: bytes) -> str:
        """Extract JSDoc comment preceding a node."""
        if node is None:
            return ""

        # Check previous sibling for comment
        if hasattr(node, "prev_sibling") and node.prev_sibling:
            prev = node.prev_sibling
            if prev.type == "comment":
                text = get_node_text(prev, source_bytes)
                if text.startswith("/**"):
                    return text[3:-2].strip()

        return ""

    def _extract_module_docstring(self, tree: Tree, source_bytes: bytes) -> str:
        """Extract module-level JSDoc comment (first comment in file)."""
        root = tree.root_node
        if root.children:
            first = root.children[0]
            if first.type == "comment":
                text = get_node_text(first, source_bytes)
                if text.startswith("/**"):
                    return text[3:-2].strip()
        return ""


# ==================== Backward Compatibility Functions ====================


def is_typescript_file(path: str) -> bool:
    """Check if file is a TypeScript/JavaScript source file."""
    return any(path.endswith(ext) for ext in (".ts", ".tsx", ".js", ".jsx"))


def get_typescript_parser():
    """Get the TypeScript parser instance (lazy loading)."""
    from ..parser import _get_parser
    return _get_parser("typescript")
