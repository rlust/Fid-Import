"""
Infer transactions by comparing consecutive portfolio snapshots.

This module analyzes changes between snapshots to automatically detect:
- New positions (buys)
- Closed positions (sells)
- Quantity changes (buys/sells)
- Potential dividends (cash increases)
"""

from typing import List, Dict, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import sqlite3
from pathlib import Path


class TransactionInferenceEngine:
    """Infer transactions from snapshot comparisons."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database path."""
        if db_path is None:
            db_path = Path.home() / "grok" / "fidelity_portfolio.db"
        self.db_path = str(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_snapshots_chronological(self) -> List[Dict]:
        """Get all snapshots in chronological order."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, timestamp, total_value
            FROM snapshots
            ORDER BY timestamp ASC
        """)

        snapshots = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return snapshots

    def get_holdings_for_snapshot(self, snapshot_id: int) -> Dict[str, Dict]:
        """Get all holdings for a specific snapshot as a dict keyed by ticker."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT ticker, quantity, value, last_price
            FROM holdings
            WHERE snapshot_id = ?
            AND ticker IS NOT NULL
            AND ticker != 'N/A'
        """, (snapshot_id,))

        holdings = {}
        for row in cursor.fetchall():
            holdings[row['ticker']] = {
                'ticker': row['ticker'],
                'quantity': Decimal(str(row['quantity'])) if row['quantity'] else Decimal('0'),
                'value': Decimal(str(row['value'])) if row['value'] else Decimal('0'),
                'last_price': Decimal(str(row['last_price'])) if row['last_price'] else Decimal('0')
            }

        conn.close()
        return holdings

    def compare_snapshots(self, prev_snapshot: Dict, curr_snapshot: Dict) -> List[Dict]:
        """
        Compare two consecutive snapshots and infer transactions.

        Args:
            prev_snapshot: Previous snapshot dict with 'id' and 'timestamp'
            curr_snapshot: Current snapshot dict with 'id' and 'timestamp'

        Returns list of inferred transactions.
        """
        prev_holdings = self.get_holdings_for_snapshot(prev_snapshot['id'])
        curr_holdings = self.get_holdings_for_snapshot(curr_snapshot['id'])

        transactions = []

        # Find all tickers in either snapshot
        all_tickers = set(prev_holdings.keys()) | set(curr_holdings.keys())

        for ticker in all_tickers:
            prev_qty = prev_holdings.get(ticker, {}).get('quantity', Decimal('0'))
            curr_qty = curr_holdings.get(ticker, {}).get('quantity', Decimal('0'))

            # Skip if no change
            if prev_qty == curr_qty:
                continue

            # Determine transaction type and amount
            qty_change = curr_qty - prev_qty

            if prev_qty == 0 and curr_qty > 0:
                # New position - BUY
                tx_type = 'buy'
                quantity = curr_qty
                price = curr_holdings[ticker]['last_price']

            elif curr_qty == 0 and prev_qty > 0:
                # Closed position - SELL
                tx_type = 'sell'
                quantity = prev_qty
                price = prev_holdings[ticker]['last_price']

            elif qty_change > 0:
                # Increased position - BUY
                tx_type = 'buy'
                quantity = qty_change
                price = curr_holdings[ticker]['last_price']

            else:  # qty_change < 0
                # Decreased position - SELL
                tx_type = 'sell'
                quantity = abs(qty_change)
                price = curr_holdings[ticker]['last_price']

            # Calculate amount
            amount = quantity * price

            # Create transaction record matching the database schema
            transaction = {
                'transaction_date': self._parse_snapshot_date(curr_snapshot['timestamp']),
                'ticker': ticker,
                'transaction_type': tx_type,
                'quantity': float(quantity),
                'price_per_share': float(price),
                'total_amount': float(amount),
                'account_id': 'INFERRED',  # Will need to determine actual account
                'notes': f'Inferred from snapshot comparison',
                'source': 'snapshot_inference'
            }

            transactions.append(transaction)

        return transactions

    def _parse_snapshot_date(self, timestamp: str) -> str:
        """
        Parse snapshot timestamp to ISO date format.

        Handles both formats:
        - Old: YYYYMMDD_HHMMSS (e.g., 20251112_111740)
        - New: YYYY-MM-DDTHH:MM:SS (ISO format)
        """
        if '_' in timestamp and len(timestamp) == 15:
            # Old format: YYYYMMDD_HHMMSS
            year = timestamp[0:4]
            month = timestamp[4:6]
            day = timestamp[6:8]
            return f"{year}-{month}-{day}"
        else:
            # Assume ISO format or similar
            # Extract just the date part
            if 'T' in timestamp:
                return timestamp.split('T')[0]
            elif ' ' in timestamp:
                return timestamp.split(' ')[0]
            else:
                # Try to parse as YYYY-MM-DD
                return timestamp[:10]

    def infer_all_transactions(self, skip_existing: bool = True) -> Dict:
        """
        Infer transactions from all consecutive snapshot pairs.

        Args:
            skip_existing: If True, skip inference for dates that already have transactions

        Returns:
            Dict with 'inferred', 'skipped', 'errors' counts and 'transactions' list
        """
        snapshots = self.get_snapshots_chronological()

        if len(snapshots) < 2:
            return {
                'inferred': 0,
                'skipped': 0,
                'errors': 0,
                'message': 'Need at least 2 snapshots to infer transactions',
                'transactions': []
            }

        all_transactions = []
        errors = []

        # Get existing transaction dates if skip_existing is True
        existing_dates = set()
        if skip_existing:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT transaction_date FROM transactions WHERE source = 'snapshot_inference'")
            existing_dates = {row['transaction_date'] for row in cursor.fetchall()}
            conn.close()

        # Compare consecutive snapshots
        for i in range(len(snapshots) - 1):
            prev_snapshot = snapshots[i]
            curr_snapshot = snapshots[i + 1]

            try:
                # Check if we should skip this date
                curr_date = self._parse_snapshot_date(curr_snapshot['timestamp'])

                if skip_existing and curr_date in existing_dates:
                    continue

                # Infer transactions
                transactions = self.compare_snapshots(
                    prev_snapshot,
                    curr_snapshot
                )

                all_transactions.extend(transactions)

            except Exception as e:
                errors.append({
                    'prev_timestamp': prev_snapshot['timestamp'],
                    'curr_timestamp': curr_snapshot['timestamp'],
                    'error': str(e)
                })

        return {
            'inferred': len(all_transactions),
            'skipped': len(existing_dates) if skip_existing else 0,
            'errors': len(errors),
            'error_details': errors,
            'transactions': all_transactions
        }

    def save_inferred_transactions(self, transactions: List[Dict]) -> int:
        """
        Save inferred transactions to database.

        Returns number of transactions saved.
        """
        if not transactions:
            return 0

        conn = self._get_connection()
        cursor = conn.cursor()

        saved = 0
        for tx in transactions:
            try:
                cursor.execute("""
                    INSERT INTO transactions
                    (account_id, ticker, transaction_type, transaction_date, quantity,
                     price_per_share, total_amount, notes, source)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tx.get('account_id', 'INFERRED'),
                    tx['ticker'],
                    tx['transaction_type'],
                    tx['transaction_date'],
                    tx['quantity'],
                    tx['price_per_share'],
                    tx['total_amount'],
                    tx.get('notes', ''),
                    tx.get('source', 'snapshot_inference')
                ))
                saved += 1
            except sqlite3.IntegrityError:
                # Skip duplicates
                continue
            except Exception as e:
                print(f"Error saving transaction: {e}")
                continue

        conn.commit()
        conn.close()

        return saved
