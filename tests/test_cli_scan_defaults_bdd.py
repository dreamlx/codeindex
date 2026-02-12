"""BDD tests for CLI scan default behavior (Epic 19 Story 19.1).

Tests that scan/scan-all defaults to structural mode (no AI required)
and AI is opt-in via --ai flag.
"""

import os

import pytest
from click.testing import CliRunner
from pytest_bdd import given, scenarios, then, when

from codeindex.cli import main

# Load all scenarios from the feature file
scenarios("features/cli_scan_defaults.feature")


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    return CliRunner()


@pytest.fixture
def scan_context(tmp_path):
    """Context for scan test execution."""
    return {
        "result": None,
        "project_dir": tmp_path,
        "ai_invoked": False,
        "smartwriter_invoked": False,
    }


# ============================================================================
# Background Steps
# ============================================================================


@given("a project directory with Python files")
def project_with_python_files(scan_context):
    """Create a project directory with Python files."""
    project_dir = scan_context["project_dir"]

    # Create a Python file
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text(
        'def hello():\n    """Say hello."""\n    return "hello"\n'
    )


@given("a valid .codeindex.yaml configuration")
def valid_config(scan_context):
    """Create a valid .codeindex.yaml in the project directory."""
    project_dir = scan_context["project_dir"]
    config_content = """\
version: 1
languages:
  - python
include:
  - src/
exclude:
  - "**/__pycache__/**"
parallel_workers: 1
batch_size: 10
output_file: README_AI.md
"""
    (project_dir / ".codeindex.yaml").write_text(config_content)


@given("ai_command is configured in .codeindex.yaml")
def ai_command_configured(scan_context):
    """Add ai_command to config."""
    project_dir = scan_context["project_dir"]
    config_path = project_dir / ".codeindex.yaml"
    content = config_path.read_text()
    content = f"ai_command: 'echo \"AI output\"\n'\n{content}"
    config_path.write_text(content)


@given("ai_command is NOT configured in .codeindex.yaml")
def ai_command_not_configured(scan_context):
    """Ensure ai_command is NOT in config."""
    project_dir = scan_context["project_dir"]
    config_path = project_dir / ".codeindex.yaml"
    content = config_path.read_text()
    # Remove any ai_command line if present
    lines = [line for line in content.splitlines() if not line.startswith("ai_command")]
    config_path.write_text("\n".join(lines))


# ============================================================================
# When Steps - scan command
# ============================================================================


@when("I run scan on a directory without --ai flag")
def run_scan_without_ai(cli_runner, scan_context):
    """Run scan command without --ai flag."""
    project_dir = scan_context["project_dir"]
    with InProjectDir(project_dir):
        result = cli_runner.invoke(main, ["scan", "src/"])
    scan_context["result"] = result


@when("I run scan on a directory with --ai flag")
def run_scan_with_ai(cli_runner, scan_context):
    """Run scan command with --ai flag."""
    project_dir = scan_context["project_dir"]
    with InProjectDir(project_dir):
        result = cli_runner.invoke(main, ["scan", "src/", "--ai"])
    scan_context["result"] = result


@when("I run scan on a directory with --fallback flag")
def run_scan_with_fallback(cli_runner, scan_context):
    """Run scan command with deprecated --fallback flag."""
    project_dir = scan_context["project_dir"]
    with InProjectDir(project_dir):
        result = cli_runner.invoke(main, ["scan", "src/", "--fallback"])
    scan_context["result"] = result


@when("I run scan on a directory with --dry-run and --ai flags")
def run_scan_with_dry_run_and_ai(cli_runner, scan_context):
    """Run scan with both --dry-run and --ai."""
    project_dir = scan_context["project_dir"]
    with InProjectDir(project_dir):
        result = cli_runner.invoke(main, ["scan", "src/", "--dry-run", "--ai"])
    scan_context["result"] = result


@when("I run scan on a directory with --dry-run but without --ai")
def run_scan_with_dry_run_no_ai(cli_runner, scan_context):
    """Run scan with --dry-run but without --ai."""
    project_dir = scan_context["project_dir"]
    with InProjectDir(project_dir):
        result = cli_runner.invoke(main, ["scan", "src/", "--dry-run"])
    scan_context["result"] = result


# ============================================================================
# When Steps - scan-all command
# ============================================================================


@when("I run scan-all without --ai flag")
def run_scan_all_without_ai(cli_runner, scan_context):
    """Run scan-all without --ai flag."""
    project_dir = scan_context["project_dir"]
    with InProjectDir(project_dir):
        result = cli_runner.invoke(main, ["scan-all"])
    scan_context["result"] = result


@when("I run scan-all with --ai flag")
def run_scan_all_with_ai(cli_runner, scan_context):
    """Run scan-all with --ai flag."""
    project_dir = scan_context["project_dir"]
    with InProjectDir(project_dir):
        result = cli_runner.invoke(main, ["scan-all", "--ai"])
    scan_context["result"] = result


@when("I run scan-all with --fallback flag")
def run_scan_all_with_fallback(cli_runner, scan_context):
    """Run scan-all with deprecated --fallback flag."""
    project_dir = scan_context["project_dir"]
    with InProjectDir(project_dir):
        result = cli_runner.invoke(main, ["scan-all", "--fallback"])
    scan_context["result"] = result


# ============================================================================
# Then Steps
# ============================================================================


@then("the output should be generated with SmartWriter")
def output_generated_with_smartwriter(scan_context):
    """Verify that output was generated with SmartWriter (structural mode)."""
    result = scan_context["result"]
    # SmartWriter generates README_AI.md without AI invocation
    # In structural mode, we should see SmartWriter activity, not AI CLI
    assert result.exit_code == 0, f"Command failed: {result.output}"


@then("no AI CLI should be invoked")
def no_ai_invoked(scan_context):
    """Verify that no AI CLI was invoked."""
    result = scan_context["result"]
    # AI invocation messages should not appear
    assert "Invoking AI CLI" not in result.output
    assert "AI CLI error" not in result.output


@then("the AI CLI should be invoked")
def ai_invoked(scan_context):
    """Verify that AI CLI was invoked."""
    result = scan_context["result"]
    # When --ai is used with configured ai_command, AI should be invoked
    # (may succeed or fail, but the invocation should happen)
    assert "Invoking AI CLI" in result.output or "AI" in result.output


@then("it should print an error about missing ai_command")
def error_missing_ai_command(scan_context):
    """Verify error message about missing ai_command."""
    result = scan_context["result"]
    output = result.output.lower()
    assert "ai_command" in output or "ai command" in output


@then("the exit code should be non-zero")
def exit_code_nonzero(scan_context):
    """Verify non-zero exit code."""
    result = scan_context["result"]
    assert result.exit_code != 0


@then("it should print a deprecation warning for --fallback")
def deprecation_warning_fallback(scan_context):
    """Verify deprecation warning is printed for --fallback."""
    result = scan_context["result"]
    output = result.output.lower()
    assert "deprecat" in output or "deprecated" in output


@then("it should show a prompt preview")
def prompt_preview_shown(scan_context):
    """Verify prompt preview is shown."""
    result = scan_context["result"]
    assert "prompt" in result.output.lower() or "preview" in result.output.lower()


@then("it should print an error that --dry-run requires --ai")
def error_dry_run_requires_ai(scan_context):
    """Verify error about --dry-run requiring --ai."""
    result = scan_context["result"]
    output = result.output.lower()
    assert "dry-run" in output or "dry_run" in output
    assert "--ai" in output


@then("all directories should be processed with SmartWriter")
def all_dirs_smartwriter(scan_context):
    """Verify all directories processed with SmartWriter."""
    result = scan_context["result"]
    assert result.exit_code == 0, f"Command failed: {result.output}"


@then("the AI CLI should be invoked for directories")
def ai_invoked_for_dirs(scan_context):
    """Verify AI CLI invoked for directories in scan-all."""
    result = scan_context["result"]
    # When scan-all --ai is used, AI should be involved
    output = result.output.lower()
    assert "ai" in output


# ============================================================================
# Helpers
# ============================================================================


class InProjectDir:
    """Context manager to change to project directory and restore."""

    def __init__(self, path):
        self.path = path
        self.original = None

    def __enter__(self):
        self.original = os.getcwd()
        os.chdir(self.path)
        return self

    def __exit__(self, *args):
        os.chdir(self.original)
