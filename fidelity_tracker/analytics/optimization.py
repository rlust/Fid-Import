"""
Portfolio Optimization Module

Implements:
- Mean-variance optimization
- Efficient frontier calculation
- Monte Carlo simulation
- Rebalancing recommendations
- Optimal portfolio suggestions
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import sqlite3
from scipy.optimize import minimize
from scipy import stats


class PortfolioOptimizer:
    """Portfolio optimization and analysis."""

    def __init__(self, db_path: Optional[str] = None):
        """Initialize with database path."""
        if db_path is None:
            db_path = Path.home() / "grok" / "fidelity_portfolio.db"
        self.db_path = str(db_path)
        self.risk_free_rate = 0.045  # 4.5% annual

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _safe_float(value: float) -> Optional[float]:
        """Convert NaN/inf to None for JSON compatibility."""
        if pd.isna(value) or np.isinf(value):
            return None
        return float(value)

    def _get_holdings_history(self, days: int = 365, min_holdings: int = 5) -> pd.DataFrame:
        """
        Get historical prices for top holdings.

        Returns DataFrame with dates as index and tickers as columns.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get top holdings by current value
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

        if not tickers:
            conn.close()
            return pd.DataFrame()

        # Get price history for each ticker
        cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

        prices_dict = {}
        for ticker in tickers:
            cursor.execute("""
                SELECT s.timestamp, h.last_price
                FROM holdings h
                JOIN snapshots s ON h.snapshot_id = s.id
                WHERE h.ticker = ?
                AND s.timestamp >= ?
                ORDER BY s.timestamp ASC
            """, (ticker, cutoff_date))

            prices = [(row['timestamp'], row['last_price']) for row in cursor.fetchall()]
            if prices:
                dates, values = zip(*prices)
                # Parse dates - handle both old (YYYYMMDD_HHMMSS) and new (ISO) formats
                parsed_dates = []
                for date_str in dates:
                    if '_' in date_str and len(date_str) == 15:
                        # Old format: YYYYMMDD_HHMMSS
                        parsed_dates.append(pd.to_datetime(date_str, format='%Y%m%d_%H%M%S'))
                    else:
                        # ISO or other format
                        parsed_dates.append(pd.to_datetime(date_str))
                series = pd.Series(values, index=parsed_dates)
                # Remove duplicate timestamps (keep last)
                series = series[~series.index.duplicated(keep='last')]
                prices_dict[ticker] = series

        conn.close()

        if not prices_dict:
            return pd.DataFrame()

        # Create DataFrame and handle duplicates/missing values
        df = pd.DataFrame(prices_dict)

        # Remove duplicate indices (keep last)
        df = df[~df.index.duplicated(keep='last')]

        # Forward-fill missing values and drop any remaining NaN
        df = df.ffill().dropna()

        return df

    def _calculate_returns_and_cov(self, prices: pd.DataFrame) -> Tuple[pd.Series, pd.DataFrame]:
        """
        Calculate expected returns and covariance matrix.

        Returns:
            Tuple of (expected_returns, covariance_matrix)
        """
        # Calculate daily returns
        returns = prices.pct_change().dropna()

        # Annualize returns (252 trading days)
        expected_returns = returns.mean() * 252

        # Annualize covariance matrix
        cov_matrix = returns.cov() * 252

        return expected_returns, cov_matrix

    def _portfolio_performance(self, weights: np.ndarray, returns: pd.Series, cov_matrix: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate portfolio return and volatility.

        Returns:
            Tuple of (return, volatility)
        """
        portfolio_return = np.sum(returns * weights)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        return portfolio_return, portfolio_volatility

    def _negative_sharpe(self, weights: np.ndarray, returns: pd.Series, cov_matrix: pd.DataFrame) -> float:
        """Calculate negative Sharpe ratio (for minimization)."""
        p_return, p_volatility = self._portfolio_performance(weights, returns, cov_matrix)

        if p_volatility == 0:
            return 0

        sharpe = (p_return - self.risk_free_rate) / p_volatility
        return -sharpe

    def optimize_sharpe(self, days: int = 365, min_holdings: int = 5) -> Dict:
        """
        Find portfolio with maximum Sharpe ratio.

        Args:
            days: Historical period for analysis
            min_holdings: Number of top holdings to include

        Returns:
            Dict with optimal weights and metrics
        """
        prices = self._get_holdings_history(days, min_holdings)

        if prices.empty or len(prices.columns) < 2:
            return {
                'success': False,
                'message': 'Insufficient data for optimization',
                'weights': {},
                'metrics': {}
            }

        returns, cov_matrix = self._calculate_returns_and_cov(prices)
        n_assets = len(returns)

        # Constraints: weights sum to 1
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}

        # Bounds: each weight between 0 and 1 (long only)
        bounds = tuple((0, 1) for _ in range(n_assets))

        # Initial guess: equal weights
        init_weights = np.array([1/n_assets] * n_assets)

        # Optimize
        result = minimize(
            self._negative_sharpe,
            init_weights,
            args=(returns, cov_matrix),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if not result.success:
            return {
                'success': False,
                'message': 'Optimization failed',
                'weights': {},
                'metrics': {}
            }

        optimal_weights = result.x
        opt_return, opt_volatility = self._portfolio_performance(optimal_weights, returns, cov_matrix)
        opt_sharpe = (opt_return - self.risk_free_rate) / opt_volatility if opt_volatility > 0 else 0

        # Format weights
        weights_dict = {
            ticker: self._safe_float(weight)
            for ticker, weight in zip(prices.columns, optimal_weights)
            if weight > 0.001  # Only include significant weights
        }

        return {
            'success': True,
            'weights': weights_dict,
            'metrics': {
                'expected_return': self._safe_float(opt_return),
                'volatility': self._safe_float(opt_volatility),
                'sharpe_ratio': self._safe_float(opt_sharpe)
            },
            'tickers': list(prices.columns)
        }

    def optimize_min_volatility(self, days: int = 365, min_holdings: int = 5) -> Dict:
        """
        Find portfolio with minimum volatility.

        Args:
            days: Historical period for analysis
            min_holdings: Number of top holdings to include

        Returns:
            Dict with optimal weights and metrics
        """
        prices = self._get_holdings_history(days, min_holdings)

        if prices.empty or len(prices.columns) < 2:
            return {
                'success': False,
                'message': 'Insufficient data for optimization',
                'weights': {},
                'metrics': {}
            }

        returns, cov_matrix = self._calculate_returns_and_cov(prices)
        n_assets = len(returns)

        # Objective: minimize volatility
        def portfolio_volatility(weights):
            return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

        # Constraints and bounds
        constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
        bounds = tuple((0, 1) for _ in range(n_assets))
        init_weights = np.array([1/n_assets] * n_assets)

        # Optimize
        result = minimize(
            portfolio_volatility,
            init_weights,
            method='SLSQP',
            bounds=bounds,
            constraints=constraints
        )

        if not result.success:
            return {
                'success': False,
                'message': 'Optimization failed',
                'weights': {},
                'metrics': {}
            }

        optimal_weights = result.x
        opt_return, opt_volatility = self._portfolio_performance(optimal_weights, returns, cov_matrix)
        opt_sharpe = (opt_return - self.risk_free_rate) / opt_volatility if opt_volatility > 0 else 0

        weights_dict = {
            ticker: self._safe_float(weight)
            for ticker, weight in zip(prices.columns, optimal_weights)
            if weight > 0.001
        }

        return {
            'success': True,
            'weights': weights_dict,
            'metrics': {
                'expected_return': self._safe_float(opt_return),
                'volatility': self._safe_float(opt_volatility),
                'sharpe_ratio': self._safe_float(opt_sharpe)
            },
            'tickers': list(prices.columns)
        }

    def calculate_efficient_frontier(self, days: int = 365, min_holdings: int = 5, num_points: int = 50) -> Dict:
        """
        Calculate the efficient frontier.

        Args:
            days: Historical period for analysis
            min_holdings: Number of top holdings to include
            num_points: Number of points on the frontier

        Returns:
            Dict with frontier points and data
        """
        prices = self._get_holdings_history(days, min_holdings)

        if prices.empty or len(prices.columns) < 2:
            return {
                'success': False,
                'message': 'Insufficient data for frontier calculation',
                'frontier': []
            }

        returns, cov_matrix = self._calculate_returns_and_cov(prices)
        n_assets = len(returns)

        # Get min and max possible returns
        min_ret = returns.min()
        max_ret = returns.max()

        target_returns = np.linspace(min_ret, max_ret, num_points)
        frontier_points = []

        for target_return in target_returns:
            # Minimize volatility for target return
            def portfolio_volatility(weights):
                return np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))

            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.sum(returns * x) - target_return}
            ]

            bounds = tuple((0, 1) for _ in range(n_assets))
            init_weights = np.array([1/n_assets] * n_assets)

            result = minimize(
                portfolio_volatility,
                init_weights,
                method='SLSQP',
                bounds=bounds,
                constraints=constraints
            )

            if result.success:
                volatility = result.fun
                sharpe = (target_return - self.risk_free_rate) / volatility if volatility > 0 else 0

                frontier_points.append({
                    'return': self._safe_float(target_return),
                    'volatility': self._safe_float(volatility),
                    'sharpe': self._safe_float(sharpe)
                })

        return {
            'success': True,
            'frontier': frontier_points,
            'tickers': list(prices.columns)
        }

    def monte_carlo_simulation(
        self,
        days: int = 365,
        min_holdings: int = 5,
        num_simulations: int = 10000,
        time_horizon: int = 252  # 1 year
    ) -> Dict:
        """
        Run Monte Carlo simulation for portfolio returns.

        Args:
            days: Historical period for analysis
            min_holdings: Number of top holdings
            num_simulations: Number of simulation paths
            time_horizon: Number of days to simulate (252 = 1 year)

        Returns:
            Dict with simulation results
        """
        prices = self._get_holdings_history(days, min_holdings)

        if prices.empty:
            return {
                'success': False,
                'message': 'Insufficient data for simulation'
            }

        returns, cov_matrix = self._calculate_returns_and_cov(prices)

        # Get current portfolio value
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT total_value FROM snapshots ORDER BY timestamp DESC LIMIT 1")
        row = cursor.fetchone()
        current_value = row['total_value'] if row else 100000
        conn.close()

        # Calculate daily returns statistics
        daily_returns = prices.pct_change().dropna()
        mean_daily_return = daily_returns.mean().mean()
        std_daily_return = daily_returns.std().mean()

        # Run simulations
        simulation_results = []

        for _ in range(num_simulations):
            # Generate random returns
            daily_rets = np.random.normal(mean_daily_return, std_daily_return, time_horizon)

            # Calculate cumulative value
            cumulative_returns = np.cumprod(1 + daily_rets)
            final_value = current_value * cumulative_returns[-1]

            simulation_results.append(final_value)

        # Calculate statistics
        simulation_results = np.array(simulation_results)

        return {
            'success': True,
            'current_value': self._safe_float(current_value),
            'statistics': {
                'mean': self._safe_float(simulation_results.mean()),
                'median': self._safe_float(np.median(simulation_results)),
                'std': self._safe_float(simulation_results.std()),
                'min': self._safe_float(simulation_results.min()),
                'max': self._safe_float(simulation_results.max()),
                'percentile_5': self._safe_float(np.percentile(simulation_results, 5)),
                'percentile_25': self._safe_float(np.percentile(simulation_results, 25)),
                'percentile_75': self._safe_float(np.percentile(simulation_results, 75)),
                'percentile_95': self._safe_float(np.percentile(simulation_results, 95))
            },
            'num_simulations': num_simulations,
            'time_horizon_days': time_horizon
        }

    def get_rebalancing_recommendations(self, days: int = 365, min_holdings: int = 5) -> Dict:
        """
        Compare current allocation with optimal and suggest rebalancing.

        Returns:
            Dict with current vs optimal weights and recommendations
        """
        # Get optimal portfolio
        optimal = self.optimize_sharpe(days, min_holdings)

        if not optimal['success']:
            return {
                'success': False,
                'message': optimal.get('message', 'Optimization failed')
            }

        # Get current allocation
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT h.ticker, SUM(h.value) as total_value
            FROM holdings h
            JOIN snapshots s ON h.snapshot_id = s.id
            WHERE s.timestamp = (SELECT MAX(timestamp) FROM snapshots)
            AND h.ticker IS NOT NULL
            AND h.ticker != 'N/A'
            AND h.ticker IN ({})
            GROUP BY h.ticker
        """.format(','.join('?' * len(optimal['tickers']))), optimal['tickers'])

        holdings = {row['ticker']: row['total_value'] for row in cursor.fetchall()}
        total_value = sum(holdings.values())

        current_weights = {
            ticker: value / total_value if total_value > 0 else 0
            for ticker, value in holdings.items()
        }

        conn.close()

        # Calculate differences
        recommendations = []
        for ticker in optimal['weights']:
            current = current_weights.get(ticker, 0)
            target = optimal['weights'][ticker]
            diff = target - current

            if abs(diff) > 0.01:  # More than 1% difference
                action = 'BUY' if diff > 0 else 'SELL'
                amount = abs(diff) * total_value

                recommendations.append({
                    'ticker': ticker,
                    'action': action,
                    'current_weight': self._safe_float(current),
                    'target_weight': self._safe_float(target),
                    'difference': self._safe_float(diff),
                    'amount': self._safe_float(amount)
                })

        return {
            'success': True,
            'current_allocation': current_weights,
            'optimal_allocation': optimal['weights'],
            'recommendations': recommendations,
            'optimal_metrics': optimal['metrics']
        }
