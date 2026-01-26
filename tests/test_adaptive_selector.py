"""Tests for AdaptiveSymbolSelector."""

from codeindex.adaptive_config import AdaptiveSymbolsConfig
from codeindex.adaptive_selector import AdaptiveSymbolSelector


class TestAdaptiveSymbolSelectorBase:
    """Test basic AdaptiveSymbolSelector functionality."""

    def test_selector_initialization_with_default_config(self):
        """应该能用默认配置初始化"""
        selector = AdaptiveSymbolSelector()

        assert selector is not None
        assert selector.config is not None

    def test_selector_initialization_with_custom_config(self):
        """应该能用自定义配置初始化"""
        config = AdaptiveSymbolsConfig(
            enabled=True,
            thresholds={"small": 100},
            limits={"small": 20},
        )
        selector = AdaptiveSymbolSelector(config)

        # 检查自定义的值被保留，并且默认值被合并
        assert selector.config.enabled is True
        assert selector.config.thresholds["small"] == 100
        assert selector.config.limits["small"] == 20
        # 默认值应该被合并进来
        assert "tiny" in selector.config.thresholds
        assert "large" in selector.config.limits

    def test_calculate_limit_returns_int(self):
        """calculate_limit应该返回整数"""
        selector = AdaptiveSymbolSelector()
        limit = selector.calculate_limit(500, 30)

        assert isinstance(limit, int)

    def test_calculate_limit_returns_positive(self):
        """calculate_limit应该返回正数"""
        selector = AdaptiveSymbolSelector()
        limit = selector.calculate_limit(500, 30)

        assert limit > 0

    def test_calculate_limit_not_exceed_total_symbols(self):
        """不应该超过实际符号数量"""
        selector = AdaptiveSymbolSelector()
        limit = selector.calculate_limit(10000, 10)  # 大文件但只有10个符号

        assert limit <= 10


class TestSizeCategoryDetermination:
    """Test file size category determination."""

    def test_tiny_file_category(self):
        """<100行的文件应该归类为tiny"""
        selector = AdaptiveSymbolSelector()
        category = selector._determine_size_category(50)

        assert category == "tiny"

    def test_tiny_boundary_99_lines(self):
        """99行应该是tiny"""
        selector = AdaptiveSymbolSelector()
        category = selector._determine_size_category(99)

        assert category == "tiny"

    def test_small_file_category(self):
        """100-200行的文件应该归类为small"""
        selector = AdaptiveSymbolSelector()

        assert selector._determine_size_category(100) == "small"
        assert selector._determine_size_category(150) == "small"
        assert selector._determine_size_category(199) == "small"

    def test_medium_file_category(self):
        """200-500行的文件应该归类为medium"""
        selector = AdaptiveSymbolSelector()

        assert selector._determine_size_category(200) == "medium"
        assert selector._determine_size_category(350) == "medium"
        assert selector._determine_size_category(499) == "medium"

    def test_large_file_category(self):
        """500-1000行的文件应该归类为large"""
        selector = AdaptiveSymbolSelector()

        assert selector._determine_size_category(500) == "large"
        assert selector._determine_size_category(750) == "large"
        assert selector._determine_size_category(999) == "large"

    def test_xlarge_file_category(self):
        """1000-2000行的文件应该归类为xlarge"""
        selector = AdaptiveSymbolSelector()

        assert selector._determine_size_category(1000) == "xlarge"
        assert selector._determine_size_category(1500) == "xlarge"
        assert selector._determine_size_category(1999) == "xlarge"

    def test_huge_file_category(self):
        """2000-5000行的文件应该归类为huge"""
        selector = AdaptiveSymbolSelector()

        assert selector._determine_size_category(2000) == "huge"
        assert selector._determine_size_category(3500) == "huge"
        assert selector._determine_size_category(4999) == "huge"

    def test_mega_file_category(self):
        """>=5000行的文件应该归类为mega"""
        selector = AdaptiveSymbolSelector()

        assert selector._determine_size_category(5000) == "mega"
        assert selector._determine_size_category(8891) == "mega"  # PHP测试文件
        assert selector._determine_size_category(100000) == "mega"


class TestConstraintApplication:
    """Test constraint application logic."""

    def test_apply_constraints_respects_min(self):
        """应该尊重min_symbols约束"""
        config = AdaptiveSymbolsConfig(min_symbols=10, max_symbols=200)
        selector = AdaptiveSymbolSelector(config)

        # 小于min的值应该被提升到min
        assert selector._apply_constraints(5, 100) == 10

    def test_apply_constraints_respects_max(self):
        """应该尊重max_symbols约束"""
        config = AdaptiveSymbolsConfig(min_symbols=5, max_symbols=100)
        selector = AdaptiveSymbolSelector(config)

        # 大于max的值应该被限制到max
        assert selector._apply_constraints(150, 200) == 100

    def test_apply_constraints_respects_total_symbols(self):
        """不应该超过实际符号数量"""
        selector = AdaptiveSymbolSelector()

        # 即使配置的limit是50，但只有30个符号，应该返回30
        assert selector._apply_constraints(50, 30) == 30

    def test_apply_constraints_doesnt_affect_valid_values(self):
        """在有效范围内的值不应该被修改"""
        config = AdaptiveSymbolsConfig(min_symbols=5, max_symbols=200)
        selector = AdaptiveSymbolSelector(config)

        assert selector._apply_constraints(30, 100) == 30
        assert selector._apply_constraints(80, 100) == 80


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_zero_lines_file(self):
        """0行文件应该返回最小符号数"""
        selector = AdaptiveSymbolSelector()
        limit = selector.calculate_limit(0, 5)

        assert limit == 5  # min_symbols

    def test_one_line_file(self):
        """单行文件应该正常处理"""
        selector = AdaptiveSymbolSelector()
        limit = selector.calculate_limit(1, 1)

        assert limit == 1

    def test_extremely_large_file(self):
        """超大文件（100万行）应该返回max_symbols"""
        config = AdaptiveSymbolsConfig(max_symbols=150)
        selector = AdaptiveSymbolSelector(config)
        limit = selector.calculate_limit(1000000, 500)

        assert limit == 150

    def test_total_symbols_less_than_limit(self):
        """符号数少于配置的limit时，应该返回实际符号数"""
        selector = AdaptiveSymbolSelector()
        # 大文件(5000行)通常limit=120，但只有10个符号
        limit = selector.calculate_limit(5000, 10)

        assert limit == 10


class TestRealWorldScenarios:
    """Test with real-world PHP project file sizes."""

    def test_php_8891_lines_file(self):
        """8891行的PHP文件应该显示120个符号"""
        selector = AdaptiveSymbolSelector()
        limit = selector.calculate_limit(8891, 57)

        # mega类别，limit应该是150，但只有57个符号
        assert limit == 57

    def test_php_8891_lines_many_symbols(self):
        """8891行的PHP文件有200个符号时"""
        selector = AdaptiveSymbolSelector()
        limit = selector.calculate_limit(8891, 200)

        # mega类别，limit=150，符号有200个
        assert limit == 150  # 应该返回配置的mega limit

    def test_php_7924_lines_file(self):
        """7924行的文件应该显示120个符号"""
        selector = AdaptiveSymbolSelector()
        limit = selector.calculate_limit(7924, 65)

        # mega类别(>5000)，但只有65个符号
        assert limit == 65

    def test_php_3521_lines_file(self):
        """3521行的文件应该显示50个符号"""
        selector = AdaptiveSymbolSelector()
        limit = selector.calculate_limit(3521, 17)

        # huge类别(2000-5000)，limit=120，但只有17个符号
        assert limit == 17

    def test_php_500_lines_file(self):
        """500行的文件应该显示50个符号"""
        selector = AdaptiveSymbolSelector()
        limit = selector.calculate_limit(500, 80)

        # large类别，limit=50
        assert limit == 50


class TestCustomConfiguration:
    """Test selector with custom configurations."""

    def test_custom_thresholds(self):
        """自定义阈值应该影响分类"""
        config = AdaptiveSymbolsConfig(
            thresholds={
                "tiny": 50,  # 缩小tiny范围
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
        )
        selector = AdaptiveSymbolSelector(config)

        # 75行在默认配置下是tiny，在自定义配置下是small
        limit = selector.calculate_limit(75, 100)
        assert limit == 12  # small的limit

    def test_custom_limits(self):
        """自定义limits应该影响返回值"""
        config = AdaptiveSymbolsConfig(
            limits={
                "tiny": 5,
                "small": 10,
                "medium": 20,
                "large": 35,
                "xlarge": 55,
                "huge": 90,
                "mega": 110,
            }
        )
        selector = AdaptiveSymbolSelector(config)

        # 500行是large，自定义limit=35
        limit = selector.calculate_limit(500, 100)
        assert limit == 35


class TestConsistency:
    """Test consistency and determinism."""

    def test_same_input_same_output(self):
        """相同输入应该产生相同输出"""
        selector = AdaptiveSymbolSelector()

        limit1 = selector.calculate_limit(1000, 50)
        limit2 = selector.calculate_limit(1000, 50)
        limit3 = selector.calculate_limit(1000, 50)

        assert limit1 == limit2 == limit3

    def test_different_selectors_same_result(self):
        """不同selector实例应该产生相同结果"""
        selector1 = AdaptiveSymbolSelector()
        selector2 = AdaptiveSymbolSelector()

        limit1 = selector1.calculate_limit(2000, 80)
        limit2 = selector2.calculate_limit(2000, 80)

        assert limit1 == limit2
