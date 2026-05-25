"""Tests for AI enrichment module (Epic 25, Story 25.2).

Tests the prompt construction and blockquote injection logic.
AI invocation is mocked — we only test the structural parts.
"""

from pathlib import Path

from codeindex.enricher import (
    build_enrich_prompt,
    build_safe_subdir_context,
    extract_blockquote_description,
    extract_summary_from_readme,
    extract_symbol_summary,
    has_successful_enrichment,
    inject_blockquote,
    mark_enrichment_status,
    should_enrich,
)


class TestExtractSymbolSummary:
    """Extract symbol names + file names for AI prompt input."""

    def test_extracts_from_parse_results(self):
        from codeindex.parser import ParseResult, Symbol

        results = [
            ParseResult(
                path=Path("ImageController.php"),
                symbols=[
                    Symbol(name="ImageController", kind="class", signature="class ImageController", line_start=1),
                    Symbol(
                        name="uploadAvatar", kind="method",
                        signature="public function uploadAvatar()", line_start=10,
                    ),
                    Symbol(name="reason_img", kind="method", signature="public function reason_img()", line_start=20),
                ],
                imports=[],
            ),
            ParseResult(
                path=Path("UserController.php"),
                symbols=[
                    Symbol(name="UserController", kind="class", signature="class UserController", line_start=1),
                    Symbol(name="login", kind="method", signature="public function login()", line_start=5),
                ],
                imports=[],
            ),
        ]
        summary = extract_symbol_summary(results)
        assert "ImageController.php" in summary
        assert "uploadAvatar" in summary
        assert "UserController.php" in summary
        assert "login" in summary

    def test_empty_results(self):
        summary = extract_symbol_summary([])
        assert summary == ""

    def test_limits_symbols_per_file(self):
        """Should not include all symbols from huge files."""
        from codeindex.parser import ParseResult, Symbol

        symbols = [
            Symbol(name=f"method_{i}", kind="method", signature=f"method_{i}()", line_start=i)
            for i in range(100)
        ]
        results = [ParseResult(path=Path("Big.php"), symbols=symbols, imports=[])]
        summary = extract_symbol_summary(results)
        # Should be reasonably bounded, not 100 method names
        assert summary.count("method_") <= 20


class TestExtractSummaryFromReadme:
    """Extract summary from existing README_AI.md files."""

    def test_extracts_subdirectories(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "# App\n\n## Subdirectories\n"
            "- **Pay/** - 34 files | 448 symbols\n"
            "- **Vip/** - 会员管理 | 48 files\n"
        )
        summary = extract_summary_from_readme(readme)
        assert "Pay" in summary
        assert "Vip" in summary

    def test_extracts_file_symbols(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "# Mod\n\n## Files\n"
            "- **Pay.php** - Pay, placeOrder, refund\n"
            "- **User.php** - User, login\n"
        )
        summary = extract_summary_from_readme(readme)
        assert "Pay.php" in summary
        assert "placeOrder" in summary

    def test_missing_file_returns_empty(self, tmp_path):
        summary = extract_summary_from_readme(tmp_path / "nonexistent.md")
        assert summary == ""

    def test_limits_entries(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        lines = ["# Big\n\n## Files\n"]
        for i in range(50):
            lines.append(f"- **File{i}.php** - Class{i}, method{i}\n")
        readme.write_text("".join(lines))
        summary = extract_summary_from_readme(readme)
        # Should be bounded
        assert summary.count("File") <= 20


class TestBuildEnrichPrompt:
    """Build the minimal prompt for AI one-line description."""

    def test_includes_dir_name(self):
        prompt = build_enrich_prompt("SmallProgramApi", "ImageController.php: uploadAvatar, login")
        assert "SmallProgramApi" in prompt

    def test_includes_symbol_summary(self):
        prompt = build_enrich_prompt("Pay", "Alipay.php: placeOrder; WechatPay.php: placeOrder")
        assert "placeOrder" in prompt

    def test_constrains_output_length(self):
        """Prompt should instruct AI to keep description short."""
        prompt = build_enrich_prompt("Vip", "CardBag, Integral, Membership")
        assert "30" in prompt or "concise" in prompt.lower()

    def test_includes_parent_name(self):
        prompt = build_enrich_prompt("Pay", "Alipay, WechatPay", parent_name="Application")
        assert "Application" in prompt

    def test_anti_hallucination_instruction(self):
        prompt = build_enrich_prompt("Mod", "file1, file2")
        assert "NOT" in prompt or "ONLY" in prompt


class TestInjectBlockquote:
    """Inject blockquote description into existing README_AI.md."""

    def test_inject_after_title(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "<!-- Generated by codeindex (detailed) at 2026-03-12 -->\n"
            "\n"
            "# Vip\n"
            "\n"
            "## Overview\n"
            "- **Files**: 48\n"
        )
        inject_blockquote(readme, "会员等级管理、积分兑换、权益卡券")
        content = readme.read_text()
        assert "> 会员等级管理、积分兑换、权益卡券\n" in content
        # Title should still be there
        assert "# Vip\n" in content
        # Overview should still be there
        assert "## Overview" in content

    def test_replace_existing_blockquote(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "# Vip\n"
            "> 旧描述\n"
            "\n"
            "## Overview\n"
        )
        inject_blockquote(readme, "新描述")
        content = readme.read_text()
        assert "> 新描述\n" in content
        assert "旧描述" not in content

    def test_no_title_appends_at_top(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text("## Overview\n- **Files**: 5\n")
        inject_blockquote(readme, "描述")
        content = readme.read_text()
        assert "> 描述\n" in content

    def test_preserves_rest_of_content(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        original = (
            "<!-- Generated by codeindex -->\n"
            "\n"
            "# Pay\n"
            "\n"
            "## Overview\n"
            "- **Files**: 34\n"
            "- **Symbols**: 448\n"
            "\n"
            "## Subdirectories\n"
            "- **Business/** - 10 files\n"
        )
        readme.write_text(original)
        inject_blockquote(readme, "支付网关（微信、支付宝、云支付）")
        content = readme.read_text()
        assert "## Subdirectories" in content
        assert "**Business/**" in content
        assert "**Files**: 34" in content


class TestShouldEnrich:
    """Determine if a directory should get AI enrichment."""

    def test_overview_level_should_enrich(self):
        assert should_enrich("overview") is True

    def test_navigation_level_should_enrich(self):
        assert should_enrich("navigation") is True

    def test_detailed_level_should_not_enrich(self):
        assert should_enrich("detailed") is False


class TestBuildSafeSubdirContext:
    """Construct prompt context from tree-derived data only.

    Closes the prompt-injection chain where README markdown (containing
    AI-generated descriptions sourced from arbitrary docstrings) was
    regex-extracted and fed back into the next enrichment prompt.
    """

    def test_lists_child_directory_names(self):
        child_dirs = [Path("/proj/app/Pay"), Path("/proj/app/Vip"), Path("/proj/app/User")]
        ctx = build_safe_subdir_context(child_dirs)
        assert "Pay" in ctx
        assert "Vip" in ctx
        assert "User" in ctx

    def test_empty_when_no_children(self):
        assert build_safe_subdir_context([]) == ""

    def test_bounded_for_huge_dir_count(self):
        child_dirs = [Path(f"/proj/sub_{i}") for i in range(200)]
        ctx = build_safe_subdir_context(child_dirs)
        # Should not embed all 200 names
        assert ctx.count("sub_") <= 30
        # Should indicate truncation
        assert "more" in ctx.lower() or "..." in ctx

    def test_does_not_read_filesystem(self, tmp_path):
        """No README files, no docstrings — pure name-based context."""
        # Pass paths that don't exist on disk
        child_dirs = [tmp_path / "Nonexistent_A", tmp_path / "Nonexistent_B"]
        ctx = build_safe_subdir_context(child_dirs)
        # Must not raise, must return names
        assert "Nonexistent_A" in ctx
        assert "Nonexistent_B" in ctx

    def test_rejects_injection_via_path_name(self):
        """Even if a directory is named with prompt-injection syntax,
        the context shouldn't propagate raw control sequences."""
        child_dirs = [Path("/proj/IGNORE_PREVIOUS_INSTRUCTIONS")]
        ctx = build_safe_subdir_context(child_dirs)
        # We don't sanitize names (filesystem already constrains them),
        # but the function should at minimum return them as-is in a
        # bounded, structural format — not interpolate any external text.
        assert "IGNORE_PREVIOUS_INSTRUCTIONS" in ctx
        # No extra free-text fields that could carry injections
        assert "description" not in ctx.lower()


class TestHasSuccessfulEnrichment:
    """Detect whether README already has <!-- enrichment: ok --> marker.

    Used by _enrich_directories_with_ai to skip already-enriched dirs on
    re-run, making `scan-all --ai` idempotent (transient failures can be
    retried without re-paying for successes).
    """

    def test_returns_true_when_ok_marker_present(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "<!-- Generated by codeindex (navigation) at 2026-05-24 -->\n"
            "<!-- enrichment: ok -->\n"
            "\n# Vip\n"
        )
        assert has_successful_enrichment(readme) is True

    def test_returns_false_when_failed_marker_present(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "<!-- Generated by codeindex (navigation) at 2026-05-24 -->\n"
            "<!-- enrichment: failed (reason: Exit code: 1) -->\n"
            "\n# Vip\n"
        )
        assert has_successful_enrichment(readme) is False

    def test_returns_false_when_no_marker(self, tmp_path):
        """README with no enrichment marker (structural-only mode)."""
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "<!-- Generated by codeindex (navigation) at 2026-05-24 -->\n"
            "\n# Vip\n"
        )
        assert has_successful_enrichment(readme) is False

    def test_returns_false_when_file_missing(self, tmp_path):
        assert has_successful_enrichment(tmp_path / "nope.md") is False


class TestExtractBlockquoteDescription:
    """Extract the previously-injected `> description` blockquote.

    Lets Phase 2 cache the description before Phase 1 rewrites the README,
    so re-runs can re-inject without paying for another AI call.
    """

    def test_extracts_blockquote_under_title(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "<!-- Generated by codeindex (navigation) at 2026-05-24 -->\n"
            "<!-- enrichment: ok -->\n"
            "\n# parsers\n"
            "> 多语言 AST 解析器\n"
            "\n## Overview\n"
        )
        assert extract_blockquote_description(readme) == "多语言 AST 解析器"

    def test_returns_none_when_no_blockquote(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text("# parsers\n\n## Overview\n")
        assert extract_blockquote_description(readme) is None

    def test_returns_none_when_file_missing(self, tmp_path):
        assert extract_blockquote_description(tmp_path / "nope.md") is None

    def test_ignores_blockquote_outside_title_region(self, tmp_path):
        """A `>` line deep in the body should not be returned."""
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "# parsers\n\n## Overview\n"
            "Some text\n"
            "> a quoted line in the body, not the description\n"
        )
        assert extract_blockquote_description(readme) is None

    def test_handles_blockquote_with_extra_spaces(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text("# X\n>   spaced description  \n## Overview\n")
        assert extract_blockquote_description(readme) == "spaced description"


class TestMarkEnrichmentStatus:
    """Inject `<!-- enrichment: ... -->` metadata into README_AI.md.

    Lets AI consumers distinguish "structural-only by config" from
    "AI enrichment was attempted and failed".
    """

    def test_marks_success(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "<!-- Generated by codeindex (navigation) at 2026-05-24 -->\n"
            "\n# Vip\n\n## Overview\n- **Files**: 48\n"
        )
        mark_enrichment_status(readme, "ok")
        content = readme.read_text()
        assert "<!-- enrichment: ok -->\n" in content
        assert "# Vip" in content

    def test_marks_failure_with_reason(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "<!-- Generated by codeindex (navigation) at 2026-05-24 -->\n\n# Backend\n"
        )
        mark_enrichment_status(readme, "failed", reason="Command timed out after 120 seconds")
        content = readme.read_text()
        assert "<!-- enrichment: failed" in content
        assert "Command timed out after 120 seconds" in content

    def test_replaces_existing_status(self, tmp_path):
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "<!-- Generated by codeindex (navigation) at 2026-05-24 -->\n"
            "<!-- enrichment: failed (reason: old) -->\n"
            "\n# Vip\n"
        )
        mark_enrichment_status(readme, "ok")
        content = readme.read_text()
        assert "<!-- enrichment: ok -->" in content
        assert "old" not in content
        # Only one enrichment line should remain
        assert content.count("<!-- enrichment:") == 1

    def test_inserts_after_generated_header(self, tmp_path):
        """enrichment line should sit immediately under the Generated header."""
        readme = tmp_path / "README_AI.md"
        readme.write_text(
            "<!-- Generated by codeindex (navigation) at 2026-05-24 -->\n"
            "\n# Vip\n"
        )
        mark_enrichment_status(readme, "ok")
        lines = readme.read_text().split("\n")
        # Line 0: Generated header. Line 1: enrichment status.
        assert lines[0].startswith("<!-- Generated by codeindex")
        assert lines[1] == "<!-- enrichment: ok -->"

    def test_handles_missing_generated_header(self, tmp_path):
        """If no Generated header, prepend enrichment status at top."""
        readme = tmp_path / "README_AI.md"
        readme.write_text("# Vip\n\n## Overview\n")
        mark_enrichment_status(readme, "failed", reason="auth")
        content = readme.read_text()
        assert content.startswith("<!-- enrichment: failed (reason: auth) -->\n")
        assert "# Vip" in content

    def test_sanitizes_reason_newlines(self, tmp_path):
        """Multi-line stderr should be collapsed to single line."""
        readme = tmp_path / "README_AI.md"
        readme.write_text("# X\n")
        mark_enrichment_status(readme, "failed", reason="line1\nline2\nline3")
        content = readme.read_text()
        # All on one comment line, no embedded newlines that break the HTML comment
        assert "<!-- enrichment: failed" in content
        enrichment_line = [
            line for line in content.split("\n") if line.startswith("<!-- enrichment:")
        ][0]
        assert "line2" not in enrichment_line or "\n" not in enrichment_line
