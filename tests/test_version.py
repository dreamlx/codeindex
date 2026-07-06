"""Tests for `codeindex --version` resolution.

Editable installs bake the version into dist-info metadata at install time,
so `codeindex --version` goes stale after a pyproject bump until reinstall.
That once masked a shipped fix: a stale `--version` made a developer believe a
fix hadn't landed. The resolver must prefer the source-tree pyproject when
reachable, and only fall back to installed metadata for wheel/pipx installs.
"""

from unittest.mock import patch

import codeindex


def test_source_version_reads_pyproject(tmp_path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nname = "ai-codeindex"\nversion = "9.9.9"\n', encoding="utf-8"
    )
    assert codeindex._source_version(pyproject) == "9.9.9"


def test_source_version_none_when_pyproject_missing(tmp_path):
    assert codeindex._source_version(tmp_path / "nope.toml") is None


def test_source_version_ignores_python_version_line(tmp_path):
    """`python_version = "..."` in [tool.mypy] must not shadow [project]."""
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        '[project]\nversion = "1.2.3"\n[tool.mypy]\npython_version = "3.10"\n',
        encoding="utf-8",
    )
    assert codeindex._source_version(pyproject) == "1.2.3"


def test_resolve_prefers_source_pyproject_over_stale_metadata():
    """Editable install with stale dist-info (0.30.0) but fresh source (9.9.9)."""
    with patch.object(codeindex, "_source_version", return_value="9.9.9"), \
         patch("importlib.metadata.version", return_value="0.30.0"):
        assert codeindex._resolve_version() == "9.9.9"


def test_resolve_falls_back_to_metadata_when_no_source():
    """Wheel/pipx install: no source pyproject reachable -> use metadata."""
    with patch.object(codeindex, "_source_version", return_value=None), \
         patch("importlib.metadata.version", return_value="0.32.0"):
        assert codeindex._resolve_version() == "0.32.0"


def test_resolve_dev_when_nothing_available():
    with patch.object(codeindex, "_source_version", return_value=None), \
         patch("importlib.metadata.version", side_effect=Exception):
        assert codeindex._resolve_version() == "0.0.0-dev"


def test_default_source_version_path_reaches_repo_pyproject():
    """Regression guard for the src-layout depth assumption.

    The default (no-arg) path must reach this repo's pyproject.toml. If the
    depth is wrong, _source_version() returns None, __version__ falls back to
    stale dist-info metadata, and this assertion fails — catching it instead
    of silently misreporting --version again.
    """
    resolved = codeindex._source_version()
    assert resolved is not None, "default _source_version() returned None — pyproject path depth wrong"
    assert resolved == codeindex.__version__
