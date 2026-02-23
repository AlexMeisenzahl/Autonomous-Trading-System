"""
Tests for core.signals module.

Verifies that entry and exit signals fire under correct conditions
and stay silent when conditions are not met.
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.signals import check_entry_long, check_exit_long


# ---------------------------------------------------------------------------
# Helper: build controlled indicator data
# ---------------------------------------------------------------------------

def make_signal_data(
    rsi_values: list,
    tema_values: list,
    bb_mid_values: list,
    volume_values: list = None,
) -> tuple:
    """Build aligned Series from lists for signal testing."""
    n = len(rsi_values)
    if volume_values is None:
        volume_values = [1000] * n  # Default: positive volume
    return (
        pd.Series(rsi_values, dtype=float),
        pd.Series(tema_values, dtype=float),
        pd.Series(bb_mid_values, dtype=float),
        pd.Series(volume_values, dtype=float),
    )


# ---------------------------------------------------------------------------
# Entry Signal Tests
# ---------------------------------------------------------------------------

class TestEntrySignal:
    def test_fires_on_correct_conditions(self):
        """Entry fires when RSI crosses above 30, TEMA <= BB mid, TEMA rising, vol > 0."""
        rsi_vals, tema_vals, bb_mid, volume = make_signal_data(
            rsi_values=[25, 28, 32, 35],     # crosses above 30 at index 2
            tema_values=[90, 92, 94, 96],     # rising
            bb_mid_values=[100, 100, 100, 100],  # tema <= bb_mid
            volume_values=[1000, 1000, 1000, 1000],
        )
        result = check_entry_long(rsi_vals, tema_vals, bb_mid, volume, rsi_threshold=30)
        assert result.iloc[2] == True

    def test_no_fire_when_rsi_doesnt_cross(self):
        """No entry if RSI is already above threshold (no cross)."""
        rsi_vals, tema_vals, bb_mid, volume = make_signal_data(
            rsi_values=[35, 36, 37, 38],     # always above 30, no cross
            tema_values=[90, 92, 94, 96],
            bb_mid_values=[100, 100, 100, 100],
        )
        result = check_entry_long(rsi_vals, tema_vals, bb_mid, volume, rsi_threshold=30)
        assert result.sum() == 0

    def test_no_fire_when_tema_above_bb(self):
        """No entry if TEMA is above BB middle."""
        rsi_vals, tema_vals, bb_mid, volume = make_signal_data(
            rsi_values=[25, 28, 32, 35],     # crosses above 30
            tema_values=[105, 106, 107, 108],  # ABOVE bb_mid → blocks entry
            bb_mid_values=[100, 100, 100, 100],
        )
        result = check_entry_long(rsi_vals, tema_vals, bb_mid, volume, rsi_threshold=30)
        assert result.sum() == 0

    def test_no_fire_when_tema_falling(self):
        """No entry if TEMA is falling."""
        rsi_vals, tema_vals, bb_mid, volume = make_signal_data(
            rsi_values=[25, 28, 32, 35],
            tema_values=[98, 96, 94, 92],     # falling → blocks entry
            bb_mid_values=[100, 100, 100, 100],
        )
        result = check_entry_long(rsi_vals, tema_vals, bb_mid, volume, rsi_threshold=30)
        assert result.sum() == 0

    def test_no_fire_on_zero_volume(self):
        """No entry if volume is zero."""
        rsi_vals, tema_vals, bb_mid, volume = make_signal_data(
            rsi_values=[25, 28, 32, 35],
            tema_values=[90, 92, 94, 96],
            bb_mid_values=[100, 100, 100, 100],
            volume_values=[1000, 1000, 0, 1000],  # zero at index 2
        )
        result = check_entry_long(rsi_vals, tema_vals, bb_mid, volume, rsi_threshold=30)
        assert result.iloc[2] == False


# ---------------------------------------------------------------------------
# Exit Signal Tests
# ---------------------------------------------------------------------------

class TestExitSignal:
    def test_fires_on_correct_conditions(self):
        """Exit fires when RSI crosses above 70, TEMA > BB mid, TEMA falling, vol > 0."""
        rsi_vals, tema_vals, bb_mid, volume = make_signal_data(
            rsi_values=[65, 68, 72, 75],     # crosses above 70 at index 2
            tema_values=[108, 106, 104, 102],  # falling
            bb_mid_values=[100, 100, 100, 100],  # tema > bb_mid
            volume_values=[1000, 1000, 1000, 1000],
        )
        result = check_exit_long(rsi_vals, tema_vals, bb_mid, volume, rsi_threshold=70)
        assert result.iloc[2] == True

    def test_no_fire_when_tema_below_bb(self):
        """No exit if TEMA is below BB middle."""
        rsi_vals, tema_vals, bb_mid, volume = make_signal_data(
            rsi_values=[65, 68, 72, 75],
            tema_values=[90, 88, 86, 84],     # below bb_mid → blocks exit
            bb_mid_values=[100, 100, 100, 100],
        )
        result = check_exit_long(rsi_vals, tema_vals, bb_mid, volume, rsi_threshold=70)
        assert result.sum() == 0

    def test_no_fire_when_tema_rising(self):
        """No exit if TEMA is rising (trend still strong)."""
        rsi_vals, tema_vals, bb_mid, volume = make_signal_data(
            rsi_values=[65, 68, 72, 75],
            tema_values=[102, 104, 106, 108],  # rising → blocks exit
            bb_mid_values=[100, 100, 100, 100],
        )
        result = check_exit_long(rsi_vals, tema_vals, bb_mid, volume, rsi_threshold=70)
        assert result.sum() == 0


# ---------------------------------------------------------------------------
# Integration: no Freqtrade imports
# ---------------------------------------------------------------------------

class TestNoFreqtradeDependency:
    def test_no_freqtrade_in_signals(self):
        """Verify signals.py has no Freqtrade imports."""
        import core.signals as mod
        with open(mod.__file__) as f:
            source = f.read()
        assert "import freqtrade" not in source
        assert "from freqtrade" not in source
        assert "import qtpylib" not in source
        assert "from technical" not in source
