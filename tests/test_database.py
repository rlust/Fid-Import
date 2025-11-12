"""
Unit tests for fidelity_tracker.core.database module
"""

import pytest
from datetime import datetime, timedelta
from fidelity_tracker.core.database import DatabaseManager


@pytest.mark.unit
class TestDatabaseManager:
    """Test DatabaseManager class"""

    def test_init_creates_tables(self, temp_db):
        """Test that database initialization creates required tables"""
        db = DatabaseManager(temp_db)
        conn = db._get_connection()
        cursor = conn.cursor()

        # Check snapshots table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='snapshots'")
        assert cursor.fetchone() is not None

        # Check accounts table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
        assert cursor.fetchone() is not None

        # Check holdings table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='holdings'")
        assert cursor.fetchone() is not None

        conn.close()

    def test_save_snapshot(self, temp_db, sample_portfolio_data):
        """Test saving a complete portfolio snapshot"""
        db = DatabaseManager(temp_db)
        snapshot_id = db.save_snapshot(sample_portfolio_data)

        assert snapshot_id is not None
        assert isinstance(snapshot_id, int)
        assert snapshot_id > 0

    def test_get_latest_snapshot(self, temp_db, sample_portfolio_data):
        """Test retrieving the latest snapshot"""
        db = DatabaseManager(temp_db)
        db.save_snapshot(sample_portfolio_data)

        latest = db.get_latest_snapshot()
        assert latest is not None
        assert latest['total_value'] == 150000.00
        assert 'timestamp' in latest
        assert 'id' in latest

    def test_get_latest_snapshot_empty_db(self, temp_db):
        """Test get_latest_snapshot returns None for empty database"""
        db = DatabaseManager(temp_db)
        latest = db.get_latest_snapshot()
        assert latest is None

    def test_get_snapshots(self, temp_db, sample_portfolio_data):
        """Test retrieving multiple snapshots"""
        db = DatabaseManager(temp_db)

        # Save 3 snapshots
        for i in range(3):
            db.save_snapshot(sample_portfolio_data)

        snapshots = db.get_snapshots(limit=2)
        assert len(snapshots) == 2
        assert snapshots[0]['id'] > snapshots[1]['id']  # Most recent first

    def test_get_holdings(self, temp_db, sample_portfolio_data):
        """Test retrieving holdings for a snapshot"""
        db = DatabaseManager(temp_db)
        snapshot_id = db.save_snapshot(sample_portfolio_data)

        holdings = db.get_holdings(snapshot_id)
        assert len(holdings) == 3  # AAPL, GOOGL, MSFT
        assert holdings[0]['symbol'] in ['AAPL', 'GOOGL', 'MSFT']

    def test_get_holdings_latest(self, temp_db, sample_portfolio_data):
        """Test retrieving holdings for latest snapshot"""
        db = DatabaseManager(temp_db)
        db.save_snapshot(sample_portfolio_data)

        holdings = db.get_holdings()  # No snapshot_id = latest
        assert len(holdings) == 3

    def test_get_holdings_empty_db(self, temp_db):
        """Test get_holdings returns empty list for empty database"""
        db = DatabaseManager(temp_db)
        holdings = db.get_holdings()
        assert holdings == []

    def test_get_portfolio_history(self, temp_db, sample_portfolio_data):
        """Test retrieving portfolio history"""
        db = DatabaseManager(temp_db)

        # Save multiple snapshots
        for i in range(5):
            db.save_snapshot(sample_portfolio_data)

        history = db.get_portfolio_history(days=7)
        assert len(history) == 5
        assert all('timestamp' in snap for snap in history)
        assert all('total_value' in snap for snap in history)

    def test_cleanup_old_snapshots(self, temp_db, sample_portfolio_data):
        """Test cleaning up old snapshots"""
        db = DatabaseManager(temp_db)
        conn = db._get_connection()
        cursor = conn.cursor()

        # Save a snapshot
        snapshot_id = db.save_snapshot(sample_portfolio_data)

        # Manually update timestamp to be 100 days old
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        cursor.execute(
            'UPDATE snapshots SET timestamp = ? WHERE id = ?',
            (old_date, snapshot_id)
        )
        conn.commit()
        conn.close()

        # Clean up snapshots older than 90 days
        deleted = db.cleanup_old_snapshots(keep_days=90)
        assert deleted == 1

        # Verify snapshot was deleted
        latest = db.get_latest_snapshot()
        assert latest is None

    def test_vacuum(self, temp_db, sample_portfolio_data):
        """Test database vacuum operation"""
        db = DatabaseManager(temp_db)
        db.save_snapshot(sample_portfolio_data)

        # Should not raise any errors
        db.vacuum()

    def test_snapshot_with_enriched_data(self, temp_db, sample_portfolio_data, sample_enrichment_data):
        """Test saving snapshot with enriched data"""
        # Add enrichment data to holdings
        for account_id, account in sample_portfolio_data['accounts'].items():
            for holding in account['holdings']:
                symbol = holding['symbol']
                if symbol in sample_enrichment_data:
                    holding.update(sample_enrichment_data[symbol])

        db = DatabaseManager(temp_db)
        snapshot_id = db.save_snapshot(sample_portfolio_data)

        holdings = db.get_holdings(snapshot_id)
        assert len(holdings) > 0
        assert holdings[0].get('company_name') is not None
        assert holdings[0].get('sector') is not None

    def test_multiple_snapshots_tracking(self, temp_db, sample_portfolio_data):
        """Test tracking multiple snapshots over time"""
        db = DatabaseManager(temp_db)

        # Save 3 snapshots with different values
        values = [100000, 105000, 110000]
        for value in values:
            data = sample_portfolio_data.copy()
            data['total_value'] = value
            db.save_snapshot(data)

        history = db.get_portfolio_history(days=1)
        assert len(history) == 3
        assert history[0]['total_value'] == 110000  # Most recent

    def test_holdings_order_by_value(self, temp_db, sample_portfolio_data):
        """Test that holdings are ordered by value descending"""
        db = DatabaseManager(temp_db)
        snapshot_id = db.save_snapshot(sample_portfolio_data)

        holdings = db.get_holdings(snapshot_id)
        values = [h['value'] for h in holdings]

        # Should be in descending order
        assert values == sorted(values, reverse=True)
