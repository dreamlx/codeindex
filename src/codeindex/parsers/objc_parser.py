"""Objective-C language parser (Story 3.1).

This parser extracts symbols from Objective-C source files (.h and .m):
- @interface declarations (headers)
- @implementation (implementation files)
- Instance methods (-)
- Class methods (+)
- Properties (@property)
- Import statements (#import)
- Inheritance relationships

Epic: #23
Story: 3.1
"""

import re
from pathlib import Path

from tree_sitter import Parser, Tree

from ..parser import Import, Inheritance, Symbol
from .base import BaseLanguageParser
from .utils import get_node_text


class ObjCParser(BaseLanguageParser):
    """Objective-C language parser.

    Supports both header files (.h) and implementation files (.m).
    Parses @interface and @implementation declarations with methods and properties.
    """

    def __init__(self, parser: Parser):
        """Initialize Objective-C parser.

        Args:
            parser: Tree-sitter parser configured for Objective-C
        """
        super().__init__(parser)

    def _preprocess_source(self, source_bytes: bytes) -> bytes:
        """Preprocess Objective-C source to handle unsupported macros.

        tree-sitter-objc doesn't support some Apple framework macros like:
        - NS_ASSUME_NONNULL_BEGIN/END
        - NS_SWIFT_NAME()
        - __attribute__()

        We replace these with comments to preserve line numbers for symbol locations.

        Args:
            source_bytes: Original source code

        Returns:
            Preprocessed source code with macros commented out
        """
        source = source_bytes.decode('utf-8', errors='replace')

        # Replace nullability macros with comments (preserve line numbers)
        source = re.sub(r'\bNS_ASSUME_NONNULL_BEGIN\b', '// NS_ASSUME_NONNULL_BEGIN', source)
        source = re.sub(r'\bNS_ASSUME_NONNULL_END\b', '// NS_ASSUME_NONNULL_END', source)

        # Comment out NS_SWIFT_NAME() - keep on same line
        source = re.sub(r'\bNS_SWIFT_NAME\([^)]*\)', '', source)

        # Comment out common attributes that cause issues
        source = re.sub(r'__attribute__\s*\([^)]*\)', '', source)
        source = re.sub(r'\b__deprecated\b', '', source)

        return source.encode('utf-8')

    def parse(self, path: Path):
        """Parse Objective-C source file with preprocessing.

        Override base parse() to add preprocessing step for Apple framework macros.

        Args:
            path: Path to source file

        Returns:
            ParseResult with extracted symbols
        """
        # Import here to avoid circular dependency
        from ..parser import ParseResult

        try:
            source_bytes = path.read_bytes()
        except Exception as e:
            return ParseResult(path=path, error=str(e), file_lines=0)

        # Calculate file lines
        file_lines = source_bytes.count(b"\n") + (
            1 if source_bytes and not source_bytes.endswith(b"\n") else 0
        )

        # Preprocess source to handle unsupported macros
        preprocessed_bytes = self._preprocess_source(source_bytes)

        # Parse with tree-sitter
        tree = self.parser.parse(preprocessed_bytes)

        # Check for syntax errors
        if tree.root_node.has_error:
            return ParseResult(
                path=path,
                error="Syntax error in source file",
                file_lines=file_lines,
            )

        # Extract all information (use preprocessed bytes for extraction)
        try:
            symbols = self.extract_symbols(tree, preprocessed_bytes)
            imports = self.extract_imports(tree, preprocessed_bytes)
            inheritances = self.extract_inheritances(tree, preprocessed_bytes)
            calls = self.extract_calls(tree, preprocessed_bytes, symbols, imports)

            return ParseResult(
                path=path,
                symbols=symbols,
                imports=imports,
                inheritances=inheritances,
                calls=calls,
                file_lines=file_lines,
            )
        except Exception as e:
            # Return partial result with error
            return ParseResult(
                path=path,
                symbols=[],
                imports=[],
                inheritances=[],
                calls=[],
                error=f"Failed to extract symbols: {e}",
                file_lines=file_lines,
            )

    def extract_symbols(self, tree: Tree, source_bytes: bytes) -> list:
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
                symbols.extend(self._extract_interface(child, source_bytes))

            # @implementation (usually in .m files)
            elif child.type == "class_implementation":
                symbols.extend(self._extract_implementation(child, source_bytes))

            # @protocol declarations (Story 3.3)
            elif child.type == "protocol_declaration":
                symbols.extend(self._extract_protocol(child, source_bytes))

        return symbols

    def _extract_interface(self, node, source_bytes: bytes) -> list[Symbol]:
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
        signature = self._build_interface_signature(node, source_bytes, class_name)
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
                prop_sym = self._extract_property(child, source_bytes, class_name)
                if prop_sym:
                    symbols.append(prop_sym)
            elif child.type == "method_declaration":
                method_sym = self._extract_method(child, source_bytes, class_name)
                if method_sym:
                    symbols.append(method_sym)
            elif child.type == "declaration_list":
                symbols.extend(
                    self._extract_declarations(child, source_bytes, class_name)
                )

        return symbols

    def _extract_implementation(self, node, source_bytes: bytes) -> list[Symbol]:
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
                        method_sym = self._extract_method(subchild, source_bytes, class_name)
                        if method_sym:
                            symbols.append(method_sym)
            elif child.type in ("method_definition", "function_definition"):
                # Fallback for direct children
                method_sym = self._extract_method(child, source_bytes, class_name)
                if method_sym:
                    symbols.append(method_sym)

        return symbols

    def _extract_declarations(
        self, decl_list_node, source_bytes: bytes, class_name: str
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
                method_sym = self._extract_method(child, source_bytes, class_name)
                if method_sym:
                    symbols.append(method_sym)

            elif child.type == "property_declaration":
                prop_sym = self._extract_property(child, source_bytes, class_name)
                if prop_sym:
                    symbols.append(prop_sym)

        return symbols

    def _extract_method(
        self, node, source_bytes: bytes, class_name: str
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
        signature = self._build_method_signature(node, source_bytes, is_class_method)

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
        self, node, source_bytes: bytes, class_name: str
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
        self, node, source_bytes: bytes, class_name: str
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
        self, node, source_bytes: bytes, is_class_method: bool
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

    def extract_imports(self, tree: Tree, source_bytes: bytes) -> list:
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
                import_obj = self._extract_import(child, source_bytes)
                if import_obj:
                    imports.append(import_obj)

        return imports

    def _extract_import(self, node, source_bytes: bytes) -> Import | None:
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

    def extract_inheritances(self, tree: Tree, source_bytes: bytes) -> list:
        """Extract inheritance relationships from Objective-C code.

        Args:
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes

        Returns:
            List of Inheritance objects
        """
        inheritances = []
        root = tree.root_node

        for child in root.children:
            if child.type == "class_interface":
                inheritances.extend(self._extract_interface_inheritance(child, source_bytes))
            elif child.type == "protocol_declaration":
                inheritances.extend(self._extract_protocol_inheritance(child, source_bytes))

        return inheritances

    def _extract_interface_inheritance(self, node, source_bytes: bytes) -> list[Inheritance]:
        """Extract inheritance from @interface.

        Args:
            node: class_interface node
            source_bytes: Source code bytes

        Returns:
            List of Inheritance objects
        """
        inheritances = []

        # Get class name (first identifier)
        class_name = None
        for child in node.children:
            if child.type == "identifier":
                class_name = get_node_text(child, source_bytes)
                break

        if not class_name:
            return inheritances

        # Extract superclass (second identifier after ':')
        found_colon = False
        for child in node.children:
            if child.type == ":":
                found_colon = True
            elif found_colon and child.type == "identifier":
                superclass = get_node_text(child, source_bytes)
                inheritances.append(
                    Inheritance(child=class_name, parent=superclass)
                )
                break

        # Extract protocol conformances (from parameterized_arguments)
        for child in node.children:
            if child.type == "parameterized_arguments":
                for subchild in child.children:
                    if subchild.type == "type_name":
                        # Get type_identifier from type_name
                        for type_child in subchild.children:
                            if type_child.type == "type_identifier":
                                protocol = get_node_text(type_child, source_bytes)
                                inheritances.append(
                                    Inheritance(child=class_name, parent=protocol)
                                )
                                break

        return inheritances

    def _extract_protocol(self, node, source_bytes: bytes) -> list[Symbol]:
        """Extract symbols from @protocol declaration (Story 3.3).

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
                method_sym = self._extract_method(child, source_bytes, protocol_name)
                if method_sym:
                    symbols.append(method_sym)
            elif child.type == "property_declaration":
                prop_sym = self._extract_property(child, source_bytes, protocol_name)
                if prop_sym:
                    symbols.append(prop_sym)
            elif child.type == "qualified_protocol_interface_declaration":
                # Handle @required/@optional sections
                for subchild in child.children:
                    if subchild.type == "method_declaration":
                        method_sym = self._extract_method(subchild, source_bytes, protocol_name)
                        if method_sym:
                            symbols.append(method_sym)
                    elif subchild.type == "property_declaration":
                        prop_sym = self._extract_property(subchild, source_bytes, protocol_name)
                        if prop_sym:
                            symbols.append(prop_sym)

        return symbols

    def _extract_protocol_inheritance(self, node, source_bytes: bytes) -> list[Inheritance]:
        """Extract inheritance from @protocol (Story 3.3).

        Args:
            node: protocol_declaration node
            source_bytes: Source code bytes

        Returns:
            List of Inheritance objects
        """
        inheritances = []

        # Get protocol name (first identifier)
        protocol_name = None
        for child in node.children:
            if child.type == "identifier":
                protocol_name = get_node_text(child, source_bytes)
                break

        if not protocol_name:
            return inheritances

        # Extract parent protocols from protocol_reference_list
        for child in node.children:
            if child.type == "protocol_reference_list":
                # Extract all identifiers in the list
                for subchild in child.children:
                    if subchild.type == "identifier":
                        parent_protocol = get_node_text(subchild, source_bytes)
                        inheritances.append(
                            Inheritance(child=protocol_name, parent=parent_protocol)
                        )

        return inheritances

    def extract_calls(self, tree: Tree, source_bytes: bytes, symbols: list, imports: list) -> list:
        """Extract function/method calls from Objective-C code.

        Args:
            tree: Tree-sitter parse tree
            source_bytes: Source code as bytes
            symbols: List of symbols (for context)
            imports: List of imports (for resolution)

        Returns:
            List of Call objects (empty for Story 3.1)
        """
        # Call graph extraction will be implemented in a future story
        # For now, return empty list to satisfy BaseLanguageParser interface
        return []
