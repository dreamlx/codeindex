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
DEFAULT_PARALLEL_WORKERS = 4
DEFAULT_BATCH_SIZE = 50

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

# Indexing strategy defaults
DEFAULT_INDEXING = {
    "max_readme_size": 50 * 1024,  # 50KB
    "symbols": {
        "max_per_file": 15,
        "include_visibility": ["public", "protected"],
        "exclude_patterns": ["get*", "set*", "__*"],
    },
    "grouping": {
        "enabled": True,
        "by": "suffix",  # suffix | function | none
        "patterns": {
            "Controller": "HTTP 请求处理",
            "Service": "业务逻辑",
            "Model": "数据模型",
            "Repository": "数据访问",
            "Command": "命令行",
            "Event": "事件处理",
            "Job": "后台任务",
            "Middleware": "中间件",
            "Exception": "异常处理",
            "Helper": "工具函数",
        },
    },
    "levels": {
        "root": "overview",      # 只有概述和模块列表
        "module": "navigation",  # 模块导航 + 关键类
        "leaf": "detailed",      # 完整符号信息
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

# Supported languages (currently PHP support added)
languages:
  - php

# Output file name
output_file: README_AI.md

# Parallel processing settings
parallel_workers: 8      # Number of parallel workers for parsing files
batch_size: 50          # Files per batch for AI processing

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

# Smart indexing settings (控制 README 生成策略)
indexing:
  max_readme_size: 51200  # 50KB, 超过则拆分
  symbols:
    max_per_file: 15      # 每文件最多列出的符号数
    include_visibility:   # 只包含这些可见性的符号
      - public
      - protected
    exclude_patterns:     # 排除匹配这些模式的符号
      - "get*"
      - "set*"
      - "__*"
  grouping:
    enabled: true
    by: suffix            # suffix | function | none
    patterns:
      Controller: "HTTP 请求处理"
      Service: "业务逻辑"
      Model: "数据模型"
  levels:
    root: overview        # 根目录：只有概述
    module: navigation    # 模块目录：导航 + 关键类
    leaf: detailed        # 叶子目录：完整信息
"""


@dataclass
class SymbolsConfig:
    """Configuration for symbol extraction."""
    max_per_file: int = 15
    include_visibility: list[str] = field(default_factory=lambda: ["public", "protected"])
    exclude_patterns: list[str] = field(default_factory=lambda: ["get*", "set*", "__*"])


@dataclass
class GroupingConfig:
    """Configuration for symbol grouping."""
    enabled: bool = True
    by: str = "suffix"  # suffix | function | none
    patterns: dict[str, str] = field(default_factory=lambda: DEFAULT_INDEXING["grouping"]["patterns"].copy())


@dataclass
class IndexingConfig:
    """Configuration for smart indexing."""
    max_readme_size: int = 50 * 1024  # 50KB
    symbols: SymbolsConfig = field(default_factory=SymbolsConfig)
    grouping: GroupingConfig = field(default_factory=GroupingConfig)
    root_level: str = "overview"      # overview | navigation | detailed
    module_level: str = "navigation"
    leaf_level: str = "detailed"

    @classmethod
    def from_dict(cls, data: dict) -> "IndexingConfig":
        """Create from config dict."""
        if not data:
            return cls()

        symbols_data = data.get("symbols", {})
        symbols = SymbolsConfig(
            max_per_file=symbols_data.get("max_per_file", 15),
            include_visibility=symbols_data.get("include_visibility", ["public", "protected"]),
            exclude_patterns=symbols_data.get("exclude_patterns", ["get*", "set*", "__*"]),
        )

        grouping_data = data.get("grouping", {})
        grouping = GroupingConfig(
            enabled=grouping_data.get("enabled", True),
            by=grouping_data.get("by", "suffix"),
            patterns=grouping_data.get("patterns", DEFAULT_INDEXING["grouping"]["patterns"].copy()),
        )

        levels = data.get("levels", {})
        return cls(
            max_readme_size=data.get("max_readme_size", 50 * 1024),
            symbols=symbols,
            grouping=grouping,
            root_level=levels.get("root", "overview"),
            module_level=levels.get("module", "navigation"),
            leaf_level=levels.get("leaf", "detailed"),
        )


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
    indexing: IndexingConfig = field(default_factory=IndexingConfig)
    parallel_workers: int = DEFAULT_PARALLEL_WORKERS
    batch_size: int = DEFAULT_BATCH_SIZE

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
            indexing=IndexingConfig.from_dict(data.get("indexing", {})),
            parallel_workers=data.get("parallel_workers", DEFAULT_PARALLEL_WORKERS),
            batch_size=data.get("batch_size", DEFAULT_BATCH_SIZE),
        )

    @staticmethod
    def create_default(path: Optional[Path] = None) -> Path:
        """Create default config file."""
        if path is None:
            path = Path.cwd() / DEFAULT_CONFIG_NAME

        with open(path, "w") as f:
            f.write(DEFAULT_CONFIG_TEMPLATE)

        return path
