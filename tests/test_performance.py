"""
Tests for core.performance.trade_logger and core.performance.analyzer modules.

Uses in-memory SQLite database for test isolation.
"""

import pytest
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.performance.trade_logger import TradeLogger
from core.performance.analyzer import PerformanceAnalyzer


@pytest.fixture
def db_path():
    """Create a temporary database for each test."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield path
    os.unlink(path)


@pytest.fixture
def logger(db_path):
    tl = TradeLogger(db_path=db_path)
    yield tl
    tl.close()


@pytest.fixture
def analyzer(db_path):
    a = PerformanceAnalyzer(db_path=db_path)
    yield a
    a.close()


# ---------------------------------------------------------------------------
# Sample data helpers
# ---------------------------------------------------------------------------

def sample_indicators(rsi=45, tema=100, bb_percent=0.5, bb_width=0.04, adx=25):
    return {
        "rsi": rsi,
        "tema": tema,
        "bb_percent": bb_percent,
        "bb_width": bb_width,
        "adx": adx,
    }


def sample_regime(volatility="medium", trend="weak_trend"):
    return {
        "volatility": volatility,
        "trend": trend,
        "combined": f"{volatility}_{trend}",
    }


def log_complete_trade(
    logger, trade_id, pair="BTC/USDT", strategy="momentum_rsi_bb",
    entry_price=100.0, exit_price=103.0, exit_reason="roi",
    entry_regime=None, exit_regime=None,
):
    """Helper to log a full entry+exit trade."""
    entry_regime = entry_regime or sample_regime()
    exit_regime = exit_regime or sample_regime()

    logger.log_entry(
        trade_id=trade_id,
        pair=pair,
        strategy=strategy,
        entry_time="2026-02-23T12:00:00",
        entry_price=entry_price,
        indicators=sample_indicators(),
        regime=entry_regime,
    )
    logger.log_exit(
        trade_id=trade_id,
        exit_time="2026-02-23T13:00:00",
        exit_price=exit_price,
        exit_reason=exit_reason,
        indicators=sample_indicators(rsi=65),
        regime=exit_regime,
        entry_price=entry_price,
        duration_minutes=60.0,
    )


# ---------------------------------------------------------------------------
# TradeLogger Tests
# ---------------------------------------------------------------------------

class TestTradeLogger:
    def test_log_entry_returns_row_id(self, logger):
        row_id = logger.log_entry(
            trade_id="1", pair="BTC/USDT", strategy="momentum_rsi_bb",
            entry_time="2026-02-23T12:00:00", entry_price=50000.0,
            indicators=sample_indicators(),
            regime=sample_regime(),
        )
        assert row_id is not None
        assert row_id > 0

    def test_log_exit_updates_trade(self, logger):
        logger.log_entry(
            trade_id="1", pair="BTC/USDT", strategy="momentum_rsi_bb",
            entry_time="2026-02-23T12:00:00", entry_price=50000.0,
            indicators=sample_indicators(),
            regime=sample_regime(),
        )
        result = logger.log_exit(
            trade_id="1",
            exit_time="2026-02-23T13:00:00",
            exit_price=51000.0,
            exit_reason="roi",
            indicators=sample_indicators(rsi=72),
            regime=sample_regime(),
            entry_price=50000.0,
            duration_minutes=60.0,
        )
        assert result is True

    def test_log_exit_nonexistent_trade_returns_false(self, logger):
        result = logger.log_exit(
            trade_id="999",
            exit_time="2026-02-23T13:00:00",
            exit_price=51000.0,
            exit_reason="roi",
            indicators=sample_indicators(),
            regime=sample_regime(),
            entry_price=50000.0,
            duration_minutes=60.0,
        )
        assert result is False

    def test_pnl_calculated_correctly(self, logger, db_path):
        logger.log_entry(
            trade_id="1", pair="BTC/USDT", strategy="momentum_rsi_bb",
            entry_time="2026-02-23T12:00:00", entry_price=100.0,
            indicators=sample_indicators(),
            regime=sample_regime(),
        )
        logger.log_exit(
            trade_id="1",
            exit_time="2026-02-23T13:00:00",
            exit_price=105.0,
            exit_reason="roi",
            indicators=sample_indicators(),
            regime=sample_regime(),
            entry_price=100.0,
            duration_minutes=60.0,
        )

        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM trade_log WHERE trade_id = '1'").fetchone()
        assert row["pnl_absolute"] == 5.0
        assert row["pnl_percent"] == 5.0
        conn.close()

    def test_regime_change_detected(self, logger, db_path):
        logger.log_entry(
            trade_id="1", pair="BTC/USDT", strategy="momentum_rsi_bb",
            entry_time="2026-02-23T12:00:00", entry_price=100.0,
            indicators=sample_indicators(),
            regime=sample_regime("low", "ranging"),
        )
        logger.log_exit(
            trade_id="1",
            exit_time="2026-02-23T13:00:00",
            exit_price=103.0,
            exit_reason="roi",
            indicators=sample_indicators(),
            regime=sample_regime("high", "strong_trend"),  # Different regime
            entry_price=100.0,
            duration_minutes=60.0,
        )

        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM trade_log WHERE trade_id = '1'").fetchone()
        assert row["regime_changed"] == 1
        conn.close()

    def test_log_regime_snapshot(self, logger, db_path):
        logger.log_regime_snapshot(
            pair="BTC/USDT",
            timestamp="2026-02-23T12:00:00",
            regime=sample_regime(),
            indicators=sample_indicators(),
        )
        import sqlite3
        conn = sqlite3.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM regime_snapshots").fetchone()[0]
        assert count == 1
        conn.close()


# ---------------------------------------------------------------------------
# PerformanceAnalyzer Tests
# ---------------------------------------------------------------------------

class TestPerformanceAnalyzer:
    def test_summary_no_trades(self, analyzer):
        result = analyzer.summary()
        assert result["total_trades"] == 0

    def test_summary_with_trades(self, logger, analyzer):
        # 3 winning trades, 1 losing trade
        log_complete_trade(logger, "1", entry_price=100, exit_price=104)  # +4%
        log_complete_trade(logger, "2", entry_price=100, exit_price=102)  # +2%
        log_complete_trade(logger, "3", entry_price=100, exit_price=101)  # +1%
        log_complete_trade(logger, "4", entry_price=100, exit_price=95)   # -5%

        result = analyzer.summary()
        assert result["total_trades"] == 4
        assert result["wins"] == 3
        assert result["losses"] == 1
        assert result["win_rate"] == 0.75

    def test_summary_filter_by_strategy(self, logger, analyzer):
        log_complete_trade(logger, "1", strategy="strat_a", exit_price=105)
        log_complete_trade(logger, "2", strategy="strat_b", exit_price=95)

        result = analyzer.summary(strategy="strat_a")
        assert result["total_trades"] == 1
        assert result["wins"] == 1

    def test_by_regime(self, logger, analyzer):
        log_complete_trade(
            logger, "1", exit_price=105,
            entry_regime=sample_regime("high", "strong_trend"),
        )
        log_complete_trade(
            logger, "2", exit_price=95,
            entry_regime=sample_regime("low", "ranging"),
        )

        result = analyzer.by_regime()
        assert "high_strong_trend" in result
        assert "low_ranging" in result
        assert result["high_strong_trend"]["wins"] == 1
        assert result["low_ranging"]["losses"] == 1

    def test_decay_not_enough_data(self, logger, analyzer):
        log_complete_trade(logger, "1")
        result = analyzer.detect_decay("momentum_rsi_bb", recent_window=20)
        assert result["has_enough_data"] is False

    def test_decay_no_decay(self, logger, analyzer):
        # 70 consistently profitable trades
        for i in range(70):
            log_complete_trade(logger, str(i), exit_price=103)

        result = analyzer.detect_decay(
            "momentum_rsi_bb", recent_window=20, baseline_window=50
        )
        assert result["has_enough_data"] is True
        assert result["decay_detected"] is False

    def test_recent_trades(self, logger, analyzer):
        log_complete_trade(logger, "1")
        log_complete_trade(logger, "2")
        log_complete_trade(logger, "3")

        result = analyzer.recent_trades(n=2)
        assert len(result) == 2


class TestNoFreqtradeDependency:
    def test_no_freqtrade_in_trade_logger(self):
        import core.performance.trade_logger as mod
        with open(mod.__file__) as f:
            source = f.read()
        assert "import freqtrade" not in source
        assert "from freqtrade" not in source

    def test_no_freqtrade_in_analyzer(self):
        import core.performance.analyzer as mod
        with open(mod.__file__) as f:
            source = f.read()
        assert "import freqtrade" not in source
        assert "from freqtrade" not in source

    def test_no_freqtrade_in_database(self):
        import core.performance.database as mod
        with open(mod.__file__) as f:
            source = f.read()
        assert "import freqtrade" not in source
        assert "from freqtrade" not in source
