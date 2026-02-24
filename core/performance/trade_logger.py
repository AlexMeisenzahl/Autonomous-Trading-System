"""
ATS Core — Trade Context Logger

Captures indicator values and regime classification at every trade
entry and exit. This is the raw data that feeds performance analysis.

No Freqtrade imports permitted in this file.
"""

import sqlite3
from datetime import datetime
from typing import Optional

from core.performance.database import get_connection


class TradeLogger:
    """
    Logs trade context (indicators + regime) to the performance database.

    Usage:
        logger = TradeLogger()  # Uses default DB path
        logger.log_entry(trade_id="1", pair="BTC/USDT", ...)
        logger.log_exit(trade_id="1", ...)
    """

    def __init__(self, db_path: str = None):
        """
        Args:
            db_path: Path to performance SQLite database.
                     Defaults to ATS_ROOT/data/performance.db
        """
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = get_connection(self._db_path)
        return self._conn

    def log_entry(
        self,
        trade_id: str,
        pair: str,
        strategy: str,
        entry_time: str,
        entry_price: float,
        indicators: dict,
        regime: dict,
    ) -> int:
        """
        Log trade entry context.

        Args:
            trade_id: Unique trade identifier (from execution engine).
            pair: Trading pair (e.g., "BTC/USDT").
            strategy: Strategy name (e.g., "momentum_rsi_bb").
            entry_time: ISO format timestamp.
            entry_price: Entry price.
            indicators: Dict with keys: rsi, tema, bb_percent, bb_width, adx
            regime: Dict from classify_regime(): volatility, trend, combined

        Returns:
            Database row ID of the inserted record.
        """
        conn = self._get_conn()
        cursor = conn.execute(
            """
            INSERT INTO trade_log (
                trade_id, pair, strategy,
                entry_time, entry_price,
                entry_rsi, entry_tema, entry_bb_percent, entry_bb_width, entry_adx,
                entry_volatility_regime, entry_trend_regime, entry_regime
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(trade_id),
                pair,
                strategy,
                entry_time,
                entry_price,
                indicators.get("rsi"),
                indicators.get("tema"),
                indicators.get("bb_percent"),
                indicators.get("bb_width"),
                indicators.get("adx"),
                regime.get("volatility"),
                regime.get("trend"),
                regime.get("combined"),
            ),
        )
        conn.commit()
        return cursor.lastrowid

    def log_exit(
        self,
        trade_id: str,
        exit_time: str,
        exit_price: float,
        exit_reason: str,
        indicators: dict,
        regime: dict,
        entry_price: float,
        duration_minutes: float,
    ) -> bool:
        """
        Log trade exit context and compute performance metrics.

        Args:
            trade_id: Trade identifier (must match a previous log_entry).
            exit_time: ISO format timestamp.
            exit_price: Exit price.
            exit_reason: Why the trade exited (roi/stoploss/signal/force_exit).
            indicators: Dict with keys: rsi, tema, bb_percent, bb_width, adx
            regime: Dict from classify_regime(): volatility, trend, combined
            entry_price: Original entry price (for P&L calculation).
            duration_minutes: How long the trade was open.

        Returns:
            True if the trade was found and updated, False otherwise.
        """
        conn = self._get_conn()

        # Calculate P&L
        pnl_absolute = exit_price - entry_price
        pnl_percent = (pnl_absolute / entry_price) * 100 if entry_price else 0

        # Check if regime changed
        cursor = conn.execute(
            "SELECT entry_regime FROM trade_log WHERE trade_id = ? ORDER BY id DESC LIMIT 1",
            (str(trade_id),),
        )
        row = cursor.fetchone()
        if row is None:
            return False

        regime_changed = 1 if row["entry_regime"] != regime.get("combined") else 0

        conn.execute(
            """
            UPDATE trade_log SET
                exit_time = ?,
                exit_price = ?,
                exit_reason = ?,
                exit_rsi = ?,
                exit_tema = ?,
                exit_bb_percent = ?,
                exit_bb_width = ?,
                exit_adx = ?,
                exit_volatility_regime = ?,
                exit_trend_regime = ?,
                exit_regime = ?,
                pnl_absolute = ?,
                pnl_percent = ?,
                duration_minutes = ?,
                regime_changed = ?
            WHERE trade_id = ? AND exit_time IS NULL
            """,
            (
                exit_time,
                exit_price,
                exit_reason,
                indicators.get("rsi"),
                indicators.get("tema"),
                indicators.get("bb_percent"),
                indicators.get("bb_width"),
                indicators.get("adx"),
                regime.get("volatility"),
                regime.get("trend"),
                regime.get("combined"),
                pnl_absolute,
                pnl_percent,
                duration_minutes,
                regime_changed,
                str(trade_id),
            ),
        )
        conn.commit()
        return True

    def log_regime_snapshot(
        self,
        pair: str,
        timestamp: str,
        regime: dict,
        indicators: dict,
    ) -> None:
        """
        Log a periodic regime snapshot (independent of trades).

        Args:
            pair: Trading pair.
            timestamp: ISO format timestamp.
            regime: Dict from classify_regime().
            indicators: Dict with bb_width, adx, rsi.
        """
        conn = self._get_conn()
        conn.execute(
            """
            INSERT INTO regime_snapshots (
                timestamp, pair, volatility_regime, trend_regime, regime,
                bb_width, adx, rsi
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                pair,
                regime.get("volatility"),
                regime.get("trend"),
                regime.get("combined"),
                indicators.get("bb_width"),
                indicators.get("adx"),
                indicators.get("rsi"),
            ),
        )
        conn.commit()

    def find_open_trade(self, pair: str) -> Optional[str]:
        """
        Find the most recent open trade (no exit logged) for a pair.

        Args:
            pair: Trading pair to search for.

        Returns:
            trade_id if found, None otherwise.
        """
        conn = self._get_conn()
        row = conn.execute(
            """
            SELECT trade_id FROM trade_log
            WHERE pair = ? AND exit_time IS NULL
            ORDER BY entry_time DESC LIMIT 1
            """,
            (pair,),
        ).fetchone()
        return row["trade_id"] if row else None

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
