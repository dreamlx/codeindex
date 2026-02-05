"""Tests for Java Spring Framework parsing.

Story 7.1.3.1: Spring Test Suite
Comprehensive tests for Spring Boot project parsing, including:
- Controller layer annotations (@RestController, @RequestMapping, etc.)
- Service layer annotations (@Service, @Transactional)
- Repository layer annotations (@Repository, @Query)
- Entity layer annotations (@Entity, @Table, JPA annotations)
- Parameter annotations (@PathVariable, @RequestBody, @Autowired)
- Validation annotations (@NotBlank, @Email, @Size)
- Spring Boot main class (@SpringBootApplication, @Configuration)
"""

from pathlib import Path

from codeindex.parser import parse_file


def load_spring_fixture(filename: str) -> Path:
    """Load Spring test fixture file."""
    return Path(__file__).parent / "fixtures" / "java" / "spring" / filename


class TestSpringControllerLayer:
    """Test Spring MVC Controller layer parsing."""

    def test_rest_controller_annotation(self):
        """Test @RestController annotation extraction."""
        fixture = load_spring_fixture("UserController.java")
        result = parse_file(fixture, "java")

        assert result.error is None
        controller = next(s for s in result.symbols if s.name == "UserController")

        # Verify @RestController annotation
        annotations = {a.name: a for a in controller.annotations}
        assert "RestController" in annotations
        assert "RequestMapping" in annotations
        assert annotations["RequestMapping"].arguments == {"value": "/api/users"}

    def test_request_mapping_methods(self):
        """Test HTTP method mapping annotations (@GetMapping, @PostMapping, etc.)."""
        fixture = load_spring_fixture("UserController.java")
        result = parse_file(fixture, "java")

        # Find all methods
        methods = {s.name: s for s in result.symbols if s.kind == "method"}

        # Test @GetMapping
        get_all = methods["UserController.getAllUsers"]
        assert any(a.name == "GetMapping" for a in get_all.annotations)

        # Test @GetMapping with path variable
        get_by_id = methods["UserController.getUserById"]
        get_mapping = next(a for a in get_by_id.annotations if a.name == "GetMapping")
        assert get_mapping.arguments == {"value": "/{id}"}

        # Test @PostMapping
        create = methods["UserController.createUser"]
        assert any(a.name == "PostMapping" for a in create.annotations)

        # Test @PutMapping
        update = methods["UserController.updateUser"]
        put_mapping = next(a for a in update.annotations if a.name == "PutMapping")
        assert put_mapping.arguments == {"value": "/{id}"}

        # Test @DeleteMapping
        delete = methods["UserController.deleteUser"]
        delete_mapping = next(a for a in delete.annotations if a.name == "DeleteMapping")
        assert delete_mapping.arguments == {"value": "/{id}"}

    def test_parameter_annotations(self):
        """Test parameter annotations (@PathVariable, @RequestBody)."""
        fixture = load_spring_fixture("UserController.java")
        result = parse_file(fixture, "java")

        # Verify method signatures include parameter annotations
        get_by_id = next(
            s for s in result.symbols if s.name == "UserController.getUserById"
        )
        assert "@PathVariable" in get_by_id.signature

        create_user = next(
            s for s in result.symbols if s.name == "UserController.createUser"
        )
        assert "@RequestBody" in create_user.signature


class TestSpringServiceLayer:
    """Test Spring Service layer parsing."""

    def test_service_annotation(self):
        """Test @Service annotation extraction."""
        fixture = load_spring_fixture("UserService.java")
        result = parse_file(fixture, "java")

        assert result.error is None
        service = next(s for s in result.symbols if s.name == "UserService")

        # Verify @Service and @Transactional annotations
        annotations = {a.name: a for a in service.annotations}
        assert "Service" in annotations
        assert "Transactional" in annotations

    def test_autowired_annotation(self):
        """Test @Autowired annotation on fields."""
        fixture = load_spring_fixture("UserService.java")
        result = parse_file(fixture, "java")

        # Find userRepository field
        repository_field = next(
            s for s in result.symbols if s.name == "UserService.userRepository"
        )

        # Verify @Autowired annotation
        assert any(a.name == "Autowired" for a in repository_field.annotations)

    def test_service_methods(self):
        """Test service method extraction with JavaDoc."""
        fixture = load_spring_fixture("UserService.java")
        result = parse_file(fixture, "java")

        methods = {s.name: s for s in result.symbols if s.kind == "method"}

        # Verify key methods exist
        assert "UserService.findAll" in methods
        assert "UserService.findById" in methods
        assert "UserService.save" in methods
        assert "UserService.deleteById" in methods

        # Verify JavaDoc extraction
        find_all = methods["UserService.findAll"]
        assert "Find all users" in find_all.docstring


class TestSpringRepositoryLayer:
    """Test Spring Data JPA Repository parsing."""

    def test_repository_annotation(self):
        """Test @Repository annotation extraction."""
        fixture = load_spring_fixture("UserRepository.java")
        result = parse_file(fixture, "java")

        assert result.error is None
        repository = next(s for s in result.symbols if s.name == "UserRepository")

        # Verify @Repository annotation
        assert any(a.name == "Repository" for a in repository.annotations)

        # Verify it's recognized as interface
        assert repository.kind == "interface"
        assert "extends JpaRepository" in repository.signature

    def test_query_annotation(self):
        """Test @Query annotation on repository methods."""
        fixture = load_spring_fixture("UserRepository.java")
        result = parse_file(fixture, "java")

        # Find findByActive method
        find_by_active = next(
            s for s in result.symbols if s.name == "UserRepository.findByActive"
        )

        # Verify @Query annotation
        query_annotation = next(a for a in find_by_active.annotations if a.name == "Query")
        assert "SELECT u FROM User u WHERE u.active = ?1" in query_annotation.arguments["value"]


class TestSpringEntityLayer:
    """Test JPA Entity parsing."""

    def test_entity_annotations(self):
        """Test @Entity and @Table annotations."""
        fixture = load_spring_fixture("User.java")
        result = parse_file(fixture, "java")

        assert result.error is None
        user_class = next(s for s in result.symbols if s.name == "User")

        # Verify @Entity and @Table annotations
        annotations = {a.name: a for a in user_class.annotations}
        assert "Entity" in annotations
        assert "Table" in annotations
        assert annotations["Table"].arguments.get("name") == "users"

    def test_jpa_field_annotations(self):
        """Test JPA field annotations (@Id, @Column, etc.)."""
        fixture = load_spring_fixture("User.java")
        result = parse_file(fixture, "java")

        fields = {s.name: s for s in result.symbols if s.kind == "field"}

        # Test @Id and @GeneratedValue
        id_field = fields["User.id"]
        assert any(a.name == "Id" for a in id_field.annotations)
        assert any(a.name == "GeneratedValue" for a in id_field.annotations)

        # Test @Column with attributes
        username_field = fields["User.username"]
        column_ann = next((a for a in username_field.annotations if a.name == "Column"), None)
        assert column_ann is not None
        # Note: complex attributes like nullable=false may be stored as full expression

        # Test @Email validation annotation
        email_field = fields["User.email"]
        assert any(a.name == "Email" for a in email_field.annotations)
        assert any(a.name == "NotBlank" for a in email_field.annotations)

    def test_validation_annotations(self):
        """Test Bean Validation annotations (@NotBlank, @Size, @Email)."""
        fixture = load_spring_fixture("User.java")
        result = parse_file(fixture, "java")

        # Find username field
        username = next(s for s in result.symbols if s.name == "User.username")

        # Verify validation annotations
        annotations = {a.name: a for a in username.annotations}
        assert "NotBlank" in annotations
        assert "Size" in annotations

    def test_lifecycle_annotations(self):
        """Test JPA lifecycle callback annotations (@PrePersist, @PreUpdate)."""
        fixture = load_spring_fixture("User.java")
        result = parse_file(fixture, "java")

        # Find lifecycle methods
        on_create = next(s for s in result.symbols if s.name == "User.onCreate")
        on_update = next(s for s in result.symbols if s.name == "User.onUpdate")

        # Verify lifecycle annotations
        assert any(a.name == "PrePersist" for a in on_create.annotations)
        assert any(a.name == "PreUpdate" for a in on_update.annotations)


class TestSpringBootMain:
    """Test Spring Boot application main class."""

    def test_spring_boot_application(self):
        """Test @SpringBootApplication annotation."""
        fixture = load_spring_fixture("Application.java")
        result = parse_file(fixture, "java")

        assert result.error is None
        app_class = next(s for s in result.symbols if s.name == "Application")

        # Verify @SpringBootApplication annotation
        assert any(a.name == "SpringBootApplication" for a in app_class.annotations)

    def test_configuration_annotation(self):
        """Test @Configuration annotation on nested class."""
        fixture = load_spring_fixture("Application.java")
        result = parse_file(fixture, "java")

        # Find WebConfig nested class
        web_config = next(s for s in result.symbols if s.name == "WebConfig")

        # Verify @Configuration annotation
        assert any(a.name == "Configuration" for a in web_config.annotations)

    def test_bean_annotation(self):
        """Test @Bean annotation on methods."""
        fixture = load_spring_fixture("Application.java")
        result = parse_file(fixture, "java")

        # Find corsConfigurer method
        cors_configurer = next(
            s for s in result.symbols if s.name == "WebConfig.corsConfigurer"
        )

        # Verify @Bean annotation
        assert any(a.name == "Bean" for a in cors_configurer.annotations)


class TestSpringPackageStructure:
    """Test Spring project package and import structure."""

    def test_package_declaration(self):
        """Test package name extraction from Spring classes."""
        fixture = load_spring_fixture("UserController.java")
        result = parse_file(fixture, "java")

        # Verify package name
        assert result.namespace == "com.example.demo.controller"

    def test_spring_imports(self):
        """Test Spring framework import extraction."""
        fixture = load_spring_fixture("UserController.java")
        result = parse_file(fixture, "java")

        # Verify Spring imports (note: UserController uses wildcard imports)
        import_modules = [imp.module for imp in result.imports]
        assert "org.springframework.web.bind.annotation.*" in import_modules
        assert "org.springframework.beans.factory.annotation.Autowired" in import_modules
        assert "org.springframework.http.ResponseEntity" in import_modules


class TestSpringAnnotationCoverage:
    """Test comprehensive annotation coverage across Spring project."""

    def test_all_spring_files_parse(self):
        """Test that all Spring fixture files parse without errors."""
        fixtures = [
            "UserController.java",
            "UserService.java",
            "UserRepository.java",
            "User.java",
            "Application.java",
        ]

        for fixture_name in fixtures:
            fixture = load_spring_fixture(fixture_name)
            result = parse_file(fixture, "java")
            assert result.error is None, f"Failed to parse {fixture_name}: {result.error}"
            assert len(result.symbols) > 0, f"No symbols extracted from {fixture_name}"

    def test_spring_annotation_types(self):
        """Test coverage of different Spring annotation types."""
        all_annotations = set()

        fixtures = [
            "UserController.java",
            "UserService.java",
            "UserRepository.java",
            "User.java",
            "Application.java",
        ]

        for fixture_name in fixtures:
            fixture = load_spring_fixture(fixture_name)
            result = parse_file(fixture, "java")

            for symbol in result.symbols:
                for annotation in symbol.annotations:
                    all_annotations.add(annotation.name)

        # Verify key Spring annotations are extracted
        expected_annotations = {
            "RestController",
            "Service",
            "Repository",
            "Entity",
            "SpringBootApplication",
            "RequestMapping",
            "GetMapping",
            "PostMapping",
            "Autowired",
            "Transactional",
        }

        assert expected_annotations.issubset(all_annotations), \
            f"Missing annotations: {expected_annotations - all_annotations}"
