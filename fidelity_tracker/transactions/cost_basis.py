"""
Cost Basis Calculator
Implements various cost basis calculation methods (FIFO, LIFO, etc.)
"""

import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from loguru import logger
from decimal import Decimal, ROUND_HALF_UP


class CostBasisCalculator:
    """Calculates cost basis for holdings using various methods"""

    METHODS = ['FIFO', 'LIFO', 'AVERAGE', 'SPECIFIC_ID']

    def __init__(self, db_path: str = 'fidelity_portfolio.db', method: str = 'FIFO'):
        """
        Initialize cost basis calculator

        Args:
            db_path: Path to SQLite database file
            method: Cost basis method (FIFO, LIFO, AVERAGE, SPECIFIC_ID)
        """
        self.db_path = db_path
        self.method = method.upper()

        if self.method not in self.METHODS:
            raise ValueError(f"Invalid method: {method}. Must be one of {self.METHODS}")

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.Connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def create_lot(
        self,
        account_id: str,
        ticker: str,
        acquisition_date: str,
        quantity: float,
        cost_per_share: float,
        lot_id: Optional[str] = None
    ) -> int:
        """
        Create a new cost basis lot

        Args:
            account_id: Account identifier
            ticker: Stock ticker symbol
            acquisition_date: Date of acquisition (ISO 8601)
            quantity: Number of shares
            cost_per_share: Cost per share
            lot_id: Optional lot identifier for specific ID method

        Returns:
            Lot ID
        """
        total_cost = Decimal(str(quantity)) * Decimal(str(cost_per_share))
        total_cost = float(total_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO cost_basis (
                    account_id, ticker, acquisition_date, quantity,
                    cost_per_share, total_cost, method, lot_id, remaining_quantity
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                account_id,
                ticker.upper(),
                acquisition_date,
                quantity,
                cost_per_share,
                total_cost,
                self.method,
                lot_id,
                quantity  # Initially, remaining_quantity = quantity
            ))

            lot_id_result = cursor.lastrowid
            conn.commit()

            logger.info(f"Created cost basis lot {lot_id_result}: {quantity} shares of {ticker} @ ${cost_per_share}")
            return lot_id_result

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to create cost basis lot: {e}")
            raise
        finally:
            conn.close()

    def get_lots(
        self,
        ticker: str,
        account_id: Optional[str] = None,
        include_closed: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get cost basis lots for a ticker

        Args:
            ticker: Stock ticker symbol
            account_id: Filter by account (optional)
            include_closed: Include closed lots (default: False)

        Returns:
            List of lot dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = 'SELECT * FROM cost_basis WHERE ticker = ?'
            params = [ticker.upper()]

            if account_id:
                query += ' AND account_id = ?'
                params.append(account_id)

            if not include_closed:
                query += ' AND is_closed = 0'

            query += ' ORDER BY acquisition_date ASC'

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def calculate_fifo(
        self,
        ticker: str,
        current_quantity: float,
        account_id: Optional[str] = None
    ) -> Tuple[float, float]:
        """
        Calculate cost basis using FIFO (First In, First Out)

        Args:
            ticker: Stock ticker symbol
            current_quantity: Current quantity held
            account_id: Account identifier (optional)

        Returns:
            Tuple of (total_cost_basis, average_cost_per_share)
        """
        lots = self.get_lots(ticker, account_id, include_closed=False)

        if not lots:
            logger.warning(f"No cost basis lots found for {ticker}")
            return (0.0, 0.0)

        remaining_qty = Decimal(str(current_quantity))
        total_cost = Decimal('0')

        for lot in lots:
            if remaining_qty <= 0:
                break

            lot_remaining = Decimal(str(lot['remaining_quantity']))
            qty_from_lot = min(remaining_qty, lot_remaining)

            cost_from_lot = qty_from_lot * Decimal(str(lot['cost_per_share']))
            total_cost += cost_from_lot
            remaining_qty -= qty_from_lot

        if remaining_qty > 0:
            logger.warning(
                f"Current quantity ({current_quantity}) exceeds available lots "
                f"by {float(remaining_qty)} shares for {ticker}"
            )

        total_cost_float = float(total_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        if current_quantity > 0:
            avg_cost = float((total_cost / Decimal(str(current_quantity))).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ))
        else:
            avg_cost = 0.0

        return (total_cost_float, avg_cost)

    def calculate_lifo(
        self,
        ticker: str,
        current_quantity: float,
        account_id: Optional[str] = None
    ) -> Tuple[float, float]:
        """
        Calculate cost basis using LIFO (Last In, First Out)

        Args:
            ticker: Stock ticker symbol
            current_quantity: Current quantity held
            account_id: Account identifier (optional)

        Returns:
            Tuple of (total_cost_basis, average_cost_per_share)
        """
        lots = self.get_lots(ticker, account_id, include_closed=False)

        if not lots:
            logger.warning(f"No cost basis lots found for {ticker}")
            return (0.0, 0.0)

        # Reverse order for LIFO
        lots = list(reversed(lots))

        remaining_qty = Decimal(str(current_quantity))
        total_cost = Decimal('0')

        for lot in lots:
            if remaining_qty <= 0:
                break

            lot_remaining = Decimal(str(lot['remaining_quantity']))
            qty_from_lot = min(remaining_qty, lot_remaining)

            cost_from_lot = qty_from_lot * Decimal(str(lot['cost_per_share']))
            total_cost += cost_from_lot
            remaining_qty -= qty_from_lot

        total_cost_float = float(total_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        if current_quantity > 0:
            avg_cost = float((total_cost / Decimal(str(current_quantity))).quantize(
                Decimal('0.01'), rounding=ROUND_HALF_UP
            ))
        else:
            avg_cost = 0.0

        return (total_cost_float, avg_cost)

    def calculate_average(
        self,
        ticker: str,
        current_quantity: float,
        account_id: Optional[str] = None
    ) -> Tuple[float, float]:
        """
        Calculate cost basis using Average Cost method

        Args:
            ticker: Stock ticker symbol
            current_quantity: Current quantity held
            account_id: Account identifier (optional)

        Returns:
            Tuple of (total_cost_basis, average_cost_per_share)
        """
        lots = self.get_lots(ticker, account_id, include_closed=False)

        if not lots:
            logger.warning(f"No cost basis lots found for {ticker}")
            return (0.0, 0.0)

        total_shares = Decimal('0')
        total_cost = Decimal('0')

        for lot in lots:
            total_shares += Decimal(str(lot['remaining_quantity']))
            total_cost += Decimal(str(lot['total_cost']))

        if total_shares == 0:
            return (0.0, 0.0)

        avg_cost_per_share = float((total_cost / total_shares).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        ))

        current_qty_decimal = Decimal(str(current_quantity))
        total_cost_for_current = current_qty_decimal * Decimal(str(avg_cost_per_share))
        total_cost_float = float(total_cost_for_current.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

        return (total_cost_float, avg_cost_per_share)

    def calculate_cost_basis(
        self,
        ticker: str,
        current_quantity: float,
        account_id: Optional[str] = None,
        method: Optional[str] = None
    ) -> Tuple[float, float]:
        """
        Calculate cost basis using configured method

        Args:
            ticker: Stock ticker symbol
            current_quantity: Current quantity held
            account_id: Account identifier (optional)
            method: Override method for this calculation (optional)

        Returns:
            Tuple of (total_cost_basis, average_cost_per_share)
        """
        calc_method = method.upper() if method else self.method

        if calc_method == 'FIFO':
            return self.calculate_fifo(ticker, current_quantity, account_id)
        elif calc_method == 'LIFO':
            return self.calculate_lifo(ticker, current_quantity, account_id)
        elif calc_method == 'AVERAGE':
            return self.calculate_average(ticker, current_quantity, account_id)
        else:
            raise ValueError(f"Method {calc_method} not implemented")

    def record_sale(
        self,
        ticker: str,
        quantity_sold: float,
        sale_price: float,
        sale_date: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Record a sale and update lots accordingly

        Args:
            ticker: Stock ticker symbol
            quantity_sold: Quantity sold
            sale_price: Sale price per share
            sale_date: Date of sale (ISO 8601)
            account_id: Account identifier (optional)

        Returns:
            Dictionary with sale details and gain/loss information
        """
        lots = self.get_lots(ticker, account_id, include_closed=False)

        if not lots:
            raise ValueError(f"No cost basis lots found for {ticker}")

        # Use FIFO for determining which lots were sold (IRS default)
        conn = self._get_connection()
        cursor = conn.cursor()

        remaining_to_sell = Decimal(str(quantity_sold))
        total_cost_basis = Decimal('0')
        lots_affected = []

        try:
            for lot in lots:
                if remaining_to_sell <= 0:
                    break

                lot_remaining = Decimal(str(lot['remaining_quantity']))
                qty_from_lot = min(remaining_to_sell, lot_remaining)

                cost_from_lot = qty_from_lot * Decimal(str(lot['cost_per_share']))
                total_cost_basis += cost_from_lot

                new_remaining = lot_remaining - qty_from_lot

                # Update lot
                cursor.execute('''
                    UPDATE cost_basis
                    SET remaining_quantity = ?, is_closed = ?
                    WHERE id = ?
                ''', (
                    float(new_remaining),
                    1 if new_remaining == 0 else 0,
                    lot['id']
                ))

                lots_affected.append({
                    'lot_id': lot['id'],
                    'quantity_sold': float(qty_from_lot),
                    'cost_per_share': lot['cost_per_share'],
                    'acquisition_date': lot['acquisition_date']
                })

                remaining_to_sell -= qty_from_lot

            if remaining_to_sell > 0:
                conn.rollback()
                raise ValueError(
                    f"Insufficient shares to sell. Tried to sell {quantity_sold}, "
                    f"but only {float(Decimal(str(quantity_sold)) - remaining_to_sell)} available"
                )

            conn.commit()

            # Calculate gain/loss
            total_proceeds = Decimal(str(quantity_sold)) * Decimal(str(sale_price))
            gain_loss = total_proceeds - total_cost_basis

            result = {
                'quantity_sold': quantity_sold,
                'sale_price': sale_price,
                'total_proceeds': float(total_proceeds.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'cost_basis': float(total_cost_basis.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'gain_loss': float(gain_loss.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)),
                'lots_affected': lots_affected
            }

            logger.info(
                f"Recorded sale: {quantity_sold} shares of {ticker} @ ${sale_price}. "
                f"Gain/Loss: ${result['gain_loss']}"
            )

            return result

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to record sale: {e}")
            raise
        finally:
            conn.close()

    def sync_from_transactions(self, account_id: Optional[str] = None) -> int:
        """
        Synchronize cost basis lots from transaction history

        Args:
            account_id: Sync specific account only (optional)

        Returns:
            Number of lots created
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get all BUY transactions
            query = "SELECT * FROM transactions WHERE transaction_type = 'BUY'"
            params = []

            if account_id:
                query += " AND account_id = ?"
                params.append(account_id)

            query += " ORDER BY transaction_date ASC"

            cursor.execute(query, params)
            buy_transactions = [dict(row) for row in cursor.fetchall()]

            lots_created = 0

            for txn in buy_transactions:
                # Check if lot already exists for this transaction
                cursor.execute(
                    'SELECT id FROM cost_basis WHERE ticker = ? AND acquisition_date = ? AND quantity = ?',
                    (txn['ticker'], txn['transaction_date'], txn['quantity'])
                )

                if cursor.fetchone():
                    continue  # Skip if lot already exists

                # Create lot
                self.create_lot(
                    account_id=txn['account_id'],
                    ticker=txn['ticker'],
                    acquisition_date=txn['transaction_date'],
                    quantity=txn['quantity'],
                    cost_per_share=txn['price_per_share']
                )

                lots_created += 1

            logger.info(f"Synchronized {lots_created} cost basis lots from transactions")
            return lots_created

        finally:
            conn.close()
