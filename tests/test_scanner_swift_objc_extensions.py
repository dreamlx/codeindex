"""Regression tests for GH #80.

``scanner.LANGUAGE_EXTENSIONS`` drifted behind the parser side:
``parser.FILE_EXTENSIONS`` (and full parser modules) supported swift / objc,
but the scanner's extension map only knew 5 languages. A user with
``languages: [swift]`` in ``.codeindex.yaml`` got an empty extension set →
every ``.swift`` file silently skipped → empty scan with no diagnostic.

These tests pin the two extension maps together so the drift cannot recur.
"""

from pathlib import Path

from codeindex.config import Config
from codeindex.parser import FILE_EXTENSIONS
from codeindex.scanner import (
    LANGUAGE_EXTENSIONS,
    get_language_extensions,
    scan_directory,
)


class TestScannerKnowsSwiftObjc:
    def test_swift_extension_present(self):
        assert get_language_extensions(["swift"]) == {".swift"}

    def test_objc_extensions_present(self):
        # Must match parser.FILE_EXTENSIONS exactly: .h and .m, NOT .mm
        # (the parser does not handle .mm — see parser.FILE_EXTENSIONS).
        assert get_language_extensions(["objc"]) == {".h", ".m"}

    def test_scanner_map_matches_parser_file_extensions(self):
        """Structural drift guard (the root cause of #80).

        Every extension the parser knows how to dispatch must also be
        scannable, otherwise a configured language matches files the
        scanner then refuses to walk into (or vice versa)."""
        scanner_exts = {ext for exts in LANGUAGE_EXTENSIONS.values() for ext in exts}
        parser_exts = set(FILE_EXTENSIONS.keys())
        assert scanner_exts == parser_exts, (
            f"scanner.LANGUAGE_EXTENSIONS and parser.FILE_EXTENSIONS have "
            f"drifted. only-in-scanner={scanner_exts - parser_exts}, "
            f"only-in-parser={parser_exts - scanner_exts}"
        )


class TestSwiftProjectScans:
    def test_swift_file_matched_by_scan(self, tmp_path: Path):
        """The #80 repro: languages:[swift] must actually match .swift files."""
        src = tmp_path / "src"
        src.mkdir()
        (src / "foo.swift").write_text("class Foo {}\n")

        config = Config(languages=["swift"], include=["src/"])
        result = scan_directory(src, config)

        assert [f.name for f in result.files] == ["foo.swift"]
