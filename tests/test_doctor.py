"""Tests for `codeindex doctor` — read-only health/sync diagnostic."""

import json

from click.testing import CliRunner

from codeindex import __version__
from codeindex.cli_config import doctor
from codeindex.doctor import (
    check_claude_md,
    check_cli,
    check_project,
    detect_plugin,
    has_errors,
    run_doctor,
)


class TestCheckCli:
    def test_reports_installed_version(self):
        f = check_cli()
        assert f.status == "ok"
        assert __version__ in f.message


class TestCheckProject:
    def test_no_config_suggests_init(self, tmp_path):
        findings = check_project(tmp_path)
        assert any(f.fix == "codeindex init" for f in findings)

    def test_config_present_ok(self, tmp_path):
        (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
        findings = check_project(tmp_path)
        assert any(f.status == "ok" and ".codeindex.yaml" in f.message for f in findings)

    def test_installed_parser_reported_ok(self, tmp_path):
        # python parser is a dev/test dependency, so it's installed here
        (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python]\n")
        findings = check_project(tmp_path)
        assert any("parsers installed" in f.message and "python" in f.message for f in findings)

    def test_missing_parser_is_error_with_pipx_fix(self, tmp_path):
        # a bogus language has no parser → error finding with a pipx inject fix
        (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [python, cobol]\n")
        findings = check_project(tmp_path)
        err = [f for f in findings if f.status == "error"]
        assert err, findings
        assert "cobol" in err[0].message
        assert err[0].fix.startswith("pipx inject ai-codeindex")


class TestCheckClaudeMd:
    def test_absent_returns_none(self, tmp_path):
        assert check_claude_md(tmp_path) is None

    def test_no_marker_is_info(self, tmp_path):
        (tmp_path / "CLAUDE.md").write_text("# My project\n")
        f = check_claude_md(tmp_path)
        assert f.status == "info"

    def test_current_marker_is_ok(self, tmp_path):
        from codeindex.claude_md import inject

        inject(tmp_path / "CLAUDE.md", __version__)
        f = check_claude_md(tmp_path)
        assert f.status == "ok"
        assert __version__ in f.message

    def test_stale_marker_is_warn(self, tmp_path):
        from codeindex.claude_md import inject

        inject(tmp_path / "CLAUDE.md", "0.0.1")
        f = check_claude_md(tmp_path)
        assert f.status == "warn"
        assert f.fix == "codeindex claude-md update"


class TestDetectPlugin:
    def test_no_claude_env_returns_none(self, tmp_path):
        # tmp_path has no .claude/plugins → not a Claude Code environment
        assert detect_plugin(tmp_path) is None

    def test_claude_env_without_plugin_suggests_install(self, tmp_path):
        (tmp_path / ".claude" / "plugins").mkdir(parents=True)
        f = detect_plugin(tmp_path)
        assert f is not None
        assert f.status == "info"
        assert "/plugin install" in f.fix

    def test_detects_installed_plugin_version(self, tmp_path):
        manifest_dir = (
            tmp_path / ".claude" / "plugins" / "cache"
            / "codeindex-claude" / "codeindex" / "0.1.3" / ".claude-plugin"
        )
        manifest_dir.mkdir(parents=True)
        (manifest_dir / "plugin.json").write_text(json.dumps({"name": "codeindex", "version": "0.1.3"}))
        f = detect_plugin(tmp_path)
        assert f.status == "ok"
        assert "0.1.3" in f.message

    def test_picks_highest_version_when_multiple_cached(self, tmp_path):
        base = tmp_path / ".claude" / "plugins" / "cache" / "codeindex-claude" / "codeindex"
        for v in ("0.1.2", "0.1.10"):
            d = base / v / ".claude-plugin"
            d.mkdir(parents=True)
            (d / "plugin.json").write_text(json.dumps({"name": "codeindex", "version": v}))
        f = detect_plugin(tmp_path)
        assert "0.1.10" in f.message  # semver-ish: 10 > 2


class TestRunDoctorAndCli:
    def test_run_doctor_skips_plugin_section_for_non_claude_env(self, tmp_path):
        findings = run_doctor(cwd=tmp_path, home=tmp_path)
        assert not any(f.section == "Claude Code plugin" for f in findings)

    def test_has_errors(self, tmp_path):
        (tmp_path / ".codeindex.yaml").write_text("version: 1\nlanguages: [cobol]\n")
        findings = run_doctor(cwd=tmp_path, home=tmp_path)
        assert has_errors(findings)

    def test_cli_smoke_exit_zero_on_clean(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME", str(tmp_path))
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(doctor, [])
            assert result.exit_code == 0
            assert "codeindex doctor" in result.output
            assert "ai-codeindex" in result.output
