"""Regression tests for GH #112 — dedup the drifted language-detection table.

`skill_helpers._LANGUAGE_EXTENSIONS` was a redundant ext→language map that had
drifted: it carried `.go`/`.rs` which no parser supports, so
`detect_project_languages` could return `go`/`rust` → written into
`.codeindex.yaml` → scan/parse produces nothing (a detect-but-unparseable
silent-empty, same class as #80). It now derives from the single source
`scanner.EXTENSION_TO_LANGUAGE`, so it can never drift from the scannable set.
"""

from codeindex.scanner import EXTENSION_TO_LANGUAGE, LANGUAGE_EXTENSIONS
from codeindex.skill_helpers import detect_project_languages


class TestExtensionToLanguage:
    def test_is_exact_inverse_of_language_extensions(self):
        expected = {
            ext: lang for lang, exts in LANGUAGE_EXTENSIONS.items() for ext in exts
        }
        assert EXTENSION_TO_LANGUAGE == expected

    def test_no_unparseable_languages(self):
        # go/rust were the drifted entries — they have no parser and must not
        # appear in the detection surface.
        assert "go" not in EXTENSION_TO_LANGUAGE.values()
        assert "rust" not in EXTENSION_TO_LANGUAGE.values()
        assert ".go" not in EXTENSION_TO_LANGUAGE
        assert ".rs" not in EXTENSION_TO_LANGUAGE


class TestDetectProjectLanguagesDeduped:
    def test_detects_supported_language(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1\n")
        (tmp_path / "App.swift").write_text("class App {}\n")
        assert detect_project_languages(tmp_path) == ["python", "swift"]

    def test_go_no_longer_detected(self, tmp_path):
        """A .go file must NOT surface a `go` language (was the #112 bug)."""
        (tmp_path / "main.go").write_text("package main\n")
        (tmp_path / "main.py").write_text("x = 1\n")
        assert detect_project_languages(tmp_path) == ["python"]

    def test_detection_set_subset_of_scannable(self, tmp_path):
        """Anything detected must be a language the scanner can actually walk."""
        for name in ("a.py", "b.ts", "c.tsx", "d.go", "e.rs", "f.swift"):
            (tmp_path / name).write_text("\n")
        detected = set(detect_project_languages(tmp_path))
        assert detected <= set(LANGUAGE_EXTENSIONS.keys())
