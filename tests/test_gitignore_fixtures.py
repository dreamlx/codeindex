"""Enforce .gitignore rules for pytest-rebuilt fixture README_AI trees.

GH #135 added ``tests/fixtures/char_graphbuffer/**/README_AI.md`` to .gitignore
because ``scan-all`` (root config includes ``tests/``) regenerates READMEs
inside fixtures that pytest rmtree-rebuilds, leaving the tree dirty. GH #183
is the same class of bug on the sibling ``tests/legacy/test_hierarchical_test/``
fixture — ``a8f1732`` deleted the committed READMEs to stop the pytest-side
dirty path but missed the scan-all side, so ``scan-all`` regenerated them and
the tree dirtied again. These tests pin both rules so the gap doesn't reopen a
third time.

Carve-out invariant (#135 comment): other fixture READMEs
(``cli_parse/``, ``graph_export/``) are legit tracked navigation assets and
must NOT be ignored — asserted here so a future broadening of the rule is
caught.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _git_check_ignore(path: Path) -> bool:
    """True if `path` is git-ignored (exit 0 from check-ignore)."""
    result = subprocess.run(
        ["git", "check-ignore", str(path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0


def test_hierarchical_fixture_readme_is_ignored():
    """GH #183: scan-all regenerates README_AI inside the pytest-rebuilt
    hierarchical fixture; it must be ignored (sibling of #135)."""
    ignored = REPO_ROOT / "tests/legacy/test_hierarchical_test/level1/level2a/level3/README_AI.md"
    assert _git_check_ignore(ignored), (
        f"{ignored} must be git-ignored — scan-all regenerates it and pytest "
        "rmtree-rebuilds the fixture; without ignore the tree dirties every run"
    )


def test_char_graphbuffer_fixture_readme_still_ignored():
    """GH #135 regression guard: the original rmtree-rebuilt fixture rule
    stays in place."""
    ignored = REPO_ROOT / "tests/fixtures/char_graphbuffer/sub/README_AI.md"
    assert _git_check_ignore(ignored), "char_graphbuffer README_AI must stay ignored (#135)"


@pytest.mark.parametrize(
    "tracked",
    [
        "tests/fixtures/cli_parse/README_AI.md",
        "tests/fixtures/graph_export/project/README_AI.md",
    ],
)
def test_navigation_fixture_readmes_not_over_ignored(tracked: str):
    """Carve-out (#135 comment): cli_parse/ and graph_export/ fixture READMEs
    are legit tracked navigation assets — a broadening of the ignore rule that
    swallows them would silently drop them from the repo."""
    not_ignored = REPO_ROOT / tracked
    assert not _git_check_ignore(not_ignored), (
        f"{tracked} must stay committable — it is a tracked navigation asset, "
        "not a pytest-rebuilt fixture"
    )
