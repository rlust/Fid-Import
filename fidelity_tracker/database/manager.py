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

    # Ticker Metadata Cache Methods (V3 Migration)

    def get_ticker_metadata(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get cached metadata for a ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with ticker metadata or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                'SELECT * FROM ticker_metadata WHERE ticker = ?',
                (ticker.upper(),)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        except sqlite3.OperationalError as e:
            # Table doesn't exist (pre-migration v3)
            if 'no such table' in str(e).lower():
                logger.debug("ticker_metadata table doesn't exist yet (run migration)")
                return None
            raise
        finally:
            conn.close()

    def save_ticker_metadata(self, ticker: str, data: Dict[str, Any]) -> None:
        """
        Save or update ticker metadata in cache

        Args:
            ticker: Stock ticker symbol
            data: Dictionary with ticker metadata (sector, industry, market_cap, etc.)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            ticker_upper = ticker.upper()

            # Check if ticker exists to determine insert vs update
            cursor.execute('SELECT update_count FROM ticker_metadata WHERE ticker = ?', (ticker_upper,))
            existing = cursor.fetchone()

            if existing:
                # Update existing record
                cursor.execute('''
                    UPDATE ticker_metadata
                    SET company_name = ?,
                        sector = ?,
                        industry = ?,
                        market_cap = ?,
                        pe_ratio = ?,
                        dividend_yield = ?,
                        last_updated = CURRENT_TIMESTAMP,
                        update_count = update_count + 1,
                        data_source = ?
                    WHERE ticker = ?
                ''', (
                    data.get('company_name'),
                    data.get('sector'),
                    data.get('industry'),
                    data.get('market_cap'),
                    data.get('pe_ratio'),
                    data.get('dividend_yield'),
                    data.get('data_source', 'yahoo_finance'),
                    ticker_upper
                ))
            else:
                # Insert new record
                cursor.execute('''
                    INSERT INTO ticker_metadata (
                        ticker, company_name, sector, industry,
                        market_cap, pe_ratio, dividend_yield, data_source
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    ticker_upper,
                    data.get('company_name'),
                    data.get('sector'),
                    data.get('industry'),
                    data.get('market_cap'),
                    data.get('pe_ratio'),
                    data.get('dividend_yield'),
                    data.get('data_source', 'yahoo_finance')
                ))

            conn.commit()
            logger.debug(f"Saved metadata for {ticker_upper} to cache")

        except sqlite3.OperationalError as e:
            # Table doesn't exist (pre-migration v3)
            if 'no such table' in str(e).lower():
                logger.debug("ticker_metadata table doesn't exist yet (run migration)")
                return
            raise
        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save ticker metadata: {e}")
            raise
        finally:
            conn.close()

    def is_metadata_stale(self, metadata: Dict[str, Any], max_age_days: int = 30) -> bool:
        """
        Check if cached metadata is stale (older than max_age_days)

        Args:
            metadata: Ticker metadata dictionary with 'last_updated' field
            max_age_days: Maximum age in days before considering stale

        Returns:
            True if stale or missing last_updated, False otherwise
        """
        if not metadata or 'last_updated' not in metadata:
            return True

        try:
            last_updated = datetime.fromisoformat(metadata['last_updated'])
            age_days = (datetime.now() - last_updated).days
            return age_days > max_age_days
        except (ValueError, TypeError):
            logger.warning(f"Invalid last_updated timestamp: {metadata.get('last_updated')}")
            return True

    def get_metadata_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the ticker metadata cache

        Returns:
            Dictionary with cache statistics
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            stats = {
                'total_tickers': 0,
                'by_sector': {},
                'by_data_source': {},
                'avg_update_count': 0
            }

            # Total tickers
            cursor.execute('SELECT COUNT(*) as count FROM ticker_metadata')
            stats['total_tickers'] = cursor.fetchone()['count']

            # By sector
            cursor.execute('''
                SELECT sector, COUNT(*) as count
                FROM ticker_metadata
                WHERE sector IS NOT NULL
                GROUP BY sector
                ORDER BY count DESC
            ''')
            stats['by_sector'] = {row['sector']: row['count'] for row in cursor.fetchall()}

            # By data source
            cursor.execute('''
                SELECT data_source, COUNT(*) as count
                FROM ticker_metadata
                GROUP BY data_source
            ''')
            stats['by_data_source'] = {row['data_source']: row['count'] for row in cursor.fetchall()}

            # Average update count
            cursor.execute('SELECT AVG(update_count) as avg FROM ticker_metadata')
            avg_row = cursor.fetchone()
            stats['avg_update_count'] = round(avg_row['avg'], 2) if avg_row['avg'] else 0

            return stats

        except sqlite3.OperationalError as e:
            # Table doesn't exist (pre-migration v3)
            if 'no such table' in str(e).lower():
                logger.debug("ticker_metadata table doesn't exist yet (run migration)")
                return {'total_tickers': 0, 'by_sector': {}, 'by_data_source': {}, 'avg_update_count': 0}
            raise
        finally:
            conn.close()
