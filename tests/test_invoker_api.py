"""Tests for the direct-HTTP-API AI backend (ADR-008).

Covers:
- ``invoke_ai_api`` — OpenAI-compatible /chat/completions via httpx, reusing
  the GH-97 transient-retry framework (429/5xx/timeout/connection retry;
  401/402/403 fail fast).
- ``resolve_ai_backend`` — precedence: ai_command (CLI) > ai.api_key (API) > none.
- ``invoke_ai`` — single-entry dispatch over the above.

httpx is mocked via pytest-httpx (``httpx_mock`` fixture).
"""

import httpx
import pytest

from codeindex.config import AIConfig, Config
from codeindex.invoker import InvokeResult, invoke_ai, invoke_ai_api, resolve_ai_backend


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Isolate from host env: explicit AIConfig + no proxy (so httpx +
    httpx_mock talk only to the mock, not the host SOCKS/HTTPS proxy)."""
    monkeypatch.delenv("CODEINDEX_AI_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    for v in ("http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"):
        monkeypatch.delenv(v, raising=False)


DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"


def _ok(content: str = "ok") -> dict:
    return {"choices": [{"message": {"content": content}}]}


class TestInvokeAiApi:
    def test_success(self, httpx_mock):
        httpx_mock.add_response(url=DEEPSEEK_URL, status_code=200, json=_ok("# README_AI.md - test"))
        result = invoke_ai_api(AIConfig(api_key="sk-x"), "hi", max_attempts=1)
        assert result.success
        assert "README_AI.md" in result.output
        assert "POST" in result.command

    def test_429_retries_then_succeeds(self, httpx_mock):
        httpx_mock.add_response(url=DEEPSEEK_URL, status_code=429, text="rate limit")
        httpx_mock.add_response(url=DEEPSEEK_URL, status_code=200, json=_ok("ok"))
        result = invoke_ai_api(AIConfig(api_key="sk-x"), "hi", max_attempts=3, retry_backoff=0)
        assert result.success
        assert result.output == "ok"
        assert len(httpx_mock.get_requests()) == 2

    def test_503_retries_then_succeeds(self, httpx_mock):
        httpx_mock.add_response(url=DEEPSEEK_URL, status_code=503, text="service unavailable")
        httpx_mock.add_response(url=DEEPSEEK_URL, status_code=200, json=_ok("ok"))
        result = invoke_ai_api(AIConfig(api_key="sk-x"), "hi", max_attempts=3, retry_backoff=0)
        assert result.success
        assert len(httpx_mock.get_requests()) == 2

    def test_timeout_retries_then_succeeds(self, httpx_mock):
        httpx_mock.add_exception(httpx.TimeoutException("timed out"), url=DEEPSEEK_URL)
        httpx_mock.add_response(url=DEEPSEEK_URL, status_code=200, json=_ok("ok"))
        result = invoke_ai_api(AIConfig(api_key="sk-x"), "hi", max_attempts=3, retry_backoff=0)
        assert result.success
        assert len(httpx_mock.get_requests()) == 2

    def test_connection_error_retries_then_succeeds(self, httpx_mock):
        httpx_mock.add_exception(httpx.ConnectError("connection refused"), url=DEEPSEEK_URL)
        httpx_mock.add_response(url=DEEPSEEK_URL, status_code=200, json=_ok("ok"))
        result = invoke_ai_api(AIConfig(api_key="sk-x"), "hi", max_attempts=3, retry_backoff=0)
        assert result.success
        assert len(httpx_mock.get_requests()) == 2

    def test_401_does_not_retry(self, httpx_mock):
        # Auth error is NOT transient — single attempt, fail fast (avoid hammering on bad keys).
        httpx_mock.add_response(url=DEEPSEEK_URL, status_code=401, text="invalid api key")
        result = invoke_ai_api(AIConfig(api_key="sk-bad"), "hi", max_attempts=3, retry_backoff=0)
        assert not result.success
        assert "401" in result.error
        assert len(httpx_mock.get_requests()) == 1

    def test_402_does_not_retry(self, httpx_mock):
        # Quota / billing — also non-transient.
        httpx_mock.add_response(url=DEEPSEEK_URL, status_code=402, text="insufficient balance")
        result = invoke_ai_api(AIConfig(api_key="sk-broke"), "hi", max_attempts=3, retry_backoff=0)
        assert not result.success
        assert "402" in result.error
        assert len(httpx_mock.get_requests()) == 1

    def test_uses_config_base_url_and_model(self, httpx_mock):
        cfg = AIConfig(provider="openai", base_url="https://api.openai.com/v1", model="gpt-4o-mini", api_key="sk-x")
        httpx_mock.add_response(url="https://api.openai.com/v1/chat/completions", status_code=200, json=_ok("ok"))
        result = invoke_ai_api(cfg, "hi", max_attempts=1)
        assert result.success
        req = httpx_mock.get_requests()[0]
        assert req.url == "https://api.openai.com/v1/chat/completions"
        import json as _json
        body = _json.loads(req.content)
        assert body["model"] == "gpt-4o-mini"

    def test_env_api_key_takes_precedence_in_authorization_header(self, httpx_mock, monkeypatch):
        monkeypatch.setenv("CODEINDEX_AI_API_KEY", "sk-env")
        httpx_mock.add_response(url=DEEPSEEK_URL, status_code=200, json=_ok("ok"))
        invoke_ai_api(AIConfig(api_key="sk-yaml"), "hi", max_attempts=1)
        req = httpx_mock.get_requests()[0]
        assert req.headers["authorization"] == "Bearer sk-env"


class TestResolveAIBackend:
    def test_ai_command_wins_over_api(self, monkeypatch):
        monkeypatch.setenv("CODEINDEX_AI_API_KEY", "sk-env")
        cfg = Config()
        cfg.ai_command = 'claude -p "{prompt}"'
        cfg.ai = AIConfig(api_key="sk-yaml")
        backend, value = resolve_ai_backend(cfg)
        assert backend == "cli"
        assert value == 'claude -p "{prompt}"'

    def test_api_when_no_ai_command(self, monkeypatch):
        monkeypatch.setenv("CODEINDEX_AI_API_KEY", "sk-env")
        cfg = Config()
        cfg.ai_command = ""
        backend, value = resolve_ai_backend(cfg)
        assert backend == "api"
        assert value is cfg.ai

    def test_api_via_yaml_key_when_no_env(self):
        cfg = Config()
        cfg.ai_command = ""
        cfg.ai = AIConfig(api_key="sk-yaml")
        backend, value = resolve_ai_backend(cfg)
        assert backend == "api"

    def test_none_when_neither(self):
        cfg = Config()  # ai_command="" + ai=AIConfig() (no key, no env)
        backend, value = resolve_ai_backend(cfg)
        assert backend == "none"
        assert value == ""


class TestInvokeAiDispatch:
    def test_routes_to_cli_when_ai_command_set(self, monkeypatch):
        captured = {}

        def fake_cli(cmd, prompt, **kw):
            captured["cmd"] = cmd
            captured["prompt"] = prompt
            return InvokeResult(success=True, output="cli-out", command=cmd)

        monkeypatch.setattr("codeindex.invoker.invoke_ai_cli", fake_cli)
        cfg = Config()
        cfg.ai_command = 'claude -p "{prompt}"'
        r = invoke_ai(cfg, "hi", timeout=30)
        assert r.success and r.output == "cli-out"
        assert captured["cmd"] == 'claude -p "{prompt}"'
        assert captured["prompt"] == "hi"

    def test_routes_to_api_when_only_api_key(self, monkeypatch):
        captured = {}

        def fake_api(ai_cfg, prompt, **kw):
            captured["model"] = ai_cfg.model
            return InvokeResult(success=True, output="api-out", command="POST")

        monkeypatch.setattr("codeindex.invoker.invoke_ai_api", fake_api)
        cfg = Config()
        cfg.ai = AIConfig(api_key="sk-yaml")
        r = invoke_ai(cfg, "hi", timeout=30)
        assert r.success and r.output == "api-out"
        assert captured["model"] == "deepseek-chat"

    def test_returns_clear_error_when_neither(self):
        cfg = Config()  # nothing configured
        r = invoke_ai(cfg, "hi", timeout=30)
        assert not r.success
        # Error message must point the user at one of the three setup paths.
        assert "CODEINDEX_AI_API_KEY" in r.error or "ai:" in r.error or "ai_command" in r.error

    def test_dry_run_api_does_not_call(self, monkeypatch):
        called = []

        def fake_api(*a, **kw):
            called.append(1)
            return InvokeResult(success=True, output="x", command="POST")

        monkeypatch.setattr("codeindex.invoker.invoke_ai_api", fake_api)
        cfg = Config()
        cfg.ai = AIConfig(api_key="sk-yaml")
        r = invoke_ai(cfg, "hi", timeout=30, dry_run=True)
        assert r.success
        assert called == []  # dry run must not hit the network
