"""Tests for the directory tree module."""

import tempfile
from pathlib import Path

from codeindex.config import Config
from codeindex.directory_tree import DirectoryTree


def _create_test_structure(base: Path):
    """Create a test directory structure."""
    # Root
    # ├── src/
    # │   ├── controller/
    # │   │   └── UserController.php
    # │   ├── service/
    # │   │   └── UserService.php
    # │   └── app.php
    # └── tests/
    #     └── test_user.php

    (base / "src").mkdir()
    (base / "src" / "controller").mkdir()
    (base / "src" / "service").mkdir()
    (base / "tests").mkdir()

    # Create PHP files
    (base / "src" / "controller" / "UserController.php").write_text("<?php class UserController {}")
    (base / "src" / "service" / "UserService.php").write_text("<?php class UserService {}")
    (base / "src" / "app.php").write_text("<?php // app entry")
    (base / "tests" / "test_user.php").write_text("<?php // tests")


def test_directory_tree_build():
    """Test building directory tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        _create_test_structure(base)

        config = Config(
            include=["src/", "tests/"],
            languages=["php"],
        )

        tree = DirectoryTree(base, config)
        stats = tree.get_stats()

        # Should have: root, src, src/controller, src/service, tests
        assert stats["total_directories"] >= 4
        assert stats["with_children"] >= 1  # src has children
        assert stats["leaf_directories"] >= 2  # controller, service are leaves


def test_directory_tree_levels():
    """Test level determination for different directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        _create_test_structure(base)

        config = Config(
            include=["src/", "tests/"],
            languages=["php"],
        )

        tree = DirectoryTree(base, config)

        # Root should be overview
        root_level = tree.get_level(base)
        assert root_level == "overview", f"Root should be overview, got {root_level}"

        # src (has children) should be navigation
        src_level = tree.get_level(base / "src")
        assert src_level == "navigation", f"src should be navigation, got {src_level}"

        # controller (leaf) should be detailed
        controller_level = tree.get_level(base / "src" / "controller")
        assert controller_level == "detailed", f"controller should be detailed, got {controller_level}"

        # service (leaf) should be detailed
        service_level = tree.get_level(base / "src" / "service")
        assert service_level == "detailed", f"service should be detailed, got {service_level}"


def test_directory_tree_children():
    """Test getting children of a directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        _create_test_structure(base)

        config = Config(
            include=["src/", "tests/"],
            languages=["php"],
        )

        tree = DirectoryTree(base, config)

        # Root children should include src and tests
        root_children = tree.get_children(base)
        root_child_names = {c.name for c in root_children}
        assert "src" in root_child_names

        # src children should include controller and service
        src_children = tree.get_children(base / "src")
        src_child_names = {c.name for c in src_children}
        assert "controller" in src_child_names
        assert "service" in src_child_names

        # Leaf directories should have no children
        controller_children = tree.get_children(base / "src" / "controller")
        assert len(controller_children) == 0


def test_directory_tree_processing_order():
    """Test bottom-up processing order."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        _create_test_structure(base)

        config = Config(
            include=["src/", "tests/"],
            languages=["php"],
        )

        tree = DirectoryTree(base, config)
        order = tree.get_processing_order()

        # Find positions
        positions = {p.name: i for i, p in enumerate(order)}

        # Leaf directories should come before their parents
        if "controller" in positions and "src" in positions:
            assert positions["controller"] < positions["src"], "controller should be processed before src"

        if "service" in positions and "src" in positions:
            assert positions["service"] < positions["src"], "service should be processed before src"


def test_directory_tree_empty():
    """Test with empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        config = Config(
            include=["src/"],
            languages=["php"],
        )

        tree = DirectoryTree(base, config)
        stats = tree.get_stats()

        # Should handle empty gracefully
        assert stats["total_directories"] >= 0


def test_directory_tree_deep_nesting():
    """Test with deeply nested directories."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create deep structure: src/a/b/c/d/file.php
        deep_path = base / "src" / "a" / "b" / "c" / "d"
        deep_path.mkdir(parents=True)
        (deep_path / "file.php").write_text("<?php class Deep {}")

        config = Config(
            include=["src/"],
            languages=["php"],
        )

        tree = DirectoryTree(base, config)

        # Check levels at different depths
        # Root -> overview
        assert tree.get_level(base) == "overview"

        # Intermediate directories with children -> navigation
        assert tree.get_level(base / "src") == "navigation"
        assert tree.get_level(base / "src" / "a") == "navigation"

        # Leaf -> detailed
        assert tree.get_level(deep_path) == "detailed"
