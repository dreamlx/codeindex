"""
Unit tests for codeindex CLAUDE.md management.

Tests the unified marker-based injection and version checking.
"""

from unittest.mock import patch

from codeindex.claude_md import (
    MARKER_PATTERN,
    build_section,
    check_outdated,
    extract_version,
    find_removed_command_docs,
    inject,
)


class TestExtractVersion:
    """Tests for version extraction from CLAUDE.md markers."""

    def test_extract_version_from_new_marker(self, tmp_path):
        """Should extract version from new-format marker."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Test\n"
            "<!-- codeindex:start v0.23.0 -->\n"
            "Content\n"
            "<!-- codeindex:end -->\n"
        )
        assert extract_version(claude_md) == "0.23.0"

    def test_extract_version_returns_none_if_no_marker(self, tmp_path):
        """Should return None if no marker exists."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test\nNo markers here")
        assert extract_version(claude_md) is None

    def test_extract_version_handles_missing_file(self, tmp_path):
        """Should return None for missing file."""
        nonexistent = tmp_path / "does_not_exist.md"
        assert extract_version(nonexistent) is None

    def test_extract_version_old_marker_without_version(self, tmp_path):
        """Should return None for old marker without version."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "<!-- codeindex:start -->\n"
            "Old content\n"
            "<!-- codeindex:end -->\n"
        )
        assert extract_version(claude_md) is None


class TestBuildSection:
    """Tests for section building."""

    def test_build_section_with_explicit_version(self):
        """Should build section with given version."""
        section = build_section("1.2.3")
        assert "<!-- codeindex:start v1.2.3 -->" in section
        assert "<!-- codeindex:end -->" in section
        assert "v1.2.3" in section

    def test_build_section_contains_quick_commands(self):
        """Should include quick commands in section."""
        section = build_section("0.23.0")
        assert "codeindex scan-all" in section
        assert "codeindex --help" in section

    def test_build_section_contains_update_hint(self):
        """Should include upgrade reminder."""
        section = build_section("0.23.0")
        assert "codeindex claude-md update" in section

    def test_build_section_does_not_hardcode_language_extensions(self):
        """Regression for GH #77.

        The template used to say 'read the actual .py / .php / .java / etc.'
        as a generic instruction — fine for Python/PHP/Java projects, but
        on a pure TS/Swift/Go project it tells the agent to read files
        that don't exist. Replace with language-neutral wording.
        """
        section = build_section("0.23.0")
        # The original template embedded examples as inline markdown code:
        # ``read the actual `.py` / `.php` / `.java` / etc.``
        # Match the backtick-wrapped form so we catch the literal example
        # but don't false-positive on a stray `.py` somewhere else.
        for hardcoded in ("`.py`", "`.php`", "`.java`"):
            assert hardcoded not in section, (
                f"Template hardcodes {hardcoded} as a language example "
                f"(GH #77). The injected section is project-locale-blind; "
                f"hardcoded examples must be language-neutral."
            )

    def test_build_section_does_not_advertise_alternative_backends(self):
        """Regression for GH #77.

        The template used to list `opencode run` and `gemini -p` as
        alternative ai_command backends in the failure-troubleshooting
        block. For a user/project that picked a specific backend (claude),
        these are noise that dilutes the section's signal density and
        makes the injection feel like it doesn't understand the project.
        Switching backends is now linked-to rather than inlined.
        """
        section = build_section("0.23.0")
        for backend in ("opencode run", "gemini -p"):
            assert backend not in section, (
                f"Template hardcodes alternative backend {backend!r} "
                f"in the injected CLAUDE.md section (GH #77). "
                f"Backend swap belongs in `codeindex --help`, not in "
                f"every project's CLAUDE.md."
            )


class TestInject:
    """Tests for CLAUDE.md injection."""

    def test_inject_creates_new_file(self, tmp_path):
        """Should create CLAUDE.md if it doesn't exist."""
        claude_md = tmp_path / "CLAUDE.md"
        assert inject(claude_md, "0.23.0") is True
        assert claude_md.exists()

        content = claude_md.read_text()
        assert "<!-- codeindex:start v0.23.0 -->" in content
        assert "<!-- codeindex:end -->" in content

    def test_inject_appends_to_existing_file(self, tmp_path):
        """Should append section to existing file without markers."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# My Project\n\nExisting content")

        assert inject(claude_md, "0.23.0") is True

        content = claude_md.read_text()
        assert "# My Project" in content
        assert "Existing content" in content
        assert "<!-- codeindex:start v0.23.0 -->" in content

    def test_inject_replaces_existing_section(self, tmp_path):
        """Should replace existing section between markers."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Header\n\n"
            "<!-- codeindex:start v0.22.0 -->\n"
            "Old content\n"
            "<!-- codeindex:end -->\n\n"
            "# Footer\n"
        )

        assert inject(claude_md, "0.23.0") is True

        content = claude_md.read_text()
        assert "<!-- codeindex:start v0.23.0 -->" in content
        assert "v0.22.0" not in content
        assert "Old content" not in content
        assert "# Header" in content
        assert "# Footer" in content

    def test_inject_replaces_old_format_markers(self, tmp_path):
        """Should replace old-format markers (without version)."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Header\n\n"
            "<!-- codeindex:start -->\n"
            "Old content\n"
            "<!-- codeindex:end -->\n\n"
            "# Footer\n"
        )

        assert inject(claude_md, "0.23.0") is True

        content = claude_md.read_text()
        assert "<!-- codeindex:start v0.23.0 -->" in content
        assert content.count("codeindex:start") == 1

    def test_inject_idempotent(self, tmp_path):
        """Multiple injections should produce same result."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# Test\n")

        inject(claude_md, "0.23.0")
        content_1 = claude_md.read_text()

        inject(claude_md, "0.23.0")
        content_2 = claude_md.read_text()

        assert content_1 == content_2
        assert content_2.count("codeindex:start") == 1

    def test_inject_preserves_surrounding_content(self, tmp_path):
        """Should preserve content before and after section."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "# Before\nImportant\n\n"
            "<!-- codeindex:start v0.22.0 -->\n"
            "Old\n"
            "<!-- codeindex:end -->\n\n"
            "# After\nAlso important"
        )

        inject(claude_md, "0.23.0")

        content = claude_md.read_text()
        assert "# Before\nImportant" in content
        assert "# After\nAlso important" in content


class TestCheckOutdated:
    """Tests for version check."""

    def test_returns_none_if_no_claude_md(self, tmp_path):
        """Should return None if CLAUDE.md doesn't exist."""
        assert check_outdated(tmp_path) is None

    def test_returns_none_if_no_markers(self, tmp_path):
        """Should return None if no codeindex markers."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("# No markers\n")
        assert check_outdated(tmp_path) is None

    def test_returns_none_if_up_to_date(self, tmp_path):
        """Should return None if version matches."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("<!-- codeindex:start v9.9.9 -->\n<!-- codeindex:end -->\n")

        with patch("codeindex.claude_md._get_current_version", return_value="9.9.9"):
            assert check_outdated(tmp_path) is None

    def test_returns_old_version_if_outdated(self, tmp_path):
        """Should return old version if update needed."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("<!-- codeindex:start v0.22.0 -->\n<!-- codeindex:end -->\n")

        with patch("codeindex.claude_md._get_current_version", return_value="0.23.0"):
            assert check_outdated(tmp_path) == "0.22.0"


class TestRemovedCommandDocs:
    """GH #177: after the v0.37.0 BREAKING removal of the post-commit hook
    (#167), CLAUDE.md sections injected by older templates still document
    deleted commands (``hooks rerun``, ``hooks install post-commit``, the
    hidden ``hooks run``, the ``hooks.post_commit`` config). An AI agent
    following the stale section runs the deleted commands and hits
    "No such command". The startup hint must detect these stale docs and
    escalate (not just a generic "run update")."""

    def test_detects_rerun_in_old_section(self, tmp_path):
        """The v0.33.3-era template carried `hooks rerun post-commit`; a
        CLAUDE.md with that section must flag the deleted command."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "<!-- codeindex:start v0.33.3 -->\n"
            "## codeindex\n"
            "codeindex hooks rerun post-commit\n"
            "<!-- codeindex:end -->\n"
        )
        hits = find_removed_command_docs(tmp_path)
        assert "hooks rerun" in hits, hits

    def test_detects_install_post_commit_and_config(self, tmp_path):
        """``hooks install post-commit`` and the ``hooks.post_commit`` config
        section were also removed (#167)."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(
            "<!-- codeindex:start v0.33.0 -->\n"
            "To enable: `codeindex hooks install post-commit`\n"
            "Configure in `hooks.post_commit` section.\n"
            "<!-- codeindex:end -->\n"
        )
        hits = find_removed_command_docs(tmp_path)
        assert "hooks install post-commit" in hits, hits
        assert "post_commit" in hits, hits

    def test_current_template_has_no_removed_commands(self, tmp_path):
        """The current template (v0.37) must not document any removed command
        — regression guard that the shipped section stays clean so a fresh
        `claude-md update` doesn't reintroduce the stale docs."""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(build_section("0.37.0"))
        assert find_removed_command_docs(tmp_path) == [], "current template flags removed commands"

    def test_no_claude_md_returns_empty(self, tmp_path):
        """No CLAUDE.md → nothing to scan → empty list (don't error)."""
        assert find_removed_command_docs(tmp_path) == []

    def test_no_markers_returns_empty(self, tmp_path):
        """A CLAUDE.md without codeindex markers has no codeindex section to
        scan — the stale-docs check only covers the injected section, not
        user prose (avoids false positives on host-authored content)."""
        (tmp_path / "CLAUDE.md").write_text("# My notes\nI use hooks rerun manually\n")
        assert find_removed_command_docs(tmp_path) == []


class TestVersionSourceConsistency:
    """GH #161: one version source everywhere.

    _get_current_version previously did its own importlib-first lookup while
    the hint print used module __version__ — under an editable install with
    stale dist-info, a fresh CLAUDE.md triggered a self-contradictory
    "v0.35.1 vs v0.35.1, run update" hint.
    """

    def test_get_current_version_matches_module_version(self):
        from codeindex import __version__
        from codeindex.claude_md import _get_current_version

        assert _get_current_version() == __version__

    def test_stale_dist_info_does_not_leak(self):
        """Even with importlib metadata disagreeing (editable install with
        stale dist-info), the check must follow the module resolver."""
        import importlib.metadata as _m
        from unittest.mock import patch as _patch

        from codeindex import __version__
        from codeindex.claude_md import _get_current_version

        with _patch.object(_m, "version", return_value="0.0.1"):
            assert _get_current_version() == __version__

    def test_fresh_claude_md_not_flagged_despite_stale_dist_info(self, tmp_path):
        """End-to-end property: CLAUDE.md at the current version must NOT be
        flagged, whatever dist-info claims (the original #161 symptom)."""
        import importlib.metadata as _m
        from unittest.mock import patch as _patch

        from codeindex import __version__

        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text(f"<!-- codeindex:start v{__version__} -->\n<!-- codeindex:end -->\n")

        with _patch.object(_m, "version", return_value="0.0.1"):
            assert check_outdated(tmp_path) is None

    def test_print_outdated_warning_goes_to_stderr(self, capsys):
        """The startup hint must not pollute stdout (breaks --output json)."""
        from unittest.mock import patch as _patch

        from codeindex.cli_claude_md import print_outdated_warning

        with _patch("codeindex.cli_claude_md.check_outdated", return_value="0.1.0"):
            print_outdated_warning()

        captured = capsys.readouterr()
        assert "hint:" in captured.err
        assert captured.out == ""

    def test_removed_docs_warning_escalates_to_stderr(self, capsys):
        """GH #177: when the codeindex section documents deleted commands,
        the startup hint must escalate to a specific warning (name the
        removed mechanisms + the new refresh policy), not a generic
        "run update". Still stderr (stdout stays clean for --output json)."""
        from unittest.mock import patch as _patch

        from codeindex.cli_claude_md import print_outdated_warning

        with _patch("codeindex.cli_claude_md.check_outdated", return_value=None), \
             _patch(
                 "codeindex.cli_claude_md.find_removed_command_docs",
                 return_value=["hooks rerun", "post_commit"],
             ):
            print_outdated_warning()

        captured = capsys.readouterr()
        assert captured.out == ""
        # Rich wraps at the terminal width, so normalize whitespace before
        # asserting (the wrapping can split "hooks rerun" across lines).
        err = " ".join(captured.err.split())
        # escalates — names the removed mechanism, not generic
        assert "removed" in err.lower()
        assert "hooks rerun" in err
        # points at the fix
        assert "claude-md update" in err
        # states the new refresh policy (so the reader knows what changed)
        assert "scan-all" in err.lower()


class TestMarkerPattern:
    """Tests for marker regex pattern."""

    def test_matches_new_format(self):
        """Should match new format with version."""
        text = "<!-- codeindex:start v0.23.0 -->\ncontent\n<!-- codeindex:end -->"
        assert MARKER_PATTERN.search(text) is not None

    def test_matches_old_format(self):
        """Should match old format without version."""
        text = "<!-- codeindex:start -->\ncontent\n<!-- codeindex:end -->"
        assert MARKER_PATTERN.search(text) is not None

    def test_no_match_without_markers(self):
        """Should not match text without markers."""
        text = "# Just a regular CLAUDE.md\nNo markers here"
        assert MARKER_PATTERN.search(text) is None
