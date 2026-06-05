"""Tests for parser installation detection (Epic 19 Story 19.4).

Checks that the init wizard detects installed/missing tree-sitter parsers
and provides guidance for installation.
"""

from codeindex.init_wizard import check_parser_installed, get_parser_install_guidance


class TestCheckParserInstalled:
    """Tests for check_parser_installed function."""

    def test_python_parser_installed(self):
        """Python parser should be detected as installed."""
        # tree_sitter_python is a dev dependency, should always be available
        assert check_parser_installed("python") is True

    def test_java_parser_installed(self):
        """Java parser should be detected as installed."""
        assert check_parser_installed("java") is True

    def test_php_parser_installed(self):
        """PHP parser should be detected as installed."""
        assert check_parser_installed("php") is True

    def test_unknown_language_not_installed(self):
        """Unknown language should report not installed."""
        assert check_parser_installed("cobol") is False

    def test_unsupported_language_not_installed(self):
        """Language without parser mapping should report not installed."""
        assert check_parser_installed("rust") is False


class TestParserInstallGuidance:
    """Tests for parser installation guidance."""

    def test_all_parsers_installed_no_missing(self):
        """When all parsers are installed, missing list should be empty."""
        # Python, Java, PHP are all installed in dev environment
        languages = ["python", "java", "php"]
        guidance = get_parser_install_guidance(languages)
        assert guidance["missing"] == []
        assert guidance["installed"] == languages

    def test_missing_parser_shows_install_command(self):
        """Missing parser should show install command."""
        languages = ["python", "cobol"]
        guidance = get_parser_install_guidance(languages)
        assert "cobol" in guidance["missing"]
        assert "python" in guidance["installed"]

    def test_empty_languages_no_guidance(self):
        """Empty language list should return empty guidance."""
        guidance = get_parser_install_guidance([])
        assert guidance["missing"] == []
        assert guidance["installed"] == []

    def test_typescript_javascript_are_known_to_parser_map(self):
        """Regression for GH #86 (4a).

        ``PARSER_PACKAGES`` used to enumerate only python/php/java, even
        though scanner gained TS/JS parsers (#73) and the parser modules
        exist under ``src/codeindex/parsers/typescript/`` and
        ``.../javascript/``. Result: ``init --yes`` on a TS project
        reported ``Warning: Missing parsers for: javascript, typescript``
        even though ``pipx inject ai-codeindex tree-sitter-{typescript,
        javascript}`` confirmed the packages were already installed.

        With the fix, TS/JS must be detected as installed in dev/CI
        (where ``[all]`` extra is installed via ``pip install -e .[dev,all]``).
        """
        assert check_parser_installed("typescript") is True
        assert check_parser_installed("javascript") is True

        guidance = get_parser_install_guidance(["typescript", "javascript"])
        assert "typescript" in guidance["installed"]
        assert "javascript" in guidance["installed"]
        assert "typescript" not in guidance["missing"]
        assert "javascript" not in guidance["missing"]

    def test_install_command_uses_pipx_inject_not_pip_install(self):
        """Regression for GH #86 (4b).

        The hint used to be ``pip install ai-codeindex[<langs>]`` — contradicts
        the entire documented install path (``pipx install ai-codeindex`` is the
        recommended path per CLAUDE.md / README / both hooks & index SKILL).
        Worse: ``pip install`` into a pipx-managed env doesn't work cleanly,
        so the hint actively misleads.

        Force a missing parser by asking for an unknown language; assert the
        hint now uses ``pipx inject``.
        """
        guidance = get_parser_install_guidance(["fortran"])
        assert "install_command" in guidance
        cmd = guidance["install_command"]
        assert cmd.startswith("pipx inject ai-codeindex"), (
            f"Install hint must point to pipx (not pip install); got: {cmd!r}"
        )
        assert "pip install" not in cmd, (
            f"Install hint still mentions `pip install` — contradicts pipx-based "
            f"recommended path (GH #86 4b). Got: {cmd!r}"
        )

    def test_parser_package_map_covers_scanner_supported_set(self):
        """Structural drift guard. ``PARSER_PACKAGES`` (used to validate
        installed parsers + build install hints) must cover every language
        ``scanner.LANGUAGE_EXTENSIONS`` knows how to scan — otherwise a
        language can be detected by ``init`` (#73) and scanned by the
        runtime, while the parser-presence check silently fails for it,
        re-introducing the GH #86 false-positive warning class."""
        from codeindex.init_wizard import PARSER_PACKAGES
        from codeindex.scanner import LANGUAGE_EXTENSIONS as SCAN_EXT

        missing = set(SCAN_EXT.keys()) - set(PARSER_PACKAGES.keys())
        assert not missing, (
            f"init_wizard.PARSER_PACKAGES is missing languages that "
            f"scanner.py knows how to scan: {sorted(missing)}. This is the "
            f"drift class that caused GH #86 — the parser-installed check "
            f"silently returns False for these and `init` warns about "
            f"\"missing parsers\" even when they're installed."
        )


class TestInitWizardPostMessage:
    """Tests for updated post-init messages (Story 19.2)."""

    def test_post_init_suggests_scan_all(self, tmp_path):
        """Post-init message should suggest scan-all (works without AI)."""
        import os

        from click.testing import CliRunner

        from codeindex.cli import main

        # Create minimal project
        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("x = 1\n")

        runner = CliRunner()
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(main, ["init", "--yes"])
        finally:
            os.chdir(original)

        assert result.exit_code == 0
        assert "scan-all" in result.output

    def test_post_init_mentions_review_config(self, tmp_path):
        """Post-init message should guide user to review config and scan."""
        import os

        from click.testing import CliRunner

        from codeindex.cli import main

        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("x = 1\n")

        runner = CliRunner()
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(main, ["init", "--yes"])
        finally:
            os.chdir(original)

        assert result.exit_code == 0
        # Should mention reviewing config and running scan-all
        assert "Review .codeindex.yaml" in result.output
        assert "scan-all" in result.output

    def test_generated_config_seeds_recommended_ai_command(self, tmp_path):
        """Generated config seeds ``RECOMMENDED_AI_COMMAND`` so first
        ``scan-all --ai`` works without an "AI not configured" wall
        (GH #75).

        Contract change vs the pre-#75 behavior: AI used to be opt-in at
        BOTH layers (yaml field absent AND ``--ai`` flag required), but
        the doubly-opt-in path broke the most common workflow — agent/
        user reads CLAUDE.md, runs ``init --yes`` then ``scan-all --ai``,
        hits a confusing error. AI remains opt-in at the CLI flag level
        (``--ai`` is still required to enable enrichment); seeding the
        yaml just removes the wall when the user does opt in.
        """
        import os

        from click.testing import CliRunner

        from codeindex.cli import main
        from codeindex.config import RECOMMENDED_AI_COMMAND, Config

        src = tmp_path / "src"
        src.mkdir()
        (src / "main.py").write_text("x = 1\n")

        runner = CliRunner()
        original = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = runner.invoke(main, ["init", "--yes"])
        finally:
            os.chdir(original)

        assert result.exit_code == 0

        config = Config.load(tmp_path / ".codeindex.yaml")
        assert config.ai_command == RECOMMENDED_AI_COMMAND, (
            f"init --yes should seed RECOMMENDED_AI_COMMAND so first "
            f"`scan --ai` works (GH #75). got: {config.ai_command!r}"
        )
