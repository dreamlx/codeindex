"""Tests for GH #77 — CLAUDE.md injection locale adaptation.

The injected ``## codeindex`` section used to be English-only. When the host
CLAUDE.md is written in Chinese, an English section breaks style mid-file and
signals "the tool didn't understand my project". This pins the remaining #77
piece: the injection follows the host language (zh/en), auto-detected from the
existing CLAUDE.md, with an explicit override.
"""

from pathlib import Path

from codeindex.claude_md import (
    build_section,
    detect_locale,
    inject,
)

# Discriminators must live in prose only — NOT in the shared code blocks /
# commands / literal marker HTML comments, which stay English in both templates.
ZH_MARKER = "导航索引"  # zh prose only
EN_MARKER = "authoritative technical documentation"  # en prose only


class TestDetectLocale:
    def test_chinese_prose_detected_as_zh(self):
        content = (
            "# 项目说明\n\n本项目使用 Python 编写，核心逻辑在 src/ 目录下。"
            "运行 `pytest` 执行测试。请先阅读架构文档再动手。\n"
        )
        assert detect_locale(content) == "zh"

    def test_english_prose_detected_as_en(self):
        content = (
            "# Project\n\nThis project is written in Python. Core logic lives "
            "under src/. Run `pytest` to execute the tests.\n"
        )
        assert detect_locale(content) == "en"

    def test_empty_defaults_to_en(self):
        assert detect_locale("") == "en"

    def test_own_zh_section_does_not_bias_english_host(self):
        """An English host that already carries a zh codeindex section must
        still detect as 'en' — detection strips our own marker block so an
        update stays idempotent and matches the *host*, not our prose."""
        host = "# My Project\n\nAll documentation here is in English only.\n\n"
        section = build_section(version="9.9.9", lang="zh")
        assert detect_locale(host + section) == "en"


class TestBuildSection:
    def test_zh_section_has_chinese_body(self):
        section = build_section(version="9.9.9", lang="zh")
        assert ZH_MARKER in section
        assert "codeindex:start v9.9.9" in section

    def test_en_section_has_english_body(self):
        section = build_section(version="9.9.9", lang="en")
        assert EN_MARKER in section


class TestInitCliWiring:
    """End-to-end: the --lang flag reaches claude_md.inject via `init --yes`."""

    def _run_init(self, proj: str, args: list[str]) -> None:
        from click.testing import CliRunner

        from codeindex.cli_config import init

        (Path(proj) / "src").mkdir(exist_ok=True)
        (Path(proj) / "src" / "main.py").write_text("x = 1\n")
        result = CliRunner().invoke(init, ["--yes", *args])
        assert result.exit_code == 0, result.output

    def test_explicit_lang_zh(self, tmp_path):
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            self._run_init(proj, ["--lang", "zh"])
            assert ZH_MARKER in (Path(proj) / "CLAUDE.md").read_text()

    def test_auto_matches_chinese_host(self, tmp_path):
        from click.testing import CliRunner

        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as proj:
            (Path(proj) / "CLAUDE.md").write_text("# 项目\n\n中文说明文档。\n")
            self._run_init(proj, [])  # --lang defaults to auto
            assert ZH_MARKER in (Path(proj) / "CLAUDE.md").read_text()


class TestInjectAutoDetect:
    def test_inject_into_chinese_host_uses_zh(self, tmp_path: Path):
        p = tmp_path / "CLAUDE.md"
        p.write_text("# 我的项目\n\n这是一个中文项目，请阅读源码。\n")
        inject(p, version="9.9.9")  # lang=None → auto-detect
        assert ZH_MARKER in p.read_text()

    def test_inject_into_english_host_uses_en(self, tmp_path: Path):
        p = tmp_path / "CLAUDE.md"
        p.write_text("# My Project\n\nThis is an English project.\n")
        inject(p, version="9.9.9")
        assert EN_MARKER in p.read_text()

    def test_fresh_file_defaults_to_en(self, tmp_path: Path):
        p = tmp_path / "CLAUDE.md"
        inject(p, version="9.9.9")  # no host content
        assert EN_MARKER in p.read_text()

    def test_explicit_lang_overrides_detection(self, tmp_path: Path):
        p = tmp_path / "CLAUDE.md"
        p.write_text("# 中文项目\n\n全中文文档。\n")
        inject(p, version="9.9.9", lang="en")  # override
        assert EN_MARKER in p.read_text()
        assert ZH_MARKER not in p.read_text()

    def test_update_preserves_zh_on_reinject(self, tmp_path: Path):
        """Idempotent update: a zh host stays zh across re-injection."""
        p = tmp_path / "CLAUDE.md"
        p.write_text("# 中文项目\n\n全中文文档，说明如何使用。\n")
        inject(p, version="9.9.9")
        inject(p, version="9.9.10")  # simulate `claude-md update`
        text = p.read_text()
        assert ZH_MARKER in text
        assert EN_MARKER not in text
        assert text.count("codeindex:start") == 1  # still a single section
