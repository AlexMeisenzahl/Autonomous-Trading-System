"""
ATS Core — Strategy Registry

Central registry of strategy configurations. Each strategy defines its
indicator parameters, signal thresholds, and risk settings in one place.

These definitions are consumed by execution-engine adapters (Freqtrade,
Polymarket, backtester, etc.) — the adapters read from here rather than
hardcoding parameters.

No Freqtrade imports permitted in this file.
"""

STRATEGIES = {
    "momentum_rsi_bb": {
        "description": (
            "RSI + TEMA + Bollinger Bands momentum strategy. "
            "Enters on oversold RSI recovery with TEMA confirmation below BB middle. "
            "Exits on overbought RSI with TEMA weakening above BB middle."
        ),
        "version": "1.0",
        "timeframe": "5m",
        "startup_candle_count": 30,
        "indicators": {
            "rsi_period": 14,
            "tema_period": 9,
            "bb_window": 20,
            "bb_stds": 2.0,
        },
        "entry": {
            "rsi_threshold": 30,
        },
        "exit": {
            "rsi_threshold": 70,
        },
        "risk": {
            "stoploss": -0.10,
            "trailing_stop": False,
            "minimal_roi": {
                "0": 0.04,
                "30": 0.02,
                "60": 0.01,
            },
        },
    },
}


def get_strategy(name: str) -> dict:
    """
    Retrieve a strategy configuration by name.

    Args:
        name: Strategy identifier (must exist in STRATEGIES).

    Returns:
        Strategy configuration dict.

    Raises:
        KeyError: If strategy name not found.
    """
    if name not in STRATEGIES:
        available = ", ".join(STRATEGIES.keys())
        raise KeyError(
            f"Strategy '{name}' not found. Available: {available}"
        )
    return STRATEGIES[name]


def list_strategies() -> list[str]:
    """Return list of all registered strategy names."""
    return list(STRATEGIES.keys())
