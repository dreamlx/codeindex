"""Tests for Java module system parsing (Java 9+).

Story 7.1.2.5: Module System
Tests parsing of Java Platform Module System (JPMS) features:
- module-info.java declarations
- requires directives
- exports directives
- opens directives
- provides/uses service declarations
- transitive dependencies
"""

from codeindex.parser import parse_file


class TestBasicModuleDeclaration:
    """Test basic module declaration."""

    def test_simple_module_declaration(self, tmp_path):
        """Test simple module declaration."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.myapp {
}
""")

        result = parse_file(java_file)

        # Module declaration should be parsed without error
        assert result.error is None
        # Module might be captured as a special symbol or just parsed successfully
        # Key goal: no parse errors

    def test_module_with_javadoc(self, tmp_path):
        """Test module with documentation."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
/**
 * Application module for user management.
 */
module com.example.users {
}
""")

        result = parse_file(java_file)

        assert result.error is None


class TestRequiresDirective:
    """Test requires directive for module dependencies."""

    def test_requires_single_module(self, tmp_path):
        """Test requires directive with single module."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.app {
    requires java.sql;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_requires_multiple_modules(self, tmp_path):
        """Test requires multiple modules."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.app {
    requires java.sql;
    requires java.logging;
    requires com.google.gson;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_requires_transitive(self, tmp_path):
        """Test requires transitive for implied readability."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.api {
    requires transitive java.sql;
    requires transitive com.example.common;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_requires_static(self, tmp_path):
        """Test requires static for optional compile-time dependency."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.app {
    requires static lombok;
    requires java.base;
}
""")

        result = parse_file(java_file)

        assert result.error is None


class TestExportsDirective:
    """Test exports directive for package visibility."""

    def test_exports_single_package(self, tmp_path):
        """Test exports single package."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.library {
    exports com.example.library.api;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_exports_multiple_packages(self, tmp_path):
        """Test exports multiple packages."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.library {
    exports com.example.library.api;
    exports com.example.library.util;
    exports com.example.library.model;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_exports_to_specific_modules(self, tmp_path):
        """Test qualified exports (exports to specific modules)."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.internal {
    exports com.example.internal.impl to com.example.app, com.example.test;
}
""")

        result = parse_file(java_file)

        assert result.error is None


class TestOpensDirective:
    """Test opens directive for reflection access."""

    def test_opens_single_package(self, tmp_path):
        """Test opens single package for reflection."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.app {
    opens com.example.app.entity;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_opens_to_specific_modules(self, tmp_path):
        """Test qualified opens (to specific modules)."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.app {
    opens com.example.app.entity to org.hibernate.orm, com.fasterxml.jackson.databind;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_open_module(self, tmp_path):
        """Test open module (all packages open for reflection)."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
open module com.example.app {
    requires java.sql;
}
""")

        result = parse_file(java_file)

        assert result.error is None


class TestServiceDirectives:
    """Test provides/uses directives for service loading."""

    def test_uses_directive(self, tmp_path):
        """Test uses directive for service consumer."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.consumer {
    uses com.example.service.DatabaseService;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_provides_directive(self, tmp_path):
        """Test provides directive for service provider."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.provider {
    provides com.example.service.DatabaseService
        with com.example.provider.MySQLDatabaseService;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_provides_multiple_implementations(self, tmp_path):
        """Test provides with multiple implementations."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.provider {
    provides com.example.service.PaymentService
        with com.example.provider.CreditCardPayment,
             com.example.provider.PayPalPayment;
}
""")

        result = parse_file(java_file)

        assert result.error is None


class TestComplexModuleDeclaration:
    """Test complex real-world module declarations."""

    def test_spring_boot_module(self, tmp_path):
        """Test Spring Boot style module declaration."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
/**
 * Spring Boot application module.
 */
module com.example.springapp {
    requires spring.boot;
    requires spring.boot.autoconfigure;
    requires spring.context;
    requires spring.web;
    requires transitive spring.data.jpa;
    requires java.sql;

    exports com.example.springapp.controller;
    exports com.example.springapp.service;

    opens com.example.springapp.entity to org.hibernate.orm.core;
    opens com.example.springapp.controller to spring.core;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_microservice_module(self, tmp_path):
        """Test microservice module with service providers."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.auth.service {
    requires transitive com.example.common;
    requires java.logging;
    requires com.auth0.jwt;

    exports com.example.auth.api;
    exports com.example.auth.model;

    provides com.example.service.AuthenticationService
        with com.example.auth.impl.JWTAuthenticationService;

    uses com.example.service.UserRepository;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_library_module(self, tmp_path):
        """Test library module with selective exports."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.library {
    requires static lombok;
    requires org.slf4j;

    exports com.example.library.api;
    exports com.example.library.spi;
    exports com.example.library.internal to com.example.library.test;
}
""")

        result = parse_file(java_file)

        assert result.error is None


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    def test_empty_module(self, tmp_path):
        """Test empty module declaration."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.empty {
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_module_with_all_directives(self, tmp_path):
        """Test module using all directive types."""
        java_file = tmp_path / "module-info.java"
        java_file.write_text("""
module com.example.full {
    requires java.base;
    requires transitive com.example.api;
    requires static lombok;

    exports com.example.full.api;
    exports com.example.full.impl to com.example.client;

    opens com.example.full.entity;
    opens com.example.full.config to spring.core;

    uses com.example.service.DataService;

    provides com.example.service.DataService
        with com.example.full.impl.DataServiceImpl;
}
""")

        result = parse_file(java_file)

        assert result.error is None

    def test_regular_java_file_not_module(self, tmp_path):
        """Test regular Java file (not module-info) still works."""
        java_file = tmp_path / "Main.java"
        java_file.write_text("""
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello World");
    }
}
""")

        result = parse_file(java_file)

        assert result.error is None
        main_class = next(s for s in result.symbols if s.name == "Main")
        assert main_class.kind == "class"
