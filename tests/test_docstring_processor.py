"""Tests for DocstringProcessor module.

Story 9.1: Docstring Processor Core

Tests:
- Hybrid mode: Simple extraction without AI
- Hybrid mode: AI for complex comments
- All-AI mode: AI processes everything
- Batch processing: Single AI call per file
- Fallback on AI failure
- Cost tracking
- JSON parsing with malformed responses
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

from codeindex.docstring_processor import DocstringProcessor
from codeindex.parser import Symbol


class TestDocstringProcessor:
    """Test DocstringProcessor class."""

    def test_init_with_hybrid_mode(self):
        """Should initialize with hybrid mode."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="hybrid",
        )

        assert processor.mode == "hybrid"
        assert processor.ai_command == 'claude -p "{prompt}"'

    def test_init_with_all_ai_mode(self):
        """Should initialize with all-AI mode."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="all-ai",
        )

        assert processor.mode == "all-ai"

    def test_hybrid_mode_simple_extraction(self):
        """Should extract simple docstrings without AI."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="hybrid",
        )

        # Simple, clean English docstring
        symbols = [
            Symbol(
                name="get_user",
                kind="function",
                signature="def get_user(id):",
                docstring="Get user by ID",
                line_start=10,
                line_end=15,
            )
        ]

        # Mock AI CLI to ensure it's NOT called
        with patch("subprocess.run") as mock_run:
            result = processor.process_file(Path("test.py"), symbols)

            # AI should NOT be called for simple docstring
            mock_run.assert_not_called()

        assert "get_user" in result
        assert result["get_user"] == "Get user by ID"

    def test_hybrid_mode_ai_for_complex(self):
        """Should use AI for complex/irregular comments."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="hybrid",
        )

        # Complex docstring with mixed language and structure
        symbols = [
            Symbol(
                name="getUserList",
                kind="method",
                signature="public function getUserList():",
                docstring="""
                /**
                 * 获取用户列表 Get user list
                 * @param int $page 页码
                 * @param int $limit 每页数量
                 * @return array User list data
                 */
                """,
                line_start=20,
                line_end=30,
            )
        ]

        # Mock AI CLI response
        ai_response = """{
            "symbols": [
                {
                    "name": "getUserList",
                    "description": "Retrieves paginated user list with filtering",
                    "quality": "high"
                }
            ]
        }"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=ai_response,
            )

            result = processor.process_file(Path("test.php"), symbols)

            # AI SHOULD be called for complex docstring
            mock_run.assert_called_once()

        assert "getUserList" in result
        assert result["getUserList"] == "Retrieves paginated user list with filtering"

    def test_all_ai_mode(self):
        """Should use AI for all docstrings in all-AI mode."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="all-ai",
        )

        symbols = [
            Symbol(
                name="simple_func",
                kind="function",
                signature="def simple_func():",
                docstring="Simple function",
                line_start=10,
                line_end=15,
            ),
            Symbol(
                name="another_func",
                kind="function",
                signature="def another_func():",
                docstring="Another simple function",
                line_start=20,
                line_end=25,
            ),
        ]

        # Mock AI response
        ai_response = """{
            "symbols": [
                {
                    "name": "simple_func",
                    "description": "Executes simple operation",
                    "quality": "high"
                },
                {
                    "name": "another_func",
                    "description": "Performs another operation",
                    "quality": "high"
                }
            ]
        }"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=ai_response,
            )

            result = processor.process_file(Path("test.py"), symbols)

            # AI SHOULD be called even for simple docstrings
            mock_run.assert_called_once()

        assert "simple_func" in result
        assert result["simple_func"] == "Executes simple operation"
        assert "another_func" in result
        assert result["another_func"] == "Performs another operation"

    def test_batch_processing(self):
        """Should make single AI call per file (not per symbol)."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="all-ai",
        )

        # 10 symbols in one file
        symbols = [
            Symbol(
                name=f"func_{i}",
                kind="function",
                signature=f"def func_{i}():",
                docstring=f"Function {i}",
                line_start=i * 10,
                line_end=i * 10 + 5,
            )
            for i in range(10)
        ]

        # Mock AI response with all 10 symbols
        ai_response = """{
            "symbols": [
                {"name": "func_0", "description": "Desc 0", "quality": "high"},
                {"name": "func_1", "description": "Desc 1", "quality": "high"},
                {"name": "func_2", "description": "Desc 2", "quality": "high"},
                {"name": "func_3", "description": "Desc 3", "quality": "high"},
                {"name": "func_4", "description": "Desc 4", "quality": "high"},
                {"name": "func_5", "description": "Desc 5", "quality": "high"},
                {"name": "func_6", "description": "Desc 6", "quality": "high"},
                {"name": "func_7", "description": "Desc 7", "quality": "high"},
                {"name": "func_8", "description": "Desc 8", "quality": "high"},
                {"name": "func_9", "description": "Desc 9", "quality": "high"}
            ]
        }"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=ai_response,
            )

            result = processor.process_file(Path("test.py"), symbols)

            # Should be called ONCE (batch processing)
            assert mock_run.call_count == 1

        # All 10 symbols should be processed
        assert len(result) == 10
        for i in range(10):
            assert f"func_{i}" in result

    def test_fallback_on_ai_failure(self):
        """Should fallback to simple extraction if AI fails."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="all-ai",
        )

        symbols = [
            Symbol(
                name="test_func",
                kind="function",
                signature="def test_func():",
                docstring="Test function with fallback",
                line_start=10,
                line_end=15,
            )
        ]

        # Mock AI failure (non-zero exit code)
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="AI error",
            )

            result = processor.process_file(Path("test.py"), symbols)

        # Should fallback to simple extraction
        assert "test_func" in result
        assert result["test_func"] == "Test function with fallback"

    def test_cost_tracking(self):
        """Should track token usage and cost."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="all-ai",
        )

        symbols = [
            Symbol(
                name="test_func",
                kind="function",
                signature="def test_func():",
                docstring="Test",
                line_start=10,
                line_end=15,
            )
        ]

        ai_response = """{
            "symbols": [
                {"name": "test_func", "description": "Test function", "quality": "high"}
            ]
        }"""

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=ai_response,
            )

            processor.process_file(Path("test.py"), symbols)

        # Should have cost tracking data
        assert hasattr(processor, "total_tokens")
        assert processor.total_tokens > 0

    def test_json_parsing_malformed(self):
        """Should handle malformed JSON gracefully."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="all-ai",
        )

        symbols = [
            Symbol(
                name="test_func",
                kind="function",
                signature="def test_func():",
                docstring="Test function",
                line_start=10,
                line_end=15,
            )
        ]

        # Mock malformed JSON response
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="{ invalid json",
            )

            result = processor.process_file(Path("test.py"), symbols)

        # Should fallback to simple extraction
        assert "test_func" in result
        assert result["test_func"] == "Test function"

    def test_empty_docstring_handling(self):
        """Should handle symbols without docstrings."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="hybrid",
        )

        symbols = [
            Symbol(
                name="no_doc",
                kind="function",
                signature="def no_doc():",
                docstring="",
                line_start=10,
                line_end=15,
            )
        ]

        result = processor.process_file(Path("test.py"), symbols)

        # Should return empty string or omit
        assert "no_doc" not in result or result["no_doc"] == ""

    def test_should_use_ai_logic(self):
        """Test _should_use_ai decision logic."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="hybrid",
        )

        # Simple English → No AI
        assert processor._should_use_ai("Get user list") is False

        # Empty → No AI
        assert processor._should_use_ai("") is False

        # Long → AI
        assert processor._should_use_ai("A" * 70) is True

        # Multi-line → AI
        assert processor._should_use_ai("Line 1\nLine 2\nLine 3") is True

        # Mixed language → AI
        assert processor._should_use_ai("获取用户列表 Get user list") is True

        # PHPDoc structure → AI
        assert processor._should_use_ai("/** @param $id User ID */") is True

    def test_fallback_extract(self):
        """Test _fallback_extract method."""
        processor = DocstringProcessor(
            ai_command='claude -p "{prompt}"',
            mode="hybrid",
        )

        # Simple case
        result = processor._fallback_extract("Get user by ID")
        assert result == "Get user by ID"

        # Multi-line: take first line
        result = processor._fallback_extract("Get user\nby ID\nfrom database")
        assert result == "Get user"

        # Too long: truncate to 60 chars
        long_doc = "A" * 100
        result = processor._fallback_extract(long_doc)
        assert len(result) <= 63  # 60 + "..."
        assert result.endswith("...")

        # Mixed language: take first line
        result = processor._fallback_extract("获取用户 Get user\n详细信息")
        assert result == "获取用户 Get user"
