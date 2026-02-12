"""Directory tree structure for hierarchical indexing."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .config import Config

logger = logging.getLogger(__name__)

LevelType = Literal["overview", "navigation", "detailed"]


@dataclass
class DirectoryNode:
    """A node in the directory tree."""
    path: Path
    has_files: bool = False
    children: set[Path] = field(default_factory=set)
    parent: Path | None = None
    depth: int = 0  # Depth from root (root = 0)

    @property
    def has_children(self) -> bool:
        """Whether this directory has indexed child directories."""
        return bool(self.children)

    @property
    def is_leaf(self) -> bool:
        """Whether this is a leaf directory (no indexed children)."""
        return not self.children


class DirectoryTree:
    """
    Pre-scanned directory tree for determining index levels.

    This enables two-pass indexing:
    1. First pass: Build tree structure
    2. Second pass: Generate READMEs with correct levels
    """

    def __init__(self, root: Path, config: Config):
        self.root = root.resolve()
        self.config = config
        self.nodes: dict[Path, DirectoryNode] = {}
        self._build_tree()

    def _build_tree(self):
        """Build the directory tree from root."""
        from .scanner import get_language_extensions, should_exclude

        # Get valid extensions for this config
        valid_extensions = get_language_extensions(self.config.languages)

        def has_indexable_files(dir_path: Path) -> bool:
            """Check if directory has any indexable files."""
            try:
                for item in dir_path.iterdir():
                    if item.is_file() and item.suffix.lower() in valid_extensions:
                        return True
            except PermissionError:
                pass
            return False

        def walk_directory(current: Path, depth: int = 0):
            """Recursively walk directory tree."""
            # Resolve path early for consistent handling throughout function
            # This ensures include path checks and exclusion checks work correctly
            current = current.resolve()

            # Check exclusions
            if should_exclude(current, self.config.exclude, self.root):
                return

            # For include paths, check if we're within them
            if self.config.include:
                in_include = False
                for include_path in self.config.include:
                    include_full = (self.root / include_path).resolve()
                    try:
                        current.relative_to(include_full)
                        in_include = True
                        break
                    except ValueError:
                        # Check if current is parent of include
                        try:
                            include_full.relative_to(current)
                            in_include = True
                            break
                        except ValueError:
                            pass
                if not in_include and current != self.root:
                    return

            # Create node for this directory
            has_files = has_indexable_files(current)

            # Only add if has files or is root
            if has_files or current == self.root or depth == 0:
                self.nodes[current] = DirectoryNode(
                    path=current,
                    has_files=has_files,
                    depth=depth,
                )

            # Recurse into subdirectories
            try:
                for item in sorted(current.iterdir()):
                    if item.is_dir() and not item.name.startswith('.'):
                        walk_directory(item, depth + 1)
            except PermissionError:
                pass

        # Walk from root
        walk_directory(self.root)

        # Build parent-child relationships
        for dir_path, node in list(self.nodes.items()):
            parent_path = dir_path.parent.resolve()
            if parent_path in self.nodes and parent_path != dir_path:
                node.parent = parent_path
                self.nodes[parent_path].children.add(dir_path)

        # Add intermediate directories that have children but weren't added
        # (directories without files but with children need to be in tree)
        dirs_to_add = {}
        for dir_path, node in list(self.nodes.items()):
            current = dir_path.parent.resolve()
            while current != self.root.parent and current not in self.nodes:
                try:
                    depth = len(current.relative_to(self.root).parts)
                except ValueError:
                    break
                dirs_to_add[current] = DirectoryNode(
                    path=current,
                    has_files=False,
                    depth=depth,
                )
                current = current.parent.resolve()

        # Add intermediate directories and rebuild relationships
        self.nodes.update(dirs_to_add)

        # Rebuild all parent-child relationships
        for dir_path, node in self.nodes.items():
            node.children.clear()

        for dir_path, node in self.nodes.items():
            parent_path = dir_path.parent.resolve()
            if parent_path in self.nodes and parent_path != dir_path:
                node.parent = parent_path
                self.nodes[parent_path].children.add(dir_path)

    def get_level(self, dir_path: Path) -> LevelType:
        """
        Determine the appropriate index level for a directory.

        Rules:
        - Root directory (depth=0) -> overview
        - Has indexed children -> navigation
        - Leaf directory (no children) -> detailed
        """
        dir_path = dir_path.resolve()
        node = self.nodes.get(dir_path)

        if node is None:
            # Not in tree, default to detailed
            return self.config.indexing.leaf_level

        # Root directory
        if node.depth == 0 or dir_path == self.root:
            return self.config.indexing.root_level

        # Has children -> navigation
        if node.has_children:
            return self.config.indexing.module_level

        # Leaf directory
        return self.config.indexing.leaf_level

    def get_children(self, dir_path: Path) -> list[Path]:
        """Get indexed child directories for a path."""
        dir_path = dir_path.resolve()
        node = self.nodes.get(dir_path)
        if node is None:
            return []
        return sorted(node.children)

    def get_processing_order(self) -> list[Path]:
        """
        Get directories in bottom-up processing order.

        Returns directories sorted by depth (deepest first),
        so children are processed before parents.

        Pass-through directories (no code files, single subdirectory)
        are excluded to avoid redundant README_AI.md generation
        in deep structures like Java Maven paths.
        """
        from .scanner import is_pass_through

        return sorted(
            (
                p for p, node in self.nodes.items()
                if not is_pass_through(p, self.config)
            ),
            key=lambda p: (self.nodes[p].depth, str(p)),
            reverse=True
        )

    def get_stats(self) -> dict:
        """Get tree statistics."""
        total = len(self.nodes)
        with_files = sum(1 for n in self.nodes.values() if n.has_files)
        with_children = sum(1 for n in self.nodes.values() if n.has_children)
        max_depth = max((n.depth for n in self.nodes.values()), default=0)

        return {
            "total_directories": total,
            "with_files": with_files,
            "with_children": with_children,
            "leaf_directories": total - with_children,
            "max_depth": max_depth,
        }

    def print_tree(self, max_depth: int = 3):
        """Print tree structure for debugging."""
        def _print_node(path: Path, indent: int = 0):
            node = self.nodes.get(path)
            if node is None or node.depth > max_depth:
                return

            level = self.get_level(path)
            prefix = "  " * indent
            marker = "📁" if node.has_children else "📄"
            files_marker = f" ({node.has_files})" if node.has_files else ""
            logger.debug(f"{prefix}{marker} {path.name} [{level}]{files_marker}")

            for child in sorted(node.children):
                _print_node(child, indent + 1)

        _print_node(self.root)
