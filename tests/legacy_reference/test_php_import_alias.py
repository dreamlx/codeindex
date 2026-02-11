"""Tests for PHP import alias extraction (Epic 10, Story 10.2.2).

Tests the extraction of import aliases from PHP use statements,
ensuring alias is stored in the alias field (not names field).
"""

from codeindex.parser import parse_file


class TestPHPImportAliasBasic:
    """Basic PHP import alias extraction tests."""

    def test_use_with_alias(self, tmp_path):
        """Test use statement with alias."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
use App\\Service\\UserService as US;
""")
        result = parse_file(php_file)

        assert len(result.imports) == 1
        assert result.imports[0].module == "App\\Service\\UserService"
        assert result.imports[0].names == []  # PHP use imports whole class
        assert result.imports[0].is_from is True
        assert result.imports[0].alias == "US"

    def test_use_without_alias(self, tmp_path):
        """Test use statement without alias."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
use App\\Model\\User;
""")
        result = parse_file(php_file)

        assert len(result.imports) == 1
        assert result.imports[0].module == "App\\Model\\User"
        assert result.imports[0].names == []
        assert result.imports[0].is_from is True
        assert result.imports[0].alias is None

    def test_multiple_use_statements(self, tmp_path):
        """Test multiple use statements."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
use App\\Service\\UserService as US;
use App\\Model\\User;
use App\\Repository\\OrderRepository as OrderRepo;
""")
        result = parse_file(php_file)

        assert len(result.imports) == 3

        # Check UserService with alias
        us_import = next(imp for imp in result.imports if "UserService" in imp.module)
        assert us_import.alias == "US"
        assert us_import.names == []

        # Check User without alias
        user_import = next(imp for imp in result.imports if imp.module == "App\\Model\\User")
        assert user_import.alias is None
        assert us_import.names == []

        # Check OrderRepository with alias
        order_import = next(imp for imp in result.imports if "OrderRepository" in imp.module)
        assert order_import.alias == "OrderRepo"
        assert order_import.names == []


class TestPHPImportAliasGroupImports:
    """Tests for PHP group imports (use App\\{A, B})."""

    def test_group_import_with_alias(self, tmp_path):
        """Test group import with aliases."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
use App\\Repository\\{UserRepository as UR, OrderRepository as OrderRepo};
""")
        result = parse_file(php_file)

        assert len(result.imports) == 2

        # Check each import is separate
        ur_import = next(imp for imp in result.imports if "UserRepository" in imp.module)
        assert ur_import.module == "App\\Repository\\UserRepository"
        assert ur_import.alias == "UR"
        assert ur_import.names == []

        order_import = next(imp for imp in result.imports if "OrderRepository" in imp.module)
        assert order_import.module == "App\\Repository\\OrderRepository"
        assert order_import.alias == "OrderRepo"
        assert order_import.names == []

    def test_group_import_without_alias(self, tmp_path):
        """Test group import without aliases."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
use App\\Repository\\{UserRepository, OrderRepository};
""")
        result = parse_file(php_file)

        assert len(result.imports) == 2

        for imp in result.imports:
            assert imp.alias is None
            assert imp.names == []
            assert "Repository" in imp.module

    def test_group_import_mixed_alias(self, tmp_path):
        """Test group import with mixed aliased/non-aliased."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
use App\\Repository\\{UserRepository as UR, OrderRepository};
""")
        result = parse_file(php_file)

        assert len(result.imports) == 2

        # One with alias
        ur_import = next(imp for imp in result.imports if "UserRepository" in imp.module)
        assert ur_import.alias == "UR"

        # One without alias
        or_import = next(imp for imp in result.imports if "OrderRepository" in imp.module)
        assert or_import.alias is None


class TestPHPImportAliasNamespace:
    """Tests for imports with namespace declarations."""

    def test_namespace_with_aliased_use(self, tmp_path):
        """Test namespace combined with aliased use."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Models;

use App\\Base\\Model as BaseModel;
use Illuminate\\Support\\Facades\\DB;
""")
        result = parse_file(php_file)

        assert len(result.imports) == 2
        assert result.namespace == "App\\Models"

        # Check BaseModel alias
        base_import = next(imp for imp in result.imports if imp.module == "App\\Base\\Model")
        assert base_import.module == "App\\Base\\Model"
        assert base_import.alias == "BaseModel"
        assert base_import.names == []

        # Check DB without alias (but uses short name)
        db_import = next(
            imp for imp in result.imports if imp.module == "Illuminate\\Support\\Facades\\DB"
        )
        assert db_import.module == "Illuminate\\Support\\Facades\\DB"
        assert db_import.alias is None
        assert db_import.names == []


class TestPHPImportAliasEdgeCases:
    """Edge cases and special scenarios."""

    def test_no_imports(self, tmp_path):
        """Test file with no use statements."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
class User {
}
""")
        result = parse_file(php_file)

        assert len(result.imports) == 0

    def test_empty_file(self, tmp_path):
        """Test empty PHP file."""
        php_file = tmp_path / "test.php"
        php_file.write_text("<?php\n")

        result = parse_file(php_file)

        assert len(result.imports) == 0

    def test_multiline_use_statement(self, tmp_path):
        """Test multiline use statement (if supported)."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
use App\\Service\\UserService
    as US;
""")
        result = parse_file(php_file)

        # Should handle multiline
        assert len(result.imports) == 1
        assert result.imports[0].alias == "US"


class TestPHPImportAliasRealWorld:
    """Real-world Laravel/Symfony style examples."""

    def test_laravel_facades_style(self, tmp_path):
        """Test Laravel Facades import pattern."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Http\\Controllers;

use Illuminate\\Http\\Request;
use Illuminate\\Support\\Facades\\DB;
use Illuminate\\Support\\Facades\\Auth;
use App\\Models\\User as UserModel;
""")
        result = parse_file(php_file)

        assert len(result.imports) == 4

        # Check UserModel has alias
        user_import = next(imp for imp in result.imports if "User" in imp.module)
        assert user_import.alias == "UserModel"

        # Check others have no alias
        request_import = next(imp for imp in result.imports if "Request" in imp.module)
        assert request_import.alias is None

    def test_symfony_use_style(self, tmp_path):
        """Test Symfony use statement pattern."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Controller;

use Symfony\\Component\\HttpFoundation\\Response;
use Symfony\\Component\\Routing\\Annotation\\Route;
use App\\Entity\\User;
""")
        result = parse_file(php_file)

        assert len(result.imports) == 3

        # All should have no alias
        for imp in result.imports:
            assert imp.alias is None
            assert imp.names == []

    def test_complex_group_imports(self, tmp_path):
        """Test complex group imports with namespace."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
namespace App\\Services;

use App\\Contracts\\{
    Authenticatable as Auth,
    Authorizable,
    Loggable as Log
};
""")
        result = parse_file(php_file)

        assert len(result.imports) == 3

        # Check Auth alias
        auth_import = next(imp for imp in result.imports if "Authenticatable" in imp.module)
        assert auth_import.module == "App\\Contracts\\Authenticatable"
        assert auth_import.alias == "Auth"

        # Check Authorizable no alias
        authz_import = next(imp for imp in result.imports if "Authorizable" in imp.module)
        assert authz_import.alias is None

        # Check Log alias
        log_import = next(imp for imp in result.imports if "Loggable" in imp.module)
        assert log_import.module == "App\\Contracts\\Loggable"
        assert log_import.alias == "Log"


class TestPHPImportAliasConsistency:
    """Tests for consistency with Python import behavior."""

    def test_names_field_always_empty(self, tmp_path):
        """Test that names field is always empty for PHP imports."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
use App\\Service\\UserService as US;
use App\\Model\\User;
use App\\Repository\\{OrderRepo as OrderRepository, ProductRepo};
""")
        result = parse_file(php_file)

        # All imports should have empty names list
        for imp in result.imports:
            assert imp.names == []
            assert imp.is_from is True

    def test_alias_field_correctness(self, tmp_path):
        """Test that alias field is correctly populated."""
        php_file = tmp_path / "test.php"
        php_file.write_text("""<?php
use App\\A as AA;
use App\\B;
""")
        result = parse_file(php_file)

        assert len(result.imports) == 2

        # First has alias
        aa_import = result.imports[0]
        assert aa_import.alias == "AA"

        # Second has no alias
        b_import = result.imports[1]
        assert b_import.alias is None
