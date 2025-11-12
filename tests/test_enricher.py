"""
Unit tests for fidelity_tracker.core.enricher module
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fidelity_tracker.core.enricher import DataEnricher


@pytest.mark.unit
class TestDataEnricher:
    """Test DataEnricher class"""

    def test_init(self):
        """Test DataEnricher initialization"""
        enricher = DataEnricher(delay=5.0, max_retries=5)
        assert enricher.delay == 5.0
        assert enricher.max_retries == 5
        assert enricher._cache == {}

    def test_init_defaults(self):
        """Test DataEnricher with default parameters"""
        enricher = DataEnricher()
        assert enricher.delay == 3.0
        assert enricher.max_retries == 3

    def test_should_skip_ticker_money_market(self):
        """Test skipping money market funds"""
        enricher = DataEnricher()

        assert enricher._should_skip_ticker("SPAXX") is True
        assert enricher._should_skip_ticker("FDRXX") is True
        assert enricher._should_skip_ticker("FDIC") is True

    def test_should_skip_ticker_cash(self):
        """Test skipping cash positions"""
        enricher = DataEnricher()

        assert enricher._should_skip_ticker("CASH") is True
        assert enricher._should_skip_ticker("USD") is True

    def test_should_not_skip_regular_ticker(self):
        """Test not skipping regular tickers"""
        enricher = DataEnricher()

        assert enricher._should_skip_ticker("AAPL") is False
        assert enricher._should_skip_ticker("GOOGL") is False
        assert enricher._should_skip_ticker("MSFT") is False

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_enrich_ticker_success(self, mock_ticker_class):
        """Test successful ticker enrichment"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'marketCap': 3000000000000,
            'trailingPE': 29.5,
            'dividendYield': 0.005,
            'fiftyTwoWeekHigh': 199.62,
            'fiftyTwoWeekLow': 143.90
        }
        mock_ticker_class.return_value = mock_ticker

        enricher = DataEnricher(delay=0.1)
        result = enricher.enrich_ticker("AAPL")

        assert result['company_name'] == 'Apple Inc.'
        assert result['sector'] == 'Technology'
        assert result['industry'] == 'Consumer Electronics'
        assert result['market_cap'] == 3000000000000
        assert result['pe_ratio'] == 29.5
        assert result['dividend_yield'] == 0.5  # Converted to percentage

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_enrich_ticker_caching(self, mock_ticker_class):
        """Test that ticker data is cached"""
        mock_ticker = Mock()
        mock_ticker.info = {'longName': 'Apple Inc.', 'sector': 'Technology'}
        mock_ticker_class.return_value = mock_ticker

        enricher = DataEnricher(delay=0.1)

        # First call
        result1 = enricher.enrich_ticker("AAPL")

        # Second call should use cache
        result2 = enricher.enrich_ticker("AAPL")

        # Should only be called once due to caching
        assert mock_ticker_class.call_count == 1
        assert result1 == result2

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_enrich_ticker_missing_fields(self, mock_ticker_class):
        """Test enrichment with missing fields"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Test Company',
            # Missing other fields
        }
        mock_ticker_class.return_value = mock_ticker

        enricher = DataEnricher(delay=0.1)
        result = enricher.enrich_ticker("TEST")

        assert result['company_name'] == 'Test Company'
        assert result['sector'] == 'Unknown'
        assert result['industry'] == 'Unknown'
        assert result['market_cap'] is None
        assert result['pe_ratio'] is None

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_enrich_ticker_api_error(self, mock_ticker_class):
        """Test handling of API errors"""
        mock_ticker_class.side_effect = Exception("API Error")

        enricher = DataEnricher(delay=0.1, max_retries=2)
        result = enricher.enrich_ticker("FAIL")

        # Should return default values on error
        assert result['company_name'] == 'Unknown'
        assert result['sector'] == 'Unknown'

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_enrich_data(self, mock_ticker_class, sample_portfolio_data):
        """Test enriching complete portfolio data"""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Test Company',
            'sector': 'Technology',
            'industry': 'Software'
        }
        mock_ticker_class.return_value = mock_ticker

        enricher = DataEnricher(delay=0.1)
        enriched = enricher.enrich_data(sample_portfolio_data)

        # Check that holdings were enriched
        for account in enriched['accounts'].values():
            for holding in account['holdings']:
                assert 'company_name' in holding
                assert 'sector' in holding
                assert 'industry' in holding

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_enrich_data_skips_money_market(self, mock_ticker_class, sample_portfolio_data):
        """Test that money market funds are skipped during enrichment"""
        # Add a money market fund
        sample_portfolio_data['accounts']['account1']['holdings'].append({
            'symbol': 'SPAXX',
            'quantity': 1000,
            'value': 1000.00
        })

        enricher = DataEnricher(delay=0.1)
        enriched = enricher.enrich_data(sample_portfolio_data)

        # SPAXX should not have enrichment data
        spaxx_holding = None
        for account in enriched['accounts'].values():
            for holding in account['holdings']:
                if holding['symbol'] == 'SPAXX':
                    spaxx_holding = holding
                    break

        assert spaxx_holding is not None
        assert 'company_name' not in spaxx_holding

        # Should not have called Yahoo Finance for SPAXX
        # Only called for AAPL, GOOGL, MSFT
        assert mock_ticker_class.call_count <= 3

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_enrich_ticker_dividend_yield_conversion(self, mock_ticker_class):
        """Test that dividend yield is properly converted to percentage"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Test Company',
            'dividendYield': 0.025  # 2.5% in decimal form
        }
        mock_ticker_class.return_value = mock_ticker

        enricher = DataEnricher(delay=0.1)
        result = enricher.enrich_ticker("TEST")

        assert result['dividend_yield'] == 2.5  # Converted to percentage

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_enrich_ticker_null_dividend_yield(self, mock_ticker_class):
        """Test handling of null dividend yield"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Test Company',
            'dividendYield': None
        }
        mock_ticker_class.return_value = mock_ticker

        enricher = DataEnricher(delay=0.1)
        result = enricher.enrich_ticker("TEST")

        assert result['dividend_yield'] is None

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    @patch('time.sleep')
    def test_delay_between_requests(self, mock_sleep, mock_ticker_class, sample_portfolio_data):
        """Test that delay is applied between API requests"""
        mock_ticker = Mock()
        mock_ticker.info = {'longName': 'Test Company'}
        mock_ticker_class.return_value = mock_ticker

        enricher = DataEnricher(delay=2.0)
        enricher.enrich_data(sample_portfolio_data)

        # Should have called sleep between requests
        # (3 tickers = 2 delays minimum)
        assert mock_sleep.call_count >= 2

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_enrich_ticker_retry_on_failure(self, mock_ticker_class):
        """Test retry logic on API failures"""
        # First call fails, second succeeds
        mock_ticker_class.side_effect = [
            Exception("API Error"),
            Mock(info={'longName': 'Test Company', 'sector': 'Technology'})
        ]

        enricher = DataEnricher(delay=0.1, max_retries=3)
        result = enricher.enrich_ticker("TEST")

        # Should succeed after retry
        assert result['company_name'] == 'Test Company'
        assert mock_ticker_class.call_count == 2

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_enrich_ticker_max_retries_exceeded(self, mock_ticker_class):
        """Test behavior when max retries is exceeded"""
        mock_ticker_class.side_effect = Exception("API Error")

        enricher = DataEnricher(delay=0.1, max_retries=2)
        result = enricher.enrich_ticker("FAIL")

        # Should return defaults after max retries
        assert result['company_name'] == 'Unknown'
        assert mock_ticker_class.call_count == 2
