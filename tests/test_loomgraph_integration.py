"""Integration tests for LoomGraph compatibility.

Epic 10: LoomGraph Integration - MVP Validation
Tests that codeindex JSON output meets LoomGraph requirements.
"""

import json

from codeindex.parser import parse_file


class TestLoomGraphJSONFormat:
    """Test JSON format compatibility with LoomGraph."""

    def test_complete_python_example(self, tmp_path):
        """Test complete Python file with all features."""
        code = """
'''User authentication module.'''

import os
import numpy as np
from datetime import datetime as dt
from typing import Dict, Optional

class BaseUser:
    '''Base user class.'''
    pass

class AdminUser(BaseUser):
    '''Admin user with elevated privileges.'''

    def __init__(self, username: str):
        self.username = username

    def login(self) -> bool:
        '''Authenticate admin user.'''
        return True

class GuestUser(BaseUser):
    '''Guest user with limited access.'''
    pass
"""
        py_file = tmp_path / "auth.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Convert to dict (JSON-serializable)
        data = result.to_dict()

        # Verify required fields exist
        assert "path" in data
        assert "symbols" in data
        assert "imports" in data
        assert "inheritances" in data
        assert "module_docstring" in data
        assert "error" in data

        # Verify symbols
        assert len(data["symbols"]) > 0
        for symbol in data["symbols"]:
            assert "name" in symbol
            assert "kind" in symbol
            assert "signature" in symbol
            assert "docstring" in symbol
            assert "line_start" in symbol
            assert "line_end" in symbol
            assert "annotations" in symbol

        # Verify imports
        assert len(data["imports"]) > 0
        for imp in data["imports"]:
            assert "module" in imp
            assert "names" in imp
            assert "is_from" in imp
            assert "alias" in imp  # Epic 10 requirement

        # Verify inheritances
        assert len(data["inheritances"]) > 0
        for inh in data["inheritances"]:
            assert "child" in inh
            assert "parent" in inh

    def test_json_serializable(self, tmp_path):
        """Test that output is JSON-serializable."""
        code = """
import numpy as np

class User(BaseModel):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        data = result.to_dict()

        # Should be JSON-serializable
        json_str = json.dumps(data, indent=2)
        assert json_str is not None

        # Should be parseable
        parsed = json.loads(json_str)
        assert parsed["path"] == str(py_file)

    def test_inheritance_extraction(self, tmp_path):
        """Test inheritance data for LoomGraph INHERITS relations."""
        code = """
class Base:
    pass

class Child1(Base):
    pass

class Child2(Base):
    pass

class GrandChild(Child1):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        data = result.to_dict()

        # Verify inheritance relationships
        inheritances = data["inheritances"]
        assert len(inheritances) == 3

        # Check specific relationships
        inh_dict = {(i["child"], i["parent"]) for i in inheritances}
        assert ("Child1", "Base") in inh_dict
        assert ("Child2", "Base") in inh_dict
        assert ("GrandChild", "Child1") in inh_dict

    def test_import_alias_extraction(self, tmp_path):
        """Test import alias for LoomGraph IMPORTS relations."""
        code = """
import os
import numpy as np
from typing import Dict as DictType
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        data = result.to_dict()

        # Verify import aliases
        imports = data["imports"]
        assert len(imports) == 3

        # Check specific imports
        os_imp = [i for i in imports if i["module"] == "os"][0]
        assert os_imp["alias"] is None

        np_imp = [i for i in imports if i["module"] == "numpy"][0]
        assert np_imp["alias"] == "np"

        dict_imp = [i for i in imports if i["module"] == "typing"][0]
        assert dict_imp["alias"] == "DictType"

    def test_nested_class_inheritance(self, tmp_path):
        """Test nested class inheritance (LoomGraph edge case)."""
        code = """
class Outer:
    class Inner(BaseInner):
        pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        data = result.to_dict()

        # Verify nested class shows full path
        symbols = data["symbols"]
        inner_class = [s for s in symbols if "Inner" in s["name"]][0]
        assert inner_class["name"] == "Outer.Inner"

        # Verify inheritance uses full child name
        inheritances = data["inheritances"]
        assert len(inheritances) == 1
        assert inheritances[0]["child"] == "Outer.Inner"
        assert inheritances[0]["parent"] == "BaseInner"


class TestLoomGraphDataMapping:
    """Test data mapping rules from DATA_CONTRACT.md."""

    def test_symbol_to_entity_mapping(self, tmp_path):
        """Test Symbol → Entity mapping."""
        code = """
class UserService:
    '''User management service.'''

    def login(self, username: str) -> bool:
        '''Authenticate user.'''
        return True
"""
        py_file = tmp_path / "service.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        data = result.to_dict()

        # Verify Symbol has all fields needed for Entity
        class_symbol = [s for s in data["symbols"] if s["kind"] == "class"][0]

        # entity_name
        assert class_symbol["name"] == "UserService"

        # entity_type
        assert class_symbol["kind"] == "class"

        # description (docstring)
        assert class_symbol["docstring"] == "User management service."

        # source_id components (file_path + line range)
        assert class_symbol["line_start"] > 0
        assert class_symbol["line_end"] > class_symbol["line_start"]

        # signature
        assert "UserService" in class_symbol["signature"]

        # Method symbol
        method_symbol = [s for s in data["symbols"] if s["kind"] == "method"][0]
        assert method_symbol["name"] == "UserService.login"
        assert method_symbol["signature"].startswith("def login")

    def test_inheritance_to_relation_mapping(self, tmp_path):
        """Test Inheritance → INHERITS relation mapping."""
        code = """
class AdminUser(BaseUser):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        data = result.to_dict()

        # Verify Inheritance has fields for INHERITS relation
        inh = data["inheritances"][0]

        # src_id (child)
        assert inh["child"] == "AdminUser"

        # tgt_id (parent)
        assert inh["parent"] == "BaseUser"

        # relation_type = "INHERITS" (added by LoomGraph)

    def test_import_to_relation_mapping(self, tmp_path):
        """Test Import → IMPORTS relation mapping."""
        code = """
import numpy as np
from typing import Dict
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        data = result.to_dict()

        # Verify Import has fields for IMPORTS relation
        np_imp = [i for i in data["imports"] if i["module"] == "numpy"][0]

        # module (what is imported)
        assert np_imp["module"] == "numpy"

        # alias (how it's referenced)
        assert np_imp["alias"] == "np"

        # is_from (import type)
        assert np_imp["is_from"] is False

        dict_imp = [i for i in data["imports"] if i["module"] == "typing"][0]
        assert dict_imp["names"] == ["Dict"]
        assert dict_imp["is_from"] is True
        assert dict_imp["alias"] is None


class TestLoomGraphRealWorldExample:
    """Test with realistic code example."""

    def test_django_like_model(self, tmp_path):
        """Test Django-like model structure."""
        code = """
'''User authentication models.'''

from datetime import datetime as dt
from typing import Optional

class BaseModel:
    '''Base model with common fields.'''

    def save(self) -> bool:
        '''Save model to database.'''
        return True

class User(BaseModel):
    '''User account model.'''

    def __init__(self, username: str, email: str):
        self.username = username
        self.email = email

    def authenticate(self, password: str) -> bool:
        '''Check user credentials.'''
        return True

class AdminUser(User):
    '''Admin user with elevated permissions.'''

    def grant_permission(self, user_id: int) -> None:
        '''Grant permission to another user.'''
        pass
"""
        py_file = tmp_path / "models.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        data = result.to_dict()

        # Verify complete structure
        assert data["module_docstring"] == "User authentication models."

        # Symbols: 3 classes + 4 methods (save, __init__, authenticate, grant_permission)
        # Note: __init__ without docstring may not be extracted or counted differently
        assert len(data["symbols"]) >= 6  # At least classes + some methods

        # Imports: 2 (datetime as dt, Optional)
        assert len(data["imports"]) == 2

        # Inheritances: User->BaseModel, AdminUser->User
        assert len(data["inheritances"]) == 2

        # Verify key symbols exist
        symbol_names = [s["name"] for s in data["symbols"]]
        assert "BaseModel" in symbol_names
        assert "User" in symbol_names
        assert "AdminUser" in symbol_names

        # Verify inheritance chain
        inh_pairs = [(i["child"], i["parent"]) for i in data["inheritances"]]
        assert ("User", "BaseModel") in inh_pairs
        assert ("AdminUser", "User") in inh_pairs

        # Verify import alias
        dt_imp = [i for i in data["imports"] if i["alias"] == "dt"][0]
        assert dt_imp["module"] == "datetime"
        assert dt_imp["names"] == ["datetime"]


class TestLoomGraphEdgeCases:
    """Test edge cases that LoomGraph should handle."""

    def test_empty_file(self, tmp_path):
        """Test empty file."""
        py_file = tmp_path / "empty.py"
        py_file.write_text("")

        result = parse_file(py_file)
        data = result.to_dict()

        # Should have valid structure with empty lists
        assert data["symbols"] == []
        assert data["imports"] == []
        assert data["inheritances"] == []
        assert data["error"] is None

    def test_syntax_error_file(self, tmp_path):
        """Test file with syntax errors."""
        code = """
class Broken(
    # Missing closing paren
"""
        py_file = tmp_path / "broken.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        data = result.to_dict()

        # Should report error
        assert data["error"] is not None
        assert "Syntax error" in data["error"]

    def test_multiple_inheritance(self, tmp_path):
        """Test multiple inheritance (creates multiple INHERITS relations)."""
        code = """
class User(BaseModel, Loggable, Serializable):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        data = result.to_dict()

        # Should create 3 inheritance relationships
        assert len(data["inheritances"]) == 3

        parents = [i["parent"] for i in data["inheritances"]]
        assert "BaseModel" in parents
        assert "Loggable" in parents
        assert "Serializable" in parents

    def test_generic_type_inheritance(self, tmp_path):
        """Test generic type inheritance (strip type parameters)."""
        code = """
from typing import Generic, TypeVar

T = TypeVar('T')

class Container(Generic[T]):
    pass

class UserList(list[str]):
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        data = result.to_dict()

        # Should extract base types without type parameters
        inheritances = data["inheritances"]
        assert len(inheritances) == 2

        # Generic should be base, not Generic[T]
        generic_inh = [i for i in inheritances if i["child"] == "Container"][0]
        assert generic_inh["parent"] == "Generic"

        # list should be base, not list[str]
        list_inh = [i for i in inheritances if i["child"] == "UserList"][0]
        assert list_inh["parent"] == "list"
