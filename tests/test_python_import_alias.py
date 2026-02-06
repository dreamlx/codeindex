"""Tests for Python import alias extraction.

Epic 10, Story 10.2.1: Python Import Alias Support
Tests extraction of import aliases from Python code.
"""

from codeindex.parser import parse_file


class TestImportAsBasic:
    """Test basic import X as Y."""

    def test_import_single_module_with_alias(self, tmp_path):
        """Test import module as alias."""
        code = "import numpy as np"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.module == "numpy"
        assert imp.names == []
        assert imp.is_from is False
        assert imp.alias == "np"

    def test_import_submodule_with_alias(self, tmp_path):
        """Test import submodule as alias."""
        code = "import os.path as ospath"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.module == "os.path"
        assert imp.alias == "ospath"

    def test_import_without_alias(self, tmp_path):
        """Test import without alias (backward compatibility)."""
        code = "import os"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.module == "os"
        assert imp.alias is None

    def test_import_multiple_modules_mixed(self, tmp_path):
        """Test multiple imports, some with aliases."""
        code = """
import os
import numpy as np
import sys
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 3
        # os: no alias
        os_imp = [i for i in result.imports if i.module == "os"][0]
        assert os_imp.alias is None

        # numpy as np
        np_imp = [i for i in result.imports if i.module == "numpy"][0]
        assert np_imp.alias == "np"

        # sys: no alias
        sys_imp = [i for i in result.imports if i.module == "sys"][0]
        assert sys_imp.alias is None


class TestFromImportAs:
    """Test from X import Y as Z."""

    def test_from_import_single_name_with_alias(self, tmp_path):
        """Test from module import name as alias."""
        code = "from datetime import datetime as dt"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.module == "datetime"
        assert imp.names == ["datetime"]
        assert imp.is_from is True
        assert imp.alias == "dt"

    def test_from_import_multiple_names_with_alias(self, tmp_path):
        """Test from module import name1, name2 as alias."""
        code = "from typing import Dict as DictType, List as ListType"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should create separate Import for each aliased name
        assert len(result.imports) == 2

        dict_imp = [i for i in result.imports if "Dict" in i.names][0]
        assert dict_imp.module == "typing"
        assert dict_imp.names == ["Dict"]
        assert dict_imp.alias == "DictType"

        list_imp = [i for i in result.imports if "List" in i.names][0]
        assert list_imp.module == "typing"
        assert list_imp.names == ["List"]
        assert list_imp.alias == "ListType"

    def test_from_import_without_alias(self, tmp_path):
        """Test from import without alias (backward compatibility)."""
        code = "from typing import Optional"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.module == "typing"
        assert imp.names == ["Optional"]
        assert imp.is_from is True
        assert imp.alias is None

    def test_from_import_mixed_aliases(self, tmp_path):
        """Test from import with mixed aliased/non-aliased names."""
        code = "from typing import Dict, Optional as Opt, List"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should have 3 imports
        assert len(result.imports) == 3

        # Dict: no alias
        dict_imp = [i for i in result.imports if "Dict" in i.names][0]
        assert dict_imp.alias is None

        # Optional as Opt
        opt_imp = [i for i in result.imports if "Optional" in i.names][0]
        assert opt_imp.alias == "Opt"

        # List: no alias
        list_imp = [i for i in result.imports if "List" in i.names][0]
        assert list_imp.alias is None


class TestComplexScenarios:
    """Test complex import scenarios."""

    def test_all_import_types_mixed(self, tmp_path):
        """Test file with all types of imports."""
        code = """
import os
import numpy as np
from typing import Dict
from datetime import datetime as dt
from pathlib import Path as P
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 5

        # Verify each import
        imports_dict = {i.module: i for i in result.imports if not i.is_from}
        from_imports = {(i.module, i.names[0]): i for i in result.imports if i.is_from}

        # import os
        assert "os" in imports_dict
        assert imports_dict["os"].alias is None

        # import numpy as np
        assert "numpy" in imports_dict
        assert imports_dict["numpy"].alias == "np"

        # from typing import Dict
        assert ("typing", "Dict") in from_imports
        assert from_imports[("typing", "Dict")].alias is None

        # from datetime import datetime as dt
        assert ("datetime", "datetime") in from_imports
        assert from_imports[("datetime", "datetime")].alias == "dt"

        # from pathlib import Path as P
        assert ("pathlib", "Path") in from_imports
        assert from_imports[("pathlib", "Path")].alias == "P"

    def test_submodule_from_import_with_alias(self, tmp_path):
        """Test from submodule import with alias."""
        code = "from os.path import join as path_join"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 1
        imp = result.imports[0]
        assert imp.module == "os.path"
        assert imp.names == ["join"]
        assert imp.alias == "path_join"

    def test_long_alias_name(self, tmp_path):
        """Test import with long alias name."""
        code = "import numpy as numpy_array_processing_library"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 1
        assert result.imports[0].alias == "numpy_array_processing_library"


class TestEdgeCases:
    """Test edge cases."""

    def test_empty_file(self, tmp_path):
        """Test empty file."""
        py_file = tmp_path / "empty.py"
        py_file.write_text("")

        result = parse_file(py_file)

        assert len(result.imports) == 0

    def test_no_imports(self, tmp_path):
        """Test file with no imports."""
        code = """
def function():
    pass

class MyClass:
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 0

    def test_import_with_underscore_alias(self, tmp_path):
        """Test import with underscore in alias."""
        code = "import numpy as np_array"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 1
        assert result.imports[0].alias == "np_array"

    def test_from_import_star_no_alias(self, tmp_path):
        """Test from module import * (no alias possible)."""
        code = "from typing import *"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should still parse, but no alias
        assert len(result.imports) == 1
        assert result.imports[0].alias is None

    def test_relative_import_with_alias(self, tmp_path):
        """Test relative import with alias."""
        code = "from . import utils as my_utils"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 1
        imp = result.imports[0]
        # Relative imports should be captured
        assert imp.alias == "my_utils"

    def test_multiline_import_with_aliases(self, tmp_path):
        """Test multiline import with aliases."""
        code = """
from typing import (
    Dict as DictType,
    List as ListType,
    Optional
)
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        assert len(result.imports) == 3

        # Dict as DictType
        dict_imp = [i for i in result.imports if "Dict" in i.names][0]
        assert dict_imp.alias == "DictType"

        # List as ListType
        list_imp = [i for i in result.imports if "List" in i.names][0]
        assert list_imp.alias == "ListType"

        # Optional (no alias)
        opt_imp = [i for i in result.imports if "Optional" in i.names][0]
        assert opt_imp.alias is None


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_existing_imports_still_work(self, tmp_path):
        """Test that existing imports without alias still work."""
        code = """
import os
import sys
from typing import Dict, List
from pathlib import Path
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # All imports should have alias=None
        for imp in result.imports:
            assert imp.alias is None

    def test_import_dataclass_has_alias_field(self, tmp_path):
        """Test that Import objects always have alias field."""
        code = "import os"
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        imp = result.imports[0]
        # Should have alias attribute (even if None)
        assert hasattr(imp, "alias")
        assert imp.alias is None
