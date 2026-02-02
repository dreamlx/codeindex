"""Tests for RouteExtractor abstract base class (Epic 6, Task 2.1)."""

from pathlib import Path

import pytest

from codeindex.parser import ParseResult
from codeindex.route_extractor import ExtractionContext, RouteExtractor, RouteInfo


class TestExtractionContext:
    """Test ExtractionContext data structure."""

    def test_create_extraction_context(self):
        """ExtractionContext should hold extraction parameters."""
        root = Path("/project")
        current = Path("/project/src")
        parse_results = [
            ParseResult(
                path=Path("test.py"),
                symbols=[],
            )
        ]

        context = ExtractionContext(
            root_path=root,
            current_dir=current,
            parse_results=parse_results,
        )

        assert context.root_path == root
        assert context.current_dir == current
        assert context.parse_results == parse_results
        assert context.framework_version == ""

    def test_extraction_context_with_version(self):
        """ExtractionContext should support framework version."""
        context = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/src"),
            parse_results=[],
            framework_version="5.0.0",
        )

        assert context.framework_version == "5.0.0"


class TestRouteExtractor:
    """Test RouteExtractor abstract base class."""

    def test_cannot_instantiate_abstract_class(self):
        """RouteExtractor is abstract and cannot be instantiated."""
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            RouteExtractor()  # type: ignore

    def test_concrete_extractor_must_implement_framework_name(self):
        """Concrete extractor must implement framework_name property."""

        class IncompleteExtractor(RouteExtractor):
            def can_extract(self, context: ExtractionContext) -> bool:
                return True

            def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
                return []

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteExtractor()  # type: ignore

    def test_concrete_extractor_must_implement_can_extract(self):
        """Concrete extractor must implement can_extract method."""

        class IncompleteExtractor(RouteExtractor):
            @property
            def framework_name(self) -> str:
                return "test"

            def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
                return []

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteExtractor()  # type: ignore

    def test_concrete_extractor_must_implement_extract_routes(self):
        """Concrete extractor must implement extract_routes method."""

        class IncompleteExtractor(RouteExtractor):
            @property
            def framework_name(self) -> str:
                return "test"

            def can_extract(self, context: ExtractionContext) -> bool:
                return True

        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            IncompleteExtractor()  # type: ignore

    def test_complete_extractor_can_be_instantiated(self):
        """Complete extractor with all methods can be instantiated."""

        class CompleteExtractor(RouteExtractor):
            @property
            def framework_name(self) -> str:
                return "testframework"

            def can_extract(self, context: ExtractionContext) -> bool:
                return context.current_dir.name == "controllers"

            def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
                return [
                    RouteInfo(
                        url="/test",
                        controller="TestController",
                        action="index",
                    )
                ]

        extractor = CompleteExtractor()

        assert extractor.framework_name == "testframework"

        # Test can_extract
        context_yes = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/controllers"),
            parse_results=[],
        )
        assert extractor.can_extract(context_yes) is True

        context_no = ExtractionContext(
            root_path=Path("/project"),
            current_dir=Path("/project/models"),
            parse_results=[],
        )
        assert extractor.can_extract(context_no) is False

        # Test extract_routes
        routes = extractor.extract_routes(context_yes)
        assert len(routes) == 1
        assert routes[0].url == "/test"
        assert routes[0].controller == "TestController"
        assert routes[0].action == "index"
