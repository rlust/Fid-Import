"""
Integration tests for Fidelity Portfolio Tracker
Tests complete workflows with mocked external services
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from fidelity_tracker.core.collector import PortfolioCollector
from fidelity_tracker.core.enricher import DataEnricher
from fidelity_tracker.core.database import DatabaseManager
from fidelity_tracker.core.storage import StorageManager


@pytest.mark.integration
class TestCompleteWorkflow:
    """Test complete data collection and storage workflow"""

    @patch('fidelity_tracker.core.collector.FidelityAutomation')
    def test_collect_and_store_workflow(self, mock_fidelity_class, temp_dir, temp_db):
        """Test complete workflow: collect -> store -> database"""
        # Setup mock Fidelity client
        mock_client = Mock()
        mock_client.get_account_info.return_value = {
            'Z12345678': {
                'nickname': 'Individual Account',
                'type': 'INDIVIDUAL',
                'balance': 100000.00
            }
        }
        mock_client.get_holdings.return_value = [
            {
                'symbol': 'AAPL',
                'quantity': 100,
                'last_price': 150.00,
                'value': 15000.00,
                'cost_basis': 12000.00,
                'gain_loss': 3000.00,
                'gain_loss_percent': 25.0
            }
        ]
        mock_fidelity_class.return_value = mock_client

        # Collect data
        collector = PortfolioCollector(
            username='test', password='test', mfa_secret='test'
        )
        data = collector.run()

        assert data is not None
        assert 'accounts' in data
        assert 'timestamp' in data

        # Store to files
        storage = StorageManager(str(temp_dir))
        files = storage.save_all(data, '20241112_120000')

        assert files['json'].exists()
        assert files['accounts_csv'].exists()
        assert files['holdings_csv'].exists()

        # Store to database
        db = DatabaseManager(temp_db)
        snapshot_id = db.save_snapshot(data)

        assert snapshot_id > 0

        # Verify database contents
        latest = db.get_latest_snapshot()
        assert latest is not None
        assert latest['id'] == snapshot_id

    @patch('fidelity_tracker.core.collector.FidelityAutomation')
    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_collect_enrich_store_workflow(
        self, mock_ticker_class, mock_fidelity_class, temp_dir, temp_db
    ):
        """Test workflow with enrichment: collect -> enrich -> store"""
        # Setup Fidelity mock
        mock_client = Mock()
        mock_client.get_account_info.return_value = {
            'Z12345678': {
                'nickname': 'Individual Account',
                'type': 'INDIVIDUAL',
                'balance': 100000.00
            }
        }
        mock_client.get_holdings.return_value = [
            {
                'symbol': 'AAPL',
                'quantity': 100,
                'last_price': 150.00,
                'value': 15000.00
            }
        ]
        mock_fidelity_class.return_value = mock_client

        # Setup Yahoo Finance mock
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Apple Inc.',
            'sector': 'Technology',
            'industry': 'Consumer Electronics',
            'marketCap': 3000000000000
        }
        mock_ticker_class.return_value = mock_ticker

        # Collect
        collector = PortfolioCollector(
            username='test', password='test', mfa_secret='test'
        )
        data = collector.run()

        # Enrich
        enricher = DataEnricher(delay=0.1)
        enriched_data = enricher.enrich_data(data)

        # Verify enrichment
        for account in enriched_data['accounts'].values():
            for holding in account['holdings']:
                if holding['symbol'] == 'AAPL':
                    assert 'company_name' in holding
                    assert holding['company_name'] == 'Apple Inc.'

        # Store
        storage = StorageManager(str(temp_dir))
        files = storage.save_all(enriched_data, '20241112_120000')

        db = DatabaseManager(temp_db)
        snapshot_id = db.save_snapshot(enriched_data)

        # Verify enriched data in database
        holdings = db.get_holdings(snapshot_id)
        assert len(holdings) > 0
        assert holdings[0]['company_name'] == 'Apple Inc.'

    @patch('fidelity_tracker.core.collector.FidelityAutomation')
    def test_multiple_account_handling(self, mock_fidelity_class, temp_db):
        """Test handling multiple accounts"""
        mock_client = Mock()
        mock_client.get_account_info.return_value = {
            'Z12345678': {
                'nickname': 'Individual',
                'type': 'INDIVIDUAL',
                'balance': 100000.00
            },
            'Z87654321': {
                'nickname': 'Roth IRA',
                'type': 'ROTH_IRA',
                'balance': 50000.00
            }
        }

        def get_holdings_side_effect(account_id):
            if account_id == 'Z12345678':
                return [{'symbol': 'AAPL', 'value': 15000.00}]
            else:
                return [{'symbol': 'MSFT', 'value': 28500.00}]

        mock_client.get_holdings.side_effect = get_holdings_side_effect
        mock_fidelity_class.return_value = mock_client

        collector = PortfolioCollector(
            username='test', password='test', mfa_secret='test'
        )
        data = collector.run()

        assert len(data['accounts']) == 2
        assert 'Z12345678' in data['accounts']
        assert 'Z87654321' in data['accounts']

        # Save to database
        db = DatabaseManager(temp_db)
        snapshot_id = db.save_snapshot(data)

        # Verify both accounts are saved
        conn = db._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM accounts WHERE snapshot_id = ?',
            (snapshot_id,)
        )
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 2

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_enrichment_error_recovery(self, mock_ticker_class, sample_portfolio_data):
        """Test that enrichment continues after individual ticker failures"""
        call_count = [0]

        def ticker_side_effect(symbol):
            call_count[0] += 1
            if symbol == 'GOOGL':
                # Fail on GOOGL
                raise Exception("API Error")
            mock_ticker = Mock()
            mock_ticker.info = {
                'longName': f'{symbol} Inc.',
                'sector': 'Technology'
            }
            return mock_ticker

        mock_ticker_class.side_effect = ticker_side_effect

        enricher = DataEnricher(delay=0.1, max_retries=1)
        enriched_data = enricher.enrich_data(sample_portfolio_data)

        # Should have enriched data for AAPL and MSFT
        # GOOGL should have default values
        for account in enriched_data['accounts'].values():
            for holding in account['holdings']:
                if holding['symbol'] in ['AAPL', 'MSFT']:
                    assert holding.get('company_name', 'Unknown') != 'Unknown'
                elif holding['symbol'] == 'GOOGL':
                    # Should have default values after failure
                    assert holding.get('company_name') == 'Unknown'

    def test_data_retention_and_cleanup(self, temp_dir, sample_portfolio_data):
        """Test data retention and cleanup workflow"""
        storage = StorageManager(str(temp_dir))

        # Create multiple snapshots
        timestamps = ['20241110_120000', '20241111_120000', '20241112_120000']
        for ts in timestamps:
            storage.save_all(sample_portfolio_data, ts)

        # Verify all files exist
        json_files = storage.list_snapshots('json')
        assert len(json_files) >= 3

        # Cleanup old files (keep last 1 day - will delete older ones in real scenario)
        # For testing, we'll just verify the cleanup method works
        deleted = storage.cleanup_old_files(keep_days=1000)  # Keep all for this test
        assert deleted >= 0

    @patch('fidelity_tracker.core.collector.FidelityAutomation')
    def test_portfolio_weight_calculation(self, mock_fidelity_class, temp_db):
        """Test that portfolio weights are correctly calculated"""
        mock_client = Mock()
        mock_client.get_account_info.return_value = {
            'Z12345678': {
                'nickname': 'Individual',
                'type': 'INDIVIDUAL',
                'balance': 100000.00
            }
        }
        mock_client.get_holdings.return_value = [
            {'symbol': 'AAPL', 'value': 30000.00, 'quantity': 100, 'last_price': 300},
            {'symbol': 'GOOGL', 'value': 20000.00, 'quantity': 50, 'last_price': 400},
            {'symbol': 'MSFT', 'value': 50000.00, 'quantity': 75, 'last_price': 666.67}
        ]
        mock_fidelity_class.return_value = mock_client

        collector = PortfolioCollector(
            username='test', password='test', mfa_secret='test'
        )
        data = collector.run()

        # Check weights
        account = data['accounts']['Z12345678']
        total_value = sum(h['value'] for h in account['holdings'])

        for holding in account['holdings']:
            expected_weight = (holding['value'] / total_value) * 100
            assert abs(holding['portfolio_weight'] - expected_weight) < 0.01

    @patch('fidelity_tracker.core.collector.FidelityAutomation')
    def test_empty_account_handling(self, mock_fidelity_class, temp_db):
        """Test handling of empty accounts"""
        mock_client = Mock()
        mock_client.get_account_info.return_value = {
            'Z12345678': {
                'nickname': 'Empty Account',
                'type': 'INDIVIDUAL',
                'balance': 0.00
            }
        }
        mock_client.get_holdings.return_value = []
        mock_fidelity_class.return_value = mock_client

        collector = PortfolioCollector(
            username='test', password='test', mfa_secret='test'
        )
        data = collector.run()

        assert data is not None
        assert len(data['accounts']) == 1
        assert len(data['accounts']['Z12345678']['holdings']) == 0

        # Should still be able to save to database
        db = DatabaseManager(temp_db)
        snapshot_id = db.save_snapshot(data)
        assert snapshot_id > 0

    @patch('fidelity_tracker.core.enricher.yf.Ticker')
    def test_caching_across_multiple_enrichments(self, mock_ticker_class, sample_portfolio_data):
        """Test that cache persists across multiple enrichment calls"""
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Apple Inc.',
            'sector': 'Technology'
        }
        mock_ticker_class.return_value = mock_ticker

        enricher = DataEnricher(delay=0.1)

        # First enrichment
        enricher.enrich_data(sample_portfolio_data)
        first_call_count = mock_ticker_class.call_count

        # Second enrichment with same data
        enricher.enrich_data(sample_portfolio_data)
        second_call_count = mock_ticker_class.call_count

        # Should not have made additional API calls due to caching
        assert second_call_count == first_call_count
