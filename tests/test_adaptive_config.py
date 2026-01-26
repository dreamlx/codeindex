"""Tests for adaptive symbols configuration."""

from codeindex.adaptive_config import (
    DEFAULT_ADAPTIVE_CONFIG,
    AdaptiveSymbolsConfig,
)


class TestAdaptiveSymbolsConfig:
    """Test AdaptiveSymbolsConfig data class."""

    def test_default_config_exists(self):
        """默认配置常量应该存在"""
        assert DEFAULT_ADAPTIVE_CONFIG is not None
        assert isinstance(DEFAULT_ADAPTIVE_CONFIG, AdaptiveSymbolsConfig)

    def test_default_config_disabled_by_default(self):
        """默认配置应该是禁用状态（向后兼容）"""
        assert DEFAULT_ADAPTIVE_CONFIG.enabled is False

    def test_default_config_has_thresholds(self):
        """默认配置应该包含完整的阈值定义"""
        config = DEFAULT_ADAPTIVE_CONFIG

        assert "tiny" in config.thresholds
        assert "small" in config.thresholds
        assert "medium" in config.thresholds
        assert "large" in config.thresholds
        assert "xlarge" in config.thresholds
        assert "huge" in config.thresholds

    def test_default_config_has_limits(self):
        """默认配置应该包含完整的限制定义"""
        config = DEFAULT_ADAPTIVE_CONFIG

        assert "tiny" in config.limits
        assert "small" in config.limits
        assert "medium" in config.limits
        assert "large" in config.limits
        assert "xlarge" in config.limits
        assert "huge" in config.limits
        assert "mega" in config.limits

    def test_default_thresholds_are_increasing(self):
        """默认阈值应该递增"""
        config = DEFAULT_ADAPTIVE_CONFIG

        assert config.thresholds["tiny"] < config.thresholds["small"]
        assert config.thresholds["small"] < config.thresholds["medium"]
        assert config.thresholds["medium"] < config.thresholds["large"]
        assert config.thresholds["large"] < config.thresholds["xlarge"]
        assert config.thresholds["xlarge"] < config.thresholds["huge"]

    def test_default_limits_are_increasing(self):
        """默认限制应该递增"""
        config = DEFAULT_ADAPTIVE_CONFIG

        assert config.limits["tiny"] <= config.limits["small"]
        assert config.limits["small"] <= config.limits["medium"]
        assert config.limits["medium"] <= config.limits["large"]
        assert config.limits["large"] <= config.limits["xlarge"]
        assert config.limits["xlarge"] <= config.limits["huge"]
        assert config.limits["huge"] <= config.limits["mega"]

    def test_default_min_max_symbols(self):
        """默认最小/最大符号数应该合理"""
        config = DEFAULT_ADAPTIVE_CONFIG

        assert config.min_symbols >= 5
        assert config.max_symbols <= 200
        assert config.min_symbols < config.max_symbols

    def test_custom_config_initialization(self):
        """应该能创建自定义配置"""
        config = AdaptiveSymbolsConfig(
            enabled=True,
            thresholds={
                "tiny": 50,
                "small": 100,
                "medium": 300,
                "large": 800,
                "xlarge": 1500,
                "huge": 4000,
            },
            limits={
                "tiny": 8,
                "small": 12,
                "medium": 25,
                "large": 40,
                "xlarge": 60,
                "huge": 100,
                "mega": 120,
            },
            min_symbols=3,
            max_symbols=150,
        )

        assert config.enabled is True
        assert config.thresholds["small"] == 100
        assert config.limits["large"] == 40
        assert config.min_symbols == 3
        assert config.max_symbols == 150

    def test_config_with_partial_overrides(self):
        """应该能部分覆盖默认配置"""
        # 测试只覆盖部分字段
        config = AdaptiveSymbolsConfig(
            enabled=True,
            thresholds=DEFAULT_ADAPTIVE_CONFIG.thresholds.copy(),
            limits={
                **DEFAULT_ADAPTIVE_CONFIG.limits,
                "large": 60,  # 只覆盖large
                "xlarge": 100,  # 只覆盖xlarge
            },
            min_symbols=DEFAULT_ADAPTIVE_CONFIG.min_symbols,
            max_symbols=DEFAULT_ADAPTIVE_CONFIG.max_symbols,
        )

        assert config.enabled is True
        assert config.limits["large"] == 60
        assert config.limits["xlarge"] == 100
        # 其他保持默认
        assert config.limits["small"] == DEFAULT_ADAPTIVE_CONFIG.limits["small"]


class TestConfigurationValidation:
    """Test configuration validation logic."""

    def test_thresholds_should_be_positive(self):
        """阈值应该是正数"""
        config = DEFAULT_ADAPTIVE_CONFIG

        for threshold in config.thresholds.values():
            assert threshold > 0

    def test_limits_should_be_positive(self):
        """限制应该是正数"""
        config = DEFAULT_ADAPTIVE_CONFIG

        for limit in config.limits.values():
            assert limit > 0

    def test_min_symbols_should_be_positive(self):
        """最小符号数应该是正数"""
        assert DEFAULT_ADAPTIVE_CONFIG.min_symbols > 0

    def test_max_symbols_should_be_reasonable(self):
        """最大符号数应该合理（不超过500）"""
        assert DEFAULT_ADAPTIVE_CONFIG.max_symbols <= 500

    def test_all_limits_within_min_max_range(self):
        """所有limits应该在min和max范围内"""
        config = DEFAULT_ADAPTIVE_CONFIG

        for limit in config.limits.values():
            assert config.min_symbols <= limit <= config.max_symbols


class TestExpectedDefaults:
    """Test expected default values from planning document."""

    def test_default_thresholds_match_plan(self):
        """默认阈值应该匹配规划文档"""
        config = DEFAULT_ADAPTIVE_CONFIG

        assert config.thresholds["tiny"] == 100
        assert config.thresholds["small"] == 200
        assert config.thresholds["medium"] == 500
        assert config.thresholds["large"] == 1000
        assert config.thresholds["xlarge"] == 2000
        assert config.thresholds["huge"] == 5000

    def test_default_limits_match_plan(self):
        """默认限制应该匹配规划文档"""
        config = DEFAULT_ADAPTIVE_CONFIG

        assert config.limits["tiny"] == 10
        assert config.limits["small"] == 15
        assert config.limits["medium"] == 30
        assert config.limits["large"] == 50
        assert config.limits["xlarge"] == 80
        assert config.limits["huge"] == 120
        assert config.limits["mega"] == 150

    def test_default_min_symbols_match_plan(self):
        """默认最小符号数应该匹配规划文档"""
        assert DEFAULT_ADAPTIVE_CONFIG.min_symbols == 5

    def test_default_max_symbols_match_plan(self):
        """默认最大符号数应该匹配规划文档"""
        assert DEFAULT_ADAPTIVE_CONFIG.max_symbols == 200
