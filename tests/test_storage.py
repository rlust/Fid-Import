"""
Unit tests for fidelity_tracker.core.storage module
"""

import pytest
import json
import csv
from pathlib import Path
from datetime import datetime, timedelta
from fidelity_tracker.core.storage import StorageManager


@pytest.mark.unit
class TestStorageManager:
    """Test StorageManager class"""

    def test_init(self, temp_dir):
        """Test StorageManager initialization"""
        storage = StorageManager(str(temp_dir))
        assert storage.output_dir == Path(temp_dir)

    def test_save_json(self, temp_dir, sample_portfolio_data):
        """Test saving data to JSON file"""
        storage = StorageManager(str(temp_dir))
        filepath = storage.save_json(sample_portfolio_data, "test_20241112_120000")

        assert filepath.exists()
        assert filepath.name == "fidelity_data_test_20241112_120000.json"

        # Verify content
        with open(filepath) as f:
            data = json.load(f)
        assert data['total_value'] == 150000.00
        assert 'accounts' in data

    def test_save_accounts_csv(self, temp_dir, sample_portfolio_data):
        """Test saving accounts to CSV"""
        storage = StorageManager(str(temp_dir))
        filepath = storage.save_accounts_csv(sample_portfolio_data, "test_20241112_120000")

        assert filepath.exists()
        assert filepath.name == "fidelity_accounts_test_20241112_120000.csv"

        # Verify content
        with open(filepath, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2  # Two accounts
        assert rows[0]['account_id'] in ['Z12345678', 'Z87654321']
        assert 'balance' in rows[0]

    def test_save_holdings_csv(self, temp_dir, sample_portfolio_data):
        """Test saving holdings to CSV"""
        storage = StorageManager(str(temp_dir))
        filepath = storage.save_holdings_csv(sample_portfolio_data, "test_20241112_120000")

        assert filepath.exists()
        assert filepath.name == "fidelity_holdings_test_20241112_120000.csv"

        # Verify content
        with open(filepath, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3  # Three holdings total
        assert rows[0]['symbol'] in ['AAPL', 'GOOGL', 'MSFT']
        assert 'value' in rows[0]
        assert 'portfolio_weight' in rows[0]

    def test_save_holdings_csv_with_enrichment(self, temp_dir, sample_portfolio_data, sample_enrichment_data):
        """Test saving enriched holdings to CSV"""
        # Add enrichment data
        for account_id, account in sample_portfolio_data['accounts'].items():
            for holding in account['holdings']:
                symbol = holding['symbol']
                if symbol in sample_enrichment_data:
                    holding.update(sample_enrichment_data[symbol])

        storage = StorageManager(str(temp_dir))
        filepath = storage.save_holdings_csv(sample_portfolio_data, "test_20241112_120000")

        # Verify enriched data is in CSV
        with open(filepath, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert rows[0].get('company_name') is not None
        assert rows[0].get('sector') is not None
        assert rows[0].get('industry') is not None

    def test_save_all(self, temp_dir, sample_portfolio_data):
        """Test saving all file formats at once"""
        storage = StorageManager(str(temp_dir))
        files = storage.save_all(sample_portfolio_data, "test_20241112_120000")

        assert 'json' in files
        assert 'accounts_csv' in files
        assert 'holdings_csv' in files

        assert files['json'].exists()
        assert files['accounts_csv'].exists()
        assert files['holdings_csv'].exists()

    def test_list_snapshots_json(self, temp_dir, sample_portfolio_data):
        """Test listing JSON snapshot files"""
        storage = StorageManager(str(temp_dir))

        # Create multiple snapshots
        for i in range(3):
            storage.save_json(sample_portfolio_data, f"test_2024111{i}_120000")

        snapshots = storage.list_snapshots('json')
        assert len(snapshots) == 3
        assert all(Path(s).suffix == '.json' for s in snapshots)

    def test_list_snapshots_csv(self, temp_dir, sample_portfolio_data):
        """Test listing CSV snapshot files"""
        storage = StorageManager(str(temp_dir))

        # Create multiple snapshots
        for i in range(2):
            storage.save_accounts_csv(sample_portfolio_data, f"test_2024111{i}_120000")

        snapshots = storage.list_snapshots('accounts_csv')
        assert len(snapshots) == 2
        assert all('accounts' in Path(s).name for s in snapshots)

    def test_list_snapshots_empty(self, temp_dir):
        """Test listing snapshots in empty directory"""
        storage = StorageManager(str(temp_dir))
        snapshots = storage.list_snapshots('json')
        assert snapshots == []

    def test_cleanup_old_files(self, temp_dir, sample_portfolio_data):
        """Test cleaning up old files"""
        storage = StorageManager(str(temp_dir))

        # Create a recent file
        recent_file = storage.save_json(sample_portfolio_data, "test_20241112_120000")

        # Create an old file
        old_timestamp = (datetime.now() - timedelta(days=100)).strftime('%Y%m%d_%H%M%S')
        old_file = storage.save_json(sample_portfolio_data, f"test_{old_timestamp}")

        # Manually set old file's modification time
        old_time = (datetime.now() - timedelta(days=100)).timestamp()
        old_file.touch()
        import os
        os.utime(old_file, (old_time, old_time))

        # Clean up files older than 90 days
        deleted = storage.cleanup_old_files(keep_days=90)
        assert deleted >= 1

        # Recent file should still exist
        assert recent_file.exists()

    def test_get_latest_snapshot(self, temp_dir, sample_portfolio_data):
        """Test getting the most recent snapshot"""
        storage = StorageManager(str(temp_dir))

        # Create snapshots at different times
        storage.save_json(sample_portfolio_data, "test_20241110_120000")
        storage.save_json(sample_portfolio_data, "test_20241111_120000")
        latest_file = storage.save_json(sample_portfolio_data, "test_20241112_120000")

        snapshots = storage.list_snapshots('json')
        # Snapshots are sorted by modification time, most recent first
        assert Path(snapshots[0]) == latest_file

    def test_portfolio_weights_in_csv(self, temp_dir, sample_portfolio_data):
        """Test that portfolio weights are correctly saved in CSV"""
        storage = StorageManager(str(temp_dir))

        # Add portfolio weights to holdings
        total_value = sample_portfolio_data['total_value']
        for account in sample_portfolio_data['accounts'].values():
            for holding in account['holdings']:
                holding['portfolio_weight'] = (holding['value'] / total_value) * 100

        filepath = storage.save_holdings_csv(sample_portfolio_data, "test_20241112_120000")

        with open(filepath, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        # Check that weights are present and reasonable
        assert all('portfolio_weight' in row for row in rows)
        total_weight = sum(float(row['portfolio_weight']) for row in rows)
        assert 99.5 <= total_weight <= 100.5  # Allow for rounding

    def test_account_weights_in_csv(self, temp_dir, sample_portfolio_data):
        """Test that account weights are correctly saved in CSV"""
        storage = StorageManager(str(temp_dir))

        # Add account weights
        for account in sample_portfolio_data['accounts'].values():
            account_balance = account['balance']
            for holding in account['holdings']:
                holding['account_weight'] = (holding['value'] / account_balance) * 100

        filepath = storage.save_holdings_csv(sample_portfolio_data, "test_20241112_120000")

        with open(filepath, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert all('account_weight' in row for row in rows)

    def test_json_serialization(self, temp_dir, sample_portfolio_data):
        """Test that JSON properly serializes all data types"""
        storage = StorageManager(str(temp_dir))

        # Add some edge case data
        sample_portfolio_data['test_null'] = None
        sample_portfolio_data['test_float'] = 123.456
        sample_portfolio_data['test_int'] = 12345

        filepath = storage.save_json(sample_portfolio_data, "test_20241112_120000")

        # Should not raise errors
        with open(filepath) as f:
            data = json.load(f)

        assert data['test_null'] is None
        assert isinstance(data['test_float'], float)
        assert isinstance(data['test_int'], int)
