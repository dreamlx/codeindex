"""Tests for the smart writer module."""

import tempfile
from pathlib import Path

from codeindex.config import GroupingConfig, IndexingConfig, SymbolsConfig
from codeindex.parser import Import, ParseResult, Symbol
from codeindex.smart_writer import SmartWriter, determine_level


def _create_mock_parse_result(
    filename: str,
    symbols: list[Symbol] = None,
    imports: list[Import] = None,
    file_lines: int = 100,
) -> ParseResult:
    """Create a mock ParseResult for testing."""
    return ParseResult(
        path=Path(f"/test/{filename}"),
        symbols=symbols or [],
        imports=imports or [],
        module_docstring="",
        error=None,
        file_lines=file_lines,
    )


def test_smart_writer_overview_level():
    """Test generating overview level README."""
    config = IndexingConfig()
    writer = SmartWriter(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)

        # Create some child directories
        child1 = dir_path / "module1"
        child2 = dir_path / "module2"
        child1.mkdir()
        child2.mkdir()

        # Create minimal README in children
        (child1 / "README_AI.md").write_text("# Module 1\nHandles user authentication")
        (child2 / "README_AI.md").write_text("# Module 2\nHandles order processing")

        parse_results = []
        child_dirs = [child1, child2]

        result = writer.write_readme(
            dir_path=dir_path,
            parse_results=parse_results,
            level="overview",
            child_dirs=child_dirs,
        )

        assert result.success
        assert result.path.exists()

        content = result.path.read_text()
        assert "overview" in content  # Generated marker
        assert "module1" in content
        assert "module2" in content
        assert "Module Structure" in content


def test_smart_writer_navigation_level():
    """Test generating navigation level README."""
    config = IndexingConfig()
    writer = SmartWriter(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)

        # Create mock parse results with different file types
        symbols = [
            Symbol(name="UserController", kind="class", signature="class UserController"),
            Symbol(name="UserController::index", kind="method", signature="public function index()"),
        ]
        parse_results = [
            _create_mock_parse_result("UserController.php", symbols),
            _create_mock_parse_result("OrderService.php", [
                Symbol(name="OrderService", kind="class", signature="class OrderService"),
            ]),
        ]

        result = writer.write_readme(
            dir_path=dir_path,
            parse_results=parse_results,
            level="navigation",
            child_dirs=[],
        )

        assert result.success
        content = result.path.read_text()
        assert "navigation" in content
        assert "Controller" in content or "UserController" in content


def test_smart_writer_detailed_level():
    """Test generating detailed level README."""
    config = IndexingConfig()
    writer = SmartWriter(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)

        symbols = [
            Symbol(name="UserService", kind="class",
                   signature="class UserService extends BaseService",
                   docstring="Handles user business logic"),
            Symbol(name="UserService::create", kind="method",
                   signature="public function create(array $data): User"),
            Symbol(name="UserService::delete", kind="method",
                   signature="public function delete(int $id): bool"),
            Symbol(name="UserService::$repository", kind="property",
                   signature="private UserRepository $repository"),
        ]

        parse_results = [
            _create_mock_parse_result("UserService.php", symbols, [
                Import(module="App\\Repository\\UserRepository", names=[], is_from=False),
            ]),
        ]

        result = writer.write_readme(
            dir_path=dir_path,
            parse_results=parse_results,
            level="detailed",
            child_dirs=[],
        )

        assert result.success
        content = result.path.read_text()
        assert "detailed" in content
        assert "UserService" in content
        assert "public function create" in content
        assert "Dependencies" in content


def test_smart_writer_grouping():
    """Test file grouping by suffix."""
    config = IndexingConfig(
        grouping=GroupingConfig(
            enabled=True,
            by="suffix",
            patterns={
                "Controller": "HTTP handlers",
                "Service": "Business logic",
            },
        )
    )
    writer = SmartWriter(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)

        parse_results = [
            _create_mock_parse_result("UserController.php", [
                Symbol(name="UserController", kind="class", signature="class UserController"),
            ]),
            _create_mock_parse_result("OrderController.php", [
                Symbol(name="OrderController", kind="class", signature="class OrderController"),
            ]),
            _create_mock_parse_result("UserService.php", [
                Symbol(name="UserService", kind="class", signature="class UserService"),
            ]),
            _create_mock_parse_result("Helper.php", [
                Symbol(name="helper", kind="function", signature="function helper()"),
            ]),
        ]

        result = writer.write_readme(
            dir_path=dir_path,
            parse_results=parse_results,
            level="detailed",
            child_dirs=[],
        )

        assert result.success
        content = result.path.read_text()

        # Check grouping headers
        assert "Controller" in content
        assert "Service" in content


def test_smart_writer_symbol_filtering():
    """Test symbol filtering by visibility and patterns."""
    config = IndexingConfig(
        symbols=SymbolsConfig(
            max_per_file=5,
            include_visibility=["public"],
            exclude_patterns=["get*", "set*"],
        )
    )
    writer = SmartWriter(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)

        symbols = [
            Symbol(name="User::create", kind="method", signature="public function create()"),
            Symbol(name="User::getName", kind="method", signature="public function getName()"),  # Should be excluded
            Symbol(name="User::setName", kind="method", signature="public function setName()"),  # Should be excluded
            # Should be excluded (private)
            Symbol(name="User::delete", kind="method", signature="private function delete()"),
            Symbol(name="User::update", kind="method", signature="public function update()"),
        ]

        parse_results = [_create_mock_parse_result("User.php", symbols)]

        result = writer.write_readme(
            dir_path=dir_path,
            parse_results=parse_results,
            level="detailed",
            child_dirs=[],
        )

        assert result.success
        content = result.path.read_text()

        # create and update should be included
        assert "create()" in content
        assert "update()" in content

        # getName, setName should be excluded
        assert "getName" not in content
        assert "setName" not in content


def test_smart_writer_size_limit():
    """Test README size truncation."""
    config = IndexingConfig(max_readme_size=1024)  # 1KB limit
    writer = SmartWriter(config)

    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)

        # Create many symbols to exceed size limit
        symbols = [
            Symbol(
                name=f"Function{i}",
                kind="function",
                signature=f"function function{i}(string $arg1, string $arg2, string $arg3): array",
                docstring=f"This is a long docstring for function {i} "
                f"that contains a lot of text to increase the size.",
            )
            for i in range(100)
        ]

        parse_results = [_create_mock_parse_result("LargeFile.php", symbols)]

        result = writer.write_readme(
            dir_path=dir_path,
            parse_results=parse_results,
            level="detailed",
            child_dirs=[],
        )

        assert result.success
        assert result.truncated
        assert result.size_bytes <= 1024 + 200  # Allow some margin for truncation notice


def test_determine_level():
    """Test level determination logic."""
    config = IndexingConfig(
        root_level="overview",
        module_level="navigation",
        leaf_level="detailed",
    )

    root = Path("/project")

    # Root directory -> overview
    level = determine_level(root, root, has_children=True, config=config)
    assert level == "overview"

    # Module with children -> navigation
    module = Path("/project/src")
    level = determine_level(module, root, has_children=True, config=config)
    assert level == "navigation"

    # Leaf without children -> detailed
    leaf = Path("/project/src/auth")
    level = determine_level(leaf, root, has_children=False, config=config)
    assert level == "detailed"
