"""BDD tests for Enhanced Help System (Epic 15 Story 15.3)."""

import subprocess

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

# Load all scenarios from the feature file
scenarios("features/help_system.feature")


# ============================================================================
# Fixtures and Context
# ============================================================================


@pytest.fixture
def help_context():
    """Context for help system test execution."""
    return {
        "command": None,
        "output": None,
        "exit_code": 0,
        "project_dir": None,
    }


# ============================================================================
# Background Steps
# ============================================================================


@given("codeindex CLI is available")
def cli_available():
    """Verify codeindex CLI is available."""
    result = subprocess.run(
        ["codeindex", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


# ============================================================================
# Given Steps - Setup
# ============================================================================


@given(parsers.parse("a .codeindex.yaml exists with {param}: {value:d}"))
def config_exists_with_param(tmp_path, help_context, param, value):
    """Create a .codeindex.yaml with specific parameter value."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    help_context["project_dir"] = project_dir

    config_content = f"""version: 1

{param}: {value}

languages:
  - python

include:
  - src/

output_file: README_AI.md
"""
    config_file = project_dir / ".codeindex.yaml"
    config_file.write_text(config_content)


@given(parsers.parse("the system has {cores:d} CPU cores"))
def system_cpu_cores(help_context, cores, monkeypatch):
    """Mock system CPU core count."""
    import os

    monkeypatch.setattr(os, "cpu_count", lambda: cores)


# ============================================================================
# When Steps - Command Execution
# ============================================================================


@when(parsers.parse('I run "{command}"'))
def run_command(help_context, command):
    """Run a codeindex command and capture output."""
    # Split command into parts
    cmd_parts = command.split()

    # Change to project directory if exists
    cwd = help_context.get("project_dir")

    result = subprocess.run(
        cmd_parts,
        capture_output=True,
        text=True,
        cwd=cwd,
    )

    help_context["command"] = command
    help_context["output"] = result.stdout + result.stderr
    help_context["exit_code"] = result.returncode


# ============================================================================
# Then Steps - Output Validation
# ============================================================================


@then(parsers.parse('the output should contain "{text}"'))
def output_contains(help_context, text):
    """Verify output contains specific text."""
    output = help_context["output"]
    assert text in output, f"Expected '{text}' in output, got:\n{output}"


@then(parsers.parse('the output should contain parameter description for "{param}"'))
def output_contains_param_description(help_context, param):
    """Verify output contains parameter description."""
    output = help_context["output"]
    # Parameter name should be in output
    assert param in output
    # Should have some description (at least 10 chars after parameter)
    param_index = output.find(param)
    assert param_index >= 0
    remaining = output[param_index:]
    # Check there's substantial content after the parameter name
    assert len(remaining) > 50


@then(parsers.parse('the output should contain "{range_text}" for {param}'))
def output_contains_range(help_context, range_text, param):
    """Verify output contains range information for parameter."""
    output = help_context["output"]
    # Find parameter section
    param_index = output.find(param)
    assert param_index >= 0

    # Check range is mentioned near parameter (within 200 chars)
    context = output[param_index : param_index + 200]
    assert range_text in context


@then("the output should use tables or structured formatting")
def output_has_formatting(help_context):
    """Verify output has structured formatting."""
    output = help_context["output"]
    # Check for table-like formatting or section headers
    has_formatting = (
        "│" in output  # Table borders
        or "=" in output  # Section separators
        or "─" in output  # Horizontal lines
        or "##" in output  # Markdown headers
    )
    assert has_formatting, "Output should have structured formatting"


@then("the output should be readable in terminal")
def output_readable(help_context):
    """Verify output is readable."""
    output = help_context["output"]
    # Should have reasonable line length (not too long)
    lines = output.split("\n")
    for line in lines:
        # Allow some long lines for URLs or paths
        if len(line) > 200 and not line.startswith("http"):
            pytest.fail(f"Line too long ({len(line)} chars): {line[:50]}...")


@then("the output should contain configuration examples")
def output_has_examples(help_context):
    """Verify output contains configuration examples."""
    output = help_context["output"]
    # Should have YAML-like content or example patterns
    has_examples = (
        "example" in output.lower()
        or ":" in output  # YAML key-value syntax
        or "```" in output  # Markdown code blocks
    )
    assert has_examples


@then("the output should contain YAML syntax examples")
def output_has_yaml_examples(help_context):
    """Verify output contains YAML syntax examples."""
    output = help_context["output"]
    # Should show YAML-like syntax
    assert ":" in output  # Key-value separator


@then(parsers.parse("the exit code should be {code:d}"))
def exit_code_matches(help_context, code):
    """Verify exit code matches expected value."""
    assert help_context["exit_code"] == code


@then(parsers.parse('the output should contain "Current value: {value:d}"'))
def output_has_current_value(help_context, value):
    """Verify output shows current configuration value."""
    output = help_context["output"]
    expected = f"Current value: {value}"
    assert expected in output or f"current value: {value}" in output.lower()


@then(parsers.parse('the output should contain "{warning}"'))
def output_has_warning(help_context, warning):
    """Verify output contains warning message."""
    output = help_context["output"]
    assert warning in output
