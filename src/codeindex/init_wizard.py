"""Interactive Setup Wizard for codeindex (Epic 15 Story 15.1).

This module provides an intelligent, interactive setup wizard that:
- Auto-detects project languages
- Infers include/exclude patterns
- Auto-tunes performance settings
- Configures AI CLI and Git Hooks
- Generates CODEINDEX.md guide

Design Philosophy:
- Smart defaults requiring zero manual input
- Complete setup in under 1 minute
- Support both interactive and non-interactive modes
"""

import os
import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set

import click

# ============================================================================
# CLAUDE.md Injection
# ============================================================================

CLAUDE_MD_MARKER_START = "<!-- codeindex:start -->"
CLAUDE_MD_MARKER_END = "<!-- codeindex:end -->"

CLAUDE_MD_SECTION = """<!-- codeindex:start -->
## codeindex

This project uses codeindex for AI-friendly code documentation.

**First-time setup** (if no README_AI.md files exist):
1. Review `.codeindex.yaml` — verify `include`/`exclude` patterns match this project's structure
2. Run `codeindex scan-all` to generate indexes
3. Optional: `codeindex hooks install post-commit` for auto-updates on commit

**Daily usage**:
- **Always read README_AI.md** before exploring source code in any directory
- If README_AI.md is missing or outdated, run: `codeindex scan <dir>`
- Check documentation coverage: `codeindex status`
<!-- codeindex:end -->"""


@dataclass
class WizardResult:
    """Result of running the interactive wizard."""

    detected_languages: List[str] = field(default_factory=list)
    suggested_patterns: Dict[str, List[str]] = field(default_factory=lambda: {"include": [], "exclude": []})
    detected_frameworks: List[str] = field(default_factory=list)
    parallel_workers: int = 8
    batch_size: int = 50
    enable_hooks: bool = False
    hooks_mode: str = "auto"
    create_codeindex_md: bool = False
    inject_claude_md: bool = True
    configure_ai: bool = False
    ai_tool: Optional[str] = None
    ai_command: Optional[str] = None
    config_created: bool = False
    codeindex_md_created: bool = False
    claude_md_injected: bool = False
    hooks_installed: bool = False


# ============================================================================
# Language Detection
# ============================================================================

# Language detection patterns
# Note: Only Python, PHP, and Java have full parser support
# Other languages are detected but will need parser implementation
LANGUAGE_EXTENSIONS: Dict[str, Set[str]] = {
    # Fully supported (with parser)
    "python": {".py", ".pyw", ".pyx"},
    "php": {".php"},
    "java": {".java"},
    # Planned support (detection only, no parser yet)
    # "javascript": {".js", ".jsx"},
    # "typescript": {".ts", ".tsx"},
    # "go": {".go"},
    # "rust": {".rs"},
    # "ruby": {".rb"},
}

# Framework detection patterns
FRAMEWORK_PATTERNS: Dict[str, Dict[str, str]] = {
    "spring": {
        "file_pattern": "*.java",
        "content_marker": "org.springframework",
    },
    "spring-boot": {
        "file_pattern": "*.java",
        "content_marker": "SpringBootApplication",
    },
    "thinkphp": {
        "file_pattern": "*.php",
        "content_marker": "think\\",
    },
    "laravel": {
        "file_pattern": "*.php",
        "content_marker": "Illuminate\\",
    },
}



# Parser package mapping: language -> tree-sitter package name
PARSER_PACKAGES = {
    "python": "tree_sitter_python",
    "php": "tree_sitter_php",
    "java": "tree_sitter_java",
}


def check_parser_installed(language: str) -> bool:
    """Check if the tree-sitter parser for a language is installed.

    Args:
        language: Language name (e.g., "python", "java", "php")

    Returns:
        True if the parser package is installed, False otherwise
    """
    package_name = PARSER_PACKAGES.get(language)
    if not package_name:
        return False

    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def get_parser_install_guidance(languages: list[str]) -> dict:
    """Get parser installation guidance for given languages.

    Args:
        languages: List of language names to check

    Returns:
        Dict with 'installed', 'missing' lists and optional 'install_command'
    """
    installed = []
    missing = []

    for lang in languages:
        if check_parser_installed(lang):
            installed.append(lang)
        else:
            missing.append(lang)

    result = {
        "installed": installed,
        "missing": missing,
    }

    if missing:
        extras = ",".join(missing)
        result["install_command"] = f"pip install ai-codeindex[{extras}]"

    return result

def detect_languages(project_dir: Path, max_scan_files: int = 1000) -> List[str]:
    """Auto-detect programming languages in the project.

    Args:
        project_dir: Project root directory
        max_scan_files: Maximum number of files to scan (performance limit)

    Returns:
        List of detected language names (e.g., ['python', 'php'])
    """
    extension_counts: Counter = Counter()
    scanned_files = 0

    # Common directories to skip
    skip_dirs = {"node_modules", ".git", "__pycache__", ".venv", "venv", ".tox", ".eggs"}

    for root, dirs, files in os.walk(project_dir):
        # Remove skip directories from walk
        dirs[:] = [d for d in dirs if d not in skip_dirs]

        for file in files:
            if scanned_files >= max_scan_files:
                break

            ext = Path(file).suffix.lower()
            if ext:
                extension_counts[ext] += 1
                scanned_files += 1

        if scanned_files >= max_scan_files:
            break

    # Map extensions to languages
    detected = []
    for language, extensions in LANGUAGE_EXTENSIONS.items():
        if any(ext in extension_counts for ext in extensions):
            detected.append(language)

    return sorted(detected)


def detect_frameworks(project_dir: Path, languages: List[str]) -> List[str]:
    """Detect web frameworks used in the project.

    Args:
        project_dir: Project root directory
        languages: List of detected languages

    Returns:
        List of detected framework names
    """
    detected_frameworks = []

    # Only check relevant frameworks based on detected languages
    for framework, pattern in FRAMEWORK_PATTERNS.items():
        if framework.startswith("spring") and "java" not in languages:
            continue
        if framework in ("thinkphp", "laravel") and "php" not in languages:
            continue

        # Search for framework markers in a few files
        for file_path in project_dir.rglob(pattern["file_pattern"]):
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                if pattern["content_marker"] in content:
                    detected_frameworks.append(framework)
                    break  # Found framework, no need to check more files
            except Exception:
                continue

            # Limit search to first 10 files per framework
            if len(detected_frameworks) > 0:
                break

    return detected_frameworks


# ============================================================================
# Pattern Inference
# ============================================================================


def infer_include_patterns(project_dir: Path) -> List[str]:
    """Infer include patterns based on project structure.

    Args:
        project_dir: Project root directory

    Returns:
        List of suggested include patterns
    """
    common_src_dirs = ["src", "lib", "app", "pkg", "cmd", "core", "modules"]
    includes = []

    for dir_name in common_src_dirs:
        candidate = project_dir / dir_name
        if candidate.is_dir():
            includes.append(f"{dir_name}/")

    # If no common directories found, suggest current directory
    if not includes:
        includes = ["."]

    return sorted(includes)


def infer_exclude_patterns(project_dir: Path) -> List[str]:
    """Infer exclude patterns based on common artifacts.

    Args:
        project_dir: Project root directory

    Returns:
        List of suggested exclude patterns
    """
    # Standard exclusions (always suggest)
    standard_excludes = [
        "**/__pycache__/**",
        "**/*.pyc",
        "**/.git/**",
        "**/node_modules/**",
        "**/.venv/**",
        "**/venv/**",
        "**/.tox/**",
        "**/.eggs/**",
        "**/build/**",
        "**/dist/**",
        "**/.pytest_cache/**",
    ]

    # Additional exclusions based on what exists
    conditional_excludes = {
        "tests": "**/tests/**",
        "test": "**/test/**",
        ".idea": "**/.idea/**",
        ".vscode": "**/.vscode/**",
        "target": "**/target/**",  # Java Maven/Gradle
        "vendor": "**/vendor/**",  # PHP Composer
    }

    excludes = standard_excludes.copy()

    for dir_name, pattern in conditional_excludes.items():
        if (project_dir / dir_name).exists():
            excludes.append(pattern)

    return sorted(set(excludes))


# ============================================================================
# Performance Auto-Tuning
# ============================================================================


def calculate_parallel_workers(file_count: int, cpu_count: Optional[int] = None) -> int:
    """Auto-tune parallel_workers based on project size.

    Args:
        file_count: Number of files in the project
        cpu_count: Number of CPU cores (default: os.cpu_count())

    Returns:
        Recommended parallel_workers value
    """
    if cpu_count is None:
        cpu_count = os.cpu_count() or 8

    # Size-based recommendations
    if file_count < 100:  # Small project
        return min(4, cpu_count)
    elif file_count < 1000:  # Medium project
        return min(8, cpu_count)
    else:  # Large project
        return min(16, cpu_count)


def calculate_batch_size(file_count: int) -> int:
    """Auto-tune batch_size based on project size.

    Args:
        file_count: Number of files in the project

    Returns:
        Recommended batch_size value
    """
    # Conservative defaults
    if file_count < 100:
        return 20
    elif file_count <= 500:  # Changed < to <=
        return 50
    elif file_count < 2000:
        return 100
    else:
        return 50  # Back to conservative for very large projects


def count_files(project_dir: Path, patterns: List[str]) -> int:
    """Count files matching include patterns.

    Args:
        project_dir: Project root directory
        patterns: List of include patterns

    Returns:
        Total number of matching files
    """
    count = 0
    skip_dirs = {"node_modules", ".git", "__pycache__", ".venv", "venv"}

    for root, dirs, files in os.walk(project_dir):
        # Remove skip directories
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        count += len(files)

    return count


# ============================================================================
# CLAUDE.md Injection Functions
# ============================================================================


def inject_claude_md(project_dir: Path) -> Path:
    """Inject codeindex instructions into CLAUDE.md.

    - Creates CLAUDE.md if it doesn't exist
    - Prepends section if no existing injection found
    - Replaces between markers if already injected (idempotent)

    Args:
        project_dir: Project root directory

    Returns:
        Path to CLAUDE.md
    """
    claude_md_path = project_dir / "CLAUDE.md"

    if not claude_md_path.exists():
        claude_md_path.write_text(CLAUDE_MD_SECTION + "\n")
        return claude_md_path

    content = claude_md_path.read_text()

    if CLAUDE_MD_MARKER_START in content:
        # Replace existing section between markers (idempotent update)
        pattern = re.compile(
            re.escape(CLAUDE_MD_MARKER_START) + r".*?" + re.escape(CLAUDE_MD_MARKER_END),
            re.DOTALL,
        )
        new_content = pattern.sub(CLAUDE_MD_SECTION, content)
        claude_md_path.write_text(new_content)
    else:
        # Prepend section to existing content
        new_content = CLAUDE_MD_SECTION + "\n\n" + content
        claude_md_path.write_text(new_content)

    return claude_md_path


def has_claude_md_injection(project_dir: Path) -> bool:
    """Check if CLAUDE.md already has codeindex injection.

    Args:
        project_dir: Project root directory

    Returns:
        True if CLAUDE.md exists and contains the codeindex marker
    """
    claude_md_path = project_dir / "CLAUDE.md"
    if not claude_md_path.exists():
        return False
    content = claude_md_path.read_text()
    return CLAUDE_MD_MARKER_START in content


# ============================================================================
# Interactive Wizard
# ============================================================================


def run_interactive_wizard(project_dir: Path) -> WizardResult:
    """Run the interactive setup wizard.

    Args:
        project_dir: Project root directory

    Returns:
        WizardResult containing all wizard outputs
    """
    result = WizardResult()

    click.secho("\n🚀 codeindex Interactive Setup Wizard\n", fg="cyan", bold=True)

    # Step 1: Detect languages
    click.echo("📝 Step 1/6: Detecting languages...")
    result.detected_languages = detect_languages(project_dir)

    if result.detected_languages:
        langs_str = ", ".join(result.detected_languages)
        click.secho(f"   Found: {langs_str}", fg="green")
    else:
        click.secho("   No languages detected. Please configure manually.", fg="yellow")

    # Step 2: Detect frameworks
    if result.detected_languages:
        click.echo("\n📦 Step 2/6: Detecting frameworks...")
        result.detected_frameworks = detect_frameworks(project_dir, result.detected_languages)

        if result.detected_frameworks:
            frameworks_str = ", ".join(result.detected_frameworks)
            click.secho(f"   Found: {frameworks_str}", fg="green")
        else:
            click.echo("   No frameworks detected.")

    # Step 3: Infer patterns
    click.echo("\n📂 Step 3/6: Analyzing project structure...")
    result.suggested_patterns["include"] = infer_include_patterns(project_dir)
    result.suggested_patterns["exclude"] = infer_exclude_patterns(project_dir)

    click.echo(f"   Include: {', '.join(result.suggested_patterns['include'])}")
    click.echo(f"   Exclude: {len(result.suggested_patterns['exclude'])} patterns")

    # Step 4: Auto-tune performance
    click.echo("\n⚡ Step 4/6: Calculating performance settings...")
    file_count = count_files(project_dir, result.suggested_patterns["include"])
    result.parallel_workers = calculate_parallel_workers(file_count)
    result.batch_size = calculate_batch_size(file_count)

    click.echo(f"   Files: {file_count}")
    click.echo(f"   Workers: {result.parallel_workers}")
    click.echo(f"   Batch size: {result.batch_size}")

    # Step 5: CLAUDE.md injection
    click.echo("\n📋 Step 5/6: AI agent integration...")
    result.inject_claude_md = click.confirm(
        "   Inject codeindex instructions into CLAUDE.md?", default=True
    )

    # Step 6: Optional features
    click.echo("\n🔧 Step 6/6: Optional features...")

    # Ask about Git Hooks
    result.enable_hooks = click.confirm("   Enable Git Hooks for auto-documentation?", default=False)
    if result.enable_hooks:
        result.hooks_mode = "auto"

    # Ask about CODEINDEX.md
    result.create_codeindex_md = click.confirm("   Create CODEINDEX.md guide for AI agents?", default=True)

    # Ask about AI CLI
    result.configure_ai = click.confirm("   Configure AI CLI integration?", default=False)
    if result.configure_ai:
        ai_tools = ["claude", "chatgpt", "custom"]
        click.echo("\n   Available AI tools:")
        for i, tool in enumerate(ai_tools, 1):
            click.echo(f"   {i}. {tool}")

        choice = click.prompt("   Select AI tool", type=int, default=1)
        result.ai_tool = ai_tools[choice - 1] if 1 <= choice <= len(ai_tools) else "claude"

        if result.ai_tool == "claude":
            result.ai_command = 'claude -p "{prompt}" --allowedTools "Read"'
        elif result.ai_tool == "chatgpt":
            result.ai_command = 'chatgpt "{prompt}"'
        else:
            result.ai_command = click.prompt("   Enter custom AI command")

    return result


def generate_config_yaml(result: WizardResult, project_dir: Path) -> str:
    """Generate .codeindex.yaml content from wizard result.

    Args:
        result: WizardResult from wizard execution
        project_dir: Project root directory

    Returns:
        YAML configuration content as string
    """
    yaml_lines = [
        "# codeindex configuration",
        "# Generated by Interactive Setup Wizard",
        "",
        "version: 1",
        "",
    ]

    # AI command (optional)
    if result.ai_command:
        yaml_lines.extend([
            f"ai_command: '{result.ai_command}'",
            "",
        ])

    # Languages
    if result.detected_languages:
        yaml_lines.append("languages:")
        for lang in result.detected_languages:
            yaml_lines.append(f"  - {lang}")
        yaml_lines.append("")

    # Include patterns
    if result.suggested_patterns["include"]:
        yaml_lines.append("include:")
        for pattern in result.suggested_patterns["include"]:
            yaml_lines.append(f"  - {pattern}")
        yaml_lines.append("")

    # Exclude patterns
    if result.suggested_patterns["exclude"]:
        yaml_lines.append("exclude:")
        for pattern in result.suggested_patterns["exclude"]:
            yaml_lines.append(f"  - \"{pattern}\"")
        yaml_lines.append("")

    # Performance settings
    yaml_lines.extend([
        "# Performance settings",
        f"parallel_workers: {result.parallel_workers}",
        f"batch_size: {result.batch_size}",
        "",
    ])

    # Git Hooks configuration
    yaml_lines.extend([
        "# Git Hooks configuration",
        "hooks:",
        "  post_commit:",
        f"    enabled: {str(result.enable_hooks).lower()}",
    ])
    if result.enable_hooks:
        yaml_lines.append(f"    mode: {result.hooks_mode}")
    yaml_lines.append("")

    yaml_lines.append("output_file: README_AI.md")

    return "\n".join(yaml_lines)


def create_codeindex_md(project_dir: Path) -> Path:
    """Create CODEINDEX.md guide for AI agents.

    Args:
        project_dir: Project root directory

    Returns:
        Path to created CODEINDEX.md file
    """
    content = """# CODEINDEX.md

**For**: AI Code Assistants (Claude Code, GitHub Copilot, etc.)
**Purpose**: Guide for understanding and using codeindex in this project

---

## 📖 Understanding This Project

**Start with README_AI.md files** - They provide AI-optimized documentation:

1. Read `README_AI.md` in project root for overview
2. Read module-specific `README_AI.md` for details
3. Use codeindex commands to generate/update documentation

---

## 🔍 Using codeindex

### Common Commands

```bash
# Generate/update all documentation
codeindex scan-all

# Check documentation coverage
codeindex status

# List indexable directories
codeindex list-dirs

# Generate global symbol index
codeindex symbols

# Technical debt analysis
codeindex tech-debt ./src
```

### Configuration

Configuration is in `.codeindex.yaml`. Key parameters:

- `languages`: Programming languages to index
- `include`/`exclude`: Directory patterns
- `parallel_workers`: Concurrent scanning (auto-tuned)
- `batch_size`: Files per batch (auto-tuned)

---

## 🔄 Auto-Update Hooks

Keep README_AI.md in sync with code changes automatically:

```bash
# Install post-commit hook
codeindex hooks install post-commit

# Check hook status
codeindex hooks status
```

When installed, README_AI.md files auto-update on every commit.
Configure behavior in `.codeindex.yaml`:

```yaml
hooks:
  post_commit:
    enabled: true
    mode: auto  # auto | sync | async | prompt | disabled
```

---

## 🎯 Best Practices for AI Agents

1. **Always read README_AI.md first** before exploring source code
2. **Use symbol tools** (if available) for precise navigation
3. **Check .codeindex.yaml** to understand project structure
4. **Run `codeindex status`** to see documentation coverage

---

## 📚 Additional Resources

- Main README: `README.md`
- Project symbols: `PROJECT_SYMBOLS.md` (if exists)
- Configuration: `.codeindex.yaml`

---

Generated by codeindex Interactive Setup Wizard
"""

    output_path = project_dir / "CODEINDEX.md"
    output_path.write_text(content)

    return output_path
