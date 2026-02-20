"""SmartWriter facade and core types.

SmartWriter dispatches to level-specific generators and handles
file I/O, truncation, and backward-compatible delegate methods.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

from ..adaptive_selector import AdaptiveSymbolSelector
from ..config import IndexingConfig
from ..framework_detect import RouteInfo
from ..parser import ParseResult, Symbol
from ..semantic_extractor import SemanticExtractor
from .detailed_generator import DetailedGenerator
from .navigation_generator import NavigationGenerator
from .overview_generator import OverviewGenerator
from .utils import (
    collect_recursive_stats,
    collect_top_symbols,
    extract_module_description,
    filter_symbols,
    format_route_table,
    get_key_symbols,
    group_files,
    truncate_content,
)


@dataclass
class WriteResult:
    """Result of writing a README file."""
    path: Path
    success: bool
    error: str = ""
    size_bytes: int = 0
    truncated: bool = False


# Level types
LevelType = Literal["overview", "navigation", "detailed"]


class SmartWriter:
    """
    Smart README writer that generates appropriate content based on level.

    Levels:
    - overview: Project/root level, only module list with descriptions
    - navigation: Module level, grouped files with key classes
    - detailed: Leaf level, full symbol information
    """

    def __init__(self, config: IndexingConfig, docstring_processor=None):
        """
        Initialize SmartWriter.

        Args:
            config: Indexing configuration (can also accept full Config object)
            docstring_processor: Optional DocstringProcessor for AI-powered
                                 docstring extraction (Epic 9)
        """
        # Handle both IndexingConfig and full Config
        if hasattr(config, 'indexing'):
            # Full Config object passed - extract indexing config
            self.config = config.indexing
        else:
            # IndexingConfig passed directly
            self.config = config

        self.max_size = self.config.max_readme_size

        # Initialize adaptive symbol selector
        self.adaptive_selector = AdaptiveSymbolSelector(
            self.config.symbols.adaptive_symbols
        )

        # Initialize semantic extractor if enabled
        if self.config.semantic.enabled:
            self.semantic_extractor = SemanticExtractor(
                use_ai=self.config.semantic.use_ai,
                ai_command=None if not self.config.semantic.use_ai else None
            )
        else:
            self.semantic_extractor = None

        # Initialize route extractor registry (Epic 6)
        from ..extractors.thinkphp import ThinkPHPRouteExtractor
        from ..route_registry import RouteExtractorRegistry

        self.route_registry = RouteExtractorRegistry()
        self.route_registry.register(ThinkPHPRouteExtractor())

        # Initialize docstring processor (Epic 9)
        self.docstring_processor = docstring_processor

        # Create generators
        self._overview_gen = OverviewGenerator(self.config)
        self._navigation_gen = NavigationGenerator(self.config)
        self._detailed_gen = DetailedGenerator(
            self.config,
            self.adaptive_selector,
            self.route_registry,
            self.docstring_processor,
        )

    def write_readme(
        self,
        dir_path: Path,
        parse_results: list[ParseResult],
        level: LevelType = "detailed",
        child_dirs: list[Path] | None = None,
        output_file: str = "README_AI.md",
    ) -> WriteResult:
        """
        Write README_AI.md with appropriate content based on level.

        Args:
            dir_path: Directory to write to
            parse_results: Parsed file results for this directory
            level: Content level (overview/navigation/detailed)
            child_dirs: Child directories with their own README_AI.md
            output_file: Output filename
        """
        output_path = dir_path / output_file
        child_dirs = child_dirs or []

        try:
            if level == "overview":
                content = self._overview_gen.generate(dir_path, parse_results, child_dirs)
            elif level == "navigation":
                content = self._navigation_gen.generate(dir_path, parse_results, child_dirs)
            else:  # detailed
                content = self._detailed_gen.generate(dir_path, parse_results, child_dirs)

            # Check size limit
            content_bytes = content.encode('utf-8')
            truncated = False
            if len(content_bytes) > self.max_size:
                content, truncated = truncate_content(content, self.max_size)
                content_bytes = content.encode('utf-8')

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)

            return WriteResult(
                path=output_path,
                success=True,
                size_bytes=len(content_bytes),
                truncated=truncated,
            )

        except Exception as e:
            return WriteResult(path=output_path, success=False, error=str(e))

    # --- Backward-compatible delegate methods ---
    # Tests and internal code call these directly; they delegate to generators/utils.

    def _generate_overview(
        self, dir_path: Path, parse_results: list[ParseResult], child_dirs: list[Path]
    ) -> str:
        return self._overview_gen.generate(dir_path, parse_results, child_dirs)

    def _generate_navigation(
        self, dir_path: Path, parse_results: list[ParseResult], child_dirs: list[Path]
    ) -> str:
        return self._navigation_gen.generate(dir_path, parse_results, child_dirs)

    def _generate_detailed(
        self, dir_path: Path, parse_results: list[ParseResult], child_dirs: list[Path]
    ) -> str:
        return self._detailed_gen.generate(dir_path, parse_results, child_dirs)

    def _format_route_table(
        self, routes: list[RouteInfo], framework: str = "thinkphp"
    ) -> list[str]:
        return format_route_table(routes, framework)

    def _group_files(self, results: list[ParseResult]) -> dict[str, list[ParseResult]]:
        return group_files(results, self.config)

    def _filter_symbols(self, symbols: list[Symbol]) -> list[Symbol]:
        return filter_symbols(symbols, self.config)

    def _get_key_symbols(self, symbols: list[Symbol]) -> list[Symbol]:
        return get_key_symbols(symbols)

    def _collect_recursive_stats(
        self, child_dirs: list[Path], output_file: str = "README_AI.md"
    ) -> dict:
        return collect_recursive_stats(child_dirs, output_file)

    def _collect_top_symbols(
        self, child_dirs: list[Path], output_file: str = "README_AI.md", limit: int = 15
    ) -> list[tuple[str, str, str]]:
        return collect_top_symbols(child_dirs, output_file, limit)

    def _extract_module_description(
        self, dir_path: Path, output_file: str = "README_AI.md"
    ) -> str:
        return extract_module_description(dir_path, output_file)

    def _extract_module_description_semantic(
        self,
        dir_path: Path,
        parse_result: Optional[ParseResult] = None
    ) -> str:
        """
        Extract module description using semantic extraction.

        This method stays on SmartWriter because it uses self.semantic_extractor.
        """
        if not self.semantic_extractor:
            return self._extract_module_description(dir_path)

        from codeindex.semantic_extractor import DirectoryContext

        files = []
        if dir_path.is_dir():
            files = [f.name for f in dir_path.iterdir() if f.is_file()]

        subdirs = []
        if dir_path.is_dir():
            subdirs = [d.name for d in dir_path.iterdir() if d.is_dir()]

        symbols = []
        imports = []
        if parse_result:
            symbols = [s.name for s in parse_result.symbols]
            imports = [imp.module for imp in parse_result.imports]

        context = DirectoryContext(
            path=str(dir_path),
            files=files,
            subdirs=subdirs,
            symbols=symbols,
            imports=imports
        )

        try:
            semantic = self.semantic_extractor.extract_directory_semantic(context)
            return semantic.description
        except Exception:
            if self.config.semantic.fallback_to_heuristic:
                return self._extract_module_description(dir_path)
            return "Module directory"

    def _truncate_content(self, content: str, max_size: int) -> tuple[str, bool]:
        return truncate_content(content, max_size)


def determine_level(
    dir_path: Path,
    root_path: Path,
    has_children: bool,
    config: IndexingConfig,
) -> LevelType:
    """
    Determine the appropriate level for a directory.

    Args:
        dir_path: The directory being processed
        root_path: The project root
        has_children: Whether this directory has subdirectories with README_AI.md
        config: Indexing configuration
    """
    try:
        rel_path = dir_path.relative_to(root_path)
        depth = len(rel_path.parts)
    except ValueError:
        depth = 0

    if depth == 0 or dir_path == root_path:
        return config.root_level

    if has_children:
        return config.module_level

    return config.leaf_level
