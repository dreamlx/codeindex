"""Objective-C header/implementation file association utilities (Story 3.2).

This module provides utilities to associate .h and .m files for the same class
and merge their parsing results for comprehensive symbol information.

Epic: #23
Story: 3.2
"""

from dataclasses import dataclass
from pathlib import Path

from .parser import ParseResult, parse_file


@dataclass
class ObjCFilePair:
    """Represents an associated .h/.m file pair.

    Attributes:
        class_name: Name of the Objective-C class
        header_file: Path to .h file (None if missing)
        implementation_file: Path to .m file (None if missing)
        header_result: ParseResult from header (None if missing)
        implementation_result: ParseResult from implementation (None if missing)
    """

    class_name: str
    header_file: Path | None = None
    implementation_file: Path | None = None
    header_result: ParseResult | None = None
    implementation_result: ParseResult | None = None

    @property
    def is_complete(self) -> bool:
        """Check if both .h and .m files are present."""
        return self.header_file is not None and self.implementation_file is not None

    @property
    def is_header_only(self) -> bool:
        """Check if only .h file is present."""
        return self.header_file is not None and self.implementation_file is None

    @property
    def is_implementation_only(self) -> bool:
        """Check if only .m file is present."""
        return self.header_file is None and self.implementation_file is not None


def find_objc_pairs(directory: Path) -> list[ObjCFilePair]:
    """Find all .h/.m file pairs in a directory.

    Matches files by basename (e.g., MyClass.h + MyClass.m).
    Handles cases where only .h or only .m exists.

    Args:
        directory: Directory to search for Objective-C files

    Returns:
        List of ObjCFilePair objects

    Example:
        >>> pairs = find_objc_pairs(Path("src"))
        >>> # Returns list of ObjCFilePair objects with header/implementation files
    """
    if not directory.exists() or not directory.is_dir():
        return []

    # Find all .h and .m files
    h_files = {f.stem: f for f in directory.glob("*.h")}
    m_files = {f.stem: f for f in directory.glob("*.m")}

    # Combine into pairs
    all_names = set(h_files.keys()) | set(m_files.keys())
    pairs = []

    for name in sorted(all_names):
        pair = ObjCFilePair(
            class_name=name,
            header_file=h_files.get(name),
            implementation_file=m_files.get(name),
        )
        pairs.append(pair)

    return pairs


def parse_objc_pair(
    header_file: Path | None = None,
    implementation_file: Path | None = None,
) -> ObjCFilePair:
    """Parse an associated .h/.m file pair.

    Args:
        header_file: Path to .h file (optional)
        implementation_file: Path to .m file (optional)

    Returns:
        ObjCFilePair with parsing results

    Raises:
        ValueError: If both files are None

    Example:
        >>> pair = parse_objc_pair(
        ...     header_file=Path("MyClass.h"),
        ...     implementation_file=Path("MyClass.m")
        ... )
        >>> # Access pair.header_result.symbols and pair.implementation_result.symbols
    """
    if header_file is None and implementation_file is None:
        raise ValueError("At least one file (header or implementation) must be provided")

    # Determine class name
    if header_file:
        class_name = header_file.stem
    else:
        class_name = implementation_file.stem

    # Parse files
    header_result = None
    implementation_result = None

    if header_file and header_file.exists():
        header_result = parse_file(header_file)

    if implementation_file and implementation_file.exists():
        implementation_result = parse_file(implementation_file)

    return ObjCFilePair(
        class_name=class_name,
        header_file=header_file if header_file and header_file.exists() else None,
        implementation_file=implementation_file if implementation_file and implementation_file.exists() else None,
        header_result=header_result,
        implementation_result=implementation_result,
    )


def merge_objc_results(pair: ObjCFilePair) -> ParseResult:
    """Merge header and implementation parsing results.

    Combines symbols, imports, and other metadata from both files into
    a single ParseResult. Prioritizes header for public API and adds
    implementation-only symbols (e.g., private methods).

    Strategy:
    - Use header result as base (if available)
    - Add implementation-only symbols (not in header)
    - Merge imports from both files
    - Merge inheritances from both files
    - Use implementation file path if header missing

    Args:
        pair: ObjCFilePair with parsed results

    Returns:
        Merged ParseResult

    Example:
        >>> pair = parse_objc_pair(Path("MyClass.h"), Path("MyClass.m"))
        >>> merged = merge_objc_results(pair)
        >>> # Contains symbols from both header and implementation
    """
    # Base result
    if pair.header_result:
        base_result = pair.header_result
        base_path = pair.header_file
    elif pair.implementation_result:
        base_result = pair.implementation_result
        base_path = pair.implementation_file
    else:
        # No results available
        return ParseResult(
            path=pair.header_file or pair.implementation_file or Path("unknown"),
            error="No parsing results available",
        )

    # Collect symbols from both files
    all_symbols = []
    symbol_signatures = set()

    # Add header symbols first (public API)
    if pair.header_result:
        for sym in pair.header_result.symbols:
            all_symbols.append(sym)
            symbol_signatures.add(sym.signature)

    # Add implementation symbols not in header (private methods, etc.)
    if pair.implementation_result:
        for sym in pair.implementation_result.symbols:
            # Skip class symbols only if we already have them from header
            if sym.kind == "class" and pair.header_result:
                continue
            # Add if not already present
            if sym.signature not in symbol_signatures:
                all_symbols.append(sym)
                symbol_signatures.add(sym.signature)

    # Merge imports
    all_imports = []
    import_modules = set()

    if pair.header_result:
        for imp in pair.header_result.imports:
            all_imports.append(imp)
            import_modules.add(imp.module)

    if pair.implementation_result:
        for imp in pair.implementation_result.imports:
            if imp.module not in import_modules:
                all_imports.append(imp)
                import_modules.add(imp.module)

    # Merge inheritances
    all_inheritances = []
    inheritance_pairs = set()

    if pair.header_result:
        for inh in pair.header_result.inheritances:
            all_inheritances.append(inh)
            inheritance_pairs.add((inh.child, inh.parent))

    if pair.implementation_result:
        for inh in pair.implementation_result.inheritances:
            if (inh.child, inh.parent) not in inheritance_pairs:
                all_inheritances.append(inh)
                inheritance_pairs.add((inh.child, inh.parent))

    # Create merged result
    return ParseResult(
        path=base_path,
        symbols=all_symbols,
        imports=all_imports,
        inheritances=all_inheritances,
        calls=base_result.calls,
        module_docstring=base_result.module_docstring,
        namespace=base_result.namespace,
        error=base_result.error,
        file_lines=base_result.file_lines,
    )


def calculate_association_accuracy(pairs: list[ObjCFilePair]) -> float:
    """Calculate association accuracy for .h/.m pairs.

    Accuracy is defined as: (complete pairs / total pairs) * 100

    Args:
        pairs: List of ObjCFilePair objects

    Returns:
        Accuracy percentage (0-100)

    Example:
        >>> pairs = find_objc_pairs(Path("src"))
        >>> accuracy = calculate_association_accuracy(pairs)
        >>> # Returns percentage (0-100) of complete .h/.m pairs
    """
    if not pairs:
        return 100.0  # No pairs = 100% accurate (vacuous truth)

    complete_pairs = sum(1 for p in pairs if p.is_complete)
    return (complete_pairs / len(pairs)) * 100.0
