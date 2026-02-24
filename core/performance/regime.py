"""
ATS Core — Regime Classification

Classifies market regimes based on volatility (Bollinger Band width)
and trend strength (ADX). Used to contextualize every trade and track
performance by market condition.

No Freqtrade imports permitted in this file.
"""

import numpy as np
from typing import Optional


def classify_volatility(
    bb_width: float,
    bb_width_history: list[float],
    low_percentile: float = 25.0,
    high_percentile: float = 75.0,
) -> str:
    """
    Classify volatility regime based on current BB width relative to history.

    Args:
        bb_width: Current Bollinger Band width value.
        bb_width_history: Recent BB width values for percentile calculation.
            Should contain at least 20 values for meaningful percentiles.
        low_percentile: Percentile below which volatility is "low" (default 25).
        high_percentile: Percentile above which volatility is "high" (default 75).

    Returns:
        "low", "medium", or "high"
    """
    if not bb_width_history or len(bb_width_history) < 2:
        return "unknown"

    low_threshold = float(np.percentile(bb_width_history, low_percentile))
    high_threshold = float(np.percentile(bb_width_history, high_percentile))

    if bb_width < low_threshold:
        return "low"
    elif bb_width > high_threshold:
        return "high"
    else:
        return "medium"


def classify_trend(adx: float) -> str:
    """
    Classify trend regime based on ADX value.

    ADX thresholds (standard interpretation):
        < 20: No meaningful trend (ranging market)
        20-30: Weak/emerging trend
        >= 30: Strong trend

    Args:
        adx: Current ADX value (0-100).

    Returns:
        "ranging", "weak_trend", or "strong_trend"
    """
    if adx is None or np.isnan(adx):
        return "unknown"

    if adx < 20:
        return "ranging"
    elif adx < 30:
        return "weak_trend"
    else:
        return "strong_trend"


def classify_regime(
    bb_width: float,
    bb_width_history: list[float],
    adx: float,
) -> dict:
    """
    Full regime classification combining volatility and trend.

    Args:
        bb_width: Current Bollinger Band width.
        bb_width_history: Recent BB width values for context.
        adx: Current ADX value.

    Returns:
        Dict with keys: volatility, trend, combined
        Example: {"volatility": "high", "trend": "strong_trend",
                  "combined": "high_strong_trend"}
    """
    vol = classify_volatility(bb_width, bb_width_history)
    trend = classify_trend(adx)
    combined = f"{vol}_{trend}"

    return {
        "volatility": vol,
        "trend": trend,
        "combined": combined,
    }
