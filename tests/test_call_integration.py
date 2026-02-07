"""
Story 11.4: Integration & JSON Output Tests

Tests for call relationship extraction integration with ParseResult,
JSON serialization, and CLI integration.
"""

import json
from pathlib import Path
import pytest
from codeindex.parser import parse_file, Call, CallType


class TestJSONSerialization:
    """AC1: JSON Output Format (3 tests)"""

    def test_basic_json_structure(self, tmp_path):
        """Test basic JSON serialization of calls."""
        code = """
def helper():
    pass

def main():
    helper()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Convert to dict
        result_dict = result.to_dict()

        # Verify structure
        assert "calls" in result_dict
        assert isinstance(result_dict["calls"], list)
        assert len(result_dict["calls"]) >= 1

        # Verify call structure
        call_dict = result_dict["calls"][0]
        assert "caller" in call_dict
        assert "callee" in call_dict
        assert "line_number" in call_dict
        assert "call_type" in call_dict
        assert "arguments_count" in call_dict

    def test_multiple_calls_json(self, tmp_path):
        """Test JSON with multiple calls."""
        code = """
def helper():
    pass

def process():
    helper()
    helper()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        result_dict = result.to_dict()

        # Should have multiple calls
        assert len(result_dict["calls"]) >= 2

        # All should have required fields
        for call_dict in result_dict["calls"]:
            assert "caller" in call_dict
            assert "callee" in call_dict
            assert "line_number" in call_dict
            assert "call_type" in call_dict

    def test_dynamic_call_json(self, tmp_path):
        """Test JSON serialization handles None callee correctly."""
        # For now, we test that JSON serialization handles None values
        # Dynamic calls (if implemented) should have callee=None
        call_dict = {
            "caller": "dynamic_caller",
            "callee": None,
            "line_number": 10,
            "call_type": "dynamic",
            "arguments_count": None
        }

        # Test that Call.from_dict handles None correctly
        call = Call.from_dict(call_dict)
        assert call.callee is None
        assert call.call_type == CallType.DYNAMIC

        # Test that to_dict preserves None
        serialized = call.to_dict()
        assert serialized["callee"] is None
        assert serialized["call_type"] == "dynamic"


class TestParseResultIntegration:
    """AC2: ParseResult Integration (3 tests)"""

    def test_calls_field_exists(self, tmp_path):
        """Test that ParseResult has calls field."""
        code = """
def test():
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Verify calls field exists
        assert hasattr(result, "calls")
        assert isinstance(result.calls, list)

    def test_empty_calls_for_no_calls(self, tmp_path):
        """Test that files with no calls have empty calls list."""
        code = """
def helper():
    x = 1 + 2
    return x
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # No function calls in this code
        assert result.calls == []

    def test_calls_populated_correctly(self, tmp_path):
        """Test that calls are populated correctly."""
        code = """
def helper():
    pass

def main():
    helper()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Should have at least one call
        assert len(result.calls) >= 1

        # Verify Call objects
        for call in result.calls:
            assert isinstance(call, Call)
            assert isinstance(call.caller, str)
            assert call.callee is None or isinstance(call.callee, str)
            assert isinstance(call.line_number, int)
            assert isinstance(call.call_type, CallType)


class TestBackwardCompatibility:
    """AC3: Backward Compatibility (2 tests)"""

    def test_existing_fields_unchanged(self, tmp_path):
        """Test that existing ParseResult fields still work."""
        code = """
class User:
    def save(self):
        pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)

        # Existing fields should still be present
        assert hasattr(result, "path")
        assert hasattr(result, "symbols")
        assert hasattr(result, "imports")
        assert hasattr(result, "inheritances")
        assert hasattr(result, "module_docstring")
        assert hasattr(result, "namespace")
        assert hasattr(result, "error")

        # They should still work correctly
        assert result.path == py_file
        assert len(result.symbols) >= 1  # User class

    def test_to_dict_includes_all_fields(self, tmp_path):
        """Test that to_dict includes both old and new fields."""
        code = """
def test():
    pass
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        result = parse_file(py_file)
        result_dict = result.to_dict()

        # Old fields
        assert "path" in result_dict
        assert "symbols" in result_dict
        assert "imports" in result_dict
        assert "inheritances" in result_dict
        assert "module_docstring" in result_dict
        assert "namespace" in result_dict

        # New field (Epic 11)
        assert "calls" in result_dict


class TestJSONRoundTrip:
    """AC4: JSON Round-Trip (2 tests)"""

    def test_call_from_dict(self):
        """Test Call.from_dict deserialization."""
        call_dict = {
            "caller": "main",
            "callee": "helper",
            "line_number": 10,
            "call_type": "function",
            "arguments_count": 2
        }

        call = Call.from_dict(call_dict)

        assert call.caller == "main"
        assert call.callee == "helper"
        assert call.line_number == 10
        assert call.call_type == CallType.FUNCTION
        assert call.arguments_count == 2

    def test_json_serialization_round_trip(self, tmp_path):
        """Test full JSON serialization and deserialization."""
        code = """
def helper():
    pass

def main():
    helper()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(code)

        # Parse
        result = parse_file(py_file)

        # Serialize to JSON
        result_dict = result.to_dict()
        json_str = json.dumps(result_dict, indent=2)

        # Deserialize
        loaded_dict = json.loads(json_str)

        # Verify structure preserved
        assert "calls" in loaded_dict
        assert isinstance(loaded_dict["calls"], list)

        # Verify calls can be reconstructed
        for call_dict in loaded_dict["calls"]:
            call = Call.from_dict(call_dict)
            assert isinstance(call, Call)
            assert isinstance(call.call_type, CallType)


class TestLanguageConsistency:
    """AC5: Cross-Language Consistency (2 tests)"""

    def test_python_and_java_same_structure(self, tmp_path):
        """Test that Python and Java produce same JSON structure."""
        # Python
        py_code = """
def helper():
    pass

def main():
    helper()
"""
        py_file = tmp_path / "test.py"
        py_file.write_text(py_code)
        py_result = parse_file(py_file)
        py_dict = py_result.to_dict()

        # Java
        java_code = """
package com.example;

public class Test {
    public static void helper() {}

    public static void main() {
        helper();
    }
}
"""
        java_file = tmp_path / "test.java"
        java_file.write_text(java_code)
        java_result = parse_file(java_file)
        java_dict = java_result.to_dict()

        # Both should have calls field
        assert "calls" in py_dict
        assert "calls" in java_dict

        # Both should have same structure for calls
        if py_dict["calls"]:
            py_call = py_dict["calls"][0]
            assert "caller" in py_call
            assert "callee" in py_call
            assert "line_number" in py_call
            assert "call_type" in py_call

        if java_dict["calls"]:
            java_call = java_dict["calls"][0]
            assert "caller" in java_call
            assert "callee" in java_call
            assert "line_number" in java_call
            assert "call_type" in java_call

    def test_call_type_values_consistent(self):
        """Test that CallType enum values are consistent."""
        # Verify enum values are strings
        assert CallType.FUNCTION.value == "function"
        assert CallType.METHOD.value == "method"
        assert CallType.STATIC_METHOD.value == "static_method"
        assert CallType.CONSTRUCTOR.value == "constructor"
        assert CallType.DYNAMIC.value == "dynamic"
