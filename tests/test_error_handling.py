"""Tests for error handling in JSON output mode.

Story 4: Structured error handling for JSON output.

Tests:
- Command-level errors (directory not found, no config)
- File-level errors (parse errors, already handled)
- Error JSON structure validation
"""

import json

from click.testing import CliRunner

from codeindex.cli_scan import scan, scan_all


class TestCommandLevelErrors:
    """Test command-level errors return structured JSON."""

    def test_scan_directory_not_found_json(self, tmp_path):
        """Should return error JSON when directory doesn't exist."""
        runner = CliRunner()

        nonexistent = tmp_path / "nonexistent"

        result = runner.invoke(scan, [str(nonexistent), "--output", "json"])

        # Should fail with exit code 1
        assert result.exit_code == 1

        # Should output valid JSON with error
        data = json.loads(result.output)

        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "DIRECTORY_NOT_FOUND"
        assert "does not exist" in data["error"]["message"].lower()
        assert str(nonexistent) in data["error"]["message"]

        # Should have empty results
        assert data["results"] == []
        assert data["summary"]["total_files"] == 0
        assert data["summary"]["errors"] == 1

    def test_scan_all_no_config_json(self, tmp_path):
        """Should return error JSON when no .codeindex.yaml found."""
        runner = CliRunner()

        # Empty directory, no config
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                scan_all, ["--root", str(empty_dir), "--output", "json"]
            )

        # Should fail with exit code 1
        assert result.exit_code == 1

        # Should output valid JSON with error
        data = json.loads(result.output)

        assert data["success"] is False
        assert "error" in data
        assert data["error"]["code"] == "NO_CONFIG_FOUND"
        assert ".codeindex.yaml" in data["error"]["message"]

    def test_scan_empty_directory_json(self, tmp_path):
        """Should succeed with empty results, not error."""
        runner = CliRunner()

        # Empty directory with config
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
include: ["."]
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                scan, [str(empty_dir), "--fallback", "--output", "json", "--quiet"]
            )

        # Should succeed (exit code 0)
        assert result.exit_code == 0

        # Should output valid JSON with no errors
        data = json.loads(result.output)

        assert data["success"] is True
        assert "error" not in data  # No command-level error
        assert data["results"] == []
        assert data["summary"]["total_files"] == 0
        assert data["summary"]["errors"] == 0


class TestErrorObjectStructure:
    """Test error object has correct structure."""

    def test_error_object_has_required_fields(self, tmp_path):
        """Error object should have code, message, detail fields."""
        runner = CliRunner()

        nonexistent = tmp_path / "nonexistent"

        result = runner.invoke(scan, [str(nonexistent), "--output", "json"])

        data = json.loads(result.output)
        error = data["error"]

        # Check all required fields
        assert "code" in error
        assert "message" in error
        assert "detail" in error

        # Code should be uppercase string
        assert isinstance(error["code"], str)
        assert error["code"].isupper()
        assert "_" in error["code"]  # e.g., DIRECTORY_NOT_FOUND

        # Message should be descriptive
        assert isinstance(error["message"], str)
        assert len(error["message"]) > 10

        # Detail can be None
        assert error["detail"] is None or isinstance(error["detail"], str)


class TestFileLevelErrors:
    """Test file-level errors are properly recorded."""

    def test_parse_error_recorded_in_result(self, tmp_path):
        """Parse errors should be in result.error field."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Create file with syntax error
        (test_dir / "broken.py").write_text("def broken(")

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
include: ["."]
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                scan, [str(test_dir), "--fallback", "--output", "json", "--quiet"]
            )

        # Should succeed (partial success)
        assert result.exit_code == 0

        data = json.loads(result.output)

        # Success is still True (partial success)
        assert data["success"] is True

        # No command-level error
        assert "error" not in data

        # But file has error
        assert len(data["results"]) == 1
        assert data["results"][0]["error"] is not None
        assert "error" in data["results"][0]["error"].lower() or \
               "syntax" in data["results"][0]["error"].lower()

        # Summary shows error count
        assert data["summary"]["errors"] == 1

    def test_mixed_success_and_error_files(self, tmp_path):
        """Should handle mix of good and broken files."""
        runner = CliRunner()

        test_dir = tmp_path / "test"
        test_dir.mkdir()

        # Good file
        (test_dir / "good.py").write_text("def good(): pass")

        # Broken file
        (test_dir / "broken.py").write_text("def broken(")

        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
include: ["."]
languages: ["python"]
""")

        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(
                scan, [str(test_dir), "--fallback", "--output", "json", "--quiet"]
            )

        # Should succeed
        assert result.exit_code == 0

        data = json.loads(result.output)

        # Should have 2 results
        assert len(data["results"]) == 2

        # One with error, one without
        errors = [r for r in data["results"] if r["error"] is not None]
        successes = [r for r in data["results"] if r["error"] is None]

        assert len(errors) == 1
        assert len(successes) == 1

        # Summary
        assert data["summary"]["total_files"] == 2
        assert data["summary"]["errors"] == 1
        assert data["summary"]["total_symbols"] > 0  # From good file
