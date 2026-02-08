"""Configuration management for codeindex."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

from codeindex.adaptive_config import DEFAULT_ADAPTIVE_CONFIG, AdaptiveSymbolsConfig

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

# Git Hooks configuration (Story 6)
hooks:
  post_commit:
    mode: auto            # auto | disabled | async | sync | prompt
    max_dirs_sync: 2      # Auto mode: ≤2 dirs = sync, >2 = async
    enabled: true         # Master switch
    log_file: ~/.codeindex/hooks/post-commit.log
"""


@dataclass
class SymbolsConfig:
    """Configuration for symbol extraction."""
    max_per_file: int = 15
    include_visibility: list[str] = field(default_factory=lambda: ["public", "protected"])
    exclude_patterns: list[str] = field(default_factory=lambda: ["get*", "set*", "__*"])
    adaptive_symbols: AdaptiveSymbolsConfig = field(default_factory=lambda: AdaptiveSymbolsConfig(
        enabled=DEFAULT_ADAPTIVE_CONFIG.enabled,
        thresholds=DEFAULT_ADAPTIVE_CONFIG.thresholds.copy(),
        limits=DEFAULT_ADAPTIVE_CONFIG.limits.copy(),
        min_symbols=DEFAULT_ADAPTIVE_CONFIG.min_symbols,
        max_symbols=DEFAULT_ADAPTIVE_CONFIG.max_symbols,
    ))


@dataclass
class GroupingConfig:
    """Configuration for file grouping."""
    enabled: bool = True
    by: str = "suffix"  # suffix | prefix | pattern
    patterns: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class SemanticConfig:
    """Configuration for semantic extraction."""
    enabled: bool = True  # Enable semantic extraction
    use_ai: bool = False  # Use AI mode (requires ai_command in Config)
    fallback_to_heuristic: bool = True  # Fallback to heuristic if AI fails

    @classmethod
    def from_dict(cls, data: dict) -> "SemanticConfig":
        """Create from config dict."""
        if not data:
            return cls()

        return cls(
            enabled=data.get("enabled", True),
            use_ai=data.get("use_ai", False),
            fallback_to_heuristic=data.get("fallback_to_heuristic", True),
        )


@dataclass
class IndexingConfig:
    """Configuration for smart indexing."""
    max_readme_size: int = 50 * 1024  # 50KB
    symbols: SymbolsConfig = field(default_factory=SymbolsConfig)
    grouping: GroupingConfig = field(default_factory=GroupingConfig)
    semantic: SemanticConfig = field(default_factory=SemanticConfig)
    root_level: str = "overview"      # overview | navigation | detailed
    module_level: str = "navigation"
    leaf_level: str = "detailed"

    @classmethod
    def from_dict(cls, data: dict) -> "IndexingConfig":
        """Create from config dict."""
        if not data:
            return cls()

        symbols_data = data.get("symbols", {})

        # Load adaptive_symbols configuration
        adaptive_data = symbols_data.get("adaptive_symbols", {})
        if adaptive_data:
            # Merge user config with defaults
            adaptive_config = AdaptiveSymbolsConfig(
                enabled=adaptive_data.get("enabled", DEFAULT_ADAPTIVE_CONFIG.enabled),
                thresholds={
                    **DEFAULT_ADAPTIVE_CONFIG.thresholds,
                    **adaptive_data.get("thresholds", {})
                },
                limits={
                    **DEFAULT_ADAPTIVE_CONFIG.limits,
                    **adaptive_data.get("limits", {})
                },
                min_symbols=adaptive_data.get("min_symbols", DEFAULT_ADAPTIVE_CONFIG.min_symbols),
                max_symbols=adaptive_data.get("max_symbols", DEFAULT_ADAPTIVE_CONFIG.max_symbols),
            )
        else:
            # Use default adaptive config
            adaptive_config = AdaptiveSymbolsConfig(
                enabled=DEFAULT_ADAPTIVE_CONFIG.enabled,
                thresholds=DEFAULT_ADAPTIVE_CONFIG.thresholds.copy(),
                limits=DEFAULT_ADAPTIVE_CONFIG.limits.copy(),
                min_symbols=DEFAULT_ADAPTIVE_CONFIG.min_symbols,
                max_symbols=DEFAULT_ADAPTIVE_CONFIG.max_symbols,
            )

        symbols = SymbolsConfig(
            max_per_file=symbols_data.get("max_per_file", 15),
            include_visibility=symbols_data.get("include_visibility", ["public", "protected"]),
            exclude_patterns=symbols_data.get("exclude_patterns", ["get*", "set*", "__*"]),
            adaptive_symbols=adaptive_config,
        )

        grouping_data = data.get("grouping", {})
        grouping = GroupingConfig(
            enabled=grouping_data.get("enabled", True),
            by=grouping_data.get("by", "suffix"),
            patterns=grouping_data.get("patterns", DEFAULT_INDEXING["grouping"]["patterns"].copy()),
        )

        # Load semantic configuration
        semantic_data = data.get("semantic", {})
        semantic = SemanticConfig.from_dict(semantic_data)

        levels = data.get("levels", {})
        return cls(
            max_readme_size=data.get("max_readme_size", 50 * 1024),
            symbols=symbols,
            grouping=grouping,
            semantic=semantic,
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
class DocstringConfig:
    """Configuration for docstring extraction (Epic 9).

    Supports AI-powered docstring extraction and normalization.

    Modes:
    - off: No docstring processing (default, backward compatible)
    - hybrid: Simple extraction + selective AI (cost-effective, <$1 per 250 dirs)
    - all-ai: AI processes everything (highest quality, higher cost)
    """

    mode: str = "off"  # off | hybrid | all-ai
    ai_command: str = ""  # AI CLI command (defaults to global ai_command)
    cost_limit: float = 1.0  # Maximum cost in USD

    @classmethod
    def from_dict(cls, data: dict, global_ai_command: str = "") -> "DocstringConfig":
        """Create from config dict.

        Args:
            data: Docstrings config dict
            global_ai_command: Global AI command to inherit if not specified

        Returns:
            DocstringConfig instance
        """
        if not data:
            return cls(ai_command=global_ai_command)

        mode = data.get("mode", "off")

        # Handle YAML parsing quirk: "off" is parsed as False
        if mode is False:
            mode = "off"

        # Validate mode
        valid_modes = ("off", "hybrid", "all-ai")
        if mode not in valid_modes:
            raise ValueError(
                f"Invalid docstring mode: {mode}. Must be one of {valid_modes}"
            )

        # Inherit global ai_command if not specified
        ai_command = data.get("ai_command", "") or global_ai_command

        return cls(
            mode=mode,
            ai_command=ai_command,
            cost_limit=data.get("cost_limit", 1.0),
        )


@dataclass
class PostCommitConfig:
    """Configuration for post-commit Git hook.

    Modes:
    - auto: Smart detection (≤2 dirs = sync, >2 = async) [default]
    - disabled: Completely disabled
    - async: Always run in background (non-blocking)
    - sync: Always run synchronously (blocking)
    - prompt: Only show reminder, don't auto-execute
    """

    mode: str = "auto"  # auto | disabled | async | sync | prompt
    enabled: bool = True  # Master switch
    max_dirs_sync: int = 2  # Threshold for auto mode
    log_file: str = "~/.codeindex/hooks/post-commit.log"

    @classmethod
    def from_dict(cls, data: dict) -> "PostCommitConfig":
        """Create from config dict."""
        if not data:
            return cls()

        mode = data.get("mode", "auto")
        valid_modes = ("auto", "disabled", "async", "sync", "prompt")
        if mode not in valid_modes:
            raise ValueError(
                f"Invalid post_commit mode: {mode}. Must be one of {valid_modes}"
            )

        return cls(
            mode=mode,
            enabled=data.get("enabled", True),
            max_dirs_sync=data.get("max_dirs_sync", 2),
            log_file=data.get("log_file", "~/.codeindex/hooks/post-commit.log"),
        )


@dataclass
class HooksConfig:
    """Configuration for Git hooks (Story 6)."""

    post_commit: PostCommitConfig = field(default_factory=PostCommitConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "HooksConfig":
        """Create from config dict."""
        if not data:
            return cls()

        return cls(
            post_commit=PostCommitConfig.from_dict(data.get("post_commit", {}))
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
    docstrings: DocstringConfig = field(default_factory=DocstringConfig)  # Epic 9
    hooks: HooksConfig = field(default_factory=HooksConfig)  # Story 6
    parallel_workers: int = DEFAULT_PARALLEL_WORKERS
    batch_size: int = DEFAULT_BATCH_SIZE

    @classmethod
    def load(cls, path: Optional[Path | str] = None) -> "Config":
        """Load config from yaml file."""
        if path is None:
            path = Path.cwd() / DEFAULT_CONFIG_NAME
        else:
            path = Path(path)

        if not path.exists():
            return cls()

        with open(path) as f:
            data = yaml.safe_load(f) or {}

        # Parse global ai_command first (needed for docstrings inheritance)
        ai_command = data.get("ai_command", DEFAULT_AI_COMMAND)

        return cls(
            version=data.get("version", 1),
            ai_command=ai_command,
            include=data.get("include", DEFAULT_INCLUDE.copy()),
            exclude=data.get("exclude", DEFAULT_EXCLUDE.copy()),
            languages=data.get("languages", DEFAULT_LANGUAGES.copy()),
            output_file=data.get("output_file", DEFAULT_OUTPUT_FILE),
            incremental=IncrementalConfig.from_dict(data.get("incremental", {})),
            indexing=IndexingConfig.from_dict(data.get("indexing", {})),
            docstrings=DocstringConfig.from_dict(
                data.get("docstrings", {}), global_ai_command=ai_command
            ),
            hooks=HooksConfig.from_dict(data.get("hooks", {})),
            parallel_workers=data.get("parallel_workers", DEFAULT_PARALLEL_WORKERS),
            batch_size=data.get("batch_size", DEFAULT_BATCH_SIZE),
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "Config":
        """Load config from YAML file (alias for load()).

        Args:
            path: Path to YAML config file

        Returns:
            Config instance
        """
        return cls.load(path)

    @staticmethod
    def create_default(path: Optional[Path] = None) -> Path:
        """Create default config file."""
        if path is None:
            path = Path.cwd() / DEFAULT_CONFIG_NAME

        with open(path, "w", encoding="utf-8") as f:
            f.write(DEFAULT_CONFIG_TEMPLATE)

        return path
