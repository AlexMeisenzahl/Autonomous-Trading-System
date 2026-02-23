"""
ATS Core — Technical Indicator Functions

Pure mathematical indicator calculations with zero execution-engine dependency.
These functions accept pandas Series/DataFrames and return pandas Series.

Dependencies: pandas, ta-lib (via talib)
No Freqtrade imports permitted in this file.
"""

import pandas as pd
import numpy as np
import talib


# ---------------------------------------------------------------------------
# Momentum Indicators
# ---------------------------------------------------------------------------

def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index.

    Args:
        close: Series of closing prices.
        period: RSI lookback period (default 14, matches ta-lib default).

    Returns:
        Series of RSI values (0-100).
    """
    return pd.Series(talib.RSI(close.values, timeperiod=period), index=close.index)


# ---------------------------------------------------------------------------
# Overlap / Moving Average Indicators
# ---------------------------------------------------------------------------

def tema(close: pd.Series, period: int = 9) -> pd.Series:
    """
    Triple Exponential Moving Average.

    Args:
        close: Series of closing prices.
        period: TEMA period (default 9, matches AlexStrategy).

    Returns:
        Series of TEMA values.
    """
    return pd.Series(talib.TEMA(close.values, timeperiod=period), index=close.index)


def bollinger_bands(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    window: int = 20,
    stds: float = 2.0,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands calculated on typical price, matching qtpylib implementation.

    IMPORTANT: AlexStrategy uses qtpylib.typical_price as input to BB,
    not raw close. This function replicates that behavior exactly.

    Typical price = (high + low + close) / 3
    Middle band = SMA(typical_price, window)
    Upper band = middle + stds * rolling_std(typical_price, window)
    Lower band = middle - stds * rolling_std(typical_price, window)

    Args:
        high: Series of high prices.
        low: Series of low prices.
        close: Series of closing prices.
        window: SMA window (default 20).
        stds: Standard deviation multiplier (default 2.0).

    Returns:
        Tuple of (upper_band, middle_band, lower_band) as Series.
    """
    typical = (high + low + close) / 3.0

    mid = typical.rolling(window=window, min_periods=window).mean()
    std = typical.rolling(window=window, min_periods=window).std()

    upper = mid + (stds * std)
    lower = mid - (stds * std)

    return upper, mid, lower


# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def crossed_above(series: pd.Series, threshold) -> pd.Series:
    """
    Detect when a series crosses above a threshold value or another series.

    Replicates qtpylib.crossed_above behavior used in AlexStrategy entry/exit
    conditions.

    Args:
        series: The indicator series to check.
        threshold: A scalar value or another Series to compare against.

    Returns:
        Boolean Series — True on the candle where the crossover occurs.
    """
    if isinstance(threshold, (int, float, np.integer, np.floating)):
        return (series > threshold) & (series.shift(1) <= threshold)
    else:
        # Series vs Series comparison
        return (series > threshold) & (series.shift(1) <= threshold.shift(1))
