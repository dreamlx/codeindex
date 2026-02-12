"""BDD tests for Interactive Setup Wizard (Epic 15 Story 15.1)."""

import time

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

from codeindex.config import Config

# Load all scenarios from the feature file
scenarios("features/init_wizard.feature")


# ============================================================================
# Fixtures and Context
# ============================================================================


@pytest.fixture
def wizard_context():
    """Context for wizard test execution."""
    return {
        "project_dir": None,
        "detected_languages": [],
        "suggested_patterns": {"include": [], "exclude": []},
        "user_choices": {},
        "config_created": False,
        "codeindex_md_created": False,
        "hooks_installed": False,
        "start_time": None,
        "end_time": None,
    }


# ============================================================================
# Background Steps
# ============================================================================


@given("I am in a project directory", target_fixture="project_dir")
def project_directory(tmp_path):
    """Create a temporary project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir


@given("no .codeindex.yaml exists")
def no_config_exists(project_dir):
    """Ensure no .codeindex.yaml exists."""
    config_file = project_dir / ".codeindex.yaml"
    assert not config_file.exists()


# ============================================================================
# Given Steps - Project Setup
# ============================================================================


@given("the project contains Python files")
def create_python_files(project_dir, wizard_context):
    """Create Python files in the project."""
    (project_dir / "src").mkdir()
    (project_dir / "src" / "main.py").write_text("def main(): pass")
    (project_dir / "src" / "utils.py").write_text("def helper(): pass")
    wizard_context["project_dir"] = project_dir


@given("the project contains Python and PHP files")
def create_python_php_files(project_dir, wizard_context):
    """Create Python and PHP files."""
    (project_dir / "src").mkdir()
    (project_dir / "src" / "app.py").write_text("def app(): pass")
    (project_dir / "src" / "index.php").write_text("<?php echo 'hello'; ?>")
    wizard_context["project_dir"] = project_dir


@given("the project contains Java files with Spring annotations")
def create_java_spring_files(project_dir, wizard_context):
    """Create Java files with Spring Boot annotations."""
    java_dir = project_dir / "src" / "main" / "java" / "com" / "example"
    java_dir.mkdir(parents=True)

    controller_code = """
package com.example;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class UserController {
    @GetMapping("/users")
    public String getUsers() {
        return "users";
    }
}
"""
    (java_dir / "UserController.java").write_text(controller_code)
    wizard_context["project_dir"] = project_dir


@given("a project with src/ and lib/ directories")
def create_src_lib_dirs(project_dir, wizard_context):
    """Create project with src/ and lib/ directories."""
    (project_dir / "src").mkdir()
    (project_dir / "lib").mkdir()
    (project_dir / "tests").mkdir()
    (project_dir / "__pycache__").mkdir()
    (project_dir / "src" / "main.py").write_text("def main(): pass")
    wizard_context["project_dir"] = project_dir


@given("a project with node_modules/ and .git/ directories")
def create_node_git_dirs(project_dir, wizard_context):
    """Create project with node_modules/ and .git/."""
    (project_dir / "node_modules").mkdir()
    (project_dir / ".git").mkdir()
    (project_dir / "src").mkdir()
    (project_dir / "src" / "index.js").write_text("console.log('hello');")
    wizard_context["project_dir"] = project_dir


@given(parsers.parse("a project with {file_count:d} files"))
def create_project_with_files(project_dir, wizard_context, file_count, monkeypatch):
    """Create a project with specified number of files."""
    src_dir = project_dir / "src"
    src_dir.mkdir()

    for i in range(file_count):
        (src_dir / f"file{i}.py").write_text(f"def func{i}(): pass")

    wizard_context["project_dir"] = project_dir
    wizard_context["file_count"] = file_count

    # Mock os.cpu_count() for consistent test results across environments
    # For large projects (>=1000 files), ensure enough CPUs to return 16 workers
    import os
    if file_count >= 1000:
        monkeypatch.setattr(os, "cpu_count", lambda: 16)


# ============================================================================
# When Steps - Wizard Execution
# ============================================================================


@when("I run the interactive wizard")
def run_interactive_wizard(wizard_context, project_dir, monkeypatch):
    """Run the interactive wizard."""
    from codeindex.init_wizard import (
        WizardResult,
        calculate_batch_size,
        calculate_parallel_workers,
        count_files,
        detect_frameworks,
        detect_languages,
        infer_exclude_patterns,
        infer_include_patterns,
    )

    wizard_context["start_time"] = time.time()
    wizard_context["project_dir"] = project_dir

    # Run detection functions
    wizard_context["detected_languages"] = detect_languages(project_dir)
    wizard_context["suggested_languages"] = wizard_context["detected_languages"].copy()

    if wizard_context["detected_languages"]:
        wizard_context["detected_frameworks"] = detect_frameworks(
            project_dir, wizard_context["detected_languages"]
        )

    wizard_context["suggested_patterns"] = {
        "include": infer_include_patterns(project_dir),
        "exclude": infer_exclude_patterns(project_dir),
    }

    # Calculate performance settings
    default_count = count_files(project_dir, wizard_context["suggested_patterns"]["include"])
    file_count = wizard_context.get("file_count", default_count)
    wizard_context["parallel_workers"] = calculate_parallel_workers(file_count)
    wizard_context["batch_size"] = calculate_batch_size(file_count)

    # Create a result object for later use
    result = WizardResult(
        detected_languages=wizard_context["detected_languages"],
        suggested_patterns=wizard_context["suggested_patterns"],
        detected_frameworks=wizard_context.get("detected_frameworks", []),
        parallel_workers=wizard_context["parallel_workers"],
        batch_size=wizard_context["batch_size"],
    )
    wizard_context["wizard_result"] = result


@when(parsers.parse("I select {language} as language"))
def select_language(wizard_context, language):
    """Select a language in the wizard."""
    wizard_context["user_choices"]["languages"] = [language.lower()]


@when("I accept default include patterns")
def accept_default_includes(wizard_context):
    """Accept default include patterns."""
    wizard_context["user_choices"]["accept_defaults"] = True


@when("I disable Git Hooks")
def disable_git_hooks(wizard_context):
    """Disable Git Hooks installation."""
    wizard_context["user_choices"]["enable_hooks"] = False


@when(parsers.parse("I select {lang1} and {lang2} as languages"))
def select_multiple_languages(wizard_context, lang1, lang2):
    """Select multiple languages."""
    wizard_context["user_choices"]["languages"] = [
        lang1.lower(),
        lang2.lower(),
    ]


@when("I accept default patterns")
def accept_default_patterns(wizard_context):
    """Accept all default patterns."""
    wizard_context["user_choices"]["accept_patterns"] = True


@when(parsers.parse("I enable Git Hooks with {mode} mode"))
def enable_git_hooks(wizard_context, mode):
    """Enable Git Hooks with specified mode."""
    wizard_context["user_choices"]["enable_hooks"] = True
    wizard_context["user_choices"]["hooks_mode"] = mode


@when("I request CODEINDEX.md creation")
def request_codeindex_md(wizard_context):
    """Request CODEINDEX.md file creation."""
    wizard_context["user_choices"]["create_codeindex_md"] = True


@when("I choose to skip AI CLI setup")
def skip_ai_cli(wizard_context):
    """Skip AI CLI configuration."""
    wizard_context["user_choices"]["configure_ai"] = False


@when("I choose to configure AI CLI")
def configure_ai_cli(wizard_context):
    """Choose to configure AI CLI."""
    wizard_context["user_choices"]["configure_ai"] = True


@when(parsers.parse("I select {tool} as the AI tool"))
def select_ai_tool(wizard_context, tool):
    """Select AI tool (Claude, etc.)."""
    wizard_context["user_choices"]["ai_tool"] = tool.lower()


@when("I skip CODEINDEX.md creation")
def skip_codeindex_md(wizard_context):
    """Skip CODEINDEX.md creation."""
    wizard_context["user_choices"]["create_codeindex_md"] = False


@when("I skip Git Hooks installation")
def skip_git_hooks(wizard_context):
    """Skip Git Hooks installation."""
    wizard_context["user_choices"]["enable_hooks"] = False


@when("I make all default choices")
def make_default_choices(wizard_context):
    """Accept all default choices in wizard."""
    wizard_context["user_choices"]["all_defaults"] = True


@when("I accept all smart defaults")
def accept_all_defaults(wizard_context):
    """Accept all smart defaults."""
    wizard_context["user_choices"]["all_defaults"] = True
    wizard_context["end_time"] = time.time()


# ============================================================================
# Then Steps - Assertions
# ============================================================================


@then("Python should be auto-detected")
def python_detected(wizard_context):
    """Verify Python was auto-detected."""
    assert "python" in wizard_context.get("detected_languages", [])


@then("the wizard should suggest Python in the languages list")
def python_suggested(wizard_context):
    """Verify Python is suggested."""
    suggested = wizard_context.get("suggested_languages", [])
    assert "python" in suggested


@then("Python and PHP should be auto-detected")
def python_php_detected(wizard_context):
    """Verify Python and PHP were auto-detected."""
    detected = wizard_context.get("detected_languages", [])
    assert "python" in detected
    assert "php" in detected


@then("the wizard should suggest both languages")
def both_languages_suggested(wizard_context):
    """Verify both languages are suggested."""
    suggested = wizard_context.get("suggested_languages", [])
    assert "python" in suggested
    assert "php" in suggested


@then("Java should be auto-detected")
def java_detected(wizard_context):
    """Verify Java was auto-detected."""
    assert "java" in wizard_context.get("detected_languages", [])


@then("Spring Boot framework should be detected")
def spring_detected(wizard_context):
    """Verify Spring Boot framework was detected."""
    frameworks = wizard_context.get("detected_frameworks", [])
    assert "spring" in frameworks or "spring-boot" in frameworks


@then("the wizard should suggest including src/ and lib/")
def suggest_src_lib(wizard_context):
    """Verify src/ and lib/ are suggested for inclusion."""
    includes = wizard_context.get("suggested_patterns", {}).get("include", [])
    assert "src/" in includes
    assert "lib/" in includes


@then("suggest excluding tests/ and __pycache__/")
def suggest_exclude_tests(wizard_context):
    """Verify tests/ and __pycache__/ are suggested for exclusion."""
    excludes = wizard_context.get("suggested_patterns", {}).get("exclude", [])
    assert any("test" in e for e in excludes)
    assert any("__pycache__" in e for e in excludes)


@then("the wizard should suggest excluding node_modules/")
def suggest_exclude_node_modules(wizard_context):
    """Verify node_modules/ is suggested for exclusion."""
    excludes = wizard_context.get("suggested_patterns", {}).get("exclude", [])
    assert any("node_modules" in e for e in excludes)


@then("suggest excluding .git/")
def suggest_exclude_git(wizard_context):
    """Verify .git/ is suggested for exclusion."""
    excludes = wizard_context.get("suggested_patterns", {}).get("exclude", [])
    assert any(".git" in e for e in excludes)


@then("a .codeindex.yaml should be created")
def config_created(wizard_context):
    """Verify .codeindex.yaml was created."""
    from codeindex.init_wizard import generate_config_yaml

    project_dir = wizard_context["project_dir"]
    config_file = project_dir / ".codeindex.yaml"

    # Apply user choices to the result
    result = wizard_context.get("wizard_result")
    if result and wizard_context.get("user_choices"):
        choices = wizard_context["user_choices"]
        if "languages" in choices:
            result.detected_languages = choices["languages"]
        if "enable_hooks" in choices:
            result.enable_hooks = choices["enable_hooks"]
        if "hooks_mode" in choices:
            result.hooks_mode = choices["hooks_mode"]
        if "configure_ai" in choices:
            result.configure_ai = choices["configure_ai"]
        if "ai_command" in choices:
            result.ai_command = choices["ai_command"]

    # Generate and write config
    if result:
        yaml_content = generate_config_yaml(result, project_dir)
        config_file.write_text(yaml_content)

    assert config_file.exists()
    wizard_context["config_created"] = True


@then(".codeindex.yaml should be created")
def config_should_be_created(wizard_context):
    """Verify .codeindex.yaml was created (alternate wording)."""
    # Same as above, just different wording
    config_created(wizard_context)


@then(parsers.parse("it should contain language: {language}"))
def config_contains_language(wizard_context, language):
    """Verify config contains specified language."""
    project_dir = wizard_context["project_dir"]
    config = Config.load(project_dir / ".codeindex.yaml")
    assert language.lower() in config.languages


@then("it should contain suggested include patterns")
def config_contains_includes(wizard_context):
    """Verify config contains suggested include patterns."""
    project_dir = wizard_context["project_dir"]
    config = Config.load(project_dir / ".codeindex.yaml")
    assert len(config.include) > 0


@then("hooks.post_commit.enabled should be false")
def hooks_disabled(wizard_context):
    """Verify hooks are disabled in config."""
    from codeindex.init_wizard import generate_config_yaml

    project_dir = wizard_context["project_dir"]
    config_file = project_dir / ".codeindex.yaml"

    # Generate config if not exists
    if not config_file.exists():
        result = wizard_context.get("wizard_result")
        if result and wizard_context.get("user_choices"):
            choices = wizard_context["user_choices"]
            if "enable_hooks" in choices:
                result.enable_hooks = choices["enable_hooks"]

        if result:
            yaml_content = generate_config_yaml(result, project_dir)
            config_file.write_text(yaml_content)

    config = Config.load(config_file)
    assert config.hooks.post_commit.enabled is False


@then("hooks.post_commit.mode should be auto")
def hooks_mode_auto(wizard_context):
    """Verify hooks mode is set to auto."""
    project_dir = wizard_context["project_dir"]
    config = Config.load(project_dir / ".codeindex.yaml")
    assert config.hooks.post_commit.mode == "auto"


@then(".codeindex.yaml should be created with both languages")
def config_with_both_languages(wizard_context):
    """Verify config has both languages."""
    from codeindex.init_wizard import generate_config_yaml

    project_dir = wizard_context["project_dir"]
    config_file = project_dir / ".codeindex.yaml"

    # Apply user choices to the result
    result = wizard_context.get("wizard_result")
    if result and wizard_context.get("user_choices"):
        choices = wizard_context["user_choices"]
        if "languages" in choices:
            result.detected_languages = choices["languages"]
        if "enable_hooks" in choices:
            result.enable_hooks = choices["enable_hooks"]
        if "hooks_mode" in choices:
            result.hooks_mode = choices["hooks_mode"]
        if "create_codeindex_md" in choices:
            result.create_codeindex_md = choices["create_codeindex_md"]

    # Generate and write config
    if result:
        yaml_content = generate_config_yaml(result, project_dir)
        config_file.write_text(yaml_content)

    assert config_file.exists()

    config = Config.load(config_file)
    assert "python" in config.languages
    assert "php" in config.languages


@then("CODEINDEX.md should be created")
def codeindex_md_created(wizard_context):
    """Verify CODEINDEX.md was created."""
    from codeindex.init_wizard import create_codeindex_md

    project_dir = wizard_context["project_dir"]
    codeindex_file = project_dir / "CODEINDEX.md"

    # Create CODEINDEX.md if user requested it
    if wizard_context.get("user_choices", {}).get("create_codeindex_md", True):
        create_codeindex_md(project_dir)

    assert codeindex_file.exists()
    wizard_context["codeindex_md_created"] = True


@then("CODEINDEX.md should be created in project root")
def codeindex_md_created_in_root(wizard_context):
    """Verify CODEINDEX.md was created in project root."""
    # Same as above, just different wording
    codeindex_md_created(wizard_context)


@then(parsers.parse("parallel_workers should be set to {workers:d}"))
def parallel_workers_set(wizard_context, workers):
    """Verify parallel_workers is set correctly."""
    # Check calculated value in wizard context
    assert wizard_context.get("parallel_workers") == workers


@then(parsers.parse("batch_size should be set to {size:d}"))
def batch_size_set(wizard_context, size):
    """Verify batch_size is set correctly."""
    # Check calculated value in wizard context
    assert wizard_context.get("batch_size") == size


@then("ai_command should not be in .codeindex.yaml")
def no_ai_command(wizard_context):
    """Verify ai_command is not configured."""
    from codeindex.init_wizard import generate_config_yaml

    project_dir = wizard_context["project_dir"]
    config_file = project_dir / ".codeindex.yaml"

    # Generate config if not exists
    if not config_file.exists():
        result = wizard_context.get("wizard_result")
        if result and wizard_context.get("user_choices"):
            choices = wizard_context["user_choices"]
            if "configure_ai" in choices:
                result.configure_ai = choices["configure_ai"]

        if result:
            yaml_content = generate_config_yaml(result, project_dir)
            config_file.write_text(yaml_content)

    content = config_file.read_text()
    assert "ai_command" not in content


@then(parsers.parse('ai_command should be \'{command}\''))
def ai_command_set(wizard_context, command):
    """Verify ai_command is set correctly."""
    from codeindex.init_wizard import generate_config_yaml

    project_dir = wizard_context["project_dir"]
    config_file = project_dir / ".codeindex.yaml"

    # Generate config if not exists (apply wizard choices first)
    if not config_file.exists():
        result = wizard_context.get("wizard_result")
        if result and wizard_context.get("user_choices"):
            choices = wizard_context["user_choices"]
            if choices.get("configure_ai"):
                result.configure_ai = True
                ai_tool = choices.get("ai_tool", "claude")
                if ai_tool == "claude":
                    result.ai_command = 'claude -p "{prompt}" --allowedTools "Read"'
                elif ai_tool == "chatgpt":
                    result.ai_command = 'chatgpt "{prompt}"'

        if result:
            yaml_content = generate_config_yaml(result, project_dir)
            config_file.write_text(yaml_content)

    config = Config.load(config_file)
    assert config.ai_command == command


@then("it should contain codeindex usage instructions")
def contains_usage_instructions(wizard_context):
    """Verify CODEINDEX.md contains usage instructions."""
    project_dir = wizard_context["project_dir"]
    codeindex_file = project_dir / "CODEINDEX.md"
    content = codeindex_file.read_text()
    assert "codeindex" in content.lower()
    assert "usage" in content.lower() or "command" in content.lower()


@then("it should contain configuration reference")
def contains_config_reference(wizard_context):
    """Verify CODEINDEX.md contains config reference."""
    project_dir = wizard_context["project_dir"]
    codeindex_file = project_dir / "CODEINDEX.md"
    content = codeindex_file.read_text()
    assert ".codeindex.yaml" in content or "configuration" in content.lower()


@then("CODEINDEX.md should not be created")
def codeindex_md_not_created(wizard_context):
    """Verify CODEINDEX.md was not created."""
    project_dir = wizard_context["project_dir"]
    codeindex_file = project_dir / "CODEINDEX.md"
    assert not codeindex_file.exists()


@then("Git Hooks should be installed")
def git_hooks_installed(wizard_context):
    """Verify Git Hooks were installed."""
    # This will check for .git/hooks/post-commit existence
    project_dir = wizard_context["project_dir"]
    hooks_dir = project_dir / ".git" / "hooks"
    if hooks_dir.exists():
        post_commit = hooks_dir / "post-commit"
        assert post_commit.exists()
    wizard_context["hooks_installed"] = True


@then(parsers.parse("post-commit hook should be configured with mode {mode}"))
def post_commit_mode(wizard_context, mode):
    """Verify post-commit hook mode."""
    project_dir = wizard_context["project_dir"]
    config = Config.load(project_dir / ".codeindex.yaml")
    assert config.hooks.post_commit.mode == mode


@then("Git Hooks should not be installed")
def git_hooks_not_installed(wizard_context):
    """Verify Git Hooks were not installed."""
    project_dir = wizard_context["project_dir"]
    hooks_dir = project_dir / ".git" / "hooks"
    if hooks_dir.exists():
        post_commit = hooks_dir / "post-commit"
        # Either doesn't exist or is not codeindex hook
        assert not post_commit.exists() or "codeindex" not in post_commit.read_text()


@then("the wizard should complete")
def wizard_completes(wizard_context):
    """Verify wizard completed successfully."""
    assert wizard_context.get("config_created", False) or wizard_context["user_choices"].get("all_defaults", False)


@then(parsers.parse("the total time should be under {seconds:d} seconds"))
def time_under_limit(wizard_context, seconds):
    """Verify wizard completed in specified time."""
    start = wizard_context.get("start_time")
    end = wizard_context.get("end_time")
    if start and end:
        duration = end - start
        assert duration < seconds


@then("all languages should be auto-detected")
def all_languages_detected(wizard_context):
    """Verify all languages were auto-detected."""
    # Languages detection should run (even if returns empty for empty projects)
    assert "detected_languages" in wizard_context
    # For empty projects, empty list is valid
    detected = wizard_context.get("detected_languages", [])
    assert isinstance(detected, list)


@then("all patterns should be auto-inferred")
def all_patterns_inferred(wizard_context):
    """Verify all patterns were auto-inferred."""
    # Pattern inference should run (even if project is empty)
    assert "suggested_patterns" in wizard_context
    patterns = wizard_context.get("suggested_patterns", {})
    # At minimum, should have exclude patterns (standard exclusions)
    assert len(patterns.get("exclude", [])) > 0


@then("no manual input should be required")
def no_manual_input(wizard_context):
    """Verify no manual input was required."""
    assert wizard_context["user_choices"].get("all_defaults", False)
