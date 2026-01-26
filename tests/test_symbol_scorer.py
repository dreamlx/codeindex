"""Tests for symbol importance scorer."""

import pytest

from codeindex.parser import Symbol
from codeindex.symbol_scorer import ScoringContext, SymbolImportanceScorer


class TestSymbolScorerBase:
    """测试符号评分器基础功能"""

    def test_scorer_initialization_without_context(self):
        """测试无上下文初始化"""
        scorer = SymbolImportanceScorer()

        assert scorer is not None
        assert scorer.context is not None
        assert scorer.context.framework == "unknown"
        assert scorer.context.file_type == "unknown"

    def test_scorer_initialization_with_context(self):
        """测试带上下文初始化"""
        context = ScoringContext(framework="thinkphp", file_type="controller", total_symbols=100)
        scorer = SymbolImportanceScorer(context)

        assert scorer.context.framework == "thinkphp"
        assert scorer.context.file_type == "controller"
        assert scorer.context.total_symbols == 100

    def test_score_returns_valid_range(self):
        """测试评分在有效范围内 (0-100)"""
        scorer = SymbolImportanceScorer()
        symbol = Symbol(
            name="test_function",
            kind="function",
            signature="def test_function()",
            docstring="",
            line_start=1,
            line_end=10,
        )

        score = scorer.score(symbol)

        assert isinstance(score, float)
        assert 0 <= score <= 100

    def test_score_is_consistent(self):
        """测试相同符号的评分一致性"""
        scorer = SymbolImportanceScorer()
        symbol = Symbol(
            name="process",
            kind="function",
            signature="def process()",
            docstring="Process data",
            line_start=1,
            line_end=50,
        )

        score1 = scorer.score(symbol)
        score2 = scorer.score(symbol)

        assert score1 == score2

    def test_different_symbols_different_scores(self):
        """测试不同符号应该有不同评分"""
        scorer = SymbolImportanceScorer()

        important = Symbol(
            name="pay",
            kind="method",
            signature="public function pay()",
            docstring="Process payment",
            line_start=1,
            line_end=100,
        )

        trivial = Symbol(
            name="getPayType",
            kind="method",
            signature="public function getPayType()",
            docstring="",
            line_start=1,
            line_end=3,
        )

        score_important = scorer.score(important)
        score_trivial = scorer.score(trivial)

        assert score_important > score_trivial


class TestVisibilityScoring:
    """测试可见性评分"""

    @pytest.fixture
    def scorer(self):
        return SymbolImportanceScorer()

    def test_php_public_method_high_score(self, scorer):
        """PHP public 方法获得高分"""
        symbol = Symbol(
            name="createOrder",
            kind="method",
            signature="public function createOrder()",
            docstring="",
            line_start=1,
            line_end=10,
        )
        score = scorer._score_visibility(symbol)
        assert score == 20.0

    def test_php_protected_method_medium_score(self, scorer):
        """PHP protected 方法获得中等分数"""
        symbol = Symbol(
            name="validateData",
            kind="method",
            signature="protected function validateData()",
            docstring="",
            line_start=1,
            line_end=10,
        )
        score = scorer._score_visibility(symbol)
        assert score == 10.0

    def test_php_private_method_low_score(self, scorer):
        """PHP private 方法获得低分"""
        symbol = Symbol(
            name="_log",
            kind="method",
            signature="private function _log()",
            docstring="",
            line_start=1,
            line_end=10,
        )
        score = scorer._score_visibility(symbol)
        assert score == 0.0

    def test_python_public_function_high_score(self, scorer):
        """Python 公共函数获得高分"""
        symbol = Symbol(
            name="process_payment",
            kind="function",
            signature="def process_payment()",
            docstring="",
            line_start=1,
            line_end=10,
        )
        score = scorer._score_visibility(symbol)
        assert score == 15.0

    def test_python_private_function_low_score(self, scorer):
        """Python 私有函数（_前缀）获得低分"""
        symbol = Symbol(
            name="_internal_helper",
            kind="function",
            signature="def _internal_helper()",
            docstring="",
            line_start=1,
            line_end=10,
        )
        score = scorer._score_visibility(symbol)
        assert score == 5.0

    def test_python_magic_method_low_score(self, scorer):
        """Python 魔术方法（__前缀）获得低分"""
        symbol = Symbol(
            name="__init__",
            kind="method",
            signature="def __init__(self)",
            docstring="",
            line_start=1,
            line_end=10,
        )
        score = scorer._score_visibility(symbol)
        assert score == 5.0
