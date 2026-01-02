"""
Performance Attribution Module

Analyzes how different holdings and sectors contribute to portfolio performance
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sqlite3


class AttributionAnalytics:
    """Calculate performance attribution by holding and sector"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def calculate_holding_attribution(
        self,
        days: int = 30
    ) -> List[Dict]:
        """
        Calculate how each holding contributed to portfolio performance

        Contribution = Weight × Return
        where Weight = (Start Value + End Value) / 2 / Total Portfolio Value
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get start and end snapshots
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute('''
                SELECT id, timestamp, total_value
                FROM snapshots
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
                LIMIT 1
            ''', (cutoff_date,))

            start_snapshot = cursor.fetchone()

            cursor.execute('''
                SELECT id, timestamp, total_value
                FROM snapshots
                ORDER BY timestamp DESC
                LIMIT 1
            ''')

            end_snapshot = cursor.fetchone()

            if not start_snapshot or not end_snapshot:
                return []

            start_id = start_snapshot['id']
            end_id = end_snapshot['id']
            total_start = start_snapshot['total_value']
            total_end = end_snapshot['total_value']

            # Get holdings at start and end
            cursor.execute('''
                SELECT ticker, value, quantity, last_price, sector
                FROM holdings
                WHERE snapshot_id = ?
            ''', (start_id,))

            start_holdings = {row['ticker']: dict(row) for row in cursor.fetchall()}

            cursor.execute('''
                SELECT ticker, value, quantity, last_price, sector, gain_loss, gain_loss_percent
                FROM holdings
                WHERE snapshot_id = ?
            ''', (end_id,))

            end_holdings = {row['ticker']: dict(row) for row in cursor.fetchall()}

            # Calculate attribution for each holding
            attributions = []

            for ticker in set(list(start_holdings.keys()) + list(end_holdings.keys())):
                start_value = start_holdings.get(ticker, {}).get('value', 0) or 0
                end_value = end_holdings.get(ticker, {}).get('value', 0) or 0

                # Calculate return
                if start_value > 0:
                    holding_return = (end_value - start_value) / start_value
                else:
                    holding_return = 0

                # Calculate average weight in portfolio
                avg_value = (start_value + end_value) / 2
                weight = avg_value / ((total_start + total_end) / 2) if total_start + total_end > 0 else 0

                # Contribution to portfolio return
                contribution = weight * holding_return

                attributions.append({
                    "ticker": ticker,
                    "sector": end_holdings.get(ticker, {}).get('sector', 'Unknown'),
                    "start_value": start_value,
                    "end_value": end_value,
                    "value_change": end_value - start_value,
                    "holding_return": holding_return,
                    "holding_return_percent": holding_return * 100,
                    "weight": weight,
                    "weight_percent": weight * 100,
                    "contribution": contribution,
                    "contribution_percent": contribution * 100,
                    "gain_loss": end_holdings.get(ticker, {}).get('gain_loss'),
                    "gain_loss_percent": end_holdings.get(ticker, {}).get('gain_loss_percent')
                })

            # Sort by contribution (descending)
            attributions.sort(key=lambda x: x['contribution'], reverse=True)

            return attributions

        finally:
            conn.close()

    def calculate_sector_attribution(
        self,
        days: int = 30
    ) -> List[Dict]:
        """
        Calculate how each sector contributed to portfolio performance
        """
        # Get holding-level attribution
        holding_attributions = self.calculate_holding_attribution(days)

        # Aggregate by sector
        sector_data = {}

        for holding in holding_attributions:
            sector = holding['sector']

            if sector not in sector_data:
                sector_data[sector] = {
                    "sector": sector,
                    "start_value": 0,
                    "end_value": 0,
                    "value_change": 0,
                    "weight": 0,
                    "contribution": 0,
                    "holdings_count": 0
                }

            sector_data[sector]["start_value"] += holding["start_value"]
            sector_data[sector]["end_value"] += holding["end_value"]
            sector_data[sector]["value_change"] += holding["value_change"]
            sector_data[sector]["weight"] += holding["weight"]
            sector_data[sector]["contribution"] += holding["contribution"]
            sector_data[sector]["holdings_count"] += 1

        # Calculate sector returns
        sector_attributions = []

        for sector, data in sector_data.items():
            sector_return = 0
            if data["start_value"] > 0:
                sector_return = data["value_change"] / data["start_value"]

            sector_attributions.append({
                "sector": sector,
                "start_value": data["start_value"],
                "end_value": data["end_value"],
                "value_change": data["value_change"],
                "sector_return": sector_return,
                "sector_return_percent": sector_return * 100,
                "weight": data["weight"],
                "weight_percent": data["weight"] * 100,
                "contribution": data["contribution"],
                "contribution_percent": data["contribution"] * 100,
                "holdings_count": data["holdings_count"]
            })

        # Sort by contribution (descending)
        sector_attributions.sort(key=lambda x: x['contribution'], reverse=True)

        return sector_attributions

    def get_top_contributors(
        self,
        days: int = 30,
        limit: int = 10
    ) -> Dict:
        """
        Get top positive and negative contributors to performance
        """
        attributions = self.calculate_holding_attribution(days)

        return {
            "top_contributors": attributions[:limit],
            "top_detractors": sorted(
                [a for a in attributions if a['contribution'] < 0],
                key=lambda x: x['contribution']
            )[:limit]
        }
