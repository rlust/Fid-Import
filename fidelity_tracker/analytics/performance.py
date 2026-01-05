"""
Performance Analytics Module

Calculates portfolio performance metrics including:
- Time-Weighted Return (TWR)
- Money-Weighted Return (MWR/IRR)
- Annualized Returns
- Attribution Analysis
"""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from decimal import Decimal
import sqlite3
import numpy as np
from scipy.optimize import newton


class PerformanceAnalytics:
    """Calculate portfolio performance metrics"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def calculate_simple_return(
        self,
        start_value: float,
        end_value: float,
        cash_flows: float = 0.0
    ) -> float:
        """
        Calculate simple return

        Return = (End Value - Start Value - Net Cash Flows) / Start Value
        """
        if start_value == 0:
            return 0.0

        return (end_value - start_value - cash_flows) / start_value

    def calculate_twr(
        self,
        snapshots: List[Dict],
        transactions: List[Dict]
    ) -> Dict[str, float]:
        """
        Calculate Time-Weighted Return (TWR)

        TWR eliminates the impact of cash flows by calculating returns
        for each period between cash flows and geometrically linking them.

        Formula: TWR = [(1 + R1) * (1 + R2) * ... * (1 + Rn)] - 1
        where Ri = (End Value - Begin Value - Cash Flow) / Begin Value
        """
        if len(snapshots) < 2:
            return {"twr": 0.0, "periods": 0}

        # Sort snapshots and transactions by date
        snapshots = sorted(snapshots, key=lambda x: x['timestamp'])
        transactions = sorted(transactions, key=lambda x: x['transaction_date'])

        # Calculate period returns
        period_returns = []

        for i in range(len(snapshots) - 1):
            start_snap = snapshots[i]
            end_snap = snapshots[i + 1]

            start_value = start_snap['total_value']
            end_value = end_snap['total_value']

            # Find cash flows in this period
            # BUY = positive (money invested), SELL = negative (money withdrawn)
            period_cash_flows = sum(
                t['total_amount'] if t['transaction_type'].upper() == 'BUY' else -t['total_amount']
                for t in transactions
                if start_snap['timestamp'] <= t['transaction_date'] < end_snap['timestamp']
                and t['transaction_type'].upper() in ['BUY', 'SELL']
            )

            if start_value == 0:
                continue

            period_return = (end_value - start_value - period_cash_flows) / start_value
            period_returns.append(period_return)

        # Calculate TWR
        if not period_returns:
            return {"twr": 0.0, "periods": 0}

        twr = 1.0
        for r in period_returns:
            twr *= (1.0 + r)
        twr -= 1.0

        return {
            "twr": twr,
            "twr_percent": twr * 100,
            "periods": len(period_returns),
            "annualized_twr": self._annualize_return(twr, len(period_returns))
        }

    def calculate_mwr(
        self,
        snapshots: List[Dict],
        transactions: List[Dict]
    ) -> Dict[str, float]:
        """
        Calculate Money-Weighted Return (MWR) using IRR

        MWR accounts for the timing and size of cash flows.
        It's calculated using the Internal Rate of Return (IRR) method.

        NPV = 0 = -Initial Investment + CF1/(1+r)^t1 + CF2/(1+r)^t2 + ... + Final Value/(1+r)^tn
        """
        if len(snapshots) < 2:
            return {"mwr": 0.0, "converged": False}

        # Sort by date
        snapshots = sorted(snapshots, key=lambda x: x['timestamp'])
        transactions = sorted(transactions, key=lambda x: x['transaction_date'])

        start_date = datetime.fromisoformat(snapshots[0]['timestamp'])
        end_date = datetime.fromisoformat(snapshots[-1]['timestamp'])

        # Build cash flow timeline
        cash_flows = []
        dates = []

        # Initial investment (negative)
        cash_flows.append(-snapshots[0]['total_value'])
        dates.append(start_date)

        # Add intermediate transactions
        for t in transactions:
            t_date = datetime.fromisoformat(t['transaction_date'])
            if start_date < t_date < end_date:
                # Buys are negative (money out), sells are positive (money in)
                amount = -t['total_amount'] if t['transaction_type'] == 'BUY' else t['total_amount']
                cash_flows.append(amount)
                dates.append(t_date)

        # Final value (positive)
        cash_flows.append(snapshots[-1]['total_value'])
        dates.append(end_date)

        # Calculate time periods in years from start
        time_periods = [(d - start_date).days / 365.25 for d in dates]

        # Define NPV function
        def npv(rate):
            return sum(cf / ((1 + rate) ** t) for cf, t in zip(cash_flows, time_periods))

        # Solve for IRR using Newton's method
        try:
            mwr = newton(npv, 0.1, maxiter=100, tol=1e-6)
            converged = True
        except:
            mwr = 0.0
            converged = False

        return {
            "mwr": mwr,
            "mwr_percent": mwr * 100,
            "converged": converged,
            "cash_flows_count": len(cash_flows)
        }

    def _annualize_return(self, total_return: float, periods: int, periods_per_year: int = 365) -> float:
        """
        Annualize a return

        Annualized Return = (1 + Total Return)^(periods_per_year / periods) - 1
        """
        if periods == 0:
            return 0.0

        return ((1 + total_return) ** (periods_per_year / periods)) - 1

    def calculate_portfolio_returns(
        self,
        days: int = 365
    ) -> Dict:
        """
        Calculate comprehensive portfolio returns for a given period
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get snapshots for the period
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            cursor.execute('''
                SELECT id, timestamp, total_value, total_gain_loss, total_return_percent
                FROM snapshots
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            ''', (cutoff_date,))

            snapshots = [dict(row) for row in cursor.fetchall()]

            if len(snapshots) < 2:
                return {
                    "error": "Insufficient data",
                    "message": f"Need at least 2 snapshots, found {len(snapshots)}"
                }

            # Get transactions for the period
            cursor.execute('''
                SELECT transaction_date, transaction_type, total_amount, ticker
                FROM transactions
                WHERE transaction_date >= ?
                ORDER BY transaction_date ASC
            ''', (cutoff_date,))

            transactions = [dict(row) for row in cursor.fetchall()]

            # Calculate metrics
            start_value = snapshots[0]['total_value']
            end_value = snapshots[-1]['total_value']

            # Calculate net cash flows: BUY = positive (invested), SELL = negative (withdrawn)
            net_cash_flows = sum(
                t['total_amount'] if t['transaction_type'].upper() == 'BUY' else -t['total_amount']
                for t in transactions
                if t['transaction_type'].upper() in ['BUY', 'SELL']
            )

            simple_return = self.calculate_simple_return(
                start_value,
                end_value,
                net_cash_flows
            )

            twr_result = self.calculate_twr(snapshots, transactions)
            mwr_result = self.calculate_mwr(snapshots, transactions)

            # Calculate period length in days
            start_date = datetime.fromisoformat(snapshots[0]['timestamp'])
            end_date = datetime.fromisoformat(snapshots[-1]['timestamp'])
            period_days = (end_date - start_date).days

            return {
                "period": {
                    "start_date": snapshots[0]['timestamp'],
                    "end_date": snapshots[-1]['timestamp'],
                    "days": period_days,
                    "snapshots_count": len(snapshots),
                    "transactions_count": len(transactions)
                },
                "values": {
                    "start_value": start_value,
                    "end_value": end_value,
                    "change": end_value - start_value,
                    "change_percent": ((end_value - start_value) / start_value * 100) if start_value > 0 else 0
                },
                "returns": {
                    "simple_return": simple_return,
                    "simple_return_percent": simple_return * 100,
                    "twr": twr_result["twr"],
                    "twr_percent": twr_result["twr_percent"],
                    "annualized_twr": twr_result.get("annualized_twr", 0),
                    "annualized_twr_percent": twr_result.get("annualized_twr", 0) * 100,
                    "mwr": mwr_result["mwr"],
                    "mwr_percent": mwr_result["mwr_percent"],
                    "mwr_converged": mwr_result["converged"]
                }
            }

        finally:
            conn.close()

    def calculate_holding_performance(
        self,
        ticker: str,
        days: int = 365
    ) -> Dict:
        """
        Calculate performance for a specific holding
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            # Get holding snapshots
            cursor.execute('''
                SELECT h.snapshot_id, h.ticker, h.quantity, h.value, h.last_price,
                       h.gain_loss, h.gain_loss_percent, s.timestamp
                FROM holdings h
                JOIN snapshots s ON h.snapshot_id = s.id
                WHERE h.ticker = ? AND s.timestamp >= ?
                ORDER BY s.timestamp ASC
            ''', (ticker, cutoff_date))

            holdings = [dict(row) for row in cursor.fetchall()]

            if len(holdings) < 2:
                return {
                    "error": "Insufficient data",
                    "ticker": ticker,
                    "message": f"Need at least 2 data points, found {len(holdings)}"
                }

            # Get transactions for this ticker
            cursor.execute('''
                SELECT transaction_date, transaction_type, quantity, total_amount
                FROM transactions
                WHERE ticker = ? AND transaction_date >= ?
                ORDER BY transaction_date ASC
            ''', (ticker, cutoff_date))

            transactions = [dict(row) for row in cursor.fetchall()]

            start_value = holdings[0]['value']
            end_value = holdings[-1]['value']

            return {
                "ticker": ticker,
                "period": {
                    "start_date": holdings[0]['timestamp'],
                    "end_date": holdings[-1]['timestamp'],
                    "data_points": len(holdings)
                },
                "performance": {
                    "start_value": start_value,
                    "end_value": end_value,
                    "change": end_value - start_value,
                    "change_percent": ((end_value - start_value) / start_value * 100) if start_value > 0 else 0,
                    "gain_loss": holdings[-1].get('gain_loss'),
                    "gain_loss_percent": holdings[-1].get('gain_loss_percent')
                },
                "transactions": {
                    "count": len(transactions),
                    "buys": sum(1 for t in transactions if t['transaction_type'] == 'BUY'),
                    "sells": sum(1 for t in transactions if t['transaction_type'] == 'SELL')
                }
            }

        finally:
            conn.close()
