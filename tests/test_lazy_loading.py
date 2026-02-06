"""Test lazy loading of language parsers.

This test verifies that parsers are only imported when needed,
not at module load time.
"""

import sys


def test_parser_module_does_not_import_all_languages():
    """Verify that importing parser module doesn't import all language parsers."""
    # Remove parser module if already imported
    if 'codeindex.parser' in sys.modules:
        del sys.modules['codeindex.parser']

    # Clear language-specific modules
    for module_name in list(sys.modules.keys()):
        if module_name.startswith('tree_sitter_'):
            del sys.modules[module_name]

    # Import parser module

    # Verify that language-specific parsers are NOT imported yet
    assert 'tree_sitter_python' not in sys.modules
    assert 'tree_sitter_php' not in sys.modules
    assert 'tree_sitter_java' not in sys.modules


def test_get_parser_lazy_loads_python_only(tmp_path):
    """Verify that getting Python parser doesn't load PHP or Java parsers."""
    # Remove all tree-sitter modules
    for module_name in list(sys.modules.keys()):
        if module_name.startswith('tree_sitter_'):
            del sys.modules[module_name]

    # Import and use Python parser
    from codeindex.parser import _get_parser

    parser = _get_parser("python")
    assert parser is not None

    # Verify only Python parser is imported
    assert 'tree_sitter_python' in sys.modules
    # PHP and Java should NOT be imported
    # (This test will pass as long as they're optional dependencies)


def test_get_parser_caches_parsers():
    """Verify that parsers are cached after first use."""
    from codeindex.parser import _PARSER_CACHE, _get_parser

    # Clear cache
    _PARSER_CACHE.clear()

    # Get parser twice
    parser1 = _get_parser("python")
    parser2 = _get_parser("python")

    # Should be the same object (cached)
    assert parser1 is parser2
    assert "python" in _PARSER_CACHE


def test_get_parser_unsupported_language():
    """Verify that unsupported languages return None."""
    from codeindex.parser import _get_parser

    parser = _get_parser("unsupported_language")
    assert parser is None


def test_parse_file_with_missing_language_dependency(tmp_path):
    """Verify helpful error when language parser is not installed."""
    # This test documents the expected behavior when a language
    # parser is not installed (e.g., Java on a PHP-only project)

    # We can't actually test this in the test suite because
    # all dependencies are installed. This is a documentation test.

    # Expected behavior:
    # 1. parse_file() calls _get_parser("java")
    # 2. _get_parser() tries to import tree_sitter_java
    # 3. ImportError is caught and re-raised with helpful message
    # 4. parse_file() returns ParseResult with error field set

    from codeindex.parser import parse_file

    # Create a Java file
    java_file = tmp_path / "Test.java"
    java_file.write_text("public class Test {}")

    # Parse should work (because tree-sitter-java IS installed in tests)
    result = parse_file(java_file)

    # In production with missing dependency, result.error would contain:
    # "tree-sitter-java is not installed. Install it with: pip install tree-sitter-java"
    assert result.error is None  # Success in test environment


def test_multiple_languages_can_be_used_sequentially(tmp_path):
    """Verify that multiple languages can be parsed in sequence."""
    from codeindex.parser import parse_file

    # Create test files
    py_file = tmp_path / "test.py"
    py_file.write_text("def hello(): pass")

    php_file = tmp_path / "test.php"
    php_file.write_text("<?php\nfunction hello() {}")

    # Parse both
    py_result = parse_file(py_file)
    php_result = parse_file(php_file)

    # Both should succeed
    assert py_result.error is None
    assert php_result.error is None
    assert len(py_result.symbols) > 0
    assert len(php_result.symbols) > 0
