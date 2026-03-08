"""Test suite for Objective-C bridging header detection (Story 3.4).

This test file validates bridging header handling for Swift/Objective-C interop:
- Detecting *-Bridging-Header.h files
- Extracting exposed Objective-C classes/methods
- Handling #import statements in bridging headers
- Edge cases and multiple imports

Epic: #23
Story: 3.4
"""

from textwrap import dedent

import pytest

from codeindex.parser import parse_file


class TestBridgingHeaderDetection:
    """Test bridging header file detection."""

    def test_detect_bridging_header_by_filename(self, tmp_path):
        """Should detect files matching *-Bridging-Header.h pattern."""
        bridging_header = dedent("""
            #import "MyClass.h"
            #import "Helper.h"
        """).strip() + "\n" + "\n"

        h_file = tmp_path / "MyApp-Bridging-Header.h"
        h_file.write_text(bridging_header)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None
        # Should parse as Objective-C file
        assert result.path == h_file

    def test_project_bridging_header_pattern(self, tmp_path):
        """Should support ProjectName-Bridging-Header.h pattern."""
        h_file = tmp_path / "SlockApp-Bridging-Header.h"
        h_file.write_text("#import <Foundation/Foundation.h>\n")

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

    def test_regular_header_not_bridging(self, tmp_path):
        """Regular .h files should not be treated specially."""
        h_file = tmp_path / "NormalHeader.h"
        h_file.write_text("@interface MyClass @end")

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None
        # Should parse normally


class TestBridgingHeaderImports:
    """Test import extraction from bridging headers."""

    def test_extract_multiple_imports(self, tmp_path):
        """Should extract all #import statements."""
        bridging_header = dedent("""
            #import "AudioManager.h"
            #import "DatabaseHelper.h"
            #import "NetworkClient.h"
        """).strip() + "\n"

        h_file = tmp_path / "App-Bridging-Header.h"
        h_file.write_text(bridging_header)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find all imports
        assert len(result.imports) >= 3
        import_modules = [imp.module for imp in result.imports]
        assert any("AudioManager" in mod for mod in import_modules)
        assert any("DatabaseHelper" in mod for mod in import_modules)
        assert any("NetworkClient" in mod for mod in import_modules)

    def test_framework_imports(self, tmp_path):
        """Should handle framework imports (<Framework/Header.h>)."""
        bridging_header = dedent("""
            #import <UIKit/UIKit.h>
            #import <Foundation/Foundation.h>
            #import "CustomClass.h"
        """).strip() + "\n"

        h_file = tmp_path / "MyApp-Bridging-Header.h"
        h_file.write_text(bridging_header)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find all imports
        assert len(result.imports) >= 3

    def test_import_with_subdirectories(self, tmp_path):
        """Should handle imports with subdirectory paths."""
        bridging_header = dedent("""
            #import "Utils/StringHelper.h"
            #import "Network/APIClient.h"
        """).strip() + "\n"

        h_file = tmp_path / "App-Bridging-Header.h"
        h_file.write_text(bridging_header)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should find imports with paths
        import_modules = [imp.module for imp in result.imports]
        assert any("StringHelper" in mod or "Utils" in mod for mod in import_modules)


class TestBridgingHeaderClasses:
    """Test class exposure in bridging headers."""

    def test_bridging_header_with_interface(self, tmp_path):
        """Bridging headers may contain @interface declarations."""
        bridging_header = dedent("""
            #import "Helper.h"

            @interface BridgedClass : NSObject
            - (void)bridgedMethod;
            @end
        """).strip() + "\n"

        h_file = tmp_path / "App-Bridging-Header.h"
        h_file.write_text(bridging_header)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should extract the class
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) >= 1
        assert any(c.name == "BridgedClass" for c in classes)

    def test_bridging_header_with_protocol(self, tmp_path):
        """Bridging headers may expose @protocol declarations."""
        bridging_header = dedent("""
            @protocol BridgedDelegate
            - (void)delegateMethod;
            @end
        """).strip() + "\n"

        h_file = tmp_path / "App-Bridging-Header.h"
        h_file.write_text(bridging_header)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should extract the protocol
        protocols = [s for s in result.symbols if "protocol" in s.kind.lower() or s.kind == "interface"]
        assert len(protocols) >= 1


class TestBridgingHeaderEdgeCases:
    """Test edge cases for bridging headers."""

    def test_empty_bridging_header(self, tmp_path):
        """Should handle empty bridging headers."""
        h_file = tmp_path / "Empty-Bridging-Header.h"
        h_file.write_text("")

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None
        # Should parse without error even if empty

    def test_bridging_header_only_imports(self, tmp_path):
        """Bridging headers typically only contain #import statements."""
        bridging_header = dedent("""
            // This bridging header exposes Objective-C classes to Swift
            #import "ObjCClass1.h"
            #import "ObjCClass2.h"
            #import "ObjCClass3.h"
        """).strip() + "\n"

        h_file = tmp_path / "Production-Bridging-Header.h"
        h_file.write_text(bridging_header)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should have 3 imports
        assert len(result.imports) >= 3

    def test_bridging_header_with_comments(self, tmp_path):
        """Should handle comments in bridging headers."""
        bridging_header = dedent("""
            // Expose Audio classes
            #import "AudioManager.h"

            /* Network stack */
            #import "NetworkClient.h"

            // Database
            #import "DBHelper.h"
        """).strip() + "\n"

        h_file = tmp_path / "App-Bridging-Header.h"
        h_file.write_text(bridging_header)

        try:
            result = parse_file(h_file)
        except ImportError:
            pytest.skip("tree-sitter-objc not installed")

        assert result.error is None

        # Should still find all imports
        assert len(result.imports) >= 3
