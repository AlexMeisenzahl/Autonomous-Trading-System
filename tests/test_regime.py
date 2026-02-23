"""
Tests for core.performance.regime module.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.performance.regime import classify_volatility, classify_trend, classify_regime


class TestClassifyVolatility:
    def test_low_volatility(self):
        history = list(range(10, 110))  # 10 to 109
        result = classify_volatility(15, history)  # Below 25th percentile
        assert result == "low"

    def test_high_volatility(self):
        history = list(range(10, 110))
        result = classify_volatility(95, history)  # Above 75th percentile
        assert result == "high"

    def test_medium_volatility(self):
        history = list(range(10, 110))
        result = classify_volatility(55, history)  # Between 25th and 75th
        assert result == "medium"

    def test_empty_history_returns_unknown(self):
        result = classify_volatility(50, [])
        assert result == "unknown"

    def test_single_value_history_returns_unknown(self):
        result = classify_volatility(50, [50])
        assert result == "unknown"


class TestClassifyTrend:
    def test_ranging(self):
        assert classify_trend(15) == "ranging"

    def test_weak_trend(self):
        assert classify_trend(25) == "weak_trend"

    def test_strong_trend(self):
        assert classify_trend(35) == "strong_trend"

    def test_boundary_20(self):
        assert classify_trend(20) == "weak_trend"

    def test_boundary_30(self):
        assert classify_trend(30) == "strong_trend"

    def test_nan_returns_unknown(self):
        import numpy as np
        assert classify_trend(np.nan) == "unknown"

    def test_none_returns_unknown(self):
        assert classify_trend(None) == "unknown"


class TestClassifyRegime:
    def test_combined_label(self):
        history = list(range(10, 110))
        result = classify_regime(bb_width=95, bb_width_history=history, adx=35)
        assert result["volatility"] == "high"
        assert result["trend"] == "strong_trend"
        assert result["combined"] == "high_strong_trend"

    def test_low_ranging(self):
        history = list(range(10, 110))
        result = classify_regime(bb_width=15, bb_width_history=history, adx=10)
        assert result["combined"] == "low_ranging"

    def test_returns_dict_with_all_keys(self):
        history = list(range(10, 110))
        result = classify_regime(bb_width=50, bb_width_history=history, adx=25)
        assert "volatility" in result
        assert "trend" in result
        assert "combined" in result


class TestNoFreqtradeDependency:
    def test_no_freqtrade_in_regime(self):
        import core.performance.regime as mod
        with open(mod.__file__) as f:
            source = f.read()
        assert "import freqtrade" not in source
        assert "from freqtrade" not in source
