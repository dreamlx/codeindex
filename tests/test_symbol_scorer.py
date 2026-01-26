"""Tests for symbol importance scorer."""

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
