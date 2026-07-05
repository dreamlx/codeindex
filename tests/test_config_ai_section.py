"""Tests for the ``ai:`` config section — direct HTTP API backend (ADR-008).

The ``ai:`` section configures the OpenAI-compatible HTTP AI backend
(DeepSeek default). ``ai_command`` (CLI) remains as a backward-compat
escape hatch — both can coexist (precedence is resolved in invoker.py's
``resolve_ai_backend``, tested in test_invoker_api.py).
"""

from textwrap import dedent

from codeindex.config import AIConfig, Config


class TestAIConfig:
    def test_defaults(self):
        cfg = AIConfig()
        assert cfg.provider == "deepseek"
        assert cfg.base_url == "https://api.deepseek.com/v1"
        assert cfg.model == "deepseek-chat"
        assert cfg.api_key == ""
        assert cfg.timeout == 120
        assert cfg.max_tokens == 4096

    def test_from_dict_empty_returns_defaults(self):
        assert AIConfig.from_dict({}) == AIConfig()
        assert AIConfig.from_dict(None) == AIConfig()

    def test_from_dict_overrides(self):
        cfg = AIConfig.from_dict({
            "provider": "openai",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini",
            "api_key": "sk-yaml",
            "timeout": 60,
            "max_tokens": 2048,
        })
        assert cfg.provider == "openai"
        assert cfg.model == "gpt-4o-mini"
        assert cfg.api_key == "sk-yaml"
        assert cfg.timeout == 60
        assert cfg.max_tokens == 2048

    def test_resolved_api_key_env_wins_over_yaml(self, monkeypatch):
        monkeypatch.setenv("CODEINDEX_AI_API_KEY", "sk-env")
        cfg = AIConfig(api_key="sk-yaml")
        assert cfg.resolved_api_key == "sk-env"

    def test_resolved_api_key_deepseek_env_backcompat(self, monkeypatch):
        """DEEPSEEK_API_KEY still works (ADR-008 initial release used it)."""
        monkeypatch.delenv("CODEINDEX_AI_API_KEY", raising=False)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-ds")
        cfg = AIConfig(api_key="sk-yaml")
        assert cfg.resolved_api_key == "sk-ds"

    def test_resolved_api_key_yaml_fallback_when_no_env(self, monkeypatch):
        monkeypatch.delenv("CODEINDEX_AI_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        cfg = AIConfig(api_key="sk-yaml")
        assert cfg.resolved_api_key == "sk-yaml"

    def test_resolved_api_key_empty_when_neither(self, monkeypatch):
        monkeypatch.delenv("CODEINDEX_AI_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        assert AIConfig().resolved_api_key == ""

    def test_provider_preset_fills_defaults(self):
        # provider=openai with no base_url/model → preset defaults applied
        cfg = AIConfig.from_dict({"provider": "openai", "api_key": "sk-x"})
        assert cfg.base_url == "https://api.openai.com/v1"
        assert cfg.model == "gpt-4o-mini"

    def test_provider_preset_overridden_by_explicit_fields(self):
        cfg = AIConfig.from_dict({
            "provider": "openai",
            "base_url": "https://my-gateway.example.com/v1",
            "model": "gpt-4o",
        })
        assert cfg.base_url == "https://my-gateway.example.com/v1"
        assert cfg.model == "gpt-4o"

    def test_provider_preset_llama_server(self):
        cfg = AIConfig.from_dict({"provider": "llama-server", "model": "qwen3.6-27b"})
        assert cfg.base_url == "http://localhost:10802/v1"
        assert cfg.model == "qwen3.6-27b"


class TestConfigLoadsAISection:
    def test_yaml_ai_block_populates_config(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CODEINDEX_AI_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        p = tmp_path / ".codeindex.yaml"
        p.write_text(dedent("""\
            version: 1
            ai:
              provider: deepseek
              base_url: https://api.deepseek.com/v1
              model: deepseek-chat
              api_key: sk-yaml
              timeout: 90
              max_tokens: 1024
        """))
        cfg = Config.load(p)
        assert cfg.ai.provider == "deepseek"
        assert cfg.ai.model == "deepseek-chat"
        assert cfg.ai.api_key == "sk-yaml"
        assert cfg.ai.resolved_api_key == "sk-yaml"
        assert cfg.ai.timeout == 90
        assert cfg.ai.max_tokens == 1024

    def test_config_ai_defaults_when_no_block(self, tmp_path, monkeypatch):
        monkeypatch.delenv("CODEINDEX_AI_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        p = tmp_path / ".codeindex.yaml"
        p.write_text("version: 1\n")
        cfg = Config.load(p)
        assert cfg.ai == AIConfig()

    def test_ai_command_still_loaded_alongside_ai(self, tmp_path):
        # Backward compat: ai_command (CLI escape hatch) still parsed.
        p = tmp_path / ".codeindex.yaml"
        p.write_text(
            'version: 1\n'
            'ai_command: \'claude -p "{prompt}" --allowedTools "Read"\'\n'
        )
        cfg = Config.load(p)
        assert cfg.ai_command == 'claude -p "{prompt}" --allowedTools "Read"'
        # ai section still defaults when absent
        assert cfg.ai.model == "deepseek-chat"
