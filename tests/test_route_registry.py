"""Tests for RouteExtractorRegistry (Epic 6, Task 2.2)."""



from codeindex.route_extractor import ExtractionContext, RouteExtractor, RouteInfo
from codeindex.route_registry import RouteExtractorRegistry


# Test extractors for registry testing
class TestFrameworkExtractor(RouteExtractor):
    """Test extractor for 'testframework'."""

    @property
    def framework_name(self) -> str:
        return "testframework"

    def can_extract(self, context: ExtractionContext) -> bool:
        return True

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        return [
            RouteInfo(
                url="/test",
                controller="TestController",
                action="index",
            )
        ]


class AnotherFrameworkExtractor(RouteExtractor):
    """Test extractor for 'anotherframework'."""

    @property
    def framework_name(self) -> str:
        return "anotherframework"

    def can_extract(self, context: ExtractionContext) -> bool:
        return True

    def extract_routes(self, context: ExtractionContext) -> list[RouteInfo]:
        return []


class TestRouteExtractorRegistry:
    """Test RouteExtractorRegistry."""

    def test_register_extractor(self):
        """Registry should store registered extractors."""
        registry = RouteExtractorRegistry()
        extractor = TestFrameworkExtractor()

        registry.register(extractor)

        retrieved = registry.get("testframework")
        assert retrieved is extractor
        assert retrieved.framework_name == "testframework"

    def test_register_multiple_extractors(self):
        """Registry should store multiple extractors."""
        registry = RouteExtractorRegistry()
        extractor1 = TestFrameworkExtractor()
        extractor2 = AnotherFrameworkExtractor()

        registry.register(extractor1)
        registry.register(extractor2)

        assert registry.get("testframework") is extractor1
        assert registry.get("anotherframework") is extractor2

    def test_get_nonexistent_extractor_returns_none(self):
        """Registry should return None for unknown framework."""
        registry = RouteExtractorRegistry()

        result = registry.get("nonexistent")

        assert result is None

    def test_register_overwrites_existing_extractor(self):
        """Registering same framework name should overwrite."""
        registry = RouteExtractorRegistry()
        extractor1 = TestFrameworkExtractor()
        extractor2 = TestFrameworkExtractor()  # Different instance, same name

        registry.register(extractor1)
        registry.register(extractor2)

        # Should return the second instance
        result = registry.get("testframework")
        assert result is extractor2
        assert result is not extractor1

    def test_list_registered_frameworks(self):
        """Registry should list all registered framework names."""
        registry = RouteExtractorRegistry()
        extractor1 = TestFrameworkExtractor()
        extractor2 = AnotherFrameworkExtractor()

        registry.register(extractor1)
        registry.register(extractor2)

        frameworks = registry.list_frameworks()

        assert "testframework" in frameworks
        assert "anotherframework" in frameworks
        assert len(frameworks) == 2

    def test_empty_registry_has_no_frameworks(self):
        """Empty registry should return empty list."""
        registry = RouteExtractorRegistry()

        frameworks = registry.list_frameworks()

        assert frameworks == []

    def test_has_extractor(self):
        """Registry should check if extractor exists."""
        registry = RouteExtractorRegistry()
        extractor = TestFrameworkExtractor()

        registry.register(extractor)

        assert registry.has_extractor("testframework") is True
        assert registry.has_extractor("nonexistent") is False

    def test_registry_is_independent(self):
        """Multiple registry instances should be independent."""
        registry1 = RouteExtractorRegistry()
        registry2 = RouteExtractorRegistry()
        extractor = TestFrameworkExtractor()

        registry1.register(extractor)

        # registry2 should not have the extractor
        assert registry1.get("testframework") is extractor
        assert registry2.get("testframework") is None
