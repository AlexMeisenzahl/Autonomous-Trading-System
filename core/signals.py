"""
ATS Core — Signal Generation Logic

Generates entry and exit signals from indicator values.
This is the trading "brain" — portable across all execution engines.

No Freqtrade imports permitted in this file.
"""

import pandas as pd
from core.indicators import crossed_above


def check_entry_long(
    rsi: pd.Series,
    tema: pd.Series,
    bb_middle: pd.Series,
    volume: pd.Series,
    rsi_threshold: int = 30,
) -> pd.Series:
    """
    Long entry signal: momentum reversal from oversold with trend confirmation.

    Conditions (ALL must be true on the same candle):
        1. RSI crosses above rsi_threshold (oversold recovery)
        2. TEMA is at or below BB middle band (not overbought)
        3. TEMA is rising (current > previous candle)
        4. Volume is positive (not a dead candle)

    Args:
        rsi: RSI indicator series.
        tema: TEMA indicator series.
        bb_middle: Bollinger Band middle band series.
        volume: Volume series.
        rsi_threshold: RSI level to cross above (default 30).

    Returns:
        Boolean Series — True where entry signal fires.
    """
    return (
        crossed_above(rsi, rsi_threshold)
        & (tema <= bb_middle)
        & (tema > tema.shift(1))
        & (volume > 0)
    )


def check_exit_long(
    rsi: pd.Series,
    tema: pd.Series,
    bb_middle: pd.Series,
    volume: pd.Series,
    rsi_threshold: int = 70,
) -> pd.Series:
    """
    Long exit signal: momentum exhaustion from overbought with trend weakening.

    Conditions (ALL must be true on the same candle):
        1. RSI crosses above rsi_threshold (entering overbought)
        2. TEMA is above BB middle band (extended)
        3. TEMA is falling (current < previous candle)
        4. Volume is positive (not a dead candle)

    Args:
        rsi: RSI indicator series.
        tema: TEMA indicator series.
        bb_middle: Bollinger Band middle band series.
        volume: Volume series.
        rsi_threshold: RSI level to cross above (default 70).

    Returns:
        Boolean Series — True where exit signal fires.
    """
    return (
        crossed_above(rsi, rsi_threshold)
        & (tema > bb_middle)
        & (tema < tema.shift(1))
        & (volume > 0)
    )
