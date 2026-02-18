"""Tests for TypeScript/JavaScript parser.

Covers Story 20.1 (foundation), 20.2 (symbols), 20.3 (imports), 20.5 (calls), 20.6 (TS-specific).
"""

from codeindex.parser import FILE_EXTENSIONS, parse_file

# ==================== Story 20.1: Foundation ====================


class TestParserFoundation:
    """Test TypeScriptParser loads correct grammar per file extension."""

    def test_ts_extension_in_file_extensions(self):
        """FILE_EXTENSIONS maps .ts to typescript."""
        assert FILE_EXTENSIONS[".ts"] == "typescript"

    def test_tsx_extension_in_file_extensions(self):
        """FILE_EXTENSIONS maps .tsx to tsx."""
        assert FILE_EXTENSIONS[".tsx"] == "tsx"

    def test_js_extension_in_file_extensions(self):
        """FILE_EXTENSIONS maps .js to javascript."""
        assert FILE_EXTENSIONS[".js"] == "javascript"

    def test_jsx_extension_in_file_extensions(self):
        """FILE_EXTENSIONS maps .jsx to javascript."""
        assert FILE_EXTENSIONS[".jsx"] == "javascript"

    def test_parse_empty_ts_file(self, tmp_path):
        """Empty .ts file returns valid ParseResult."""
        test_file = tmp_path / "empty.ts"
        test_file.write_text("")
        result = parse_file(test_file)
        assert result.error is None
        assert result.symbols == []
        assert result.imports == []

    def test_parse_empty_js_file(self, tmp_path):
        """Empty .js file returns valid ParseResult."""
        test_file = tmp_path / "empty.js"
        test_file.write_text("")
        result = parse_file(test_file)
        assert result.error is None

    def test_parse_empty_tsx_file(self, tmp_path):
        """Empty .tsx file returns valid ParseResult."""
        test_file = tmp_path / "empty.tsx"
        test_file.write_text("")
        result = parse_file(test_file)
        assert result.error is None

    def test_parse_empty_jsx_file(self, tmp_path):
        """Empty .jsx file returns valid ParseResult."""
        test_file = tmp_path / "empty.jsx"
        test_file.write_text("")
        result = parse_file(test_file)
        assert result.error is None

    def test_parse_minimal_ts(self, tmp_path):
        """Minimal TS file parses without error."""
        test_file = tmp_path / "minimal.ts"
        test_file.write_text("const x: number = 1;\n")
        result = parse_file(test_file)
        assert result.error is None

    def test_parse_minimal_js(self, tmp_path):
        """Minimal JS file parses without error."""
        test_file = tmp_path / "minimal.js"
        test_file.write_text("const x = 1;\n")
        result = parse_file(test_file)
        assert result.error is None

    def test_file_lines_counted(self, tmp_path):
        """File lines are correctly counted."""
        test_file = tmp_path / "lines.ts"
        test_file.write_text("const a = 1;\nconst b = 2;\nconst c = 3;\n")
        result = parse_file(test_file)
        assert result.file_lines == 3

    def test_parser_routing_ts(self, tmp_path):
        """Parser routes .ts to TypeScriptParser."""
        test_file = tmp_path / "test.ts"
        test_file.write_text("function greet(): string { return 'hello'; }\n")
        result = parse_file(test_file)
        assert result.error is None
        assert len(result.symbols) >= 1

    def test_parser_routing_jsx(self, tmp_path):
        """Parser routes .jsx to TypeScriptParser with JS grammar."""
        test_file = tmp_path / "test.jsx"
        test_file.write_text("function App() { return null; }\n")
        result = parse_file(test_file)
        assert result.error is None
        assert len(result.symbols) >= 1


# ==================== Story 20.2: Symbol Extraction ====================


class TestFunctionExtraction:
    """Test function declaration extraction."""

    def test_named_function(self, tmp_path):
        """Named function declaration."""
        code = "function greet(name: string): string {\n  return `Hello, ${name}`;\n}\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.symbols) == 1
        assert result.symbols[0].name == "greet"
        assert result.symbols[0].kind == "function"
        assert "greet" in result.symbols[0].signature

    def test_arrow_function_const(self, tmp_path):
        """Arrow function assigned to const."""
        code = "const add = (a: number, b: number): number => a + b;\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        funcs = [s for s in result.symbols if s.name == "add"]
        assert len(funcs) == 1
        assert funcs[0].kind == "function"

    def test_async_function(self, tmp_path):
        """Async function declaration."""
        code = "async function fetchData(url: string): Promise<any> {\n  return fetch(url);\n}\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.symbols) == 1
        assert result.symbols[0].name == "fetchData"
        assert "async" in result.symbols[0].signature

    def test_exported_function(self, tmp_path):
        """Exported function declaration."""
        code = "export function helper(): void {}\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        funcs = [s for s in result.symbols if s.name == "helper"]
        assert len(funcs) == 1

    def test_generator_function(self, tmp_path):
        """Generator function declaration."""
        code = (
            "function* range(start: number, end: number): Generator<number>"
            " {\n  for (let i = start; i < end; i++) yield i;\n}\n"
        )
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        funcs = [s for s in result.symbols if s.name == "range"]
        assert len(funcs) == 1

    def test_js_function(self, tmp_path):
        """Plain JS function declaration."""
        code = "function greet(name) {\n  return 'Hello, ' + name;\n}\n"
        test_file = tmp_path / "test.js"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.symbols) == 1
        assert result.symbols[0].name == "greet"
        assert result.symbols[0].kind == "function"


class TestClassExtraction:
    """Test class declaration extraction."""

    def test_simple_class(self, tmp_path):
        """Simple class with methods."""
        code = """class Calculator {
  add(a: number, b: number): number {
    return a + b;
  }

  subtract(a: number, b: number): number {
    return a - b;
  }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        class_syms = [s for s in result.symbols if s.kind == "class"]
        assert len(class_syms) == 1
        assert class_syms[0].name == "Calculator"

        methods = [s for s in result.symbols if s.kind == "method"]
        method_names = [m.name for m in methods]
        assert "Calculator.add" in method_names
        assert "Calculator.subtract" in method_names

    def test_class_with_constructor(self, tmp_path):
        """Class with constructor."""
        code = """class UserService {
  private db: Database;

  constructor(db: Database) {
    this.db = db;
  }

  getUser(id: string): User {
    return this.db.find(id);
  }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        constructors = [s for s in result.symbols if "constructor" in s.name.lower()]
        assert len(constructors) == 1

    def test_class_with_static_method(self, tmp_path):
        """Class with static method."""
        code = """class MathUtils {
  static square(x: number): number {
    return x * x;
  }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        methods = [s for s in result.symbols if s.kind == "method"]
        assert any("square" in m.name for m in methods)
        assert any("static" in m.signature for m in methods)

    def test_class_with_getter_setter(self, tmp_path):
        """Class with getter and setter."""
        code = """class Person {
  private _name: string = '';

  get name(): string {
    return this._name;
  }

  set name(value: string) {
    this._name = value;
  }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        methods = [s for s in result.symbols if s.kind == "method"]
        method_names = [m.name for m in methods]
        assert any("name" in n for n in method_names)

    def test_generic_class(self, tmp_path):
        """Generic class declaration."""
        code = """class Container<T> {
  private value: T;

  constructor(value: T) {
    this.value = value;
  }

  get(): T {
    return this.value;
  }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        class_syms = [s for s in result.symbols if s.kind == "class"]
        assert len(class_syms) == 1
        assert class_syms[0].name == "Container"

    def test_abstract_class(self, tmp_path):
        """Abstract class declaration."""
        code = """abstract class Shape {
  abstract area(): number;

  describe(): string {
    return `Area: ${this.area()}`;
  }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        class_syms = [s for s in result.symbols if s.kind == "class"]
        assert len(class_syms) == 1
        assert "abstract" in class_syms[0].signature

    def test_export_default_class(self, tmp_path):
        """Export default class."""
        code = """export default class App {
  run(): void {}
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        class_syms = [s for s in result.symbols if s.kind == "class"]
        assert len(class_syms) == 1
        assert class_syms[0].name == "App"


class TestInterfaceExtraction:
    """Test interface declaration extraction (TypeScript only)."""

    def test_simple_interface(self, tmp_path):
        """Simple interface declaration."""
        code = """interface User {
  name: string;
  age: number;
  greet(): string;
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        ifaces = [s for s in result.symbols if s.kind == "interface"]
        assert len(ifaces) == 1
        assert ifaces[0].name == "User"

    def test_interface_with_generics(self, tmp_path):
        """Interface with generic type parameters."""
        code = """interface Repository<T> {
  find(id: string): T;
  findAll(): T[];
  save(entity: T): void;
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        ifaces = [s for s in result.symbols if s.kind == "interface"]
        assert len(ifaces) == 1
        assert ifaces[0].name == "Repository"

    def test_exported_interface(self, tmp_path):
        """Exported interface."""
        code = """export interface Config {
  host: string;
  port: number;
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        ifaces = [s for s in result.symbols if s.kind == "interface"]
        assert len(ifaces) == 1


class TestEnumExtraction:
    """Test enum declaration extraction (TypeScript only)."""

    def test_string_enum(self, tmp_path):
        """String enum declaration."""
        code = """enum Direction {
  Up = 'UP',
  Down = 'DOWN',
  Left = 'LEFT',
  Right = 'RIGHT',
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        enums = [s for s in result.symbols if s.kind == "enum"]
        assert len(enums) == 1
        assert enums[0].name == "Direction"

    def test_numeric_enum(self, tmp_path):
        """Numeric enum declaration."""
        code = """enum StatusCode {
  OK = 200,
  NotFound = 404,
  ServerError = 500,
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        enums = [s for s in result.symbols if s.kind == "enum"]
        assert len(enums) == 1
        assert enums[0].name == "StatusCode"

    def test_const_enum(self, tmp_path):
        """Const enum declaration."""
        code = """const enum Color {
  Red,
  Green,
  Blue,
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        enums = [s for s in result.symbols if s.kind == "enum"]
        assert len(enums) == 1
        assert enums[0].name == "Color"


class TestTypeAliasExtraction:
    """Test type alias extraction (TypeScript only)."""

    def test_simple_type_alias(self, tmp_path):
        """Simple type alias."""
        code = "type ID = string;\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        types = [s for s in result.symbols if s.kind == "type_alias"]
        assert len(types) == 1
        assert types[0].name == "ID"

    def test_union_type_alias(self, tmp_path):
        """Union type alias."""
        code = "type Status = 'active' | 'inactive' | 'pending';\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        types = [s for s in result.symbols if s.kind == "type_alias"]
        assert len(types) == 1
        assert types[0].name == "Status"

    def test_generic_type_alias(self, tmp_path):
        """Generic type alias."""
        code = "type Nullable<T> = T | null;\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        types = [s for s in result.symbols if s.kind == "type_alias"]
        assert len(types) == 1
        assert types[0].name == "Nullable"


class TestVariableExtraction:
    """Test top-level const/let/var extraction."""

    def test_const_declaration(self, tmp_path):
        """Top-level const declaration."""
        code = "const MAX_RETRIES = 3;\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        # Const without arrow function should be variable
        vars_ = [s for s in result.symbols if s.name == "MAX_RETRIES"]
        assert len(vars_) == 1
        assert vars_[0].kind == "variable"

    def test_const_object(self, tmp_path):
        """Top-level const object."""
        code = """const CONFIG = {
  host: 'localhost',
  port: 3000,
};
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        vars_ = [s for s in result.symbols if s.name == "CONFIG"]
        assert len(vars_) == 1


# ==================== Story 20.3: Import/Export Extraction ====================


class TestImportExtraction:
    """Test import statement extraction."""

    def test_named_import(self, tmp_path):
        """Named imports from module."""
        code = "import { useState, useEffect } from 'react';\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.imports) >= 1
        react_imports = [i for i in result.imports if i.module == "react"]
        assert len(react_imports) >= 1
        all_names = []
        for imp in react_imports:
            all_names.extend(imp.names)
        assert "useState" in all_names
        assert "useEffect" in all_names

    def test_default_import(self, tmp_path):
        """Default import from module."""
        code = "import React from 'react';\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        react_imports = [i for i in result.imports if i.module == "react"]
        assert len(react_imports) >= 1

    def test_namespace_import(self, tmp_path):
        """Namespace import."""
        code = "import * as utils from './utils';\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        utils_imports = [i for i in result.imports if i.module == "./utils"]
        assert len(utils_imports) >= 1

    def test_side_effect_import(self, tmp_path):
        """Side-effect import."""
        code = "import './styles.css';\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        css_imports = [i for i in result.imports if i.module == "./styles.css"]
        assert len(css_imports) >= 1

    def test_type_only_import(self, tmp_path):
        """Type-only import (TypeScript)."""
        code = "import type { FC } from 'react';\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        react_imports = [i for i in result.imports if i.module == "react"]
        assert len(react_imports) >= 1

    def test_commonjs_require(self, tmp_path):
        """CommonJS require pattern."""
        code = "const fs = require('fs');\n"
        test_file = tmp_path / "test.js"
        test_file.write_text(code)
        result = parse_file(test_file)
        fs_imports = [i for i in result.imports if i.module == "fs"]
        assert len(fs_imports) >= 1

    def test_mixed_imports(self, tmp_path):
        """Mixed import styles in one file."""
        code = """import React from 'react';
import { useState } from 'react';
import * as path from 'path';
import './global.css';
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.imports) >= 4

    def test_reexport(self, tmp_path):
        """Re-export from module."""
        code = "export { default as Button } from './Button';\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        button_imports = [i for i in result.imports if i.module == "./Button"]
        assert len(button_imports) >= 1

    def test_barrel_export(self, tmp_path):
        """Barrel export (export * from)."""
        code = "export * from './helpers';\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        helper_imports = [i for i in result.imports if i.module == "./helpers"]
        assert len(helper_imports) >= 1


# ==================== Story 20.4: Inheritance Extraction ====================


class TestInheritanceExtraction:
    """Test class inheritance extraction."""

    def test_class_extends(self, tmp_path):
        """Class extending another class."""
        code = """class Animal {}
class Dog extends Animal {}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "Dog"
        assert result.inheritances[0].parent == "Animal"

    def test_class_implements(self, tmp_path):
        """Class implementing interfaces."""
        code = """interface Serializable {}
interface Comparable {}
class User implements Serializable, Comparable {}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        user_inh = [i for i in result.inheritances if i.child == "User"]
        assert len(user_inh) == 2
        parents = {i.parent for i in user_inh}
        assert "Serializable" in parents
        assert "Comparable" in parents

    def test_class_extends_and_implements(self, tmp_path):
        """Class with both extends and implements."""
        code = """class BaseService {}
interface Loggable {}
class UserService extends BaseService implements Loggable {}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        userservice_inh = [i for i in result.inheritances if i.child == "UserService"]
        assert len(userservice_inh) == 2
        parents = {i.parent for i in userservice_inh}
        assert "BaseService" in parents
        assert "Loggable" in parents

    def test_interface_extends(self, tmp_path):
        """Interface extending another interface."""
        code = """interface Readable {}
interface Writable extends Readable {}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.inheritances) == 1
        assert result.inheritances[0].child == "Writable"
        assert result.inheritances[0].parent == "Readable"

    def test_interface_extends_multiple(self, tmp_path):
        """Interface extending multiple interfaces."""
        code = """interface A {}
interface B {}
interface C extends A, B {}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        c_inh = [i for i in result.inheritances if i.child == "C"]
        assert len(c_inh) == 2

    def test_no_inheritance(self, tmp_path):
        """Class with no inheritance."""
        code = "class Standalone { method(): void {} }\n"
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.inheritances) == 0

    def test_generic_extends(self, tmp_path):
        """Generic class with extends."""
        code = """class BaseRepo<T> {}
class UserRepo extends BaseRepo<User> {}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.inheritances) >= 1
        assert result.inheritances[0].child == "UserRepo"


# ==================== Story 20.5: Call Extraction ====================


class TestCallExtraction:
    """Test function/method call extraction."""

    def test_function_call(self, tmp_path):
        """Direct function call."""
        code = """function greet(): string { return 'hello'; }
function main() { greet(); }
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.calls) >= 1
        callees = [c.callee for c in result.calls]
        assert any("greet" in c for c in callees if c)

    def test_method_call(self, tmp_path):
        """Method call on this."""
        code = """class Foo {
  bar(): void {}
  baz(): void {
    this.bar();
  }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.calls) >= 1

    def test_constructor_call(self, tmp_path):
        """Constructor call with new."""
        code = """class Foo {}
function create() { return new Foo(); }
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.calls) >= 1
        constructor_calls = [c for c in result.calls if c.call_type.value == "constructor"]
        assert len(constructor_calls) >= 1

    def test_static_method_call(self, tmp_path):
        """Static method call."""
        code = """class MathUtils {
  static square(x: number): number { return x * x; }
}
function main() { MathUtils.square(5); }
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.calls) >= 1

    def test_chained_call(self, tmp_path):
        """Chained method calls."""
        code = """function process(arr: number[]) {
  return arr.filter(x => x > 0).map(x => x * 2);
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert len(result.calls) >= 2


# ==================== Story 20.6: TS-Specific Features ====================


class TestTSSpecificFeatures:
    """Test TypeScript/JavaScript specific features."""

    def test_decorator_on_class(self, tmp_path):
        """Decorator on class (TS experimental decorators)."""
        code = """function sealed(constructor: Function) {}

@sealed
class BugReport {
  title: string;
  constructor(t: string) { this.title = t; }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        classes = [s for s in result.symbols if s.kind == "class"]
        assert len(classes) == 1
        assert classes[0].name == "BugReport"

    def test_react_function_component_tsx(self, tmp_path):
        """React function component in TSX."""
        code = """interface Props {
  name: string;
}

function Greeting(props: Props) {
  return <div>Hello, {props.name}</div>;
}
"""
        test_file = tmp_path / "test.tsx"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert result.error is None
        funcs = [s for s in result.symbols if s.name == "Greeting"]
        assert len(funcs) == 1

    def test_react_arrow_component_tsx(self, tmp_path):
        """React arrow function component in TSX."""
        code = """const Button = (props: { label: string }) => {
  return <button>{props.label}</button>;
};
"""
        test_file = tmp_path / "test.tsx"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert result.error is None
        funcs = [s for s in result.symbols if s.name == "Button"]
        assert len(funcs) == 1

    def test_namespace_declaration(self, tmp_path):
        """Namespace declaration (TS)."""
        code = """namespace Validation {
  export function isValid(s: string): boolean {
    return s.length > 0;
  }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        # Should find the namespace or its contents
        symbols = [s for s in result.symbols if "Validation" in s.name]
        assert len(symbols) >= 1

    def test_ambient_declaration_dts(self, tmp_path):
        """Ambient declaration in .d.ts file (parsed as .ts)."""
        code = """declare module 'my-module' {
  export function doSomething(): void;
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert result.error is None

    def test_jsx_parses_without_error(self, tmp_path):
        """JSX code parses without error."""
        code = """function App() {
  return (
    <div className="app">
      <h1>Hello World</h1>
    </div>
  );
}
"""
        test_file = tmp_path / "test.jsx"
        test_file.write_text(code)
        result = parse_file(test_file)
        assert result.error is None
        funcs = [s for s in result.symbols if s.name == "App"]
        assert len(funcs) == 1

    def test_async_generator(self, tmp_path):
        """Async generator function."""
        code = """async function* generateSequence(start: number, end: number) {
  for (let i = start; i <= end; i++) {
    yield i;
  }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        funcs = [s for s in result.symbols if s.name == "generateSequence"]
        assert len(funcs) == 1


# ==================== Integration Tests ====================


class TestIntegration:
    """End-to-end integration tests."""

    def test_complex_ts_file(self, tmp_path):
        """Complex TypeScript file with multiple features."""
        code = """import { EventEmitter } from 'events';

interface Logger {
  log(message: string): void;
}

enum LogLevel {
  Info = 'info',
  Warn = 'warn',
  Error = 'error',
}

type LogEntry = {
  level: LogLevel;
  message: string;
};

class ConsoleLogger extends EventEmitter implements Logger {
  private level: LogLevel = LogLevel.Info;

  constructor() {
    super();
  }

  log(message: string): void {
    const entry: LogEntry = { level: this.level, message };
    console.log(entry);
    this.emit('log', entry);
  }

  static create(): ConsoleLogger {
    return new ConsoleLogger();
  }
}

export default ConsoleLogger;
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)

        assert result.error is None

        # Check imports
        assert len(result.imports) >= 1

        # Check symbols
        kind_names = {s.kind for s in result.symbols}
        assert "interface" in kind_names
        assert "enum" in kind_names
        assert "class" in kind_names

        # Check inheritance
        logger_inh = [i for i in result.inheritances if i.child == "ConsoleLogger"]
        assert len(logger_inh) >= 1

        # Check calls
        assert len(result.calls) >= 1

    def test_js_file_integration(self, tmp_path):
        """Full JS file integration test."""
        code = """const express = require('express');

class Router {
  constructor() {
    this.routes = [];
  }

  get(path, handler) {
    this.routes.push({ path, handler, method: 'GET' });
  }

  post(path, handler) {
    this.routes.push({ path, handler, method: 'POST' });
  }
}

function createApp() {
  const app = express();
  const router = new Router();
  router.get('/', (req, res) => res.send('Hello'));
  return app;
}

module.exports = { Router, createApp };
"""
        test_file = tmp_path / "test.js"
        test_file.write_text(code)
        result = parse_file(test_file)

        assert result.error is None
        assert len(result.symbols) >= 4  # Router class + methods + createApp
        assert len(result.imports) >= 1  # require('express')

    def test_to_dict_includes_all_fields(self, tmp_path):
        """ParseResult.to_dict() includes all fields for JSON output."""
        code = """import { Foo } from './foo';
class Bar extends Foo {
  method(): void { this.run(); }
}
"""
        test_file = tmp_path / "test.ts"
        test_file.write_text(code)
        result = parse_file(test_file)
        d = result.to_dict()
        assert "symbols" in d
        assert "imports" in d
        assert "inheritances" in d
        assert "calls" in d
        assert "file_lines" in d
