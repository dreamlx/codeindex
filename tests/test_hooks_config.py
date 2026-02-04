"""Tests for hooks configuration.

Story 6: Git Hooks performance optimization - Config support.
"""


from codeindex.config import Config, HooksConfig


class TestHooksConfig:
    """Test hooks configuration loading and defaults."""

    def test_default_hooks_config(self):
        """Should have default hooks configuration."""
        config = HooksConfig()

        assert config.post_commit.mode == "auto"
        assert config.post_commit.max_dirs_sync == 2
        assert config.post_commit.enabled is True

    def test_hooks_config_disabled_mode(self):
        """Should support disabled mode."""
        config = HooksConfig.from_dict(
            {"post_commit": {"mode": "disabled", "enabled": False}}
        )

        assert config.post_commit.mode == "disabled"
        assert config.post_commit.enabled is False

    def test_hooks_config_async_mode(self):
        """Should support async mode."""
        config = HooksConfig.from_dict({"post_commit": {"mode": "async"}})

        assert config.post_commit.mode == "async"

    def test_hooks_config_sync_mode(self):
        """Should support sync mode."""
        config = HooksConfig.from_dict({"post_commit": {"mode": "sync"}})

        assert config.post_commit.mode == "sync"

    def test_hooks_config_prompt_mode(self):
        """Should support prompt mode."""
        config = HooksConfig.from_dict({"post_commit": {"mode": "prompt"}})

        assert config.post_commit.mode == "prompt"

    def test_hooks_config_custom_threshold(self):
        """Should support custom max_dirs_sync threshold."""
        config = HooksConfig.from_dict({"post_commit": {"max_dirs_sync": 5}})

        assert config.post_commit.max_dirs_sync == 5

    def test_hooks_config_custom_log_file(self):
        """Should support custom log file path."""
        log_path = "~/.my-logs/post-commit.log"
        config = HooksConfig.from_dict({"post_commit": {"log_file": log_path}})

        assert config.post_commit.log_file == log_path

    def test_config_loads_hooks_from_yaml(self, tmp_path):
        """Should load hooks configuration from .codeindex.yaml."""
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text(
            """
version: 1
hooks:
  post_commit:
    mode: async
    max_dirs_sync: 3
    log_file: ~/.codeindex/hooks/my-log.log
"""
        )

        config = Config.load(str(config_file))

        assert config.hooks.post_commit.mode == "async"
        assert config.hooks.post_commit.max_dirs_sync == 3
        assert config.hooks.post_commit.log_file == "~/.codeindex/hooks/my-log.log"

    def test_config_with_disabled_hooks(self, tmp_path):
        """Should support completely disabled hooks."""
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text(
            """
version: 1
hooks:
  post_commit:
    mode: disabled
    enabled: false
"""
        )

        config = Config.load(str(config_file))

        assert config.hooks.post_commit.mode == "disabled"
        assert config.hooks.post_commit.enabled is False

    def test_config_with_prompt_mode(self, tmp_path):
        """Should support prompt-only mode."""
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text(
            """
version: 1
hooks:
  post_commit:
    mode: prompt
"""
        )

        config = Config.load(str(config_file))

        assert config.hooks.post_commit.mode == "prompt"
        assert config.hooks.post_commit.enabled is True


class TestPostCommitConfig:
    """Test PostCommitConfig specifics."""

    def test_valid_modes(self):
        """Should only accept valid modes."""
        valid_modes = ["auto", "disabled", "async", "sync", "prompt"]

        for mode in valid_modes:
            config = HooksConfig.from_dict({"post_commit": {"mode": mode}})
            assert config.post_commit.mode == mode

    def test_auto_mode_is_default(self):
        """Auto mode should be the default (smart detection)."""
        config = HooksConfig()
        assert config.post_commit.mode == "auto"

    def test_max_dirs_sync_default(self):
        """max_dirs_sync should default to 2."""
        config = HooksConfig()
        assert config.post_commit.max_dirs_sync == 2

    def test_enabled_default_true(self):
        """Post-commit hook should be enabled by default."""
        config = HooksConfig()
        assert config.post_commit.enabled is True
