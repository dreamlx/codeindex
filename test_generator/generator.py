#!/usr/bin/env python3
"""Generate test files from YAML specs and Jinja2 templates.

Usage:
    python test_generator/generator.py \
        --spec test_generator/specs/python.yaml \
        --template test_generator/templates/inheritance_test.py.j2 \
        --output tests/test_python_inheritance.py

    python test_generator/generator.py --spec specs/python.yaml --dry-run

Note: This is a CLI tool - print() statements are intentional for user output.
"""
# ruff: noqa: T201

import sys
from pathlib import Path

import jinja2
import yaml


def load_spec(spec_path: str) -> dict:
    """Load and validate a YAML test specification."""
    path = Path(spec_path)
    if not path.exists():
        print(f"ERROR: Spec file not found: {spec_path}")
        sys.exit(1)

    spec = yaml.safe_load(path.read_text())

    # Validate required keys
    required = ["language", "code_templates", "test_scenarios"]
    for key in required:
        if key not in spec:
            print(f"ERROR: Missing required key '{key}' in {spec_path}")
            sys.exit(1)

    # Validate template references
    templates = spec["code_templates"]
    for scenario in spec["test_scenarios"]:
        for test in scenario["tests"]:
            if test["template"] not in templates:
                print(
                    f"ERROR: Template '{test['template']}' referenced by "
                    f"{scenario['class_name']}::{test['method']} not found"
                )
                sys.exit(1)

    return spec


def load_template(template_path: str) -> jinja2.Template:
    """Load a Jinja2 template."""
    path = Path(template_path)
    if not path.exists():
        print(f"ERROR: Template file not found: {template_path}")
        sys.exit(1)

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(path.parent)),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Custom filter: render code as triple-quoted string
    # Code content starts at column 0 (same as legacy test format)
    def to_code_string(code):
        """Render code as a triple-quoted Python string."""
        if not code or not code.strip():
            return '""'
        return '"""\n' + code + '"""'

    def py_escape(s):
        """Escape backslashes for embedding in Python string literals."""
        return s.replace("\\", "\\\\")

    def to_var_name(s):
        """Convert a string to a valid Python variable name."""
        import re

        return re.sub(r"[^a-zA-Z0-9_]", "_", s).lower()

    env.filters["to_code_string"] = to_code_string
    env.filters["py_escape"] = py_escape
    env.filters["to_var_name"] = to_var_name

    return env.get_template(path.name)


def generate(spec: dict, template: jinja2.Template) -> str:
    """Generate test file content from spec and template."""
    return template.render(**spec)


def main():
    args = sys.argv[1:]

    spec_path = None
    template_path = None
    output_path = None
    dry_run = False

    i = 0
    while i < len(args):
        if args[i] == "--spec" and i + 1 < len(args):
            spec_path = args[i + 1]
            i += 2
        elif args[i] == "--template" and i + 1 < len(args):
            template_path = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i] == "--dry-run":
            dry_run = True
            i += 1
        elif args[i] == "--help":
            print(__doc__)
            sys.exit(0)
        else:
            print(f"Unknown argument: {args[i]}")
            sys.exit(1)

    if not spec_path or not template_path:
        print("Usage: generator.py --spec <yaml> --template <j2> [--output <py>] [--dry-run]")
        sys.exit(1)

    # Load
    print(f"Loading spec: {spec_path}")
    spec = load_spec(spec_path)

    print(f"Loading template: {template_path}")
    template = load_template(template_path)

    # Generate
    print("Generating test file...")
    content = generate(spec, template)

    # Stats
    lines = content.count("\n") + 1
    classes = sum(1 for s in spec["test_scenarios"])
    methods = sum(len(s["tests"]) for s in spec["test_scenarios"])
    print(f"  Lines: {lines}")
    print(f"  Classes: {classes}")
    print(f"  Methods: {methods}")

    if dry_run:
        print("\n--- DRY RUN (not writing) ---")
        print(content)
        return

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content)
        print(f"\nWritten to: {output_path}")
    else:
        print(content)


if __name__ == "__main__":
    main()
