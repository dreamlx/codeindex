"""Tests for AI enrichment module (Epic 25, Story 25.2).

Tests the prompt construction and blockquote injection logic.
AI invocation is mocked — we only test the structural parts.
"""

from pathlib import Path

from codeindex.enricher import (
    build_enrich_prompt,
    extract_summary_from_readme,
    extract_symbol_summary,
    inject_blockquote,
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
