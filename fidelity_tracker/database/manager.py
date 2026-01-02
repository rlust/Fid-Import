"""
Database manager for SQLite operations
Handles schema creation, data storage, and queries
"""

import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
from loguru import logger


class DatabaseManager:
    """Manages SQLite database operations"""

    def __init__(self, db_path: str = 'fidelity_portfolio.db'):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        """Create database schema if it doesn't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    total_value REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER,
                    account_id TEXT,
                    nickname TEXT,
                    balance REAL,
                    withdrawal_balance REAL,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
                )
            ''')

            # Holdings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS holdings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER,
                    account_id TEXT,
                    ticker TEXT,
                    company_name TEXT,
                    quantity REAL,
                    last_price REAL,
                    value REAL,
                    sector TEXT,
                    industry TEXT,
                    market_cap REAL,
                    pe_ratio REAL,
                    dividend_yield REAL,
                    portfolio_weight REAL,
                    account_weight REAL,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
                )
            ''')

            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_holdings_snapshot ON holdings(snapshot_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_holdings_ticker ON holdings(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_accounts_snapshot ON accounts(snapshot_id)')

            conn.commit()
            logger.debug("Database schema ensured")

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create schema: {e}")
            raise
        finally:
            conn.close()

    def save_snapshot(self, data: Dict[str, Any]) -> int:
        """
        Save a complete portfolio snapshot

        Args:
            data: Dictionary containing accounts and holdings data

        Returns:
            Snapshot ID
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            accounts = data.get('accounts', {})
            total_value = sum(account.get('balance', 0) for account in accounts.values())
            timestamp = data.get('timestamp', datetime.now().isoformat())

            # Insert snapshot
            cursor.execute(
                'INSERT INTO snapshots (timestamp, total_value) VALUES (?, ?)',
                (timestamp, total_value)
            )
            snapshot_id = cursor.lastrowid

            # Insert accounts
            for account_id, account_data in accounts.items():
                cursor.execute('''
                    INSERT INTO accounts (snapshot_id, account_id, nickname, balance, withdrawal_balance)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    snapshot_id,
                    account_id,
                    account_data.get('nickname', ''),
                    account_data.get('balance', 0),
                    account_data.get('withdrawal_balance', 0)
                ))

            # Insert holdings
            for account_id, account_data in accounts.items():
                for stock in account_data.get('stocks', []):
                    cursor.execute('''
                        INSERT INTO holdings (
                            snapshot_id, account_id, ticker, company_name, quantity, last_price, value,
                            sector, industry, market_cap, pe_ratio, dividend_yield, portfolio_weight, account_weight
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        snapshot_id,
                        account_id,
                        stock.get('ticker', ''),
                        stock.get('company_name', ''),
                        stock.get('quantity', 0),
                        stock.get('last_price', 0),
                        stock.get('value', 0),
                        stock.get('sector', ''),
                        stock.get('industry', ''),
                        stock.get('market_cap'),
                        stock.get('pe_ratio'),
                        stock.get('dividend_yield'),
                        stock.get('portfolio_weight', 0),
                        stock.get('account_weight', 0)
                    ))

            conn.commit()
            logger.success(f"Saved snapshot {snapshot_id} with ${total_value:,.2f} total value")
            return snapshot_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save snapshot: {e}")
            raise
        finally:
            conn.close()

    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """Get the most recent snapshot"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM snapshots ORDER BY id DESC LIMIT 1')
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
        finally:
            conn.close()

    def get_snapshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent snapshots

        Args:
            limit: Maximum number of snapshots to return

        Returns:
            List of snapshot dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'SELECT * FROM snapshots ORDER BY id DESC LIMIT ?',
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_holdings(self, snapshot_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get holdings for a snapshot

        Args:
            snapshot_id: Snapshot ID (if None, uses latest)

        Returns:
            List of holding dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if snapshot_id is None:
                latest = self.get_latest_snapshot()
                if latest is None:
                    return []
                snapshot_id = latest['id']

            cursor.execute(
                'SELECT * FROM holdings WHERE snapshot_id = ? ORDER BY value DESC',
                (snapshot_id,)
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def cleanup_old_snapshots(self, keep_days: int = 90) -> int:
        """
        Delete snapshots older than specified days

        Args:
            keep_days: Number of days to keep

        Returns:
            Number of deleted snapshots
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cutoff_date = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
            cursor.execute(
                "DELETE FROM snapshots WHERE strftime('%s', timestamp) < ?",
                (cutoff_date,)
            )
            deleted = cursor.rowcount
            conn.commit()
            logger.info(f"Deleted {deleted} snapshots older than {keep_days} days")
            return deleted
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to cleanup snapshots: {e}")
            raise
        finally:
            conn.close()

    def get_portfolio_history(self, days: int = 30) -> List[Tuple[str, float]]:
        """
        Get portfolio value history

        Args:
            days: Number of days of history

        Returns:
            List of (timestamp, total_value) tuples
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            cursor.execute('''
                SELECT timestamp, total_value
                FROM snapshots
                WHERE strftime('%s', timestamp) >= ?
                ORDER BY timestamp ASC
            ''', (cutoff_date,))
            return [(row['timestamp'], row['total_value']) for row in cursor.fetchall()]
        finally:
            conn.close()

    def vacuum(self) -> None:
        """Optimize database"""
        conn = self._get_connection()
        try:
            conn.execute('VACUUM')
            logger.info("Database optimized")
        finally:
            conn.close()
