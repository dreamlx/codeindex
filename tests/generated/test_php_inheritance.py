"""Tests for PHP inheritance extraction.

Auto-generated from: test_generator/specs/php.yaml
Generator: test_generator/generator.py
Template: test_generator/templates/inheritance_test.py.j2

DO NOT EDIT MANUALLY - changes will be overwritten.
To modify tests, edit the YAML spec and regenerate.
"""


from codeindex.parser import parse_file


class TestPHPInheritanceBasic:
    """Test basic PHP inheritance extraction."""

    def test_extends_single_inheritance(self, tmp_path):
        """Single inheritance with extends keyword."""
        code = """
<?php
class BaseUser {
    public function save() {}
}

class AdminUser extends BaseUser {
    public function grant() {}
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "AdminUser"
        assert result.inheritances[0].parent == "BaseUser"

    def test_implements_single_interface(self, tmp_path):
        """Single interface implementation."""
        code = """
<?php
interface Authenticatable {
    public function authenticate();
}

class User implements Authenticatable {
    public function authenticate() {}
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert result.inheritances[0].parent == "Authenticatable"

    def test_implements_multiple_interfaces(self, tmp_path):
        """Multiple interface implementation."""
        code = """
<?php
interface Authenticatable {}
interface Loggable {}

class User implements Authenticatable, Loggable {
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        user_inh = [
            inh for inh in result.inheritances if inh.child == "User"
        ]
        assert len(user_inh) == 2
        user_parents = {inh.parent for inh in user_inh}
        assert "Authenticatable" in user_parents
        assert "Loggable" in user_parents

    def test_extends_and_implements_combined(self, tmp_path):
        """Class with extends and implements combined."""
        code = """
<?php
class Model {}
interface Authenticatable {}

class User extends Model implements Authenticatable {
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        user_inh = [
            inh for inh in result.inheritances if inh.child == "User"
        ]
        assert len(user_inh) == 2
        user_parents = {inh.parent for inh in user_inh}
        assert "Model" in user_parents
        assert "Authenticatable" in user_parents

class TestPHPInheritanceNamespace:
    """Test PHP inheritance with namespaces."""

    def test_inheritance_with_namespace(self, tmp_path):
        """Inheritance with namespace declarations."""
        code = """
<?php
namespace App\\Models;

class BaseModel {
}

class User extends BaseModel {
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "App\\Models\\User"
        assert result.inheritances[0].parent == "App\\Models\\BaseModel"

    def test_inheritance_with_use_statement(self, tmp_path):
        """Inheritance with use statement for parent class."""
        code = """
<?php
namespace App\\Models;

use App\\Base\\Model;

class User extends Model {
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "App\\Models\\User"
        assert result.inheritances[0].parent == "App\\Base\\Model"

    def test_inheritance_with_multiple_use_statements(self, tmp_path):
        """Inheritance resolving multiple use statements."""
        code = """
<?php
namespace App\\Models;

use App\\Base\\Model;
use Illuminate\\Contracts\\Auth\\Authenticatable;

class User extends Model implements Authenticatable {
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        app_models_user_inh = [
            inh for inh in result.inheritances if inh.child == "App\\Models\\User"
        ]
        assert len(app_models_user_inh) == 2
        app_models_user_parents = {inh.parent for inh in app_models_user_inh}
        assert "App\\Base\\Model" in app_models_user_parents
        assert "Illuminate\\Contracts\\Auth\\Authenticatable" in app_models_user_parents

    def test_inheritance_with_aliased_use(self, tmp_path):
        """Inheritance with aliased use statement."""
        code = """
<?php
namespace App\\Models;

use App\\Base\\Model as BaseModel;

class User extends BaseModel {
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "App\\Models\\User"
        assert result.inheritances[0].parent == "App\\Base\\Model"

class TestPHPInheritanceModifiers:
    """Test PHP inheritance with class modifiers."""

    def test_abstract_class_as_parent(self, tmp_path):
        """Abstract class as parent."""
        code = """
<?php
abstract class BaseModel {
    abstract public function save();
}

class User extends BaseModel {
    public function save() {}
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert result.inheritances[0].parent == "BaseModel"

    def test_final_class_as_child(self, tmp_path):
        """Final class as child (can extend but cannot be extended)."""
        code = """
<?php
class Model {
}

final class User extends Model {
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert result.inheritances[0].parent == "Model"

class TestPHPInheritanceEdgeCases:
    """Test PHP edge cases."""

    def test_no_inheritance(self, tmp_path):
        """Class with no inheritance."""
        code = """
<?php
class User {
    public function save() {}
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 0

    def test_empty_file(self, tmp_path):
        """Empty PHP file."""
        code = """
<?php
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 0

    def test_multiple_classes_with_inheritance(self, tmp_path):
        """Multiple classes with different inheritance."""
        code = """
<?php
class BaseModel {
}

class User extends BaseModel {
}

class Post extends BaseModel {
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 2
        user_inh = [
            inh for inh in result.inheritances if inh.child == "User"
        ]
        assert len(user_inh) == 1
        user_parents = {inh.parent for inh in user_inh}
        assert "BaseModel" in user_parents
        post_inh = [
            inh for inh in result.inheritances if inh.child == "Post"
        ]
        assert len(post_inh) == 1
        post_parents = {inh.parent for inh in post_inh}
        assert "BaseModel" in post_parents

    def test_inheritance_chain(self, tmp_path):
        """Inheritance chain (A extends B, B extends C)."""
        code = """
<?php
class Model {
}

class BaseUser extends Model {
}

class AdminUser extends BaseUser {
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 2
        baseuser_inh = [
            inh for inh in result.inheritances if inh.child == "BaseUser"
        ]
        assert len(baseuser_inh) == 1
        baseuser_parents = {inh.parent for inh in baseuser_inh}
        assert "Model" in baseuser_parents
        adminuser_inh = [
            inh for inh in result.inheritances if inh.child == "AdminUser"
        ]
        assert len(adminuser_inh) == 1
        adminuser_parents = {inh.parent for inh in adminuser_inh}
        assert "BaseUser" in adminuser_parents

class TestPHPInheritanceGroupImports:
    """Test PHP group imports."""

    def test_group_import_with_inheritance(self, tmp_path):
        """Inheritance with group import syntax."""
        code = """
<?php
namespace App\\Models;

use App\\Contracts\\{Authenticatable, Loggable};

class User implements Authenticatable, Loggable {
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        app_models_user_inh = [
            inh for inh in result.inheritances if inh.child == "App\\Models\\User"
        ]
        assert len(app_models_user_inh) == 2
        app_models_user_parents = {inh.parent for inh in app_models_user_inh}
        assert "App\\Contracts\\Authenticatable" in app_models_user_parents
        assert "App\\Contracts\\Loggable" in app_models_user_parents

class TestPHPInheritanceRealWorld:
    """Test real-world Laravel/Symfony patterns."""

    def test_laravel_model_style(self, tmp_path):
        """Laravel Model inheritance pattern."""
        code = """
<?php
namespace App\\Models;

use Illuminate\\Database\\Eloquent\\Model;
use Illuminate\\Contracts\\Auth\\Authenticatable;

class User extends Model implements Authenticatable {
    protected $table = 'users';
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        app_models_user_inh = [
            inh for inh in result.inheritances if inh.child == "App\\Models\\User"
        ]
        assert len(app_models_user_inh) == 2
        app_models_user_parents = {inh.parent for inh in app_models_user_inh}
        assert "Illuminate\\Database\\Eloquent\\Model" in app_models_user_parents
        assert "Illuminate\\Contracts\\Auth\\Authenticatable" in app_models_user_parents

    def test_symfony_controller_style(self, tmp_path):
        """Symfony Controller inheritance pattern."""
        code = """
<?php
namespace App\\Controller;

use Symfony\\Bundle\\FrameworkBundle\\Controller\\AbstractController;

class UserController extends AbstractController {
    public function index() {}
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "App\\Controller\\UserController"
        assert result.inheritances[0].parent == "Symfony\\Bundle\\FrameworkBundle\\Controller\\AbstractController"

class TestPHPInheritanceAdvanced:
    """Test advanced PHP inheritance patterns."""

    def test_interface_extends_interface(self, tmp_path):
        """Interface extending another interface."""
        code = """
<?php
interface Readable {
    public function read();
}

interface Streamable extends Readable {
    public function stream();
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 0

    def test_trait_usage(self, tmp_path):
        """Class using a trait (use keyword inside class)."""
        code = """
<?php
trait Timestamps {
    public function getCreatedAt() {}
}

class User {
    use Timestamps;
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 0

    def test_extends_with_constructor(self, tmp_path):
        """Inheritance with constructor."""
        code = """
<?php
class BaseModel {
    public function __construct() {}
}

class User extends BaseModel {
    public function __construct() {
        parent::__construct();
    }
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "User"
        assert result.inheritances[0].parent == "BaseModel"

    def test_multiple_interfaces_and_extends(self, tmp_path):
        """Class extending and implementing multiple interfaces."""
        code = """
<?php
class Model {}
interface Authenticatable {}
interface Serializable {}

class User extends Model implements Authenticatable, Serializable {
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        user_inh = [
            inh for inh in result.inheritances if inh.child == "User"
        ]
        assert len(user_inh) == 3
        user_parents = {inh.parent for inh in user_inh}
        assert "Model" in user_parents
        assert "Authenticatable" in user_parents
        assert "Serializable" in user_parents

    def test_readonly_class(self, tmp_path):
        """PHP 8.2 readonly class with inheritance."""
        code = """
<?php
class BaseDTO {
}

readonly class UserDTO extends BaseDTO {
    public function __construct(
        public string $name,
        public string $email,
    ) {}
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "UserDTO"
        assert result.inheritances[0].parent == "BaseDTO"

    def test_enum_implements(self, tmp_path):
        """PHP 8.1 enum implementing interface."""
        code = """
<?php
interface HasLabel {
    public function label(): string;
}

enum Status: string implements HasLabel {
    case Active = 'active';
    case Inactive = 'inactive';

    public function label(): string {
        return $this->value;
    }
}
"""
        test_file = tmp_path / "test.php"
        test_file.write_text(code)

        result = parse_file(test_file)

        assert len(result.inheritances) == 0
