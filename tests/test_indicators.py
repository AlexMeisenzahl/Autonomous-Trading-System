"""
Tests for core.indicators module.

Verifies that indicator calculations produce correct output shapes,
ranges, and behaviors without any Freqtrade dependency.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.indicators import rsi, tema, bollinger_bands, crossed_above


# ---------------------------------------------------------------------------
# Fixtures — synthetic OHLCV data
# ---------------------------------------------------------------------------

def make_ohlcv(n: int = 200, seed: int = 42) -> pd.DataFrame:
    """Generate realistic-ish synthetic OHLCV data."""
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 0.5, n))
    high = close + rng.uniform(0.1, 1.0, n)
    low = close - rng.uniform(0.1, 1.0, n)
    open_ = close + rng.normal(0, 0.3, n)
    volume = rng.uniform(1000, 50000, n)
    return pd.DataFrame({
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
    })


@pytest.fixture
def ohlcv():
    return make_ohlcv()


# ---------------------------------------------------------------------------
# RSI Tests
# ---------------------------------------------------------------------------

class TestRSI:
    def test_output_shape(self, ohlcv):
        result = rsi(ohlcv["close"])
        assert len(result) == len(ohlcv)

    def test_output_range(self, ohlcv):
        result = rsi(ohlcv["close"])
        valid = result.dropna()
        assert valid.min() >= 0
        assert valid.max() <= 100

    def test_returns_series(self, ohlcv):
        result = rsi(ohlcv["close"])
        assert isinstance(result, pd.Series)

    def test_custom_period(self, ohlcv):
        r14 = rsi(ohlcv["close"], period=14)
        r7 = rsi(ohlcv["close"], period=7)
        # Different periods should produce different values
        assert not r14.equals(r7)


# ---------------------------------------------------------------------------
# TEMA Tests
# ---------------------------------------------------------------------------

class TestTEMA:
    def test_output_shape(self, ohlcv):
        result = tema(ohlcv["close"])
        assert len(result) == len(ohlcv)

    def test_returns_series(self, ohlcv):
        result = tema(ohlcv["close"])
        assert isinstance(result, pd.Series)

    def test_tracks_price(self, ohlcv):
        """TEMA should roughly follow close price (high correlation)."""
        result = tema(ohlcv["close"], period=9)
        valid_mask = result.notna() & ohlcv["close"].notna()
        corr = result[valid_mask].corr(ohlcv["close"][valid_mask])
        assert corr > 0.95


# ---------------------------------------------------------------------------
# Bollinger Bands Tests
# ---------------------------------------------------------------------------

class TestBollingerBands:
    def test_output_shapes(self, ohlcv):
        upper, mid, lower = bollinger_bands(
            ohlcv["high"], ohlcv["low"], ohlcv["close"]
        )
        assert len(upper) == len(ohlcv)
        assert len(mid) == len(ohlcv)
        assert len(lower) == len(ohlcv)

    def test_band_ordering(self, ohlcv):
        """Upper > middle > lower everywhere (where defined)."""
        upper, mid, lower = bollinger_bands(
            ohlcv["high"], ohlcv["low"], ohlcv["close"]
        )
        valid = upper.notna() & mid.notna() & lower.notna()
        assert (upper[valid] >= mid[valid]).all()
        assert (mid[valid] >= lower[valid]).all()

    def test_uses_typical_price(self, ohlcv):
        """Middle band should be SMA of typical price, not close."""
        upper, mid, lower = bollinger_bands(
            ohlcv["high"], ohlcv["low"], ohlcv["close"], window=20
        )
        typical = (ohlcv["high"] + ohlcv["low"] + ohlcv["close"]) / 3.0
        expected_mid = typical.rolling(window=20, min_periods=20).mean()
        valid = mid.notna() & expected_mid.notna()
        pd.testing.assert_series_equal(
            mid[valid].reset_index(drop=True),
            expected_mid[valid].reset_index(drop=True),
            check_names=False,
        )


# ---------------------------------------------------------------------------
# crossed_above Tests
# ---------------------------------------------------------------------------

class TestCrossedAbove:
    def test_scalar_crossover(self):
        """Detects cross above a scalar threshold."""
        s = pd.Series([25, 28, 31, 35, 29])
        result = crossed_above(s, 30)
        # Index 2: 31 > 30 and 28 <= 30 → True
        assert result.iloc[2] == True
        # Index 3: 35 > 30 but 31 > 30 (already above) → False
        assert result.iloc[3] == False

    def test_no_false_positive_when_already_above(self):
        """No signal if already above threshold."""
        s = pd.Series([32, 33, 34, 35])
        result = crossed_above(s, 30)
        assert result.sum() == 0  # Never crosses, always above

    def test_series_crossover(self):
        """Detects cross above another series."""
        a = pd.Series([10, 20, 30, 25])
        b = pd.Series([15, 25, 20, 30])
        result = crossed_above(a, b)
        # Index 2: 30 > 20 and 20 <= 25 → True
        assert result.iloc[2] == True


# ---------------------------------------------------------------------------
# Integration: no Freqtrade imports
# ---------------------------------------------------------------------------

class TestNoFreqtradeDependency:
    def test_no_freqtrade_in_indicators(self):
        """Verify indicators.py has no Freqtrade imports."""
        import core.indicators as mod
        source_file = mod.__file__
        with open(source_file) as f:
            source = f.read()
        assert "import freqtrade" not in source
        assert "from freqtrade" not in source
        assert "import qtpylib" not in source
        assert "from technical" not in source
