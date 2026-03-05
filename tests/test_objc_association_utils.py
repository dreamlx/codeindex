"""Test suite for Objective-C file association utilities (Story 3.2).

This test file validates the association and merging utilities:
- find_objc_pairs() - finding matching .h/.m files
- parse_objc_pair() - parsing associated files
- merge_objc_results() - merging symbols from both files
- calculate_association_accuracy() - measuring accuracy

Epic: #23
Story: 3.2
"""

from pathlib import Path
from textwrap import dedent

import pytest

from codeindex.objc_association import (
    calculate_association_accuracy,
    find_objc_pairs,
    merge_objc_results,
    parse_objc_pair,
)


class TestFindObjCPairs:
    """Test finding .h/.m file pairs in directories."""

    def test_find_complete_pairs(self, tmp_path):
        """Should find matching .h and .m files."""
        # Create matching pairs
        (tmp_path / "Calculator.h").write_text("@interface Calculator @end")
        (tmp_path / "Calculator.m").write_text("@implementation Calculator @end")
        (tmp_path / "Person.h").write_text("@interface Person @end")
        (tmp_path / "Person.m").write_text("@implementation Person @end")

        pairs = find_objc_pairs(tmp_path)

        assert len(pairs) == 2

        # Check Calculator pair
        calc_pair = next((p for p in pairs if p.class_name == "Calculator"), None)
        assert calc_pair is not None
        assert calc_pair.is_complete
        assert calc_pair.header_file == tmp_path / "Calculator.h"
        assert calc_pair.implementation_file == tmp_path / "Calculator.m"

    def test_find_header_only(self, tmp_path):
        """Should handle .h files without .m."""
        (tmp_path / "Protocol.h").write_text("@interface Protocol @end")

        pairs = find_objc_pairs(tmp_path)

        assert len(pairs) == 1
        assert pairs[0].is_header_only
        assert pairs[0].header_file == tmp_path / "Protocol.h"
        assert pairs[0].implementation_file is None

    def test_find_implementation_only(self, tmp_path):
        """Should handle .m files without .h."""
        (tmp_path / "Helper.m").write_text("@implementation Helper @end")

        pairs = find_objc_pairs(tmp_path)

        assert len(pairs) == 1
        assert pairs[0].is_implementation_only
        assert pairs[0].header_file is None
        assert pairs[0].implementation_file == tmp_path / "Helper.m"

    def test_find_mixed_pairs(self, tmp_path):
        """Should handle mix of complete and incomplete pairs."""
        (tmp_path / "Complete.h").write_text("@interface Complete @end")
        (tmp_path / "Complete.m").write_text("@implementation Complete @end")
        (tmp_path / "HeaderOnly.h").write_text("@interface HeaderOnly @end")
        (tmp_path / "ImplOnly.m").write_text("@implementation ImplOnly @end")

        pairs = find_objc_pairs(tmp_path)

        assert len(pairs) == 3

        complete = next((p for p in pairs if p.class_name == "Complete"), None)
        assert complete.is_complete

        header_only = next((p for p in pairs if p.class_name == "HeaderOnly"), None)
        assert header_only.is_header_only

        impl_only = next((p for p in pairs if p.class_name == "ImplOnly"), None)
        assert impl_only.is_implementation_only

    def test_empty_directory(self, tmp_path):
        """Should return empty list for empty directory."""
        pairs = find_objc_pairs(tmp_path)
        assert len(pairs) == 0

    def test_nonexistent_directory(self):
        """Should return empty list for nonexistent directory."""
        pairs = find_objc_pairs(Path("/nonexistent/path"))
        assert len(pairs) == 0


class TestParseObjCPair:
    """Test parsing associated .h/.m file pairs."""

    def test_parse_complete_pair(self, tmp_path):
        """Should parse both .h and .m files."""
        header = dedent("""
            @interface Calculator : NSObject
            - (NSInteger)add:(NSInteger)a to:(NSInteger)b;
            @end
        """).strip()

        impl = dedent("""
            @implementation Calculator
            - (NSInteger)add:(NSInteger)a to:(NSInteger)b {
                return a + b;
            }
            @end
        """).strip()

        h_file = tmp_path / "Calculator.h"
        m_file = tmp_path / "Calculator.m"
        h_file.write_text(header)
        m_file.write_text(impl)

        try:
            pair = parse_objc_pair(header_file=h_file, implementation_file=m_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert pair.class_name == "Calculator"
        assert pair.is_complete
        assert pair.header_result is not None
        assert pair.implementation_result is not None
        assert pair.header_result.error is None
        assert pair.implementation_result.error is None

    def test_parse_header_only(self, tmp_path):
        """Should parse .h file alone."""
        h_file = tmp_path / "Protocol.h"
        h_file.write_text("@interface Protocol : NSObject\n@end")

        try:
            pair = parse_objc_pair(header_file=h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert pair.class_name == "Protocol"
        assert pair.is_header_only
        assert pair.header_result is not None
        assert pair.implementation_result is None

    def test_parse_implementation_only(self, tmp_path):
        """Should parse .m file alone."""
        m_file = tmp_path / "Helper.m"
        m_file.write_text("@implementation Helper\n@end")

        try:
            pair = parse_objc_pair(implementation_file=m_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert pair.class_name == "Helper"
        assert pair.is_implementation_only
        assert pair.header_result is None
        assert pair.implementation_result is not None

    def test_parse_nonexistent_files(self, tmp_path):
        """Should handle nonexistent files gracefully."""
        h_file = tmp_path / "Missing.h"
        m_file = tmp_path / "Missing.m"

        try:
            pair = parse_objc_pair(header_file=h_file, implementation_file=m_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Should create pair but with no results
        assert pair.class_name == "Missing"
        assert pair.header_result is None
        assert pair.implementation_result is None


class TestMergeObjCResults:
    """Test merging header and implementation results."""

    def test_merge_complete_pair(self, tmp_path):
        """Should merge symbols from both .h and .m."""
        header = dedent("""
            @interface Math : NSObject
            @property (nonatomic, assign) NSInteger value;
            - (NSInteger)square;
            @end
        """).strip()

        impl = dedent("""
            @implementation Math
            - (NSInteger)square {
                return self.value * self.value;
            }
            - (void)privateHelper {
                // Private method
            }
            @end
        """).strip()

        h_file = tmp_path / "Math.h"
        m_file = tmp_path / "Math.m"
        h_file.write_text(header)
        m_file.write_text(impl)

        try:
            pair = parse_objc_pair(header_file=h_file, implementation_file=m_file)
            merged = merge_objc_results(pair)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Should have symbols from both files
        assert len(merged.symbols) >= 3  # class + property + methods

        # Should include property from header
        properties = [s for s in merged.symbols if s.kind == "property"]
        assert len(properties) >= 1

        # Should include methods from both
        methods = [s for s in merged.symbols if s.kind == "method"]
        assert len(methods) >= 2  # square + privateHelper

    def test_merge_header_only(self, tmp_path):
        """Should use header symbols when no implementation."""
        h_file = tmp_path / "Protocol.h"
        h_file.write_text("@interface Protocol : NSObject\n@end")

        try:
            pair = parse_objc_pair(header_file=h_file)
            merged = merge_objc_results(pair)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Should have header symbols
        assert len(merged.symbols) >= 1
        assert merged.path == h_file

    def test_merge_implementation_only(self, tmp_path):
        """Should use implementation symbols when no header."""
        m_file = tmp_path / "Helper.m"
        m_file.write_text("@implementation Helper\n@end")

        try:
            pair = parse_objc_pair(implementation_file=m_file)
            merged = merge_objc_results(pair)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Should have implementation symbols
        assert len(merged.symbols) >= 1
        assert merged.path == m_file

    def test_merge_deduplicates_class_symbols(self, tmp_path):
        """Should not duplicate class symbols from .h and .m."""
        h_file = tmp_path / "Foo.h"
        m_file = tmp_path / "Foo.m"
        h_file.write_text("@interface Foo : NSObject\n@end")
        m_file.write_text("@implementation Foo\n@end")

        try:
            pair = parse_objc_pair(header_file=h_file, implementation_file=m_file)
            merged = merge_objc_results(pair)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        # Should have only 1 class symbol, not 2
        classes = [s for s in merged.symbols if s.kind == "class"]
        assert len(classes) == 1


class TestAssociationAccuracy:
    """Test association accuracy calculation."""

    def test_accuracy_all_complete_pairs(self, tmp_path):
        """Should be 100% when all pairs are complete."""
        (tmp_path / "A.h").write_text("@interface A @end")
        (tmp_path / "A.m").write_text("@implementation A @end")
        (tmp_path / "B.h").write_text("@interface B @end")
        (tmp_path / "B.m").write_text("@implementation B @end")

        pairs = find_objc_pairs(tmp_path)
        accuracy = calculate_association_accuracy(pairs)

        assert accuracy == 100.0

    def test_accuracy_partial_pairs(self, tmp_path):
        """Should calculate correct percentage for partial matches."""
        (tmp_path / "Complete.h").write_text("@interface Complete @end")
        (tmp_path / "Complete.m").write_text("@implementation Complete @end")
        (tmp_path / "HeaderOnly.h").write_text("@interface HeaderOnly @end")
        (tmp_path / "ImplOnly.m").write_text("@implementation ImplOnly @end")

        pairs = find_objc_pairs(tmp_path)
        accuracy = calculate_association_accuracy(pairs)

        # 1 complete out of 3 total = 33.3%
        assert 33.0 <= accuracy <= 34.0

    def test_accuracy_no_complete_pairs(self, tmp_path):
        """Should be 0% when no pairs are complete."""
        (tmp_path / "HeaderOnly.h").write_text("@interface HeaderOnly @end")
        (tmp_path / "ImplOnly.m").write_text("@implementation ImplOnly @end")

        pairs = find_objc_pairs(tmp_path)
        accuracy = calculate_association_accuracy(pairs)

        assert accuracy == 0.0

    def test_accuracy_empty_directory(self):
        """Should be 100% for empty directory (vacuous truth)."""
        accuracy = calculate_association_accuracy([])
        assert accuracy == 100.0
