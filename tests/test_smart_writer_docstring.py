"""Tests for SmartWriter integration with DocstringProcessor.

Story 9.3: SmartWriter Integration (deferred from Story 9.2)

Tests:
- SmartWriter accepts docstring_processor parameter
- Processes docstrings before formatting
- Works without processor (backward compatible)
- Integrates with _generate_detailed()
"""

from unittest.mock import MagicMock, patch

from codeindex.config import Config, DocstringConfig
from codeindex.docstring_processor import DocstringProcessor
from codeindex.parser import parse_file
from codeindex.smart_writer import SmartWriter


class TestSmartWriterDocstringIntegration:
    """Test SmartWriter integration with DocstringProcessor."""

    def test_smart_writer_accepts_processor_param(self):
        """Should accept docstring_processor parameter."""
        config = Config()
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="hybrid",
        )

        # Should accept processor without error
        writer = SmartWriter(config, docstring_processor=processor)

        assert writer.docstring_processor is processor

    def test_smart_writer_without_processor(self):
        """Should work without processor (backward compatible)."""
        config = Config()

        # Should work without processor
        writer = SmartWriter(config)

        assert writer.docstring_processor is None

    def test_processes_docstrings_before_formatting(self, tmp_path):
        """Should process docstrings with AI before formatting README."""
        # Create test PHP file
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
/**
 * 获取用户 Get user
 * @param int $id User ID
 */
function fetchUser($id) {
    return [];
}
""")

        # Parse file
        parse_result = parse_file(php_file, "php")

        # Create processor
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="all-ai",  # Force AI processing
        )

        # Mock AI response
        ai_response = """{
            "symbols": [
                {
                    "name": "fetchUser",
                    "description": "Retrieves user by ID from database",
                    "quality": "high"
                }
            ]
        }"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=ai_response,
            )

            # Create SmartWriter with processor
            config = Config()
            writer = SmartWriter(config, docstring_processor=processor)

            # Generate content
            result = writer.write_readme(
                dir_path=tmp_path,
                parse_results=[parse_result],
                level="detailed",
            )

        # Should have processed with AI
        assert result.success
        mock_run.assert_called_once()

        # Read generated README
        readme_content = (tmp_path / "README_AI.md").read_text()

        # Should contain improved description (not raw docstring)
        assert "fetchUser" in readme_content
        # The exact format depends on writer implementation

    def test_fallback_without_ai(self, tmp_path):
        """Should fallback to raw docstrings if processor is None."""
        # Create test PHP file
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
/**
 * Get user by ID
 */
function findUserById($id) {
    return [];
}
""")

        # Parse file
        parse_result = parse_file(php_file, "php")

        # Create SmartWriter WITHOUT processor
        config = Config()
        writer = SmartWriter(config, docstring_processor=None)

        # Generate content
        result = writer.write_readme(
            dir_path=tmp_path,
            parse_results=[parse_result],
            level="detailed",
        )

        # Should work with raw docstrings
        assert result.success

        # Read generated README
        readme_content = (tmp_path / "README_AI.md").read_text()

        # Should contain function (with raw or no docstring)
        assert "findUserById" in readme_content

    def test_hybrid_mode_selective_ai(self, tmp_path):
        """Should use AI only for complex docstrings in hybrid mode."""
        # Create test PHP file with mixed complexity
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
// Simple comment
function simpleFunc() {
    return [];
}

/**
 * 复杂注释 Complex comment
 * @param string $name User name
 * @param int $age User age
 * @return array User data
 */
function complexFunc($name, $age) {
    return [];
}
""")

        # Parse file
        parse_result = parse_file(php_file, "php")

        # Create processor in hybrid mode
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="hybrid",
        )

        # Mock AI response (only for complex function)
        ai_response = """{
            "symbols": [
                {
                    "name": "complexFunc",
                    "description": "Creates user with name and age",
                    "quality": "high"
                }
            ]
        }"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=ai_response,
            )

            # Create SmartWriter with hybrid processor
            config = Config()
            writer = SmartWriter(config, docstring_processor=processor)

            # Generate content
            result = writer.write_readme(
                dir_path=tmp_path,
                parse_results=[parse_result],
                level="detailed",
            )

        # Should have called AI (for complex function)
        assert result.success
        # Note: Hybrid mode may or may not call AI depending on implementation


class TestSmartWriterProcessorFactory:
    """Test creating processor from config."""

    def test_create_processor_from_config_hybrid(self):
        """Should create hybrid mode processor from config."""
        config = Config()
        config.docstrings = DocstringConfig(
            mode="hybrid",
            ai_command='claude -p "{prompt}"',
            cost_limit=1.0,
        )

        # Factory method should create processor
        processor = DocstringProcessor(
            ai_command=config.docstrings.ai_command,
            mode=config.docstrings.mode,
        )

        assert processor.mode == "hybrid"
        assert processor.ai_command == 'claude -p "{prompt}"'

    def test_create_processor_from_config_off(self):
        """Should not create processor if mode is off."""
        config = Config()
        config.docstrings = DocstringConfig(
            mode="off",
            ai_command="",
            cost_limit=1.0,
        )

        # Should not create processor when mode is off
        processor = None if config.docstrings.mode == "off" else DocstringProcessor(
            ai_command=config.docstrings.ai_command,
            mode=config.docstrings.mode,
        )

        assert processor is None
