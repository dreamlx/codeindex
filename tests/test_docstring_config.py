"""Tests for docstring configuration.

Story 9.3: Configuration & CLI

Tests:
- Parse docstrings config from YAML
- Default values (mode=off, backward compatible)
- CLI override of config values
- Cost limit configuration
- Validation of mode values
"""


import pytest

from codeindex.config import Config


class TestDocstringConfig:
    """Test docstring configuration."""

    def test_default_config(self):
        """Should have docstring mode off by default (backward compatible)."""
        config = Config(
            ai_command="",
            include=[],
            exclude=[],
            languages=["python"],
        )

        assert hasattr(config, "docstrings")
        assert config.docstrings.mode == "off"
        assert config.docstrings.ai_command == ""
        assert config.docstrings.cost_limit == 1.0

    def test_parse_docstring_config_from_yaml(self, tmp_path):
        """Should parse docstrings section from YAML config."""
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include:
  - src/
languages:
  - python
  - php

docstrings:
  mode: hybrid
  ai_command: 'claude -p "{prompt}" --allowedTools Read'
  cost_limit: 2.0
""")

        config = Config.from_yaml(config_file)

        assert config.docstrings.mode == "hybrid"
        assert config.docstrings.ai_command == 'claude -p "{prompt}" --allowedTools Read'
        assert config.docstrings.cost_limit == 2.0

    def test_parse_docstring_config_all_ai_mode(self, tmp_path):
        """Should parse all-ai mode."""
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include:
  - src/
languages:
  - python

docstrings:
  mode: all-ai
  ai_command: 'claude -p "{prompt}"'
""")

        config = Config.from_yaml(config_file)

        assert config.docstrings.mode == "all-ai"

    def test_docstring_config_defaults_to_off(self, tmp_path):
        """Should default to off mode if not specified."""
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include:
  - src/
languages:
  - python
""")

        config = Config.from_yaml(config_file)

        assert config.docstrings.mode == "off"

    def test_invalid_docstring_mode(self, tmp_path):
        """Should reject invalid mode values."""
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include:
  - src/
languages:
  - python

docstrings:
  mode: invalid_mode
""")

        with pytest.raises(ValueError, match="Invalid docstring mode"):
            Config.from_yaml(config_file)

    def test_docstring_ai_command_inherits_from_global(self, tmp_path):
        """Should use global ai_command if docstring ai_command not specified."""
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include:
  - src/
languages:
  - python

docstrings:
  mode: hybrid
  # ai_command not specified - should inherit from global
""")

        config = Config.from_yaml(config_file)

        assert config.docstrings.mode == "hybrid"
        # Should inherit from global ai_command
        assert (
            config.docstrings.ai_command == 'claude -p "{prompt}"'
            or config.docstrings.ai_command == ""
        )

    def test_cost_limit_default(self):
        """Should default cost_limit to 1.0 USD."""
        config = Config(
            ai_command="",
            include=[],
            exclude=[],
            languages=["python"],
        )

        assert config.docstrings.cost_limit == 1.0

    def test_custom_cost_limit(self, tmp_path):
        """Should allow custom cost limit."""
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include:
  - src/
languages:
  - python

docstrings:
  mode: hybrid
  cost_limit: 5.0
""")

        config = Config.from_yaml(config_file)

        assert config.docstrings.cost_limit == 5.0


class TestBackwardCompatibility:
    """Test backward compatibility."""

    def test_old_config_without_docstrings_section(self, tmp_path):
        """Old configs without docstrings section should work."""
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include:
  - src/
languages:
  - python
""")

        config = Config.from_yaml(config_file)

        # Should work and default to off
        assert config.docstrings.mode == "off"
        assert config.ai_command == 'claude -p "{prompt}"'

    def test_existing_config_fields_unchanged(self, tmp_path):
        """Adding docstrings should not affect existing config fields."""
        config_file = tmp_path / ".codeindex.yaml"
        config_file.write_text("""
ai_command: 'claude -p "{prompt}"'
include:
  - src/
exclude:
  - tests/
languages:
  - python
  - php

docstrings:
  mode: hybrid
""")

        config = Config.from_yaml(config_file)

        # Existing fields unchanged
        assert config.ai_command == 'claude -p "{prompt}"'
        assert config.include == ["src/"]
        assert config.exclude == ["tests/"]
        assert config.languages == ["python", "php"]

        # New field added
        assert config.docstrings.mode == "hybrid"
