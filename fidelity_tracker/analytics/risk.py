"""
Risk Analytics Module

Calculates portfolio risk metrics including:
- Volatility (standard deviation)
- Sharpe ratio
- Beta vs benchmark
- Value at Risk (VaR)
- Maximum drawdown
- Correlation matrix
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from scipy import stats


class RiskAnalytics:
    """Calculate risk metrics for portfolio and holdings."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database path."""
        if db_path is None:
            db_path = Path.home() / "grok" / "fidelity_portfolio.db"
        self.db_path = str(db_path)
        self.risk_free_rate = 0.045  # 4.5% annual risk-free rate (approximate current T-bill rate)

    @staticmethod
    def _safe_float(value: float) -> Optional[float]:
        """Convert NaN/inf to None for JSON compatibility."""
        if pd.isna(value) or np.isinf(value):
            return None
        return float(value)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_portfolio_returns(self, days: int = 365) -> pd.Series:
        """
        Calculate daily portfolio returns from snapshots.

        Returns:
            Series of daily returns (percentage)
        """
        conn = self._get_connection()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = """
            SELECT timestamp, total_value
            FROM snapshots
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """

        df = pd.read_sql_query(query, conn, params=(cutoff_date,))
        conn.close()

        if len(df) < 2:
            return pd.Series([])

        # Calculate daily returns as percentage change
        df['returns'] = df['total_value'].pct_change() * 100

        # Drop NaN (first row has no previous value)
        returns = df['returns'].dropna()

        return returns

    def _get_holding_returns(self, ticker: str, days: int = 365) -> pd.Series:
        """
        Calculate daily returns for a specific holding.

        Args:
            ticker: Stock ticker symbol
            days: Number of days to look back

        Returns:
            Series of daily returns (percentage)
        """
        conn = self._get_connection()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = """
            SELECT s.timestamp, h.last_price
            FROM holdings h
            JOIN snapshots s ON h.snapshot_id = s.id
            WHERE h.ticker = ?
            AND s.timestamp >= ?
            ORDER BY s.timestamp ASC
        """

        df = pd.read_sql_query(query, conn, params=(ticker, cutoff_date))
        conn.close()

        if len(df) < 2:
            return pd.Series([])

        # Calculate daily returns
        df['returns'] = df['last_price'].pct_change() * 100
        returns = df['returns'].dropna()

        return returns

    def _get_benchmark_returns(self, benchmark: str = '^GSPC', days: int = 365) -> pd.Series:
        """
        Get benchmark returns from database.

        Args:
            benchmark: Benchmark ticker symbol (default: ^GSPC for S&P 500)
            days: Number of days to look back

        Returns:
            Series of daily returns (percentage)
        """
        conn = self._get_connection()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = """
            SELECT bd.date, bd.close_price
            FROM benchmark_data bd
            JOIN benchmarks b ON bd.benchmark_id = b.id
            WHERE b.ticker = ?
            AND bd.date >= ?
            ORDER BY bd.date ASC
        """

        df = pd.read_sql_query(query, conn, params=(benchmark, cutoff_date))
        conn.close()

        if len(df) < 2:
            return pd.Series([])

        # Calculate daily returns
        df['returns'] = df['close_price'].pct_change() * 100
        returns = df['returns'].dropna()

        return returns

    def calculate_volatility(self, days: int = 365) -> Dict[str, float]:
        """
        Calculate portfolio volatility (standard deviation of returns).

        Args:
            days: Number of days to analyze

        Returns:
            Dict with daily and annualized volatility
        """
        returns = self._get_portfolio_returns(days)

        if len(returns) < 2:
            return {
                'daily_volatility': 0.0,
                'annualized_volatility': 0.0,
                'data_points': 0
            }

        daily_vol = returns.std()
        # Annualize using sqrt(252) for trading days
        annualized_vol = daily_vol * np.sqrt(252)

        return {
            'daily_volatility': self._safe_float(daily_vol),
            'annualized_volatility': self._safe_float(annualized_vol),
            'data_points': len(returns)
        }

    def calculate_sharpe_ratio(self, days: int = 365) -> Dict[str, float]:
        """
        Calculate Sharpe ratio (risk-adjusted return).

        Sharpe Ratio = (Portfolio Return - Risk Free Rate) / Portfolio Volatility

        Args:
            days: Number of days to analyze

        Returns:
            Dict with Sharpe ratio and components
        """
        returns = self._get_portfolio_returns(days)

        if len(returns) < 2:
            return {
                'sharpe_ratio': 0.0,
                'annualized_return': 0.0,
                'annualized_volatility': 0.0,
                'risk_free_rate': self.risk_free_rate
            }

        # Calculate annualized return
        mean_daily_return = returns.mean()
        annualized_return = (1 + mean_daily_return / 100) ** 252 - 1

        # Calculate annualized volatility
        daily_vol = returns.std()
        annualized_vol = daily_vol * np.sqrt(252) / 100  # Convert to decimal

        # Calculate Sharpe ratio
        if annualized_vol > 0:
            sharpe = (annualized_return - self.risk_free_rate) / annualized_vol
        else:
            sharpe = 0.0

        return {
            'sharpe_ratio': self._safe_float(sharpe),
            'annualized_return': self._safe_float(annualized_return),
            'annualized_volatility': self._safe_float(annualized_vol),
            'risk_free_rate': self.risk_free_rate
        }

    def calculate_beta(self, days: int = 365, benchmark: str = '^GSPC') -> Dict[str, float]:
        """
        Calculate portfolio beta vs benchmark.

        Beta = Covariance(Portfolio, Benchmark) / Variance(Benchmark)

        Args:
            days: Number of days to analyze
            benchmark: Benchmark symbol

        Returns:
            Dict with beta and related metrics
        """
        portfolio_returns = self._get_portfolio_returns(days)
        benchmark_returns = self._get_benchmark_returns(benchmark, days)

        if len(portfolio_returns) < 2 or len(benchmark_returns) < 2:
            return {
                'beta': 1.0,
                'alpha': 0.0,
                'r_squared': 0.0,
                'correlation': 0.0,
                'data_points': 0
            }

        # Align the series by index (in case of missing dates)
        aligned = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        }).dropna()

        if len(aligned) < 2:
            return {
                'beta': 1.0,
                'alpha': 0.0,
                'r_squared': 0.0,
                'correlation': 0.0,
                'data_points': 0
            }

        # Calculate beta using linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            aligned['benchmark'],
            aligned['portfolio']
        )

        # Beta is the slope
        beta = slope

        # Alpha is the intercept (annualized)
        alpha = intercept * 252

        # R-squared
        r_squared = r_value ** 2

        # Correlation
        correlation = aligned['portfolio'].corr(aligned['benchmark'])

        return {
            'beta': self._safe_float(beta),
            'alpha': self._safe_float(alpha),
            'r_squared': self._safe_float(r_squared),
            'correlation': self._safe_float(correlation),
            'data_points': len(aligned)
        }

    def calculate_value_at_risk(self, days: int = 365, confidence: float = 0.95) -> Dict[str, float]:
        """
        Calculate Value at Risk (VaR) - maximum expected loss at given confidence level.

        Uses historical method.

        Args:
            days: Number of days to analyze
            confidence: Confidence level (default 95%)

        Returns:
            Dict with VaR metrics
        """
        returns = self._get_portfolio_returns(days)

        if len(returns) < 2:
            return {
                'var_percent': 0.0,
                'var_amount': 0.0,
                'confidence_level': confidence,
                'data_points': 0
            }

        # Calculate VaR at the specified confidence level
        var_percentile = (1 - confidence) * 100
        var_percent = np.percentile(returns, var_percentile)

        # Get current portfolio value
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT total_value FROM snapshots ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        current_value = row['total_value'] if row else 0
        conn.close()

        # VaR in dollar amount
        var_amount = current_value * (var_percent / 100)

        return {
            'var_percent': self._safe_float(var_percent),
            'var_amount': self._safe_float(var_amount),
            'confidence_level': confidence,
            'current_value': self._safe_float(current_value),
            'data_points': len(returns)
        }

    def calculate_max_drawdown(self, days: int = 365) -> Dict[str, float]:
        """
        Calculate maximum drawdown - largest peak-to-trough decline.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with max drawdown metrics
        """
        conn = self._get_connection()

        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        query = """
            SELECT timestamp, total_value
            FROM snapshots
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """

        df = pd.read_sql_query(query, conn, params=(cutoff_date,))
        conn.close()

        if len(df) < 2:
            return {
                'max_drawdown_percent': 0.0,
                'max_drawdown_amount': 0.0,
                'peak_date': None,
                'trough_date': None,
                'recovery_date': None,
                'data_points': 0
            }

        values = df['total_value'].values
        dates = df['timestamp'].values

        # Calculate running maximum
        running_max = np.maximum.accumulate(values)

        # Calculate drawdown at each point
        drawdown = (values - running_max) / running_max * 100

        # Find maximum drawdown
        max_dd_idx = np.argmin(drawdown)
        max_dd_percent = drawdown[max_dd_idx]

        # Find peak before maximum drawdown
        peak_idx = np.argmax(running_max[:max_dd_idx + 1] == running_max[max_dd_idx])

        # Find recovery date (when value returns to peak)
        recovery_idx = None
        peak_value = values[peak_idx]
        for i in range(max_dd_idx + 1, len(values)):
            if values[i] >= peak_value:
                recovery_idx = i
                break

        max_dd_amount = values[max_dd_idx] - values[peak_idx]

        return {
            'max_drawdown_percent': self._safe_float(max_dd_percent),
            'max_drawdown_amount': self._safe_float(max_dd_amount),
            'peak_date': str(dates[peak_idx]),
            'trough_date': str(dates[max_dd_idx]),
            'recovery_date': str(dates[recovery_idx]) if recovery_idx is not None else None,
            'data_points': len(df)
        }

    def calculate_correlation_matrix(self, days: int = 365, min_holdings: int = 5) -> Dict:
        """
        Calculate correlation matrix between top holdings.

        Args:
            days: Number of days to analyze
            min_holdings: Minimum number of holdings to include

        Returns:
            Dict with correlation matrix and tickers
        """
        # Get top holdings by current value
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT h.ticker, SUM(h.value) as total_value
            FROM holdings h
            JOIN snapshots s ON h.snapshot_id = s.id
            WHERE s.timestamp = (SELECT MAX(timestamp) FROM snapshots)
            AND h.ticker IS NOT NULL
            AND h.ticker != 'N/A'
            GROUP BY h.ticker
            ORDER BY total_value DESC
            LIMIT ?
        """, (min_holdings,))

        tickers = [row['ticker'] for row in cursor.fetchall()]
        conn.close()

        if len(tickers) < 2:
            return {
                'tickers': tickers,
                'matrix': [],
                'message': 'Not enough holdings for correlation analysis'
            }

        # Get returns for each ticker
        returns_dict = {}
        for ticker in tickers:
            returns = self._get_holding_returns(ticker, days)
            if len(returns) >= 2:
                returns_dict[ticker] = returns

        # Create DataFrame with aligned returns
        returns_df = pd.DataFrame(returns_dict).dropna()

        if len(returns_df) < 2 or len(returns_df.columns) < 2:
            return {
                'tickers': list(returns_dict.keys()),
                'matrix': [],
                'message': 'Insufficient data for correlation analysis'
            }

        # Calculate correlation matrix
        corr_matrix = returns_df.corr()

        return {
            'tickers': list(corr_matrix.columns),
            'matrix': corr_matrix.values.tolist(),
            'data_points': len(returns_df)
        }

    def get_comprehensive_risk_report(self, days: int = 365) -> Dict:
        """
        Get comprehensive risk analysis report.

        Args:
            days: Number of days to analyze

        Returns:
            Dict with all risk metrics
        """
        return {
            'period_days': days,
            'volatility': self.calculate_volatility(days),
            'sharpe_ratio': self.calculate_sharpe_ratio(days),
            'beta': self.calculate_beta(days),
            'value_at_risk': self.calculate_value_at_risk(days),
            'max_drawdown': self.calculate_max_drawdown(days),
            'generated_at': datetime.now().isoformat()
        }
