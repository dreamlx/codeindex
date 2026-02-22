"""Tests for TypeScript cross-file import callee resolution.

Tests _build_import_map and _resolve_callee in TypeScriptParser,
verifying that callees are resolved using import information.
"""

from pathlib import Path

import pytest

from codeindex.parser import Call, CallType, Import, parse_file


# ---------------------------------------------------------------------------
# Helper: parse TS source and return calls
# ---------------------------------------------------------------------------

def _parse_ts_calls(tmp_path: Path, code: str) -> list[Call]:
    ts_file = tmp_path / "test.ts"
    ts_file.write_text(code, encoding="utf-8")
    result = parse_file(ts_file)
    assert not result.error, f"Parse error: {result.error}"
    return result.calls


# ---------------------------------------------------------------------------
# _build_import_map unit tests
# ---------------------------------------------------------------------------

class TestBuildImportMap:
    """Test _build_import_map produces correct mappings."""

    def _get_parser(self):
        from codeindex.parsers.typescript_parser import TypeScriptParser
        return TypeScriptParser.create_for_file(Path("test.ts"))

    def test_named_import(self):
        parser = self._get_parser()
        imports = [Import(module="./tool-executor", names=["executeToolCall"], is_from=True)]
        m = parser._build_import_map(imports)
        assert m == {"executeToolCall": "./tool-executor.executeToolCall"}

    def test_default_import(self):
        parser = self._get_parser()
        imports = [Import(module="./llm-client", names=["LLMClient"], is_from=True, alias="LLMClient")]
        m = parser._build_import_map(imports)
        assert m == {"LLMClient": "./llm-client"}

    def test_namespace_import(self):
        parser = self._get_parser()
        imports = [Import(module="./utils", names=["*"], is_from=True, alias="utils")]
        m = parser._build_import_map(imports)
        assert m == {"utils": "./utils"}

    def test_commonjs_require(self):
        parser = self._get_parser()
        imports = [Import(module="./helper", names=["doWork"], is_from=False, alias="doWork")]
        m = parser._build_import_map(imports)
        assert m == {"doWork": "./helper.doWork"}

    def test_commonjs_whole_module(self):
        parser = self._get_parser()
        imports = [Import(module="./helper", names=[], is_from=False, alias="helper")]
        m = parser._build_import_map(imports)
        assert m == {"helper": "./helper"}

    def test_multiple_named_imports(self):
        parser = self._get_parser()
        imports = [Import(module="./utils", names=["foo", "bar"], is_from=True)]
        m = parser._build_import_map(imports)
        assert m == {"foo": "./utils.foo", "bar": "./utils.bar"}


# ---------------------------------------------------------------------------
# _resolve_callee unit tests
# ---------------------------------------------------------------------------

class TestResolveCallee:
    """Test _resolve_callee with various callee patterns."""

    def _get_parser(self):
        from codeindex.parsers.typescript_parser import TypeScriptParser
        return TypeScriptParser.create_for_file(Path("test.ts"))

    def test_direct_match(self):
        parser = self._get_parser()
        m = {"executeToolCall": "./tool-executor.executeToolCall"}
        assert parser._resolve_callee("executeToolCall", m) == "./tool-executor.executeToolCall"

    def test_prefix_match(self):
        parser = self._get_parser()
        m = {"LLMClient": "./llm-client"}
        assert parser._resolve_callee("LLMClient.chat", m) == "./llm-client.chat"

    def test_skip_this(self):
        parser = self._get_parser()
        m = {"foo": "./mod.foo"}
        assert parser._resolve_callee("this.foo", m) == "this.foo"

    def test_skip_super(self):
        parser = self._get_parser()
        m = {"foo": "./mod.foo"}
        assert parser._resolve_callee("super.foo", m) == "super.foo"

    def test_no_match_passthrough(self):
        parser = self._get_parser()
        m = {"other": "./mod.other"}
        assert parser._resolve_callee("localFunc", m) == "localFunc"

    def test_empty_import_map(self):
        parser = self._get_parser()
        assert parser._resolve_callee("foo", {}) == "foo"

    def test_namespace_prefix(self):
        parser = self._get_parser()
        m = {"utils": "./utils"}
        assert parser._resolve_callee("utils.format", m) == "./utils.format"


# ---------------------------------------------------------------------------
# Integration: full parse with import resolution
# ---------------------------------------------------------------------------

class TestImportCallResolution:
    """End-to-end tests: parse TS source and verify resolved callees."""

    def test_named_import_call(self, tmp_path):
        code = """\
import { executeToolCall } from './tool-executor';

function handleChat() {
    executeToolCall('grep', {});
}
"""
        calls = _parse_ts_calls(tmp_path, code)
        callees = [c.callee for c in calls]
        assert "./tool-executor.executeToolCall" in callees

    def test_default_import_method_call(self, tmp_path):
        code = """\
import LLMClient from './llm-client';

function run() {
    LLMClient.chat('hello');
}
"""
        calls = _parse_ts_calls(tmp_path, code)
        callees = [c.callee for c in calls]
        assert "./llm-client.chat" in callees

    def test_namespace_import_call(self, tmp_path):
        code = """\
import * as utils from './utils';

function run() {
    utils.format('test');
}
"""
        calls = _parse_ts_calls(tmp_path, code)
        callees = [c.callee for c in calls]
        assert "./utils.format" in callees

    def test_this_call_unchanged(self, tmp_path):
        code = """\
import { helper } from './helper';

class MyClass {
    doWork() {
        this.internal();
    }
}
"""
        calls = _parse_ts_calls(tmp_path, code)
        this_calls = [c.callee for c in calls if c.callee.startswith("this.")]
        assert "this.internal" in this_calls

    def test_no_import_passthrough(self, tmp_path):
        code = """\
function run() {
    localHelper();
}
"""
        calls = _parse_ts_calls(tmp_path, code)
        callees = [c.callee for c in calls]
        assert "localHelper" in callees

    def test_class_method_cross_file_call(self, tmp_path):
        code = """\
import { streamLLMWithTools } from './llm-stream';

class SkillRouter {
    async _handleChatInner() {
        await streamLLMWithTools(this.config);
    }
}
"""
        calls = _parse_ts_calls(tmp_path, code)
        cross_file = [c for c in calls if c.callee == "./llm-stream.streamLLMWithTools"]
        assert len(cross_file) == 1
        assert cross_file[0].caller == "SkillRouter._handleChatInner"

    def test_new_expression_with_import(self, tmp_path):
        code = """\
import { Worker } from './worker';

function start() {
    const w = new Worker();
}
"""
        calls = _parse_ts_calls(tmp_path, code)
        constructors = [c for c in calls if c.call_type == CallType.CONSTRUCTOR]
        assert any("./worker.Worker" in c.callee for c in constructors)

