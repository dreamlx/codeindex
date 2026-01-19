"""Configuration management for codeindex."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

DEFAULT_CONFIG_NAME = ".codeindex.yaml"
DEFAULT_OUTPUT_FILE = "README_AI.md"
DEFAULT_AI_COMMAND = 'claude -p "{prompt}" --allowedTools "Read"'
DEFAULT_INCLUDE = ["src/", "lib/", "tests/", "examples/"]
DEFAULT_EXCLUDE = [
    "**/__pycache__/**",
    "**/node_modules/**",
    "**/.git/**",
]
DEFAULT_LANGUAGES = ["python"]

# Incremental update defaults
DEFAULT_INCREMENTAL = {
    "enabled": True,
    "thresholds": {
        "skip_lines": 5,  # Changes < this: skip update
        "current_only": 50,  # Changes < this: update current dir only
        "suggest_full": 200,  # Changes > this: suggest full update
    },
    "auto_update": {
        "on_commit": True,  # Auto-update on git commit
        "project_index": False,  # Auto-update PROJECT_INDEX.md
    },
}

DEFAULT_CONFIG_TEMPLATE = """\
# codeindex configuration
version: 1

# AI CLI command template
# {prompt} will be replaced with the actual prompt
# Examples:
#   claude -p "{prompt}" --allowedTools "Read"
#   opencode run "{prompt}"
#   gemini "{prompt}"
ai_command: 'claude -p "{prompt}" --allowedTools "Read"'

# Directories to scan (tests included for better AI understanding)
include:
  - src/
  - lib/
  - tests/
  - examples/

# Patterns to exclude
exclude:
  - "**/__pycache__/**"
  - "**/node_modules/**"
  - "**/.git/**"
  - "**/venv/**"
  - "**/.venv/**"

# Supported languages (V1: python only)
languages:
  - python

# Output file name
output_file: README_AI.md

# Incremental update settings
incremental:
  enabled: true
  thresholds:
    skip_lines: 5        # Changes < this: skip update (trivial)
    current_only: 50     # Changes < this: update current dir only
    suggest_full: 200    # Changes > this: suggest full update
  auto_update:
    on_commit: true      # Auto-update on git commit
    project_index: false # Auto-update PROJECT_INDEX.md
"""


@dataclass
class IncrementalConfig:
    """Configuration for incremental updates."""

    enabled: bool = True
    skip_lines: int = 5
    current_only: int = 50
    suggest_full: int = 200
    auto_on_commit: bool = True
    auto_project_index: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "IncrementalConfig":
        """Create from config dict."""
        if not data:
            return cls()
        thresholds = data.get("thresholds", {})
        auto_update = data.get("auto_update", {})
        return cls(
            enabled=data.get("enabled", True),
            skip_lines=thresholds.get("skip_lines", 5),
            current_only=thresholds.get("current_only", 50),
            suggest_full=thresholds.get("suggest_full", 200),
            auto_on_commit=auto_update.get("on_commit", True),
            auto_project_index=auto_update.get("project_index", False),
        )


@dataclass
class Config:
    """Configuration for codeindex."""

    version: int = 1
    ai_command: str = DEFAULT_AI_COMMAND
    include: list[str] = field(default_factory=lambda: DEFAULT_INCLUDE.copy())
    exclude: list[str] = field(default_factory=lambda: DEFAULT_EXCLUDE.copy())
    languages: list[str] = field(default_factory=lambda: DEFAULT_LANGUAGES.copy())
    output_file: str = DEFAULT_OUTPUT_FILE
    incremental: IncrementalConfig = field(default_factory=IncrementalConfig)

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Config":
        """Load config from yaml file."""
        if path is None:
            path = Path.cwd() / DEFAULT_CONFIG_NAME

        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        return cls(
            version=data.get("version", 1),
            ai_command=data.get("ai_command", DEFAULT_AI_COMMAND),
            include=data.get("include", DEFAULT_INCLUDE.copy()),
            exclude=data.get("exclude", DEFAULT_EXCLUDE.copy()),
            languages=data.get("languages", DEFAULT_LANGUAGES.copy()),
            output_file=data.get("output_file", DEFAULT_OUTPUT_FILE),
            incremental=IncrementalConfig.from_dict(data.get("incremental", {})),
        )

    @staticmethod
    def create_default(path: Optional[Path] = None) -> Path:
        """Create default config file."""
        if path is None:
            path = Path.cwd() / DEFAULT_CONFIG_NAME

        with open(path, "w") as f:
            f.write(DEFAULT_CONFIG_TEMPLATE)

        return path
