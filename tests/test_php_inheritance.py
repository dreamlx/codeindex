"""Tests for PHP inheritance extraction (Epic 10, Story 10.1.2).

Tests the extraction of class inheritance relationships from PHP code,
including extends and implements keywords.
"""

from codeindex.parser import parse_file


class TestPHPInheritanceBasic:
    """Basic PHP inheritance extraction tests."""

    def test_extends_single_inheritance(self, tmp_path):
        """Test single inheritance with extends keyword."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class BaseUser {
    public function save() {}
}

class AdminUser extends BaseUser {
    public function grant() {}
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "AdminUser"
        assert result.inheritances[0].parent == "BaseUser"

    def test_implements_single_interface(self, tmp_path):
        """Test single interface implementation."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
interface Authenticatable {
    public function authenticate();
}

class User implements Authenticatable {
    public function authenticate() {}
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert result.inheritances[0].parent == "Authenticatable"

    def test_implements_multiple_interfaces(self, tmp_path):
        """Test multiple interface implementation."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
interface Authenticatable {}
interface Loggable {}

class User implements Authenticatable, Loggable {
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 2
        children = [inh.child for inh in result.inheritances]
        parents = [inh.parent for inh in result.inheritances]

        assert all(child == "User" for child in children)
        assert "Authenticatable" in parents
        assert "Loggable" in parents

    def test_extends_and_implements_combined(self, tmp_path):
        """Test class that both extends and implements."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class Model {}
interface Authenticatable {}

class User extends Model implements Authenticatable {
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 2

        # Find extends relationship
        extends_rel = next(inh for inh in result.inheritances if inh.parent == "Model")
        assert extends_rel.child == "User"

        # Find implements relationship
        implements_rel = next(inh for inh in result.inheritances if inh.parent == "Authenticatable")
        assert implements_rel.child == "User"


class TestPHPInheritanceNamespace:
    """PHP inheritance with namespace tests."""

    def test_inheritance_with_namespace(self, tmp_path):
        """Test inheritance with namespace declarations."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Models;

class BaseModel {
}

class User extends BaseModel {
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "App\\Models\\User"
        assert result.inheritances[0].parent == "App\\Models\\BaseModel"

    def test_inheritance_with_use_statement(self, tmp_path):
        """Test inheritance with use statement for parent class."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Models;

use App\\Base\\Model;

class User extends Model {
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "App\\Models\\User"
        assert result.inheritances[0].parent == "App\\Base\\Model"

    def test_inheritance_with_multiple_use_statements(self, tmp_path):
        """Test inheritance resolving multiple use statements."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Models;

use App\\Base\\Model;
use Illuminate\\Contracts\\Auth\\Authenticatable;

class User extends Model implements Authenticatable {
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 2

        # Check extends relationship
        extends_rel = next(inh for inh in result.inheritances if "Model" in inh.parent)
        assert extends_rel.child == "App\\Models\\User"
        assert extends_rel.parent == "App\\Base\\Model"

        # Check implements relationship
        implements_rel = next(inh for inh in result.inheritances if "Authenticatable" in inh.parent)
        assert implements_rel.child == "App\\Models\\User"
        assert implements_rel.parent == "Illuminate\\Contracts\\Auth\\Authenticatable"

    def test_inheritance_with_aliased_use(self, tmp_path):
        """Test inheritance with aliased use statement."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Models;

use App\\Base\\Model as BaseModel;

class User extends BaseModel {
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "App\\Models\\User"
        assert result.inheritances[0].parent == "App\\Base\\Model"


class TestPHPInheritanceModifiers:
    """PHP inheritance with class modifiers tests."""

    def test_abstract_class_as_parent(self, tmp_path):
        """Test abstract class can be a parent."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
abstract class BaseModel {
    abstract public function save();
}

class User extends BaseModel {
    public function save() {}
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert result.inheritances[0].parent == "BaseModel"

    def test_final_class_as_child(self, tmp_path):
        """Test final class can extend (but cannot be extended)."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class Model {
}

final class User extends Model {
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert result.inheritances[0].parent == "Model"


class TestPHPInheritanceEdgeCases:
    """Edge cases and special scenarios."""

    def test_no_inheritance(self, tmp_path):
        """Test class with no inheritance."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class User {
    public function save() {}
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 0

    def test_empty_file(self, tmp_path):
        """Test empty PHP file."""
        php_file = tmp_path / "test.php"
        php_file.write_text("<?php\n")

        result = parse_file(php_file)

        assert len(result.inheritances) == 0

    def test_multiple_classes_with_inheritance(self, tmp_path):
        """Test multiple classes with different inheritance."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class BaseModel {
}

class User extends BaseModel {
}

class Post extends BaseModel {
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 2

        children = [inh.child for inh in result.inheritances]
        assert "User" in children
        assert "Post" in children

        # Both extend BaseModel
        assert all(inh.parent == "BaseModel" for inh in result.inheritances)

    def test_inheritance_chain(self, tmp_path):
        """Test inheritance chain (A extends B, B extends C)."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class Model {
}

class BaseUser extends Model {
}

class AdminUser extends BaseUser {
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 2

        # BaseUser extends Model
        base_rel = next(inh for inh in result.inheritances if inh.child == "BaseUser")
        assert base_rel.parent == "Model"

        # AdminUser extends BaseUser
        admin_rel = next(inh for inh in result.inheritances if inh.child == "AdminUser")
        assert admin_rel.parent == "BaseUser"


class TestPHPInheritanceGroupImports:
    """Tests for group imports (use App\\{A, B})."""

    def test_group_import_with_inheritance(self, tmp_path):
        """Test inheritance with group import."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Models;

use App\\Contracts\\{Authenticatable, Loggable};

class User implements Authenticatable, Loggable {
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 2

        parents = [inh.parent for inh in result.inheritances]
        assert "App\\Contracts\\Authenticatable" in parents
        assert "App\\Contracts\\Loggable" in parents


class TestPHPInheritanceRealWorld:
    """Real-world Laravel/Symfony style examples."""

    def test_laravel_model_style(self, tmp_path):
        """Test Laravel Model inheritance pattern."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Model;
use Illuminate\\Contracts\\Auth\\Authenticatable;

class User extends Model implements Authenticatable {
    protected $table = 'users';
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 2
        assert result.inheritances[0].child == "App\\Models\\User"
        assert result.inheritances[1].child == "App\\Models\\User"

        parents = [inh.parent for inh in result.inheritances]
        assert "Illuminate\\Database\\Eloquent\\Model" in parents
        assert "Illuminate\\Contracts\\Auth\\Authenticatable" in parents

    def test_symfony_controller_style(self, tmp_path):
        """Test Symfony Controller inheritance pattern."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Controller;

use Symfony\\Bundle\\FrameworkBundle\\Controller\\AbstractController;

class UserController extends AbstractController {
    public function index() {}
}
""")
        result = parse_file(php_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "App\\Controller\\UserController"
        assert result.inheritances[0].parent == (
            "Symfony\\Bundle\\FrameworkBundle\\Controller\\AbstractController"
        )
