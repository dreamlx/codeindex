"""Tests for Spring Framework route extractor.

Story 7.2: Spring Route Extraction
Tests extraction of Spring REST routes from controllers:
- @RestController, @Controller
- @RequestMapping, @GetMapping, @PostMapping, @PutMapping, @DeleteMapping
- Path variables, request parameters
- Controller-level and method-level mappings
"""

from codeindex.extractors.spring import SpringRouteExtractor
from codeindex.parser import parse_file


class TestBasicRouteExtraction:
    """Test basic Spring route extraction."""

    def test_get_mapping(self, tmp_path):
        """Test @GetMapping extraction."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text("""
package com.example.controller;

import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
}
""")

        result = parse_file(java_file)
        extractor = SpringRouteExtractor()
        routes = extractor.extract_routes(result)

        assert len(routes) == 1
        route = routes[0]
        # url contains HTTP method and path: "GET /api/users/{id}"
        assert "GET" in route.url
        assert "/api/users/{id}" in route.url
        assert route.controller == "UserController"
        assert route.action == "getUser"

    def test_post_mapping(self, tmp_path):
        """Test @PostMapping extraction."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text("""
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @PostMapping
    public User createUser(@RequestBody UserDTO dto) {
        return userService.create(dto);
    }
}
""")

        result = parse_file(java_file)
        extractor = SpringRouteExtractor()
        routes = extractor.extract_routes(result)

        assert len(routes) == 1
        assert "POST" in routes[0].url
        assert "/api/users" in routes[0].url
        assert routes[0].action == "createUser"

    def test_put_mapping(self, tmp_path):
        """Test @PutMapping extraction."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text("""
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @PutMapping("/{id}")
    public User updateUser(@PathVariable Long id, @RequestBody UserDTO dto) {
        return userService.update(id, dto);
    }
}
""")

        result = parse_file(java_file)
        extractor = SpringRouteExtractor()
        routes = extractor.extract_routes(result)

        assert len(routes) == 1
        assert "PUT" in routes[0].url
        assert "/api/users/{id}" in routes[0].url

    def test_delete_mapping(self, tmp_path):
        """Test @DeleteMapping extraction."""
        java_file = tmp_path / "UserController.java"
        java_file.write_text("""
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {

    @DeleteMapping("/{id}")
    public void deleteUser(@PathVariable Long id) {
        userService.delete(id);
    }
}
""")

        result = parse_file(java_file)
        extractor = SpringRouteExtractor()
        routes = extractor.extract_routes(result)

        assert len(routes) == 1
        assert "DELETE" in routes[0].url
        assert "/api/users/{id}" in routes[0].url


class TestMultipleRoutes:
    """Test multiple routes in one controller."""

    def test_crud_controller(self, tmp_path):
        """Test full CRUD controller with all HTTP methods."""
        java_file = tmp_path / "BookController.java"
        java_file.write_text("""
import org.springframework.web.bind.annotation.*;
import java.util.List;

@RestController
@RequestMapping("/api/books")
public class BookController {

    @GetMapping
    public List<Book> listAll() {
        return bookService.findAll();
    }

    @GetMapping("/{id}")
    public Book getById(@PathVariable Long id) {
        return bookService.findById(id);
    }

    @PostMapping
    public Book create(@RequestBody BookDTO dto) {
        return bookService.create(dto);
    }

    @PutMapping("/{id}")
    public Book update(@PathVariable Long id, @RequestBody BookDTO dto) {
        return bookService.update(id, dto);
    }

    @DeleteMapping("/{id}")
    public void delete(@PathVariable Long id) {
        bookService.delete(id);
    }
}
""")

        result = parse_file(java_file)
        extractor = SpringRouteExtractor()
        routes = extractor.extract_routes(result)

        assert len(routes) == 5

        # Verify HTTP methods are present
        urls = [r.url for r in routes]
        assert any("GET" in url for url in urls)
        assert any("POST" in url for url in urls)
        assert any("PUT" in url for url in urls)
        assert any("DELETE" in url for url in urls)

        # Verify paths
        assert any("/api/books" in url and "/api/books/" not in url for url in urls)
        assert any("/api/books/{id}" in url for url in urls)


class TestControllerAnnotation:
    """Test @Controller vs @RestController."""

    def test_rest_controller(self, tmp_path):
        """Test @RestController annotation."""
        java_file = tmp_path / "ApiController.java"
        java_file.write_text("""
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class ApiController {

    @GetMapping("/data")
    public Data getData() {
        return data;
    }
}
""")

        result = parse_file(java_file)
        extractor = SpringRouteExtractor()
        routes = extractor.extract_routes(result)

        assert len(routes) == 1
        assert "/api/data" in routes[0].url

    def test_controller_annotation(self, tmp_path):
        """Test @Controller annotation (MVC controller)."""
        java_file = tmp_path / "ViewController.java"
        java_file.write_text("""
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

@Controller
@RequestMapping("/views")
public class ViewController {

    @GetMapping("/home")
    public String home() {
        return "home";
    }
}
""")

        result = parse_file(java_file)
        extractor = SpringRouteExtractor()
        routes = extractor.extract_routes(result)

        # Should also extract routes from @Controller
        assert len(routes) == 1
        assert "/views/home" in routes[0].url


class TestEdgeCases:
    """Test edge cases."""

    def test_no_controller_annotation(self, tmp_path):
        """Test class without @Controller/@RestController."""
        java_file = tmp_path / "NotController.java"
        java_file.write_text("""
import org.springframework.web.bind.annotation.*;

public class NotController {

    @GetMapping("/test")
    public String test() {
        return "test";
    }
}
""")

        result = parse_file(java_file)
        extractor = SpringRouteExtractor()
        routes = extractor.extract_routes(result)

        # Should not extract routes from non-controller classes
        assert len(routes) == 0

    def test_empty_controller(self, tmp_path):
        """Test controller with no mapped methods."""
        java_file = tmp_path / "EmptyController.java"
        java_file.write_text("""
import org.springframework.web.bind.annotation.*;

@RestController
public class EmptyController {
    // No mapped methods
}
""")

        result = parse_file(java_file)
        extractor = SpringRouteExtractor()
        routes = extractor.extract_routes(result)

        assert len(routes) == 0

    def test_method_without_mapping(self, tmp_path):
        """Test controller with non-mapped methods."""
        java_file = tmp_path / "MixedController.java"
        java_file.write_text("""
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class MixedController {

    @GetMapping("/mapped")
    public String mapped() {
        return "mapped";
    }

    // This method has no mapping annotation
    public String notMapped() {
        return "not mapped";
    }
}
""")

        result = parse_file(java_file)
        extractor = SpringRouteExtractor()
        routes = extractor.extract_routes(result)

        # Should only extract mapped methods
        assert len(routes) == 1
        assert routes[0].action == "mapped"


class TestLineNumbers:
    """Test route line number extraction."""

    def test_route_line_numbers(self, tmp_path):
        """Test that routes include correct line numbers."""
        java_file = tmp_path / "Controller.java"
        java_file.write_text("""
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api")
public class Controller {

    @GetMapping("/route1")
    public String route1() {
        return "route1";
    }

    @PostMapping("/route2")
    public String route2() {
        return "route2";
    }
}
""")

        result = parse_file(java_file)
        extractor = SpringRouteExtractor()
        routes = extractor.extract_routes(result)

        assert len(routes) == 2

        # Both routes should have line numbers
        for route in routes:
            assert route.line_number > 0
