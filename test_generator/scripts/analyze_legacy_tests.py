#!/usr/bin/env python3
"""Analyze legacy test files to extract test scenarios.

This script parses legacy hand-written test files and extracts:
- Test classes and methods
- Code templates (from docstrings)
- Assertions
- Expected values

Output: JSON report for migration planning

Note: This is a CLI tool - print() statements are intentional for user output.
"""
# ruff: noqa: T201

import ast
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


class TestAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze test file structure."""

    def __init__(self):
        self.test_classes = {}
        self.current_class = None

    def visit_ClassDef(self, node):
        """Visit class definitions (test classes)."""
        if node.name.startswith("Test"):
            self.current_class = node.name
            self.test_classes[node.name] = {"docstring": ast.get_docstring(node) or "", "methods": []}
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        """Visit function definitions (test methods)."""
        if self.current_class and node.name.startswith("test_"):
            method_info = self._analyze_method(node)
            self.test_classes[self.current_class]["methods"].append(method_info)
        self.generic_visit(node)

    def _analyze_method(self, node: ast.FunctionDef) -> Dict[str, Any]:
        """Analyze a single test method."""
        source = ast.unparse(node)

        # Extract code template from triple-quoted string
        code_template = self._extract_code_template(source)

        # Extract assertions
        assertions = self._extract_assertions(node)

        return {
            "name": node.name,
            "docstring": ast.get_docstring(node) or "",
            "code_template": code_template,
            "assertions": assertions,
            "line_start": node.lineno,
            "line_end": node.end_lineno,
        }

    def _extract_code_template(self, source: str) -> str:
        """Extract code template from test method source."""
        # Match code = """...""" or code = '''...'''
        pattern = r'code\s*=\s*["\'\s]*("""|\'\'\')(.*?)\1'
        match = re.search(pattern, source, re.DOTALL)
        if match:
            return match.group(2).strip()
        return ""

    def _extract_assertions(self, node: ast.FunctionDef) -> List[str]:
        """Extract assertion statements from test method."""
        assertions = []
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                assertions.append(ast.unparse(child.test))
        return assertions


def analyze_test_file(filepath: Path) -> Dict[str, Any]:
    """Analyze a test file and return structured data."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse AST
    tree = ast.parse(content, filename=str(filepath))

    # Analyze
    analyzer = TestAnalyzer()
    analyzer.visit(tree)

    # Count statistics
    total_methods = sum(len(cls["methods"]) for cls in analyzer.test_classes.values())
    total_assertions = sum(
        len(method["assertions"]) for cls in analyzer.test_classes.values() for method in cls["methods"]
    )

    return {
        "file": str(filepath),
        "test_classes": analyzer.test_classes,
        "statistics": {
            "total_classes": len(analyzer.test_classes),
            "total_methods": total_methods,
            "total_assertions": total_assertions,
            "avg_assertions_per_method": total_assertions / total_methods if total_methods > 0 else 0,
        },
    }


def generate_markdown_report(analysis: Dict[str, Any], output_path: Path):
    """Generate markdown analysis report."""
    lines = [
        "# Python Inheritance Test Analysis",
        "",
        f"**File**: `{analysis['file']}`",
        "**Analysis Date**: 2026-02-11",
        "",
        "---",
        "",
        "## 📊 Statistics",
        "",
        f"- **Test Classes**: {analysis['statistics']['total_classes']}",
        f"- **Test Methods**: {analysis['statistics']['total_methods']}",
        f"- **Total Assertions**: {analysis['statistics']['total_assertions']}",
        f"- **Avg Assertions/Method**: {analysis['statistics']['avg_assertions_per_method']:.1f}",
        "",
        "---",
        "",
        "## 📋 Test Classes and Methods",
        "",
    ]

    for class_name, class_data in analysis["test_classes"].items():
        lines.append(f"### {class_name}")
        lines.append("")
        if class_data["docstring"]:
            lines.append(f"**Description**: {class_data['docstring']}")
            lines.append("")

        lines.append(f"**Methods**: {len(class_data['methods'])}")
        lines.append("")

        for method in class_data["methods"]:
            lines.append(f"#### `{method['name']}`")
            lines.append("")
            if method["docstring"]:
                lines.append(f"- **Description**: {method['docstring']}")
            lines.append(f"- **Lines**: {method['line_start']}-{method['line_end']}")
            lines.append(f"- **Assertions**: {len(method['assertions'])}")

            if method["code_template"]:
                lines.append("")
                lines.append("**Code Template**:")
                lines.append("```python")
                lines.append(method["code_template"])
                lines.append("```")

            if method["assertions"]:
                lines.append("")
                lines.append("**Assertions**:")
                for assertion in method["assertions"]:
                    lines.append(f"- `{assertion}`")

            lines.append("")

        lines.append("---")
        lines.append("")

    # Write report
    output_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_legacy_tests.py <test_file_path> [--output-json|--output-md]")
        print("")
        print("Examples:")
        print("  python analyze_legacy_tests.py tests/test_python_inheritance.py")
        print("  python analyze_legacy_tests.py tests/test_python_inheritance.py --output-json")
        print("  python analyze_legacy_tests.py tests/test_python_inheritance.py --output-md report.md")
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    # Analyze
    analysis = analyze_test_file(filepath)

    # Output format
    if "--output-json" in sys.argv:
        print(json.dumps(analysis, indent=2))
    elif "--output-md" in sys.argv:
        md_index = sys.argv.index("--output-md")
        if md_index + 1 < len(sys.argv):
            output_path = Path(sys.argv[md_index + 1])
            generate_markdown_report(analysis, output_path)
            print(f"✅ Markdown report generated: {output_path}")
        else:
            print("Error: --output-md requires output file path")
            sys.exit(1)
    else:
        # Default: print summary
        stats = analysis["statistics"]
        print(f"📊 Analysis Summary: {filepath.name}")
        print("")
        print(f"  Test Classes: {stats['total_classes']}")
        print(f"  Test Methods: {stats['total_methods']}")
        print(f"  Assertions: {stats['total_assertions']}")
        print(f"  Avg Assertions/Method: {stats['avg_assertions_per_method']:.1f}")
        print("")
        print("Class Breakdown:")
        for class_name, class_data in analysis["test_classes"].items():
            print(f"  - {class_name}: {len(class_data['methods'])} methods")


if __name__ == "__main__":
    main()
