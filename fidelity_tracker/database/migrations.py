"""
Database migration manager
Handles schema upgrades and versioning
"""

import sqlite3
from typing import Optional
from pathlib import Path
from loguru import logger
from datetime import datetime


class MigrationManager:
    """Manages database schema migrations"""

    def __init__(self, db_path: str = 'fidelity_portfolio.db'):
        """
        Initialize migration manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._ensure_version_table()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_version_table(self) -> None:
        """Create schema_version table if it doesn't exist"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL,
                    description TEXT
                )
            ''')
            conn.commit()

            # Check if version 1 exists, if not add it (existing schema)
            cursor.execute('SELECT version FROM schema_version WHERE version = 1')
            if not cursor.fetchone():
                cursor.execute(
                    'INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?)',
                    (1, datetime.now().isoformat(), 'Initial schema')
                )
                conn.commit()

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create version table: {e}")
            raise
        finally:
            conn.close()

    def get_current_version(self) -> int:
        """Get current schema version"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT MAX(version) as version FROM schema_version')
            row = cursor.fetchone()
            return row['version'] if row['version'] else 0
        finally:
            conn.close()

    def migrate_to_v2(self) -> None:
        """
        Migrate to version 2: Add performance tracking features

        New tables:
        - transactions
        - cost_basis
        - benchmarks
        - benchmark_data
        - calculated_metrics
        - user_preferences

        New columns:
        - holdings: cost_basis, gain_loss, gain_loss_percent, day_change, day_change_percent
        - snapshots: total_cost_basis, total_gain_loss, total_return_percent, day_change
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            logger.info("Starting migration to version 2...")

            # Create transactions table
            logger.info("Creating transactions table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    transaction_date TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price_per_share REAL,
                    total_amount REAL NOT NULL,
                    fees REAL DEFAULT 0,
                    notes TEXT,
                    source TEXT DEFAULT 'manual',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_ticker ON transactions(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_account ON transactions(account_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type)')

            # Create cost_basis table
            logger.info("Creating cost_basis table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cost_basis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id TEXT NOT NULL,
                    ticker TEXT NOT NULL,
                    acquisition_date TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    cost_per_share REAL NOT NULL,
                    total_cost REAL NOT NULL,
                    method TEXT DEFAULT 'FIFO',
                    lot_id TEXT,
                    remaining_quantity REAL NOT NULL,
                    is_closed BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cost_basis_ticker ON cost_basis(ticker)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cost_basis_account ON cost_basis(account_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_cost_basis_date ON cost_basis(acquisition_date)')

            # Create benchmarks table
            logger.info("Creating benchmarks table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS benchmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    ticker TEXT NOT NULL UNIQUE,
                    description TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Seed benchmark data
            benchmarks = [
                ('S&P 500', '^GSPC', 'S&P 500 Index'),
                ('NASDAQ Composite', '^IXIC', 'NASDAQ Composite Index'),
                ('Dow Jones', '^DJI', 'Dow Jones Industrial Average'),
                ('Russell 2000', '^RUT', 'Russell 2000 Index')
            ]

            for name, ticker, description in benchmarks:
                cursor.execute('''
                    INSERT OR IGNORE INTO benchmarks (name, ticker, description)
                    VALUES (?, ?, ?)
                ''', (name, ticker, description))

            # Create benchmark_data table
            logger.info("Creating benchmark_data table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS benchmark_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    benchmark_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    close_price REAL NOT NULL,
                    open_price REAL,
                    high_price REAL,
                    low_price REAL,
                    volume REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (benchmark_id) REFERENCES benchmarks(id),
                    UNIQUE(benchmark_id, date)
                )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_benchmark_data_date ON benchmark_data(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_benchmark_data_benchmark ON benchmark_data(benchmark_id)')

            # Create calculated_metrics table
            logger.info("Creating calculated_metrics table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS calculated_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL,
                    metric_type TEXT NOT NULL,
                    ticker TEXT,
                    value REAL NOT NULL,
                    metadata TEXT,
                    calculated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (snapshot_id) REFERENCES snapshots(id),
                    UNIQUE(snapshot_id, metric_type, ticker)
                )
            ''')

            cursor.execute('CREATE INDEX IF NOT EXISTS idx_calculated_metrics_snapshot ON calculated_metrics(snapshot_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_calculated_metrics_type ON calculated_metrics(metric_type)')

            # Create user_preferences table
            logger.info("Creating user_preferences table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Seed default preferences
            preferences = [
                ('cost_basis_method', '"FIFO"'),
                ('default_benchmark', '"^GSPC"'),
                ('risk_free_rate', '0.045'),
                ('date_range_default', '90'),
                ('theme', '"light"')
            ]

            for key, value in preferences:
                cursor.execute('''
                    INSERT OR IGNORE INTO user_preferences (key, value)
                    VALUES (?, ?)
                ''', (key, value))

            # Add new columns to holdings table
            logger.info("Adding new columns to holdings table...")
            new_holding_columns = [
                ('cost_basis', 'REAL'),
                ('gain_loss', 'REAL'),
                ('gain_loss_percent', 'REAL'),
                ('day_change', 'REAL'),
                ('day_change_percent', 'REAL')
            ]

            for col_name, col_type in new_holding_columns:
                try:
                    cursor.execute(f'ALTER TABLE holdings ADD COLUMN {col_name} {col_type}')
                except sqlite3.OperationalError as e:
                    if 'duplicate column' in str(e).lower():
                        logger.debug(f"Column {col_name} already exists in holdings table")
                    else:
                        raise

            # Add new columns to snapshots table
            logger.info("Adding new columns to snapshots table...")
            new_snapshot_columns = [
                ('total_cost_basis', 'REAL'),
                ('total_gain_loss', 'REAL'),
                ('total_return_percent', 'REAL'),
                ('day_change', 'REAL')
            ]

            for col_name, col_type in new_snapshot_columns:
                try:
                    cursor.execute(f'ALTER TABLE snapshots ADD COLUMN {col_name} {col_type}')
                except sqlite3.OperationalError as e:
                    if 'duplicate column' in str(e).lower():
                        logger.debug(f"Column {col_name} already exists in snapshots table")
                    else:
                        raise

            # Record migration
            cursor.execute(
                'INSERT INTO schema_version (version, applied_at, description) VALUES (?, ?, ?)',
                (2, datetime.now().isoformat(), 'Add performance tracking features')
            )

            conn.commit()
            logger.success("Successfully migrated to version 2")

        except Exception as e:
            conn.rollback()
            logger.error(f"Migration to v2 failed: {e}")
            raise
        finally:
            conn.close()

    def migrate(self, target_version: Optional[int] = None) -> None:
        """
        Run migrations to target version (or latest if not specified)

        Args:
            target_version: Target schema version (default: latest)
        """
        current_version = self.get_current_version()
        latest_version = 2  # Update this as we add more migrations

        if target_version is None:
            target_version = latest_version

        if current_version >= target_version:
            logger.info(f"Database already at version {current_version}, no migration needed")
            return

        logger.info(f"Migrating database from version {current_version} to {target_version}")

        # Run migrations in order
        if current_version < 2 <= target_version:
            self.migrate_to_v2()

        logger.success(f"Database migration complete. Current version: {self.get_current_version()}")

    def rollback_to_v1(self) -> None:
        """
        Rollback to version 1 (remove v2 features)
        WARNING: This will delete all transaction and performance tracking data
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            logger.warning("Rolling back to version 1...")

            # Drop v2 tables
            tables_to_drop = [
                'calculated_metrics',
                'benchmark_data',
                'benchmarks',
                'cost_basis',
                'transactions',
                'user_preferences'
            ]

            for table in tables_to_drop:
                cursor.execute(f'DROP TABLE IF EXISTS {table}')
                logger.info(f"Dropped table: {table}")

            # Remove v2 columns from holdings
            # Note: SQLite doesn't support DROP COLUMN directly
            # We would need to recreate the table, which is complex
            # For now, we'll just leave the columns (they'll be NULL)
            logger.warning("Note: New columns in holdings/snapshots tables remain (will be NULL)")

            # Remove version 2 record
            cursor.execute('DELETE FROM schema_version WHERE version = 2')

            conn.commit()
            logger.success("Rollback to version 1 complete")

        except Exception as e:
            conn.rollback()
            logger.error(f"Rollback failed: {e}")
            raise
        finally:
            conn.close()
