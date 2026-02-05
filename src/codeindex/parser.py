"""Multi-language AST parser using tree-sitter."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict

import tree_sitter_java as tsjava
import tree_sitter_php as tsphp
import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser


@dataclass
class Symbol:
    """Represents a code symbol (class, function, etc.)."""

    name: str
    kind: str  # class, function, method
    signature: str = ""
    docstring: str = ""
    line_start: int = 0
    line_end: int = 0
    annotations: list["Annotation"] = field(default_factory=list)  # Story 7.1.2.1

    def to_dict(self) -> dict:
        """Convert Symbol to JSON-serializable dict."""
        return {
            "name": self.name,
            "kind": self.kind,
            "signature": self.signature,
            "docstring": self.docstring,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "annotations": [a.to_dict() for a in self.annotations],
        }


@dataclass
class Import:
    """Represents an import statement."""

    module: str
    names: list[str] = field(default_factory=list)
    is_from: bool = False

    def to_dict(self) -> dict:
        """Convert Import to JSON-serializable dict."""
        return {
            "module": self.module,
            "names": self.names,
            "is_from": self.is_from,
        }


@dataclass
class Annotation:
    """Represents a code annotation/decorator (e.g., Java @RestController).

    Story 7.1.2.1: Annotation Extraction
    Supports extraction of annotations from Java classes, methods, and fields.
    """

    name: str
    arguments: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert Annotation to JSON-serializable dict."""
        return {
            "name": self.name,
            "arguments": self.arguments,
        }


@dataclass
class ParseResult:
    """Result of parsing a file."""

    path: Path
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[Import] = field(default_factory=list)
    module_docstring: str = ""
    namespace: str = ""  # PHP namespace
    error: str | None = None
    file_lines: int = 0  # Number of lines in the file

    def to_dict(self) -> dict:
        """Convert ParseResult to JSON-serializable dict."""
        return {
            "path": str(self.path),
            "symbols": [symbol.to_dict() for symbol in self.symbols],
            "imports": [imp.to_dict() for imp in self.imports],
            "module_docstring": self.module_docstring,
            "namespace": self.namespace,
            "error": self.error,
            "file_lines": self.file_lines,
        }


# Initialize languages
PY_LANGUAGE = Language(tspython.language())
PHP_LANGUAGE = Language(tsphp.language_php())
JAVA_LANGUAGE = Language(tsjava.language())

# Language-specific parsers
PARSERS: Dict[str, Parser] = {
    "python": Parser(PY_LANGUAGE),
    "php": Parser(PHP_LANGUAGE),
    "java": Parser(JAVA_LANGUAGE),
}

# File extension to language mapping
FILE_EXTENSIONS: Dict[str, str] = {
    ".py": "python",
    ".php": "php",
    ".phtml": "php",
    ".java": "java",
}


def _get_node_text(node, source_bytes: bytes) -> str:
    """Extract text from a tree-sitter node."""
    return source_bytes[node.start_byte : node.end_byte].decode("utf-8")


def _extract_docstring(node, source_bytes: bytes) -> str:
    """Extract docstring from first child if it's a string."""
    if node.child_count == 0:
        return ""

    # Look for expression_statement containing string
    for child in node.children:
        if child.type == "block":
            for block_child in child.children:
                if block_child.type == "expression_statement":
                    for expr_child in block_child.children:
                        if expr_child.type == "string":
                            text = _get_node_text(expr_child, source_bytes)
                            # Remove quotes
                            if text.startswith('"""') or text.startswith("'''"):
                                return text[3:-3].strip()
                            elif text.startswith('"') or text.startswith("'"):
                                return text[1:-1].strip()
                    break
            break

    return ""


def _parse_function(
    node,
    source_bytes: bytes,
    class_name: str = "",
    decorators: list[str] | None = None
) -> Symbol:
    """Parse a function definition node."""
    name = ""
    signature_parts = []

    for child in node.children:
        if child.type == "identifier":  # function name is 'identifier', not 'name'
            name = _get_node_text(child, source_bytes)
        elif child.type == "parameters":
            signature_parts.append(_get_node_text(child, source_bytes))
        elif child.type == "type":
            signature_parts.append(f" -> {_get_node_text(child, source_bytes)}")

    kind = "method" if class_name else "function"
    full_name = f"{class_name}.{name}" if class_name else name
    signature = f"def {name}{''.join(signature_parts)}"
    docstring = _extract_docstring(node, source_bytes)

    return Symbol(
        name=full_name,
        kind=kind,
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_class(node, source_bytes: bytes) -> list[Symbol]:
    """Parse a class definition node and its methods."""
    symbols = []
    class_name = ""
    bases = []

    for child in node.children:
        if child.type == "identifier":  # class name is 'identifier', not 'name'
            class_name = _get_node_text(child, source_bytes)
        elif child.type == "argument_list":
            bases.append(_get_node_text(child, source_bytes))

    signature = f"class {class_name}"
    if bases:
        signature += "".join(bases)

    docstring = _extract_docstring(node, source_bytes)

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

    # Parse methods
    for child in node.children:
        if child.type == "block":
            for block_child in child.children:
                if block_child.type == "function_definition":
                    method = _parse_function(block_child, source_bytes, class_name)
                    symbols.append(method)

    return symbols


def _parse_import(node, source_bytes: bytes) -> Import | None:
    """Parse an import statement."""
    if node.type == "import_statement":
        # import foo, bar
        names = []
        for child in node.children:
            if child.type == "dotted_name":
                names.append(_get_node_text(child, source_bytes))
            elif child.type == "aliased_import":
                for ac in child.children:
                    if ac.type == "dotted_name":
                        names.append(_get_node_text(ac, source_bytes))
                        break
        if names:
            return Import(module=names[0], names=names[1:] if len(names) > 1 else [], is_from=False)

    elif node.type == "import_from_statement":
        # from foo import bar, baz
        module = ""
        names = []
        for child in node.children:
            if child.type == "dotted_name":
                if not module:
                    module = _get_node_text(child, source_bytes)
                else:
                    names.append(_get_node_text(child, source_bytes))
            elif child.type == "relative_import":
                module = _get_node_text(child, source_bytes)
            elif child.type == "aliased_import":
                for ac in child.children:
                    if ac.type == "dotted_name":
                        names.append(_get_node_text(ac, source_bytes))
                        break
                    elif ac.type == "identifier":
                        names.append(_get_node_text(ac, source_bytes))
                        break
            elif child.type == "identifier":
                names.append(_get_node_text(child, source_bytes))

        if module:
            return Import(module=module, names=names, is_from=True)

    return None


def _extract_module_docstring(tree, source_bytes: bytes) -> str:
    """Extract module-level docstring."""
    root = tree.root_node
    for child in root.children:
        if child.type == "expression_statement":
            for expr_child in child.children:
                if expr_child.type == "string":
                    text = _get_node_text(expr_child, source_bytes)
                    if text.startswith('"""') or text.startswith("'''"):
                        return text[3:-3].strip()
                    elif text.startswith('"') or text.startswith("'"):
                        return text[1:-1].strip()
            break
        elif child.type not in ("comment",):
            break
    return ""


def parse_file(path: Path, language: str | None = None) -> ParseResult:
    """
    Parse a source file (Python or PHP) and extract symbols and imports.

    Args:
        path: Path to the source file
        language: Optional language override ("python" or "php").
                  If None, language is detected from file extension.

    Returns:
        ParseResult containing symbols, imports, and docstrings
    """
    try:
        source_bytes = path.read_bytes()
    except Exception as e:
        return ParseResult(path=path, error=str(e), file_lines=0)

    # Calculate file lines
    file_lines = source_bytes.count(b"\n") + (
        1 if source_bytes and not source_bytes.endswith(b"\n") else 0
    )

    # Determine language
    if language is None:
        language = _get_language(path)
    if not language:
        return ParseResult(
            path=path, error=f"Unsupported file type: {path.suffix}", file_lines=file_lines
        )

    # Validate language
    if language not in PARSERS:
        return ParseResult(
            path=path, error=f"Unsupported language: {language}", file_lines=file_lines
        )

    # Get appropriate parser
    parser = PARSERS.get(language)
    if not parser:
        return ParseResult(
            path=path, error=f"No parser for language: {language}", file_lines=file_lines
        )

    try:
        tree = parser.parse(source_bytes)
    except Exception as e:
        return ParseResult(path=path, error=f"Parse error: {e}", file_lines=file_lines)

    # Check for syntax errors
    if tree.root_node.has_error:
        return ParseResult(
            path=path,
            error="Syntax error in file (tree-sitter parse failure)",
            file_lines=file_lines,
        )

    symbols: list[Symbol] = []
    imports: list[Import] = []
    module_docstring = ""

    # Language-specific parsing
    if language == "python":
        module_docstring = _extract_module_docstring(tree, source_bytes)
        root = tree.root_node
        for child in root.children:
            if child.type == "function_definition":
                symbols.append(_parse_function(child, source_bytes))
            elif child.type == "class_definition":
                symbols.extend(_parse_class(child, source_bytes))
            elif child.type == "decorated_definition":
                for dec_child in child.children:
                    if dec_child.type == "function_definition":
                        symbols.append(_parse_function(dec_child, source_bytes))
                    elif dec_child.type == "class_definition":
                        symbols.extend(_parse_class(dec_child, source_bytes))
            elif child.type in ("import_statement", "import_from_statement"):
                imp = _parse_import(child, source_bytes)
                if imp:
                    imports.append(imp)

    elif language == "php":
        # PHP parsing
        root = tree.root_node
        namespace = ""

        for child in root.children:
            if child.type == "namespace_definition":
                namespace = _parse_php_namespace(child, source_bytes)
            elif child.type == "namespace_use_declaration":
                use_imports = _parse_php_use(child, source_bytes)
                imports.extend(use_imports)
            elif child.type == "class_declaration":
                symbols.extend(_parse_php_class(child, source_bytes))
            elif child.type == "function_definition":
                symbols.append(_parse_php_function(child, source_bytes))
            elif child.type in ("include_expression", "require_expression"):
                imp = _parse_php_include(child, source_bytes)
                if imp:
                    imports.append(imp)

        # Extract module docstring from PHP file comments
        module_docstring = ""
        for child in root.children:
            if child.type == "comment" and child.text.startswith(b"/**"):
                module_docstring = _extract_php_docstring(child, source_bytes)
                break

        return ParseResult(
            path=path,
            symbols=symbols,
            imports=imports,
            module_docstring=module_docstring,
            namespace=namespace,
            file_lines=file_lines,
        )

    elif language == "java":
        # Java parsing
        root = tree.root_node
        namespace = ""  # Java package name

        for child in root.children:
            if child.type == "package_declaration":
                namespace = _parse_java_package(child, source_bytes)
            elif child.type == "class_declaration":
                symbols.extend(_parse_java_class(child, source_bytes))
            elif child.type == "interface_declaration":
                symbols.extend(_parse_java_interface(child, source_bytes))
            elif child.type == "enum_declaration":
                symbols.extend(_parse_java_enum(child, source_bytes))
            elif child.type == "record_declaration":
                symbols.extend(_parse_java_record(child, source_bytes))
            elif child.type == "import_declaration":
                imp = _parse_java_import(child, source_bytes)
                if imp:
                    imports.append(imp)

        # Extract module docstring from first JavaDoc comment
        module_docstring = _extract_java_module_docstring(tree, source_bytes)

        return ParseResult(
            path=path,
            symbols=symbols,
            imports=imports,
            module_docstring=module_docstring,
            namespace=namespace,
            file_lines=file_lines,
        )

    return ParseResult(
        path=path,
        symbols=symbols,
        imports=imports,
        module_docstring=module_docstring,
        file_lines=file_lines,
    )


def parse_directory(paths: list[Path]) -> list[ParseResult]:
    """Parse multiple files."""
    return [parse_file(p) for p in paths]

def _get_language(file_path: Path) -> str:
    """Determine language from file extension."""
    suffix = file_path.suffix.lower()
    return FILE_EXTENSIONS.get(suffix)

def _extract_php_docstring(node, source_bytes: bytes) -> str:
    """
    Extract docstring from PHPDoc/DocComment or inline comments.

    For PHP, the comment is often a sibling node (previous sibling)
    rather than a child node.

    Supports:
    - PHPDoc blocks: /** ... */
    - Inline comments: // ...
    """
    # First check children (for class-level comments)
    for child in node.children:
        if child.type == "comment":
            text = _get_node_text(child, source_bytes)
            if text.startswith("/**"):
                return _parse_phpdoc_text(text)
            elif text.startswith("//"):
                # Inline comment: remove // and strip
                return text[2:].strip()

    # Check previous sibling (for method-level comments)
    if node.prev_sibling and node.prev_sibling.type == "comment":
        text = _get_node_text(node.prev_sibling, source_bytes)
        if text.startswith("/**"):
            return _parse_phpdoc_text(text)
        elif text.startswith("//"):
            # Inline comment: remove // and strip
            return text[2:].strip()

    return ""


def _parse_phpdoc_text(text: str) -> str:
    """
    Parse PHPDoc comment text and extract description.

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

def _parse_php_function(node, source_bytes: bytes, class_name: str = "") -> Symbol:
    """Parse a PHP function definition node (standalone function, not method)."""
    name = ""
    params = ""
    return_type = ""

    for child in node.children:
        if child.type == "name":
            name = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            return_type = _get_node_text(child, source_bytes)

    signature = f"function {name}{params}"
    if return_type:
        signature += f": {return_type}"

    docstring = _extract_php_docstring(node, source_bytes)

    return Symbol(
        name=name,
        kind="function",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_php_method(node, source_bytes: bytes, class_name: str) -> Symbol:
    """Parse a PHP method declaration node with visibility, static, and return type."""
    name = ""
    params = ""
    return_type = ""
    visibility = ""
    is_static = False

    for child in node.children:
        if child.type == "visibility_modifier":
            visibility = _get_node_text(child, source_bytes)
        elif child.type == "static_modifier":
            is_static = True
        elif child.type == "name":
            name = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            return_type = _get_node_text(child, source_bytes)

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

    docstring = _extract_php_docstring(node, source_bytes)
    full_name = f"{class_name}::{name}"

    return Symbol(
        name=full_name,
        kind="method",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
    )


def _parse_php_property(node, source_bytes: bytes, class_name: str) -> Symbol:
    """Parse a PHP property declaration node."""
    prop_name = ""
    visibility = ""
    is_static = False
    prop_type = ""

    for child in node.children:
        if child.type == "visibility_modifier":
            visibility = _get_node_text(child, source_bytes)
        elif child.type == "static_modifier":
            is_static = True
        elif child.type in ("named_type", "primitive_type", "optional_type"):
            prop_type = _get_node_text(child, source_bytes)
        elif child.type == "property_element":
            for prop_child in child.children:
                if prop_child.type == "variable_name":
                    prop_name = _get_node_text(prop_child, source_bytes)

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

def _parse_php_class(node, source_bytes: bytes) -> list[Symbol]:
    """Parse a PHP class definition node with extends, implements, properties and methods."""
    symbols = []
    class_name = ""
    extends = ""
    implements = []
    is_abstract = False
    is_final = False

    for child in node.children:
        if child.type == "name":
            class_name = _get_node_text(child, source_bytes)
        elif child.type == "abstract_modifier":
            is_abstract = True
        elif child.type == "final_modifier":
            is_final = True
        elif child.type == "base_clause":
            # extends BaseClass
            for bc_child in child.children:
                if bc_child.type == "name":
                    extends = _get_node_text(bc_child, source_bytes)
        elif child.type == "class_interface_clause":
            # implements Interface1, Interface2
            for ic_child in child.children:
                if ic_child.type == "name":
                    implements.append(_get_node_text(ic_child, source_bytes))

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

    docstring = _extract_php_docstring(node, source_bytes)

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
                    prop = _parse_php_property(decl, source_bytes, class_name)
                    symbols.append(prop)
                elif decl.type == "method_declaration":
                    method = _parse_php_method(decl, source_bytes, class_name)
                    symbols.append(method)

    return symbols

def _parse_php_include(node, source_bytes: bytes) -> Import | None:
    """Parse PHP include/require statements."""
    if node.type == "include_expression" or node.type == "require_expression":
        for child in node.children:
            if child.type == "string":
                module = _get_node_text(child, source_bytes)
                # Remove quotes
                module = module.strip('\'"')
                return Import(module=module, names=[], is_from=False)
    return None


def _parse_php_namespace(node, source_bytes: bytes) -> str:
    """Parse PHP namespace definition."""
    for child in node.children:
        if child.type == "namespace_name":
            return _get_node_text(child, source_bytes)
    return ""


def _parse_php_use(node, source_bytes: bytes) -> list[Import]:
    """
    Parse PHP use statement.

    Handles:
    - use App\\Service\\UserService;
    - use App\\Model\\User as UserModel;
    - use App\\Repository\\{UserRepository, OrderRepository};
    """
    imports = []
    base_namespace = ""

    for child in node.children:
        if child.type == "namespace_name":
            # Group import base: use App\Repository\{...}
            base_namespace = _get_node_text(child, source_bytes)

        elif child.type == "namespace_use_clause":
            # Single import
            module = ""
            alias = ""

            for clause_child in child.children:
                if clause_child.type == "qualified_name":
                    module = _get_node_text(clause_child, source_bytes)
                elif clause_child.type == "name" and module:
                    # This is the alias (after 'as')
                    alias = _get_node_text(clause_child, source_bytes)

            if module:
                # If there's a base namespace (group import), prepend it
                if base_namespace:
                    module = f"{base_namespace}\\{module}"

                imports.append(Import(
                    module=module,
                    names=[alias] if alias else [],
                    is_from=True,  # PHP use is similar to Python's from...import
                ))

        elif child.type == "namespace_use_group":
            # Group import: {UserRepository, OrderRepository}
            for group_child in child.children:
                if group_child.type == "namespace_use_clause":
                    name = ""
                    alias = ""
                    for clause_child in group_child.children:
                        if clause_child.type == "qualified_name":
                            name = _get_node_text(clause_child, source_bytes)
                        elif clause_child.type == "name":
                            if not name:
                                name = _get_node_text(clause_child, source_bytes)
                            else:
                                alias = _get_node_text(clause_child, source_bytes)

                    if name:
                        full_module = f"{base_namespace}\\{name}" if base_namespace else name
                        imports.append(Import(
                            module=full_module,
                            names=[alias] if alias else [],
                            is_from=True,
                        ))

    return imports


# ==================== Java Parser Functions ====================


def _extract_java_modifiers(node: Node, source_bytes: bytes) -> list[str]:
    """
    Extract modifiers (public, private, static, etc.) from a Java node.

    Args:
        node: Tree-sitter node to extract modifiers from
        source_bytes: Source code as bytes

    Returns:
        List of modifier strings (e.g., ['public', 'static', 'final'])
    """
    modifiers = []
    for child in node.children:
        if child.type == "modifiers":
            for mod_child in child.children:
                modifiers.append(_get_node_text(mod_child, source_bytes))
    return modifiers


def _build_java_signature(modifiers: list[str], *parts: str) -> str:
    """
    Build a Java signature string from modifiers and parts.

    Args:
        modifiers: List of modifier strings (e.g., ['public', 'static'])
        *parts: Additional signature parts (e.g., return type, name, parameters)

    Returns:
        Complete signature string (e.g., "public static void main(String[] args)")
    """
    signature_parts = []

    # Add modifiers if present
    if modifiers:
        signature_parts.append(" ".join(modifiers))

    # Add remaining parts
    signature_parts.extend(parts)

    return " ".join(signature_parts)


def _extract_java_annotations(node: Node, source_bytes: bytes) -> list[Annotation]:
    """Extract annotations from a Java node.

    Story 7.1.2.1: Annotation Extraction
    Extracts annotations like @RestController, @GetMapping("/path"), etc.

    Args:
        node: Tree-sitter node to extract annotations from
        source_bytes: Source code as bytes

    Returns:
        List of Annotation objects
    """
    annotations = []

    for child in node.children:
        if child.type == "modifiers":
            for mod_child in child.children:
                if mod_child.type == "marker_annotation":
                    # Simple annotation without arguments: @Entity
                    name = ""
                    for name_child in mod_child.children:
                        if name_child.type in ("identifier", "scoped_identifier"):
                            name = _get_node_text(name_child, source_bytes)
                    if name:
                        annotations.append(Annotation(name=name, arguments={}))

                elif mod_child.type == "annotation":
                    # Annotation with arguments: @RequestMapping("/path")
                    name = ""
                    arguments = {}

                    for ann_child in mod_child.children:
                        if ann_child.type in ("identifier", "scoped_identifier"):
                            name = _get_node_text(ann_child, source_bytes)
                        elif ann_child.type == "annotation_argument_list":
                            arguments = _parse_annotation_arguments(ann_child, source_bytes)

                    if name:
                        annotations.append(Annotation(name=name, arguments=arguments))

    return annotations


def _parse_annotation_arguments(arg_list_node: Node, source_bytes: bytes) -> dict[str, str]:
    """Parse annotation arguments into a dictionary.

    Args:
        arg_list_node: annotation_argument_list node
        source_bytes: Source code as bytes

    Returns:
        Dictionary of argument name -> value
        For single value annotations like @GetMapping("/path"), returns {"value": "/path"}
    """
    arguments = {}

    for child in arg_list_node.children:
        if child.type == "element_value_pair":
            # Named argument: name = "value"
            key = ""
            value = ""
            for pair_child in child.children:
                if pair_child.type == "identifier":
                    key = _get_node_text(pair_child, source_bytes)
                elif pair_child.type == "string_literal":
                    value = _get_node_text(pair_child, source_bytes).strip('"')
                elif pair_child.type in ("decimal_integer_literal", "true", "false"):
                    value = _get_node_text(pair_child, source_bytes)
                elif pair_child.type == "element_value_array_initializer":
                    # Array value: {"/users", "/user"}
                    value = _get_node_text(pair_child, source_bytes)

            if key and value:
                arguments[key] = value

        elif child.type == "string_literal":
            # Single unnamed string argument: @GetMapping("/path")
            # Maps to "value" key by Java convention
            value = _get_node_text(child, source_bytes).strip('"')
            arguments["value"] = value
        elif child.type == "decimal_integer_literal":
            # Single unnamed integer argument
            value = _get_node_text(child, source_bytes)
            arguments["value"] = value

    return arguments


def _find_child_by_type(node: Node, type_name: str) -> Node | None:
    """
    Find first child node of a specific type.

    Args:
        node: Parent node to search in
        type_name: Type of child to find

    Returns:
        First matching child node, or None if not found
    """
    for child in node.children:
        if child.type == type_name:
            return child
    return None


def _extract_java_docstring(node: Node, source_bytes: bytes) -> str:
    """
    Extract JavaDoc comment from a node.

    JavaDoc comments are /** ... */ blocks that appear before declarations.
    They are typically previous siblings of the node.
    """
    # Check previous siblings for JavaDoc comments
    if (hasattr(node, 'prev_sibling') and node.prev_sibling and
            node.prev_sibling.type == "block_comment"):
        comment_text = _get_node_text(node.prev_sibling, source_bytes)
        if comment_text.startswith("/**"):
            # Remove /** and */ and clean up
            return comment_text[3:-2].strip()

    # Check children for comment (less common)
    for child in node.children:
        if child.type == "block_comment":
            comment_text = _get_node_text(child, source_bytes)
            if comment_text.startswith("/**"):
                return comment_text[3:-2].strip()

    return ""


def _parse_java_method(node: Node, source_bytes: bytes, class_name: str = "") -> Symbol:
    """Parse a Java method declaration."""
    name = ""
    params = ""
    return_type = ""
    type_params = ""  # Story 7.1.2.2: Method-level generic parameters
    throws_clause = ""  # Story 7.1.2.3: Throws declarations

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            name = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)
        elif child.type == "type_identifier" or child.type == "void_type":
            return_type = _get_node_text(child, source_bytes)
        elif child.type in ("generic_type", "array_type", "scoped_type_identifier"):
            return_type = _get_node_text(child, source_bytes)
        elif child.type == "type_parameters":  # Story 7.1.2.2: Capture method generics
            type_params = _get_node_text(child, source_bytes)
        elif child.type == "throws":  # Story 7.1.2.3: Capture throws clause
            throws_clause = _get_node_text(child, source_bytes)

    # Build signature using helper
    return_str = return_type if return_type else "void"
    full_name = f"{class_name}.{name}" if class_name else name
    # Include type parameters if present (e.g., <T extends Comparable<T>>)
    method_decl = f"{type_params} {return_str}" if type_params else return_str
    signature = _build_java_signature(modifiers, method_decl, f"{name}{params}")
    # Append throws clause if present (e.g., "throws IOException, SQLException")
    if throws_clause:
        signature += f" {throws_clause}"

    docstring = _extract_java_docstring(node, source_bytes)

    return Symbol(
        name=full_name,
        kind="method" if class_name else "function",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    )


def _parse_java_constructor(node: Node, source_bytes: bytes, class_name: str) -> Symbol:
    """Parse a Java constructor declaration."""
    name = ""
    params = ""
    throws_clause = ""  # Story 7.1.2.3: Throws declarations

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            name = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)
        elif child.type == "throws":  # Story 7.1.2.3: Capture throws clause
            throws_clause = _get_node_text(child, source_bytes)

    # Build signature using helper
    full_name = f"{class_name}.{name}"
    signature = _build_java_signature(modifiers, f"{name}{params}")
    # Append throws clause if present (e.g., "throws IOException, SQLException")
    if throws_clause:
        signature += f" {throws_clause}"

    docstring = _extract_java_docstring(node, source_bytes)

    return Symbol(
        name=full_name,
        kind="constructor",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    )


def _parse_java_field(node: Node, source_bytes: bytes, class_name: str = "") -> list[Symbol]:
    """Parse a Java field declaration."""
    type_name = ""
    field_names = []

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type in ("type_identifier", "generic_type", "array_type",
                          "integral_type", "floating_point_type", "boolean_type"):
            type_name = _get_node_text(child, source_bytes)
        elif child.type == "variable_declarator":
            for var_child in child.children:
                if var_child.type == "identifier":
                    field_names.append(_get_node_text(var_child, source_bytes))

    # Create symbols for each field
    symbols = []
    for field_name in field_names:
        full_name = f"{class_name}.{field_name}" if class_name else field_name

        # Build signature using helper
        signature = _build_java_signature(modifiers, type_name, field_name)

        symbols.append(Symbol(
            name=full_name,
            kind="field",
            signature=signature,
            docstring="",  # Fields typically don't have individual docstrings
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            annotations=annotations,  # Story 7.1.2.1
        ))

    return symbols


def _parse_java_class(node: Node, source_bytes: bytes) -> list[Symbol]:
    """Parse a Java class declaration."""
    symbols = []
    class_name = ""
    type_params = ""
    superclass = ""
    interfaces = []

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            class_name = _get_node_text(child, source_bytes)
        elif child.type == "type_parameters":
            type_params = _get_node_text(child, source_bytes)
        elif child.type == "superclass":
            for super_child in child.children:
                if super_child.type == "type_identifier":
                    superclass = _get_node_text(super_child, source_bytes)
        elif child.type == "super_interfaces":
            for interface_child in child.children:
                if interface_child.type == "type_list":
                    for type_child in interface_child.children:
                        if type_child.type == "type_identifier":
                            interfaces.append(_get_node_text(type_child, source_bytes))

    # Build class signature using helper
    class_decl = class_name + type_params if type_params else class_name
    signature_parts = ["class", class_decl]
    if superclass:
        signature_parts.append(f"extends {superclass}")
    if interfaces:
        signature_parts.append(f"implements {', '.join(interfaces)}")

    signature = _build_java_signature(modifiers, *signature_parts)
    docstring = _extract_java_docstring(node, source_bytes)

    # Add class symbol
    symbols.append(Symbol(
        name=class_name,
        kind="class",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    ))

    # Parse class body (methods, fields, constructors)
    for child in node.children:
        if child.type == "class_body":
            for body_child in child.children:
                if body_child.type == "method_declaration":
                    method = _parse_java_method(body_child, source_bytes, class_name)
                    symbols.append(method)
                elif body_child.type == "constructor_declaration":
                    constructor = _parse_java_constructor(body_child, source_bytes, class_name)
                    symbols.append(constructor)
                elif body_child.type == "field_declaration":
                    fields = _parse_java_field(body_child, source_bytes, class_name)
                    symbols.extend(fields)
                elif body_child.type == "class_declaration":
                    # Nested class
                    nested_symbols = _parse_java_class(body_child, source_bytes)
                    symbols.extend(nested_symbols)

    return symbols


def _parse_java_interface(node: Node, source_bytes: bytes) -> list[Symbol]:
    """Parse a Java interface declaration."""
    symbols = []
    interface_name = ""
    type_params = ""
    extends = []

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            interface_name = _get_node_text(child, source_bytes)
        elif child.type == "type_parameters":
            type_params = _get_node_text(child, source_bytes)
        elif child.type == "extends_interfaces":
            for ext_child in child.children:
                if ext_child.type == "type_list":
                    for type_child in ext_child.children:
                        if type_child.type in (
                            "type_identifier",
                            "generic_type",
                            "scoped_type_identifier",
                        ):
                            extends.append(_get_node_text(type_child, source_bytes))

    # Build interface signature using helper
    interface_decl = interface_name + type_params if type_params else interface_name
    signature_parts = ["interface", interface_decl]
    if extends:
        signature_parts.append(f"extends {', '.join(extends)}")

    signature = _build_java_signature(modifiers, *signature_parts)
    docstring = _extract_java_docstring(node, source_bytes)

    # Add interface symbol
    symbols.append(Symbol(
        name=interface_name,
        kind="interface",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    ))

    # Parse interface body (method declarations)
    for child in node.children:
        if child.type == "interface_body":
            for body_child in child.children:
                if body_child.type == "method_declaration":
                    method = _parse_java_method(body_child, source_bytes, interface_name)
                    symbols.append(method)

    return symbols


def _parse_java_enum(node: Node, source_bytes: bytes) -> list[Symbol]:
    """Parse a Java enum declaration."""
    symbols = []
    enum_name = ""

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            enum_name = _get_node_text(child, source_bytes)

    # Build enum signature using helper
    signature = _build_java_signature(modifiers, "enum", enum_name)
    docstring = _extract_java_docstring(node, source_bytes)

    # Add enum symbol
    symbols.append(Symbol(
        name=enum_name,
        kind="enum",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    ))

    # Parse enum body (constants, methods)
    for child in node.children:
        if child.type == "enum_body":
            for body_child in child.children:
                if body_child.type == "method_declaration":
                    method = _parse_java_method(body_child, source_bytes, enum_name)
                    symbols.append(method)
                elif body_child.type == "constructor_declaration":
                    constructor = _parse_java_constructor(body_child, source_bytes, enum_name)
                    symbols.append(constructor)

    return symbols


def _parse_java_record(node: Node, source_bytes: bytes) -> list[Symbol]:
    """Parse a Java record declaration (Java 14+)."""
    symbols = []
    record_name = ""
    type_params = ""
    params = ""

    # Extract modifiers and annotations using helpers
    modifiers = _extract_java_modifiers(node, source_bytes)
    annotations = _extract_java_annotations(node, source_bytes)  # Story 7.1.2.1

    for child in node.children:
        if child.type == "identifier":
            record_name = _get_node_text(child, source_bytes)
        elif child.type == "type_parameters":
            type_params = _get_node_text(child, source_bytes)
        elif child.type == "formal_parameters":
            params = _get_node_text(child, source_bytes)

    # Build record signature using helper
    name_part = record_name + type_params if type_params else record_name
    signature = _build_java_signature(modifiers, "record", f"{name_part}{params}")
    docstring = _extract_java_docstring(node, source_bytes)

    # Add record symbol
    symbols.append(Symbol(
        name=record_name,
        kind="record",
        signature=signature,
        docstring=docstring,
        line_start=node.start_point[0] + 1,
        line_end=node.end_point[0] + 1,
        annotations=annotations,  # Story 7.1.2.1
    ))

    # Parse record body (methods)
    for child in node.children:
        if child.type == "class_body":  # Records use class_body too
            for body_child in child.children:
                if body_child.type == "method_declaration":
                    method = _parse_java_method(body_child, source_bytes, record_name)
                    symbols.append(method)

    return symbols


def _parse_java_import(node: Node, source_bytes: bytes) -> Import | None:
    """Parse a Java import statement."""
    module = ""
    is_static = False
    is_wildcard = False

    for child in node.children:
        if child.type == "scoped_identifier" or child.type == "identifier":
            module = _get_node_text(child, source_bytes)
        elif child.type == "asterisk":
            is_wildcard = True
        elif child.type == "static":
            is_static = True

    if module:
        # Handle wildcard imports
        if is_wildcard:
            module = module + ".*"

        return Import(
            module=module,
            names=[],  # Java imports don't have "as" aliases like Python
            is_from=is_static,  # Use is_from to indicate static imports
        )

    return None


def _extract_java_module_docstring(tree, source_bytes: bytes) -> str:
    """Extract module-level JavaDoc comment."""
    root = tree.root_node

    # Look for first block comment (/** ... */)
    for child in root.children:
        if child.type == "block_comment":
            comment_text = _get_node_text(child, source_bytes)
            if comment_text.startswith("/**"):
                return comment_text[3:-2].strip()
        elif child.type in ("class_declaration", "interface_declaration",
                           "enum_declaration", "record_declaration"):
            # Found a declaration, extract its docstring as module docstring
            return _extract_java_docstring(child, source_bytes)

    return ""


def _parse_java_package(node: Node, source_bytes: bytes) -> str:
    """Extract Java package declaration."""
    for child in node.children:
        if child.type == "scoped_identifier" or child.type == "identifier":
            return _get_node_text(child, source_bytes)
    return ""
