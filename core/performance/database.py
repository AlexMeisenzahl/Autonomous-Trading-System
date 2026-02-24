"""
ATS Core — Performance Database

SQLite storage for trade context logs and regime snapshots.
Separate database from Freqtrade — this is ATS's own performance memory.

No Freqtrade imports permitted in this file.
"""

import sqlite3
import os
from pathlib import Path


DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "performance.db"


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """
    Get a SQLite connection, creating the database and tables if needed.

    Args:
        db_path: Path to database file. Defaults to ATS_ROOT/data/performance.db

    Returns:
        sqlite3.Connection with row_factory set to sqlite3.Row
    """
    if db_path is None:
        db_path = str(DEFAULT_DB_PATH)

    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # Better concurrent read performance
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn: sqlite3.Connection) -> None:
    """Create tables if they don't exist."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS trade_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id TEXT NOT NULL,
            pair TEXT NOT NULL,
            strategy TEXT NOT NULL,

            -- Entry context
            entry_time TEXT NOT NULL,
            entry_price REAL NOT NULL,
            entry_rsi REAL,
            entry_tema REAL,
            entry_bb_percent REAL,
            entry_bb_width REAL,
            entry_adx REAL,
            entry_volatility_regime TEXT,
            entry_trend_regime TEXT,
            entry_regime TEXT,

            -- Exit context (NULL until trade closes)
            exit_time TEXT,
            exit_price REAL,
            exit_reason TEXT,
            exit_rsi REAL,
            exit_tema REAL,
            exit_bb_percent REAL,
            exit_bb_width REAL,
            exit_adx REAL,
            exit_volatility_regime TEXT,
            exit_trend_regime TEXT,
            exit_regime TEXT,

            -- Performance
            pnl_absolute REAL,
            pnl_percent REAL,
            duration_minutes REAL,
            regime_changed INTEGER,

            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS regime_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            pair TEXT NOT NULL,
            volatility_regime TEXT,
            trend_regime TEXT,
            regime TEXT,
            bb_width REAL,
            adx REAL,
            rsi REAL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_trade_log_strategy
            ON trade_log(strategy);
        CREATE INDEX IF NOT EXISTS idx_trade_log_regime
            ON trade_log(entry_regime);
        CREATE INDEX IF NOT EXISTS idx_trade_log_pair
            ON trade_log(pair);
        CREATE INDEX IF NOT EXISTS idx_regime_snapshots_pair
            ON regime_snapshots(pair, timestamp);
    """)
    conn.commit()
