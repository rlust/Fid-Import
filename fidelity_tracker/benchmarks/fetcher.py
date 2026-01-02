"""
Benchmark Data Fetcher
Fetches historical data for market benchmarks (S&P 500, NASDAQ, etc.)
"""

import sqlite3
import yfinance as yf
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from loguru import logger


class BenchmarkFetcher:
    """Fetches and stores benchmark market data"""

    def __init__(self, db_path: str = 'fidelity_portfolio.db'):
        """
        Initialize benchmark fetcher

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_benchmark_by_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get benchmark by ticker symbol

        Args:
            ticker: Benchmark ticker (e.g., ^GSPC for S&P 500)

        Returns:
            Benchmark dictionary or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM benchmarks WHERE ticker = ?', (ticker,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_active_benchmarks(self) -> List[Dict[str, Any]]:
        """
        Get all active benchmarks

        Returns:
            List of benchmark dictionaries
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM benchmarks WHERE is_active = 1 ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def fetch_benchmark_data(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch benchmark historical data from Yahoo Finance

        Args:
            ticker: Benchmark ticker (e.g., ^GSPC)
            start_date: Start date (ISO 8601 format, optional)
            end_date: End date (ISO 8601 format, optional)
            days: Number of days of history (alternative to start_date)

        Returns:
            List of daily price data dictionaries
        """
        try:
            # Determine date range
            if days:
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=days)
            elif start_date:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00')) if end_date else datetime.now()
            else:
                # Default to 1 year
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=365)

            logger.info(f"Fetching {ticker} data from {start_dt.date()} to {end_dt.date()}")

            # Fetch from Yahoo Finance
            benchmark = yf.Ticker(ticker)
            hist = benchmark.history(start=start_dt, end=end_dt)

            if hist.empty:
                logger.warning(f"No data returned for {ticker}")
                return []

            # Convert to list of dictionaries
            data = []
            for date, row in hist.iterrows():
                data.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'close': float(row['Close']),
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'volume': float(row['Volume'])
                })

            logger.success(f"Fetched {len(data)} days of data for {ticker}")
            return data

        except Exception as e:
            logger.error(f"Failed to fetch benchmark data for {ticker}: {e}")
            raise

    def save_benchmark_data(
        self,
        ticker: str,
        data: List[Dict[str, Any]],
        replace: bool = False
    ) -> int:
        """
        Save benchmark data to database

        Args:
            ticker: Benchmark ticker
            data: List of daily price data dictionaries
            replace: Replace existing data for same dates (default: False, skip duplicates)

        Returns:
            Number of records saved
        """
        benchmark = self.get_benchmark_by_ticker(ticker)

        if not benchmark:
            raise ValueError(f"Benchmark {ticker} not found in database")

        conn = self._get_connection()
        cursor = conn.cursor()

        saved_count = 0

        try:
            for record in data:
                if replace:
                    # Delete existing record for this date
                    cursor.execute('''
                        DELETE FROM benchmark_data
                        WHERE benchmark_id = ? AND date = ?
                    ''', (benchmark['id'], record['date']))

                try:
                    cursor.execute('''
                        INSERT INTO benchmark_data (
                            benchmark_id, date, close_price, open_price,
                            high_price, low_price, volume
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        benchmark['id'],
                        record['date'],
                        record['close'],
                        record['open'],
                        record['high'],
                        record['low'],
                        record['volume']
                    ))
                    saved_count += 1

                except sqlite3.IntegrityError:
                    # Duplicate date, skip if not replacing
                    if not replace:
                        continue
                    raise

            conn.commit()
            logger.info(f"Saved {saved_count} records for {ticker}")
            return saved_count

        except Exception as e:
            conn.rollback()
            logger.error(f"Failed to save benchmark data: {e}")
            raise
        finally:
            conn.close()

    def sync_benchmark(
        self,
        ticker: str,
        days: int = 365,
        replace: bool = False
    ) -> int:
        """
        Fetch and save benchmark data

        Args:
            ticker: Benchmark ticker
            days: Number of days to fetch (default: 365)
            replace: Replace existing data (default: False)

        Returns:
            Number of records saved
        """
        logger.info(f"Syncing benchmark {ticker}...")

        data = self.fetch_benchmark_data(ticker, days=days)
        saved = self.save_benchmark_data(ticker, data, replace=replace)

        logger.success(f"Synced {saved} records for {ticker}")
        return saved

    def sync_all_benchmarks(self, days: int = 365, replace: bool = False) -> Dict[str, int]:
        """
        Sync all active benchmarks

        Args:
            days: Number of days to fetch (default: 365)
            replace: Replace existing data (default: False)

        Returns:
            Dictionary mapping ticker to number of records saved
        """
        benchmarks = self.get_active_benchmarks()
        results = {}

        for benchmark in benchmarks:
            try:
                saved = self.sync_benchmark(benchmark['ticker'], days=days, replace=replace)
                results[benchmark['ticker']] = saved
            except Exception as e:
                logger.error(f"Failed to sync {benchmark['ticker']}: {e}")
                results[benchmark['ticker']] = 0

        total_saved = sum(results.values())
        logger.success(f"Synced {len(benchmarks)} benchmarks, {total_saved} total records")

        return results

    def get_benchmark_history(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get benchmark historical data from database

        Args:
            ticker: Benchmark ticker
            start_date: Start date (ISO 8601, optional)
            end_date: End date (ISO 8601, optional)
            days: Number of days (alternative to start_date)

        Returns:
            List of daily price data
        """
        benchmark = self.get_benchmark_by_ticker(ticker)

        if not benchmark:
            raise ValueError(f"Benchmark {ticker} not found")

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = 'SELECT * FROM benchmark_data WHERE benchmark_id = ?'
            params = [benchmark['id']]

            if days:
                cutoff_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
                query += ' AND date >= ?'
                params.append(cutoff_date)
            else:
                if start_date:
                    query += ' AND date >= ?'
                    params.append(start_date)
                if end_date:
                    query += ' AND date <= ?'
                    params.append(end_date)

            query += ' ORDER BY date ASC'

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

        finally:
            conn.close()

    def calculate_returns(
        self,
        ticker: str,
        days: int = 30
    ) -> Dict[str, float]:
        """
        Calculate returns for a benchmark

        Args:
            ticker: Benchmark ticker
            days: Period in days

        Returns:
            Dictionary with return metrics
        """
        data = self.get_benchmark_history(ticker, days=days)

        if len(data) < 2:
            return {'return_percent': 0.0, 'data_points': len(data)}

        start_price = data[0]['close_price']
        end_price = data[-1]['close_price']

        return_percent = ((end_price - start_price) / start_price) * 100

        return {
            'ticker': ticker,
            'period_days': days,
            'start_date': data[0]['date'],
            'end_date': data[-1]['date'],
            'start_price': start_price,
            'end_price': end_price,
            'return_percent': return_percent,
            'data_points': len(data)
        }
