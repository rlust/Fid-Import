"""
Data enricher using Yahoo Finance
Adds company information, sector, industry, and financial metrics
"""

from typing import Dict, Any, Optional, Callable
from time import sleep
import yfinance as yf
from loguru import logger


class DataEnricher:
    """Enriches portfolio data with Yahoo Finance information"""

    def __init__(self, delay: float = 3.0, max_retries: int = 3, progress_callback: Optional[Callable] = None):
        """
        Initialize the enricher

        Args:
            delay: Delay between API calls in seconds
            max_retries: Maximum number of retries for failed requests
            progress_callback: Optional callback function for progress updates (current, total, ticker)
        """
        self.delay = delay
        self.max_retries = max_retries
        self.progress_callback = progress_callback
        self._cache = {}  # Cache ticker data to avoid duplicate calls

    def enrich_ticker(self, ticker: str, db: Optional[Any] = None) -> Dict[str, Any]:
        """
        Fetch enrichment data for a single ticker

        Args:
            ticker: Stock ticker symbol
            db: Optional DatabaseManager instance for persistent caching

        Returns:
            Dictionary with company information
        """
        ticker_clean = ticker.replace('**', '').strip()

        # Skip cash/money market funds
        if not ticker_clean or ticker_clean in ['N/A', 'FZDXX', 'FDRXX', 'SPAXX', 'SPRXX', 'FDLXX', 'FZFXX']:
            return {
                'company_name': 'Cash/Money Market',
                'sector': 'Cash',
                'industry': 'Money Market',
                'market_cap': None,
                'pe_ratio': None,
                'dividend_yield': None
            }

        # Check in-memory cache first (fastest)
        if ticker_clean in self._cache:
            logger.debug(f"Using in-memory cached data for {ticker_clean}")
            return self._cache[ticker_clean]

        # Check persistent cache (database) if available
        if db:
            cached_metadata = db.get_ticker_metadata(ticker_clean)
            if cached_metadata and not db.is_metadata_stale(cached_metadata, max_age_days=30):
                logger.debug(f"Using persistent cached data for {ticker_clean} (age: {cached_metadata.get('last_updated')})")
                # Convert database format to enricher format
                stock_info = {
                    'company_name': cached_metadata.get('company_name', ticker_clean),
                    'sector': cached_metadata.get('sector', 'Unknown'),
                    'industry': cached_metadata.get('industry', 'Unknown'),
                    'market_cap': cached_metadata.get('market_cap'),
                    'pe_ratio': cached_metadata.get('pe_ratio'),
                    'dividend_yield': cached_metadata.get('dividend_yield')
                }
                # Also cache in memory for this session
                self._cache[ticker_clean] = stock_info
                return stock_info

        # Fetch from Yahoo Finance with retry logic
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Fetching data for {ticker_clean} (attempt {attempt + 1}/{self.max_retries})...")
                yf_ticker = yf.Ticker(ticker_clean)
                info = yf_ticker.info

                stock_info = {
                    'company_name': info.get('longName', info.get('shortName', ticker_clean)),
                    'sector': info.get('sector', 'Unknown'),
                    'industry': info.get('industry', 'Unknown'),
                    'market_cap': info.get('marketCap'),
                    'pe_ratio': info.get('trailingPE'),
                    'dividend_yield': info.get('dividendYield')
                }

                # Cache the result in memory
                self._cache[ticker_clean] = stock_info

                # Save to persistent cache if available
                if db:
                    db.save_ticker_metadata(ticker_clean, stock_info)
                    logger.debug(f"Saved {ticker_clean} to persistent cache")

                logger.success(f"✓ {ticker_clean}: {stock_info['company_name']}")

                sleep(self.delay)
                return stock_info

            except Exception as e:
                error_msg = str(e)
                if 'Rate limit' in error_msg or '429' in error_msg:
                    wait_time = self.delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(f"Rate limited on {ticker_clean}. Waiting {wait_time}s...")
                    sleep(wait_time)
                    if attempt < self.max_retries - 1:
                        continue
                else:
                    logger.error(f"Error fetching {ticker_clean}: {error_msg}")
                    break

        # If all retries failed, return defaults
        default_info = {
            'company_name': ticker_clean,
            'sector': 'Unknown',
            'industry': 'Unknown',
            'market_cap': None,
            'pe_ratio': None,
            'dividend_yield': None
        }
        self._cache[ticker_clean] = default_info
        return default_info

    def enrich_accounts(self, accounts: Dict[str, Any], total_portfolio_value: float, db: Optional[Any] = None) -> Dict[str, Any]:
        """
        Enrich all accounts with Yahoo Finance data

        Args:
            accounts: Dictionary of account data
            total_portfolio_value: Total portfolio value for weight calculations
            db: Optional DatabaseManager instance for persistent caching

        Returns:
            Enriched accounts dictionary
        """
        # Get unique tickers
        unique_tickers = set()
        for account_data in accounts.values():
            for stock in account_data.get('stocks', []):
                ticker = stock.get('ticker', '').replace('**', '').strip()
                if ticker and ticker not in ['N/A', 'FZDXX', 'FDRXX', 'SPAXX', 'SPRXX', 'FDLXX', 'FZFXX']:
                    unique_tickers.add(ticker)

        logger.info(f"Enriching {len(unique_tickers)} unique tickers...")

        # Fetch data for each unique ticker
        for i, ticker in enumerate(sorted(unique_tickers), 1):
            logger.info(f"[{i}/{len(unique_tickers)}] Processing {ticker}...")

            # Call progress callback if provided
            if self.progress_callback:
                self.progress_callback(i, len(unique_tickers), ticker)

            self.enrich_ticker(ticker, db=db)

        # Apply enrichment data to all holdings
        for account_id, account_data in accounts.items():
            enriched_stocks = []
            for stock in account_data.get('stocks', []):
                ticker = stock.get('ticker', '').replace('**', '').strip()

                # Copy stock data
                enriched_stock = stock.copy()

                # Add enrichment data
                if ticker in self._cache:
                    enriched_stock.update(self._cache[ticker])
                elif not ticker or ticker in ['N/A', 'FZDXX', 'FDRXX', 'SPAXX', 'SPRXX', 'FDLXX', 'FZFXX']:
                    enriched_stock.update({
                        'company_name': 'Cash/Money Market',
                        'sector': 'Cash',
                        'industry': 'Money Market',
                        'market_cap': None,
                        'pe_ratio': None,
                        'dividend_yield': None
                    })

                # Ensure weights are calculated
                if 'portfolio_weight' not in enriched_stock:
                    enriched_stock['portfolio_weight'] = (
                        (stock.get('value', 0) / total_portfolio_value * 100)
                        if total_portfolio_value > 0 else 0
                    )
                if 'account_weight' not in enriched_stock:
                    enriched_stock['account_weight'] = (
                        (stock.get('value', 0) / account_data.get('balance', 1) * 100)
                        if account_data.get('balance', 0) > 0 else 0
                    )

                enriched_stocks.append(enriched_stock)

            accounts[account_id]['stocks'] = enriched_stocks

        logger.success(f"Enrichment complete! Processed {len(unique_tickers)} tickers")
        return accounts

    def enrich_data(self, data: Dict[str, Any], db: Optional[Any] = None) -> Dict[str, Any]:
        """
        Enrich complete dataset

        Args:
            data: Dictionary containing accounts and other data
            db: Optional DatabaseManager instance for persistent caching

        Returns:
            Enriched data dictionary
        """
        accounts = data.get('accounts', {})
        total_portfolio_value = sum(account.get('balance', 0) for account in accounts.values())

        data['accounts'] = self.enrich_accounts(accounts, total_portfolio_value, db=db)
        return data

    def _should_skip_ticker(self, ticker: str) -> bool:
        """Check if ticker should be skipped (cash/money market)"""
        ticker_clean = ticker.replace('**', '').strip()
        return not ticker_clean or ticker_clean in [
            'N/A', 'CASH', 'USD', 'FZDXX', 'FDRXX', 'SPAXX',
            'SPRXX', 'FDLXX', 'FZFXX', 'FDIC'
        ]

    def clear_cache(self) -> None:
        """Clear the ticker data cache"""
        cache_size = len(self._cache)
        self._cache.clear()
        logger.info(f"Enrichment cache cleared ({cache_size} tickers)")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'cached_tickers': len(self._cache),
            'cache_size_bytes': len(str(self._cache)),
            'tickers': list(self._cache.keys())
        }
