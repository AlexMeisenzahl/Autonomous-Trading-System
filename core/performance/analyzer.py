"""
ATS Core — Performance Analyzer

Computes performance metrics from logged trade data. Provides:
- Overall summary (win rate, expectancy, profit factor)
- Breakdown by regime
- Decay detection (comparing recent vs historical performance)

No Freqtrade imports permitted in this file.
"""

import sqlite3
from typing import Optional

from core.performance.database import get_connection


class PerformanceAnalyzer:
    """
    Analyzes trade performance from the performance database.

    Usage:
        analyzer = PerformanceAnalyzer()
        print(analyzer.summary())
        print(analyzer.by_regime())
        print(analyzer.detect_decay("momentum_rsi_bb"))
    """

    def __init__(self, db_path: str = None):
        self._db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = get_connection(self._db_path)
        return self._conn

    def summary(
        self,
        strategy: str = None,
        regime: str = None,
    ) -> dict:
        """
        Overall performance summary for closed trades.

        Args:
            strategy: Filter by strategy name (optional).
            regime: Filter by entry regime (optional).

        Returns:
            Dict with: total_trades, wins, losses, win_rate, avg_win_pct,
            avg_loss_pct, expectancy_pct, profit_factor, avg_duration_min
        """
        conn = self._get_conn()

        where_clauses = ["exit_time IS NOT NULL"]
        params = []

        if strategy:
            where_clauses.append("strategy = ?")
            params.append(strategy)
        if regime:
            where_clauses.append("entry_regime = ?")
            params.append(regime)

        where = " AND ".join(where_clauses)

        rows = conn.execute(
            f"SELECT pnl_percent, duration_minutes FROM trade_log WHERE {where}",
            params,
        ).fetchall()

        if not rows:
            return {
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "win_rate": 0.0,
                "avg_win_pct": 0.0,
                "avg_loss_pct": 0.0,
                "expectancy_pct": 0.0,
                "profit_factor": 0.0,
                "avg_duration_min": 0.0,
            }

        pnls = [r["pnl_percent"] for r in rows]
        durations = [r["duration_minutes"] for r in rows if r["duration_minutes"] is not None]

        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        total = len(pnls)
        win_count = len(wins)
        loss_count = len(losses)
        win_rate = win_count / total if total > 0 else 0.0

        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0

        # Expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

        # Profit factor = gross_wins / abs(gross_losses)
        gross_wins = sum(wins)
        gross_losses = abs(sum(losses))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float("inf") if gross_wins > 0 else 0.0

        avg_duration = sum(durations) / len(durations) if durations else 0.0

        return {
            "total_trades": total,
            "wins": win_count,
            "losses": loss_count,
            "win_rate": round(win_rate, 4),
            "avg_win_pct": round(avg_win, 4),
            "avg_loss_pct": round(avg_loss, 4),
            "expectancy_pct": round(expectancy, 4),
            "profit_factor": round(profit_factor, 4),
            "avg_duration_min": round(avg_duration, 2),
        }

    def by_regime(self, strategy: str = None) -> dict:
        """
        Performance breakdown by entry regime.

        Args:
            strategy: Filter by strategy name (optional).

        Returns:
            Dict keyed by regime label, each containing a summary dict.
        """
        conn = self._get_conn()

        where_clauses = ["exit_time IS NOT NULL", "entry_regime IS NOT NULL"]
        params = []

        if strategy:
            where_clauses.append("strategy = ?")
            params.append(strategy)

        where = " AND ".join(where_clauses)

        regimes = conn.execute(
            f"SELECT DISTINCT entry_regime FROM trade_log WHERE {where}",
            params,
        ).fetchall()

        result = {}
        for row in regimes:
            regime_name = row["entry_regime"]
            result[regime_name] = self.summary(strategy=strategy, regime=regime_name)

        return result

    def detect_decay(
        self,
        strategy: str,
        recent_window: int = 20,
        baseline_window: int = 50,
    ) -> dict:
        """
        Detect performance decay by comparing recent trades vs baseline.

        Compares the last `recent_window` trades against the preceding
        `baseline_window` trades. If recent performance is significantly
        worse, flags potential decay.

        Args:
            strategy: Strategy name to analyze.
            recent_window: Number of most recent trades to evaluate.
            baseline_window: Number of preceding trades as baseline.

        Returns:
            Dict with: has_enough_data, recent (summary), baseline (summary),
            win_rate_delta, expectancy_delta, decay_detected, recommendation
        """
        conn = self._get_conn()

        rows = conn.execute(
            """
            SELECT pnl_percent, duration_minutes, entry_regime
            FROM trade_log
            WHERE strategy = ? AND exit_time IS NOT NULL
            ORDER BY exit_time DESC
            """,
            (strategy,),
        ).fetchall()

        total_needed = recent_window + baseline_window

        if len(rows) < recent_window:
            return {
                "has_enough_data": False,
                "total_closed_trades": len(rows),
                "needed": total_needed,
                "recommendation": f"Need at least {recent_window} closed trades for analysis.",
            }

        recent_pnls = [r["pnl_percent"] for r in rows[:recent_window]]
        baseline_pnls = [r["pnl_percent"] for r in rows[recent_window:recent_window + baseline_window]]

        if not baseline_pnls:
            return {
                "has_enough_data": False,
                "total_closed_trades": len(rows),
                "needed": total_needed,
                "recommendation": f"Need at least {total_needed} closed trades for decay comparison.",
            }

        recent_summary = self._compute_summary(recent_pnls)
        baseline_summary = self._compute_summary(baseline_pnls)

        wr_delta = recent_summary["win_rate"] - baseline_summary["win_rate"]
        exp_delta = recent_summary["expectancy_pct"] - baseline_summary["expectancy_pct"]

        # Decay heuristic: win rate dropped >15% OR expectancy went negative
        # when baseline was positive
        decay_detected = False
        reasons = []

        if wr_delta < -0.15:
            decay_detected = True
            reasons.append(f"Win rate dropped {abs(wr_delta)*100:.1f}%")

        if baseline_summary["expectancy_pct"] > 0 and recent_summary["expectancy_pct"] < 0:
            decay_detected = True
            reasons.append("Expectancy turned negative")

        if recent_summary["profit_factor"] < 1.0 and baseline_summary["profit_factor"] >= 1.0:
            decay_detected = True
            reasons.append("Profit factor dropped below 1.0")

        if decay_detected:
            recommendation = f"DECAY DETECTED: {'; '.join(reasons)}. Consider reducing position size or pausing strategy."
        else:
            recommendation = "No significant decay detected. Strategy performance is stable."

        return {
            "has_enough_data": True,
            "total_closed_trades": len(rows),
            "recent": recent_summary,
            "baseline": baseline_summary,
            "win_rate_delta": round(wr_delta, 4),
            "expectancy_delta": round(exp_delta, 4),
            "decay_detected": decay_detected,
            "recommendation": recommendation,
        }

    def recent_trades(self, n: int = 20, strategy: str = None) -> list[dict]:
        """
        Retrieve the most recent N closed trades with full context.

        Args:
            n: Number of trades to retrieve.
            strategy: Filter by strategy name (optional).

        Returns:
            List of trade dicts, most recent first.
        """
        conn = self._get_conn()

        where_clauses = ["exit_time IS NOT NULL"]
        params = []

        if strategy:
            where_clauses.append("strategy = ?")
            params.append(strategy)

        where = " AND ".join(where_clauses)
        params.append(n)

        rows = conn.execute(
            f"SELECT * FROM trade_log WHERE {where} ORDER BY exit_time DESC LIMIT ?",
            params,
        ).fetchall()

        return [dict(r) for r in rows]

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    @staticmethod
    def _compute_summary(pnls: list[float]) -> dict:
        """Compute summary metrics from a list of P&L percentages."""
        if not pnls:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_win_pct": 0.0,
                "avg_loss_pct": 0.0,
                "expectancy_pct": 0.0,
                "profit_factor": 0.0,
            }

        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        total = len(pnls)
        win_rate = len(wins) / total if total else 0.0
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0
        expectancy = (win_rate * avg_win) + ((1 - win_rate) * avg_loss)

        gross_wins = sum(wins)
        gross_losses = abs(sum(losses))
        profit_factor = gross_wins / gross_losses if gross_losses > 0 else float("inf") if gross_wins > 0 else 0.0

        return {
            "total_trades": total,
            "win_rate": round(win_rate, 4),
            "avg_win_pct": round(avg_win, 4),
            "avg_loss_pct": round(avg_loss, 4),
            "expectancy_pct": round(expectancy, 4),
            "profit_factor": round(profit_factor, 4),
        }
