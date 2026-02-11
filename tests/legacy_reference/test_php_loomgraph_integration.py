"""Tests for PHP LoomGraph integration (Epic 10, Story 10.3).

Tests the complete LoomGraph data extraction from PHP code,
ensuring JSON output includes all required fields for knowledge graph construction.
"""

import json
from pathlib import Path

from codeindex.parser import parse_file


class TestPHPLoomGraphJSONFormat:
    """Test JSON format validation for LoomGraph integration."""

    def test_json_output_has_inheritances_field(self, tmp_path):
        """Test that ParseResult includes inheritances field."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class Parent {}
class Child extends Parent {}
""")
        result = parse_file(php_file)

        # Convert to dict (simulate JSON serialization)
        result_dict = {
            "path": str(result.path),
            "symbols": [
                {"name": s.name, "kind": s.kind, "signature": s.signature}
                for s in result.symbols
            ],
            "imports": [
                {"module": i.module, "names": i.names, "is_from": i.is_from, "alias": i.alias}
                for i in result.imports
            ],
            "inheritances": [
                {"child": inh.child, "parent": inh.parent} for inh in result.inheritances
            ],
            "namespace": result.namespace,
        }

        assert "inheritances" in result_dict
        assert isinstance(result_dict["inheritances"], list)

    def test_json_output_has_alias_field_in_imports(self, tmp_path):
        """Test that Import objects have alias field."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
use App\\Service\\UserService as US;
""")
        result = parse_file(php_file)

        assert len(result.imports) == 1
        imp = result.imports[0]

        # Check alias is accessible as attribute
        assert hasattr(imp, "alias")
        assert imp.alias == "US"

        # Check names is empty
        assert imp.names == []

    def test_json_serialization_complete(self, tmp_path):
        """Test complete JSON serialization with all fields."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Models;

use App\\Base\\Model;

class User extends Model {
    public function save() {}
}
""")
        result = parse_file(php_file)

        # Serialize to JSON
        result_dict = {
            "path": str(result.path),
            "symbols": [
                {
                    "name": s.name,
                    "kind": s.kind,
                    "signature": s.signature,
                    "line_start": s.line_start,
                    "line_end": s.line_end,
                }
                for s in result.symbols
            ],
            "imports": [
                {
                    "module": i.module,
                    "names": i.names,
                    "is_from": i.is_from,
                    "alias": i.alias,
                }
                for i in result.imports
            ],
            "inheritances": [
                {"child": inh.child, "parent": inh.parent} for inh in result.inheritances
            ],
            "namespace": result.namespace,
            "module_docstring": result.module_docstring,
            "file_lines": result.file_lines,
        }

        # Ensure can serialize to JSON
        json_str = json.dumps(result_dict, indent=2)
        assert json_str is not None

        # Verify structure
        parsed = json.loads(json_str)
        assert "inheritances" in parsed
        assert "imports" in parsed
        assert parsed["namespace"] == "App\\Models"


class TestPHPLoomGraphRealWorld:
    """Test real-world PHP framework patterns."""

    def test_laravel_model_pattern(self, tmp_path):
        """Test Laravel Eloquent Model pattern."""
        php_file = tmp_path / "User.php"
        php_file.write_text("""<?php
namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Model;
use Illuminate\\Contracts\\Auth\\Authenticatable;

class User extends Model implements Authenticatable {
    protected $table = 'users';
    protected $fillable = ['name', 'email'];

    public function authenticate() {
        return true;
    }
}
""")
        result = parse_file(php_file)

        # Check namespace
        assert result.namespace == "App\\Models"

        # Check imports
        assert len(result.imports) == 2
        import_modules = [imp.module for imp in result.imports]
        assert "Illuminate\\Database\\Eloquent\\Model" in import_modules
        assert "Illuminate\\Contracts\\Auth\\Authenticatable" in import_modules

        # Check inheritances (extends + implements)
        assert len(result.inheritances) == 2
        assert result.inheritances[0].child == "App\\Models\\User"
        assert result.inheritances[1].child == "App\\Models\\User"

        parents = [inh.parent for inh in result.inheritances]
        assert "Illuminate\\Database\\Eloquent\\Model" in parents
        assert "Illuminate\\Contracts\\Auth\\Authenticatable" in parents

    def test_symfony_controller_pattern(self, tmp_path):
        """Test Symfony Controller pattern."""
        php_file = tmp_path / "UserController.php"
        php_file.write_text("""<?php
namespace App\\Controller;

use Symfony\\Bundle\\FrameworkBundle\\Controller\\AbstractController;
use Symfony\\Component\\HttpFoundation\\Response;
use Symfony\\Component\\Routing\\Annotation\\Route;

class UserController extends AbstractController {
    #[Route('/users', name: 'user_list')]
    public function index(): Response {
        return new Response();
    }

    #[Route('/users/{id}', name: 'user_show')]
    public function show(int $id): Response {
        return new Response();
    }
}
""")
        result = parse_file(php_file)

        # Check namespace
        assert result.namespace == "App\\Controller"

        # Check imports (no aliases)
        assert len(result.imports) == 3
        for imp in result.imports:
            assert imp.alias is None

        # Check inheritance
        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "App\\Controller\\UserController"
        assert (
            result.inheritances[0].parent
            == "Symfony\\Bundle\\FrameworkBundle\\Controller\\AbstractController"
        )

    def test_mixed_namespace_resolution(self, tmp_path):
        """Test complex namespace resolution with group imports."""
        php_file = tmp_path / "Service.php"
        php_file.write_text("""<?php
namespace App\\Services;

use App\\Contracts\\{Authenticatable as Auth, Loggable, Cacheable};
use Illuminate\\Support\\Facades\\{DB, Cache as CacheFacade};

class UserService implements Auth, Loggable {
    public function authenticate() {}
    public function log() {}
}
""")
        result = parse_file(php_file)

        # Check group imports are split correctly
        assert len(result.imports) == 5

        # Check aliases
        auth_import = next(
            imp for imp in result.imports if imp.module == "App\\Contracts\\Authenticatable"
        )
        assert auth_import.alias == "Auth"

        cache_import = next(
            imp for imp in result.imports if imp.module == "Illuminate\\Support\\Facades\\Cache"
        )
        assert cache_import.alias == "CacheFacade"

        # Check inheritances use resolved names
        assert len(result.inheritances) == 2
        parents = [inh.parent for inh in result.inheritances]
        assert "App\\Contracts\\Authenticatable" in parents
        assert "App\\Contracts\\Loggable" in parents


class TestPHPLoomGraphEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_class_without_inheritance(self, tmp_path):
        """Test class with no inheritance relationships."""
        php_file = tmp_path / "Simple.php"
        php_file.write_text("""<?php
class SimpleClass {
    public function method() {}
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 0
        assert len(result.symbols) == 2  # class + method

    def test_file_without_imports(self, tmp_path):
        """Test file with no use statements."""
        php_file = tmp_path / "NoImports.php"
        php_file.write_text("""<?php
namespace App;

class NoImports {
    public function test() {}
}
""")
        result = parse_file(php_file)

        assert len(result.imports) == 0
        assert result.namespace == "App"

    def test_file_without_namespace(self, tmp_path):
        """Test file without namespace declaration."""
        php_file = tmp_path / "Global.php"
        php_file.write_text("""<?php
use Some\\Class;

class GlobalClass extends Class {
}
""")
        result = parse_file(php_file)

        assert result.namespace == ""
        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "GlobalClass"
        assert result.inheritances[0].parent == "Some\\Class"

    def test_empty_file(self, tmp_path):
        """Test empty PHP file."""
        php_file = tmp_path / "Empty.php"
        php_file.write_text("<?php\n")

        result = parse_file(php_file)

        assert len(result.symbols) == 0
        assert len(result.imports) == 0
        assert len(result.inheritances) == 0
        assert result.namespace == ""

    def test_multiple_classes_in_file(self, tmp_path):
        """Test file with multiple class definitions."""
        php_file = tmp_path / "Multiple.php"
        php_file.write_text("""<?php
namespace App;

class Base {}

class Child1 extends Base {}

class Child2 extends Base {}

class GrandChild extends Child1 {}
""")
        result = parse_file(php_file)

        # Should have 3 inheritance relationships
        assert len(result.inheritances) == 3

        # Check inheritance chain
        children = {inh.child for inh in result.inheritances}
        assert "App\\Child1" in children
        assert "App\\Child2" in children
        assert "App\\GrandChild" in children


class TestPHPLoomGraphSampleFile:
    """Test the example PHP LoomGraph sample file."""

    def test_loomgraph_sample_file_exists(self):
        """Test that loomgraph_sample.php exists."""
        sample_file = Path("examples/loomgraph_sample.php")
        assert sample_file.exists()

    def test_loomgraph_sample_file_parsing(self):
        """Test parsing of loomgraph_sample.php."""
        sample_file = Path("examples/loomgraph_sample.php")
        result = parse_file(sample_file)

        assert result.error is None
        assert result.namespace == "App\\Example"

    def test_loomgraph_sample_has_imports(self):
        """Test loomgraph_sample.php has expected imports."""
        sample_file = Path("examples/loomgraph_sample.php")
        result = parse_file(sample_file)

        # Should have at least 5 imports
        assert len(result.imports) >= 5

        # Check for specific imports with aliases
        modules = [imp.module for imp in result.imports]
        assert "Illuminate\\Database\\Eloquent\\Model" in modules
        assert "Illuminate\\Contracts\\Auth\\Authenticatable" in modules

        # Check alias is used
        base_model = next(
            imp for imp in result.imports if "Eloquent\\Model" in imp.module
        )
        assert base_model.alias == "BaseModel"

    def test_loomgraph_sample_has_inheritances(self):
        """Test loomgraph_sample.php has expected inheritance relationships."""
        sample_file = Path("examples/loomgraph_sample.php")
        result = parse_file(sample_file)

        # Should have multiple inheritance relationships
        assert len(result.inheritances) >= 4

        # Check for specific inheritances
        children = {inh.child for inh in result.inheritances}
        assert "App\\Example\\User" in children
        assert "App\\Example\\AdminUser" in children
        assert "App\\Example\\UserController" in children

    def test_loomgraph_sample_json_export(self):
        """Test JSON export of loomgraph_sample.php."""
        sample_file = Path("examples/loomgraph_sample.php")
        result = parse_file(sample_file)

        # Create JSON structure
        output = {
            "path": str(result.path),
            "namespace": result.namespace,
            "symbols": [
                {
                    "name": s.name,
                    "kind": s.kind,
                    "signature": s.signature,
                    "docstring": s.docstring,
                }
                for s in result.symbols
            ],
            "imports": [
                {
                    "module": i.module,
                    "names": i.names,
                    "is_from": i.is_from,
                    "alias": i.alias,
                }
                for i in result.imports
            ],
            "inheritances": [
                {"child": inh.child, "parent": inh.parent} for inh in result.inheritances
            ],
        }

        # Ensure JSON serializable
        json_str = json.dumps(output, indent=2)
        assert len(json_str) > 0

        # Parse back to verify structure
        parsed = json.loads(json_str)
        assert parsed["namespace"] == "App\\Example"
        assert len(parsed["inheritances"]) >= 4
        assert len(parsed["imports"]) >= 5
