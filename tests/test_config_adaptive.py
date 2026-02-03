"""Tests for adaptive symbols configuration loading in Config."""

import tempfile
from pathlib import Path

import yaml

from codeindex.adaptive_config import DEFAULT_ADAPTIVE_CONFIG, AdaptiveSymbolsConfig
from codeindex.config import Config, SymbolsConfig


class TestSymbolsConfigAdaptive:
    """Test SymbolsConfig with adaptive_symbols field."""

    def test_symbols_config_has_adaptive_field(self):
        """SymbolsConfig应该有adaptive_symbols字段"""
        config = SymbolsConfig()

        assert hasattr(config, "adaptive_symbols")
        assert isinstance(config.adaptive_symbols, AdaptiveSymbolsConfig)

    def test_symbols_config_default_adaptive_disabled(self):
        """默认adaptive_symbols应该是禁用的（向后兼容）"""
        config = SymbolsConfig()

        assert config.adaptive_symbols.enabled is False

    def test_symbols_config_uses_default_adaptive_config(self):
        """默认应该使用DEFAULT_ADAPTIVE_CONFIG"""
        config = SymbolsConfig()

        assert config.adaptive_symbols.thresholds == DEFAULT_ADAPTIVE_CONFIG.thresholds
        assert config.adaptive_symbols.limits == DEFAULT_ADAPTIVE_CONFIG.limits


class TestConfigLoadingAdaptive:
    """Test Config loading with adaptive_symbols configuration."""

    def test_load_config_without_adaptive(self):
        """加载没有adaptive_symbols的配置（向后兼容）"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "indexing": {
                        "symbols": {
                            "max_per_file": 20,
                        }
                    }
                },
                f,
            )
            config_path = Path(f.name)

        try:
            config = Config.load(config_path)

            # 应该加载成功
            assert config.indexing.symbols.max_per_file == 20
            # adaptive_symbols应该使用默认值（禁用）
            assert config.indexing.symbols.adaptive_symbols.enabled is False
        finally:
            config_path.unlink()

    def test_load_config_with_adaptive_enabled(self):
        """加载启用adaptive_symbols的配置"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "indexing": {
                        "symbols": {
                            "max_per_file": 15,
                            "adaptive_symbols": {
                                "enabled": True,
                            },
                        }
                    }
                },
                f,
            )
            config_path = Path(f.name)

        try:
            config = Config.load(config_path)

            assert config.indexing.symbols.adaptive_symbols.enabled is True
            # 其他应该使用默认值
            expected_thresholds = DEFAULT_ADAPTIVE_CONFIG.thresholds
            assert config.indexing.symbols.adaptive_symbols.thresholds == expected_thresholds
        finally:
            config_path.unlink()

    def test_load_config_with_custom_thresholds(self):
        """加载自定义thresholds配置"""
        custom_thresholds = {
            "tiny": 50,
            "small": 150,
            "medium": 400,
            "large": 900,
            "xlarge": 1800,
            "huge": 4500,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "indexing": {
                        "symbols": {
                            "adaptive_symbols": {
                                "enabled": True,
                                "thresholds": custom_thresholds,
                            },
                        }
                    }
                },
                f,
            )
            config_path = Path(f.name)

        try:
            config = Config.load(config_path)

            assert config.indexing.symbols.adaptive_symbols.enabled is True
            assert config.indexing.symbols.adaptive_symbols.thresholds == custom_thresholds
        finally:
            config_path.unlink()

    def test_load_config_with_custom_limits(self):
        """加载自定义limits配置"""
        custom_limits = {
            "tiny": 8,
            "small": 12,
            "medium": 25,
            "large": 40,
            "xlarge": 60,
            "huge": 100,
            "mega": 120,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "indexing": {
                        "symbols": {
                            "adaptive_symbols": {
                                "enabled": True,
                                "limits": custom_limits,
                            },
                        }
                    }
                },
                f,
            )
            config_path = Path(f.name)

        try:
            config = Config.load(config_path)

            assert config.indexing.symbols.adaptive_symbols.limits == custom_limits
        finally:
            config_path.unlink()

    def test_load_config_with_partial_overrides(self):
        """加载部分覆盖的配置"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "indexing": {
                        "symbols": {
                            "adaptive_symbols": {
                                "enabled": True,
                                "limits": {
                                    "large": 60,  # 只覆盖large
                                    "xlarge": 100,  # 只覆盖xlarge
                                },
                            },
                        }
                    }
                },
                f,
            )
            config_path = Path(f.name)

        try:
            config = Config.load(config_path)

            # 覆盖的值应该生效
            assert config.indexing.symbols.adaptive_symbols.limits["large"] == 60
            assert config.indexing.symbols.adaptive_symbols.limits["xlarge"] == 100
            # 其他保持默认
            expected_small = DEFAULT_ADAPTIVE_CONFIG.limits["small"]
            assert config.indexing.symbols.adaptive_symbols.limits["small"] == expected_small
        finally:
            config_path.unlink()

    def test_load_config_with_min_max_symbols(self):
        """加载min_symbols和max_symbols配置"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "indexing": {
                        "symbols": {
                            "adaptive_symbols": {
                                "enabled": True,
                                "min_symbols": 3,
                                "max_symbols": 150,
                            },
                        }
                    }
                },
                f,
            )
            config_path = Path(f.name)

        try:
            config = Config.load(config_path)

            assert config.indexing.symbols.adaptive_symbols.min_symbols == 3
            assert config.indexing.symbols.adaptive_symbols.max_symbols == 150
        finally:
            config_path.unlink()


class TestConfigurationMerging:
    """Test configuration merging logic (user + defaults)."""

    def test_merge_preserves_user_thresholds(self):
        """用户配置的thresholds应该保留"""
        custom_thresholds = {"small": 300}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "indexing": {
                        "symbols": {
                            "adaptive_symbols": {
                                "enabled": True,
                                "thresholds": custom_thresholds,
                            },
                        }
                    }
                },
                f,
            )
            config_path = Path(f.name)

        try:
            config = Config.load(config_path)

            # 用户配置的值应该覆盖
            assert config.indexing.symbols.adaptive_symbols.thresholds["small"] == 300
            # 其他应该使用默认值
            assert "tiny" in config.indexing.symbols.adaptive_symbols.thresholds
            assert "medium" in config.indexing.symbols.adaptive_symbols.thresholds
        finally:
            config_path.unlink()

    def test_merge_preserves_user_limits(self):
        """用户配置的limits应该保留"""
        custom_limits = {"huge": 200}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "indexing": {
                        "symbols": {
                            "adaptive_symbols": {
                                "enabled": True,
                                "limits": custom_limits,
                            },
                        }
                    }
                },
                f,
            )
            config_path = Path(f.name)

        try:
            config = Config.load(config_path)

            # 用户配置的值应该覆盖
            assert config.indexing.symbols.adaptive_symbols.limits["huge"] == 200
            # 其他应该使用默认值
            assert "tiny" in config.indexing.symbols.adaptive_symbols.limits
            assert "small" in config.indexing.symbols.adaptive_symbols.limits
        finally:
            config_path.unlink()


class TestBackwardCompatibility:
    """Test backward compatibility with existing configs."""

    def test_old_config_still_works(self):
        """旧配置文件应该仍然工作"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "indexing": {
                        "symbols": {
                            "max_per_file": 25,
                            "include_visibility": ["public"],
                        }
                    }
                },
                f,
            )
            config_path = Path(f.name)

        try:
            config = Config.load(config_path)

            # 旧配置应该正常加载
            assert config.indexing.symbols.max_per_file == 25
            assert config.indexing.symbols.include_visibility == ["public"]
            # adaptive_symbols应该使用默认值（禁用）
            assert config.indexing.symbols.adaptive_symbols.enabled is False
        finally:
            config_path.unlink()

    def test_empty_adaptive_symbols_uses_defaults(self):
        """空的adaptive_symbols配置应该使用默认值"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "indexing": {
                        "symbols": {
                            "adaptive_symbols": {},
                        }
                    }
                },
                f,
            )
            config_path = Path(f.name)

        try:
            config = Config.load(config_path)

            # 应该使用默认配置
            expected_enabled = DEFAULT_ADAPTIVE_CONFIG.enabled
            expected_thresholds = DEFAULT_ADAPTIVE_CONFIG.thresholds
            assert config.indexing.symbols.adaptive_symbols.enabled == expected_enabled
            assert config.indexing.symbols.adaptive_symbols.thresholds == expected_thresholds
        finally:
            config_path.unlink()
