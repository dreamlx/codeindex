"""Init seeds the ``ai:`` direct-API section (not ai_command) — ADR-008.

Non-interactive ``init`` and the wizard's "no CLI" path must emit an ``ai:``
section (DeepSeek default). ``ai_command`` (CLI) is only emitted when the user
explicitly chose a CLI backend (escape hatch).
"""

from codeindex.init_wizard import WizardResult, generate_config_yaml


def _minimal_result(**overrides):
    r = WizardResult(
        detected_languages=["python"],
        suggested_patterns={"include": ["src/"], "exclude": []},
    )
    for k, v in overrides.items():
        setattr(r, k, v)
    return r


class TestInitSeedsAISection:
    def test_no_ai_command_emits_ai_section(self, tmp_path):
        yaml = generate_config_yaml(_minimal_result(), tmp_path)
        assert "ai:" in yaml
        assert "deepseek" in yaml
        assert "deepseek-chat" in yaml
        assert "CODEINDEX_AI_API_KEY" in yaml  # the env-var hint
        # No uncommented ai_command — CLI escape hatch must stay commented out.
        for line in yaml.splitlines():
            assert not line.strip().startswith("ai_command:"), (
                f"init must not seed ai_command (Claude CLI dead, ADR-008): {line!r}"
            )

    def test_ai_command_emitted_when_user_chose_cli(self, tmp_path):
        yaml = generate_config_yaml(
            _minimal_result(ai_command='claude -p "{prompt}"'), tmp_path
        )
        assert 'ai_command: \'claude -p "{prompt}"\'' in yaml
