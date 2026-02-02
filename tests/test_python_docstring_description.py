"""Tests for Python docstring description extraction (Epic 6, P2, Task 3.5)."""

from textwrap import dedent

from codeindex.parser import parse_file


class TestPythonDocstringDescription:
    """Test Python docstring extraction for route descriptions."""

    def test_extract_description_from_function_docstring(self, tmp_path):
        """Should extract description from Python function docstring."""
        # Arrange
        py_file = tmp_path / "views.py"
        py_file.write_text(
            dedent(
                '''
                def get_user_list(request):
                    """Get list of all users."""
                    return []
                '''
            )
        )

        # Act
        result = parse_file(py_file)

        # Assert
        assert not result.error
        functions = [s for s in result.symbols if s.kind == "function"]
        assert len(functions) == 1
        assert "Get list of all users" in functions[0].docstring

    def test_extract_description_from_method_docstring(self, tmp_path):
        """Should extract description from Python method docstring."""
        py_file = tmp_path / "views.py"
        py_file.write_text(
            dedent(
                '''
                class UserView:
                    def get(self, request):
                        """Retrieve user profile data."""
                        return {}
                '''
            )
        )

        result = parse_file(py_file)

        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) == 1
        assert "Retrieve user profile data" in methods[0].docstring

    def test_extract_first_line_from_multiline_docstring(self, tmp_path):
        """Should extract first line from multi-line Python docstring."""
        py_file = tmp_path / "views.py"
        py_file.write_text(
            dedent(
                '''
                def create_user(request):
                    """
                    Create a new user account.

                    This function validates the request data and
                    creates a new user in the database.

                    Args:
                        request: HTTP request object

                    Returns:
                        User object
                    """
                    pass
                '''
            )
        )

        result = parse_file(py_file)

        functions = [s for s in result.symbols if s.kind == "function"]
        assert len(functions) == 1
        # Should extract the summary line
        assert "Create a new user account" in functions[0].docstring

    def test_extract_description_with_chinese_characters(self, tmp_path):
        """Should extract Chinese descriptions from Python docstrings."""
        py_file = tmp_path / "views.py"
        py_file.write_text(
            dedent(
                '''
                def lottery_draw(request):
                    """幸运抽奖"""
                    return {}
                '''
            )
        )

        result = parse_file(py_file)

        functions = [s for s in result.symbols if s.kind == "function"]
        assert len(functions) == 1
        assert "幸运抽奖" in functions[0].docstring

    def test_no_docstring_returns_empty_string(self, tmp_path):
        """Function without docstring should have empty docstring."""
        py_file = tmp_path / "views.py"
        py_file.write_text(
            dedent(
                '''
                def undocumented(request):
                    return True
                '''
            )
        )

        result = parse_file(py_file)

        functions = [s for s in result.symbols if s.kind == "function"]
        assert len(functions) == 1
        assert functions[0].docstring == ""

    def test_extract_description_from_class_method(self, tmp_path):
        """Should extract description from class-based view method."""
        py_file = tmp_path / "views.py"
        py_file.write_text(
            dedent(
                '''
                class UserAPIView:
                    """User API endpoint."""

                    def list(self, request):
                        """List all users with pagination."""
                        pass

                    def create(self, request):
                        """Create new user account."""
                        pass

                    def update(self, request, user_id):
                        """Update existing user information."""
                        pass
                '''
            )
        )

        result = parse_file(py_file)

        methods = [s for s in result.symbols if s.kind == "method"]
        assert len(methods) == 3

        # Check each method has its description
        # Method names may include class prefix, so check if method name ends with the target
        list_method = [m for m in methods if m.name.endswith("list")][0]
        create_method = [m for m in methods if m.name.endswith("create")][0]
        update_method = [m for m in methods if m.name.endswith("update")][0]

        assert "List all users with pagination" in list_method.docstring
        assert "Create new user account" in create_method.docstring
        assert "Update existing user information" in update_method.docstring

    def test_extract_description_google_style_docstring(self, tmp_path):
        """Should extract summary from Google-style docstring."""
        py_file = tmp_path / "views.py"
        py_file.write_text(
            dedent(
                '''
                def process_payment(request):
                    """Process payment transaction.

                    Args:
                        request: Payment request data

                    Returns:
                        dict: Payment result

                    Raises:
                        PaymentError: If payment fails
                    """
                    pass
                '''
            )
        )

        result = parse_file(py_file)

        functions = [s for s in result.symbols if s.kind == "function"]
        assert len(functions) == 1
        # Should extract just the summary line
        assert "Process payment transaction" in functions[0].docstring

    def test_extract_description_numpy_style_docstring(self, tmp_path):
        """Should extract summary from NumPy-style docstring."""
        py_file = tmp_path / "analytics.py"
        py_file.write_text(
            dedent(
                '''
                def calculate_metrics(data):
                    """
                    Calculate statistical metrics from data.

                    Parameters
                    ----------
                    data : array_like
                        Input data array

                    Returns
                    -------
                    dict
                        Calculated metrics
                    """
                    pass
                '''
            )
        )

        result = parse_file(py_file)

        functions = [s for s in result.symbols if s.kind == "function"]
        assert len(functions) == 1
        # Should extract the summary
        assert "Calculate statistical metrics from data" in functions[0].docstring
