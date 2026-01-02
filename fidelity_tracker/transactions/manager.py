"""
Transaction Manager
Handles CRUD operations for investment transactions
"""

import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from decimal import Decimal


class TransactionManager:
    """Manages investment transactions"""

    TRANSACTION_TYPES = ['BUY', 'SELL', 'DIVIDEND', 'FEE', 'SPLIT', 'TRANSFER']

    def __init__(self, db_path: str = 'fidelity_portfolio.db'):
        """
        Initialize transaction manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_transaction(
        self,
        account_id: str,
        ticker: str,
        transaction_type: str,
        transaction_date: str,
        quantity: float,
        total_amount: float,
        price_per_share: Optional[float] = None,
        fees: float = 0.0,
        notes: Optional[str] = None,
        source: str = 'manual'
    ) -> int:
        """
        Create a new transaction

        Args:
            account_id: Account identifier
            ticker: Stock ticker symbol
            transaction_type: Type of transaction (BUY, SELL, DIVIDEND, FEE, SPLIT, TRANSFER)
            transaction_date: Date of transaction (ISO 8601 format)
            quantity: Number of shares
            total_amount: Total transaction amount
            price_per_share: Price per share (optional, calculated if not provided)
            fees: Transaction fees (default: 0)
            notes: Optional notes
            source: Source of transaction (manual, imported, inferred)

        Returns:
            Transaction ID
        """
        if transaction_type not in self.TRANSACTION_TYPES:
            raise ValueError(f"Invalid transaction type: {transaction_type}. Must be one of {self.TRANSACTION_TYPES}")

        # Auto-calculate price_per_share if not provided
        if price_per_share is None and quantity != 0:
            price_per_share = abs(total_amount / quantity)

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO transactions (
                    account_id, ticker, transaction_type, transaction_date,
                    quantity, price_per_share, total_amount, fees, notes, source, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                account_id,
                ticker.upper(),
                transaction_type,
                transaction_date,
                quantity,
                price_per_share,
                total_amount,
                fees,
                notes,
                source,
                datetime.now().isoformat()
            ))

            transaction_id = cursor.lastrowid
            conn.commit()

            logger.success(f"Created transaction {transaction_id}: {transaction_type} {quantity} shares of {ticker}")
            return transaction_id

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create transaction: {e}")
            raise
        finally:
            conn.close()

    def get_transaction(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """
        Get transaction by ID

        Args:
            transaction_id: Transaction ID

        Returns:
            Transaction dictionary or None if not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM transactions WHERE id = ?', (transaction_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_transactions(
        self,
        account_id: Optional[str] = None,
        ticker: Optional[str] = None,
        transaction_type: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get transactions with filters

        Args:
            account_id: Filter by account (optional)
            ticker: Filter by ticker (optional)
            transaction_type: Filter by type (optional)
            start_date: Filter by start date (optional, ISO 8601)
            end_date: Filter by end date (optional, ISO 8601)
            limit: Maximum number of results (optional)
            offset: Number of results to skip (default: 0)

        Returns:
            List of transaction dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = 'SELECT * FROM transactions WHERE 1=1'
            params = []

            if account_id:
                query += ' AND account_id = ?'
                params.append(account_id)

            if ticker:
                query += ' AND ticker = ?'
                params.append(ticker.upper())

            if transaction_type:
                query += ' AND transaction_type = ?'
                params.append(transaction_type)

            if start_date:
                query += ' AND transaction_date >= ?'
                params.append(start_date)

            if end_date:
                query += ' AND transaction_date <= ?'
                params.append(end_date)

            query += ' ORDER BY transaction_date DESC, id DESC'

            if limit:
                query += ' LIMIT ? OFFSET ?'
                params.extend([limit, offset])

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def update_transaction(
        self,
        transaction_id: int,
        **fields
    ) -> bool:
        """
        Update transaction fields

        Args:
            transaction_id: Transaction ID
            **fields: Fields to update

        Returns:
            True if successful, False if transaction not found
        """
        allowed_fields = {
            'account_id', 'ticker', 'transaction_type', 'transaction_date',
            'quantity', 'price_per_share', 'total_amount', 'fees', 'notes'
        }

        # Filter out invalid fields
        updates = {k: v for k, v in fields.items() if k in allowed_fields}

        if not updates:
            logger.warning("No valid fields to update")
            return False

        # Add updated_at
        updates['updated_at'] = datetime.now().isoformat()

        # Build query
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [transaction_id]

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                f'UPDATE transactions SET {set_clause} WHERE id = ?',
                values
            )
            conn.commit()

            if cursor.rowcount == 0:
                logger.warning(f"Transaction {transaction_id} not found")
                return False

            logger.info(f"Updated transaction {transaction_id}")
            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to update transaction: {e}")
            raise
        finally:
            conn.close()

    def delete_transaction(self, transaction_id: int) -> bool:
        """
        Delete transaction

        Args:
            transaction_id: Transaction ID

        Returns:
            True if successful, False if transaction not found
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
            conn.commit()

            if cursor.rowcount == 0:
                logger.warning(f"Transaction {transaction_id} not found")
                return False

            logger.info(f"Deleted transaction {transaction_id}")
            return True

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to delete transaction: {e}")
            raise
        finally:
            conn.close()

    def get_transactions_by_ticker(self, ticker: str) -> List[Dict[str, Any]]:
        """
        Get all transactions for a specific ticker

        Args:
            ticker: Stock ticker symbol

        Returns:
            List of transactions ordered by date
        """
        return self.get_transactions(ticker=ticker)

    def get_transactions_summary(
        self,
        account_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for transactions

        Args:
            account_id: Filter by account (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)

        Returns:
            Dictionary with summary statistics
        """
        transactions = self.get_transactions(
            account_id=account_id,
            start_date=start_date,
            end_date=end_date
        )

        summary = {
            'total_transactions': len(transactions),
            'by_type': {},
            'total_invested': 0.0,
            'total_proceeds': 0.0,
            'total_dividends': 0.0,
            'total_fees': 0.0
        }

        for txn in transactions:
            txn_type = txn['transaction_type']

            # Count by type
            summary['by_type'][txn_type] = summary['by_type'].get(txn_type, 0) + 1

            # Sum amounts
            if txn_type == 'BUY':
                summary['total_invested'] += abs(txn['total_amount'])
            elif txn_type == 'SELL':
                summary['total_proceeds'] += abs(txn['total_amount'])
            elif txn_type == 'DIVIDEND':
                summary['total_dividends'] += abs(txn['total_amount'])

            summary['total_fees'] += txn.get('fees', 0)

        return summary

    def import_transactions_from_csv(self, csv_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Import multiple transactions from CSV data

        Args:
            csv_data: List of transaction dictionaries

        Returns:
            Dictionary with import results (success_count, error_count, errors)
        """
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': []
        }

        for i, row in enumerate(csv_data):
            try:
                self.create_transaction(
                    account_id=row['account_id'],
                    ticker=row['ticker'],
                    transaction_type=row['transaction_type'],
                    transaction_date=row['transaction_date'],
                    quantity=float(row['quantity']),
                    total_amount=float(row['total_amount']),
                    price_per_share=float(row.get('price_per_share')) if row.get('price_per_share') else None,
                    fees=float(row.get('fees', 0)),
                    notes=row.get('notes'),
                    source='imported'
                )
                results['success_count'] += 1

            except Exception as e:
                results['error_count'] += 1
                results['errors'].append({
                    'row': i + 1,
                    'data': row,
                    'error': str(e)
                })
                logger.warning(f"Failed to import row {i + 1}: {e}")

        logger.info(f"Import complete: {results['success_count']} succeeded, {results['error_count']} failed")
        return results
