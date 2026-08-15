"""JS/TS test-file exclude suggestions (GH #165).

Root cause of graph-export edge pollution (77% of edges from test files,
mocks all unresolved): the wizard/config template never suggested JS/TS
test patterns, so `.codeindex.yaml` shipped without them. Fixed at the
config seam — a `--exclude-tests` flag would let scan-all and
graph-export see different trees.
"""

from pathlib import Path

from codeindex.config_help import CONFIG_PARAMS
from codeindex.init_wizard import infer_exclude_patterns

JS_TS_TEST_PATTERNS = [
    "**/*.spec.ts",
    "**/*.spec.tsx",
    "**/*.spec.js",
    "**/*.test.ts",
    "**/*.test.tsx",
    "**/*.test.js",
    "**/__tests__/**",
]


def test_suggests_test_excludes_when_spec_files_exist(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "foo.service.ts").write_text("export class Foo {}\n")
    (tmp_path / "src" / "foo.service.spec.ts").write_text("describe('Foo', () => {});\n")

    excludes = infer_exclude_patterns(tmp_path)

    for pattern in JS_TS_TEST_PATTERNS:
        assert pattern in excludes, f"missing {pattern}"


def test_no_test_excludes_for_pure_python_project(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.py").write_text("x = 1\n")

    excludes = infer_exclude_patterns(tmp_path)

    assert not any(p in excludes for p in JS_TS_TEST_PATTERNS)


def test_explain_exclude_lists_test_patterns() -> None:
    """graph-export's warning says 'run: codeindex config explain exclude' —
    that output must actually contain the test patterns it points to."""
    exclude_help = CONFIG_PARAMS["exclude"]
    text = exclude_help.get("recommendations", "") + exclude_help.get("example", "")

    assert "**/*.spec.ts" in text
    assert "**/__tests__/**" in text
