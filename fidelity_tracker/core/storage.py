"""
Storage handlers for JSON and CSV formats
"""

import json
import csv
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
from loguru import logger


class StorageManager:
    """Manages JSON and CSV file operations"""

    def __init__(self, output_dir: str = '.'):
        """
        Initialize storage manager

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def save_json(self, data: Dict[str, Any], timestamp: str = None) -> Path:
        """
        Save data to JSON file

        Args:
            data: Data dictionary to save
            timestamp: Optional timestamp string (generated if not provided)

        Returns:
            Path to saved file
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        filename = self.output_dir / f'fidelity_data_{timestamp}.json'

        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            logger.success(f"Saved JSON: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save JSON: {e}")
            raise

    def save_accounts_csv(self, accounts: Dict[str, Any], timestamp: str = None) -> Path:
        """
        Save accounts summary to CSV

        Args:
            accounts: Dictionary of account data
            timestamp: Optional timestamp string

        Returns:
            Path to saved file
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        filename = self.output_dir / f'fidelity_accounts_{timestamp}.csv'

        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Account ID', 'Nickname', 'Balance', 'Withdrawal Balance'])

                for account_id, account_data in accounts.items():
                    writer.writerow([
                        account_id,
                        account_data.get('nickname', ''),
                        account_data.get('balance', 0),
                        account_data.get('withdrawal_balance', 0)
                    ])

            logger.success(f"Saved accounts CSV: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save accounts CSV: {e}")
            raise

    def save_holdings_csv(self, accounts: Dict[str, Any], timestamp: str = None) -> Path:
        """
        Save holdings to CSV with all enrichment data

        Args:
            accounts: Dictionary of account data
            timestamp: Optional timestamp string

        Returns:
            Path to saved file
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        filename = self.output_dir / f'fidelity_holdings_{timestamp}.csv'

        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'Account ID', 'Account Nickname', 'Ticker', 'Company Name',
                    'Quantity', 'Last Price', 'Value',
                    'Sector', 'Industry', 'Market Cap', 'PE Ratio', 'Dividend Yield (%)',
                    'Portfolio Weight (%)', 'Account Weight (%)'
                ])

                for account_id, account_data in accounts.items():
                    nickname = account_data.get('nickname', '')
                    for stock in account_data.get('stocks', []):
                        dividend_yield = stock.get('dividend_yield')
                        dividend_yield_pct = (dividend_yield * 100) if dividend_yield else None

                        writer.writerow([
                            account_id,
                            nickname,
                            stock.get('ticker', ''),
                            stock.get('company_name', ''),
                            stock.get('quantity', 0),
                            stock.get('last_price', 0),
                            stock.get('value', 0),
                            stock.get('sector', ''),
                            stock.get('industry', ''),
                            stock.get('market_cap', ''),
                            stock.get('pe_ratio', ''),
                            round(dividend_yield_pct, 2) if dividend_yield_pct else '',
                            round(stock.get('portfolio_weight', 0), 2),
                            round(stock.get('account_weight', 0), 2)
                        ])

            logger.success(f"Saved holdings CSV: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save holdings CSV: {e}")
            raise

    def save_all(self, data: Dict[str, Any], timestamp: str = None) -> Dict[str, Path]:
        """
        Save data to all formats (JSON, accounts CSV, holdings CSV)

        Args:
            data: Complete data dictionary
            timestamp: Optional timestamp string

        Returns:
            Dictionary mapping format names to file paths
        """
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        accounts = data.get('accounts', {})

        return {
            'json': self.save_json(data, timestamp),
            'accounts_csv': self.save_accounts_csv(accounts, timestamp),
            'holdings_csv': self.save_holdings_csv(accounts, timestamp)
        }

    def cleanup_old_files(self, keep_days: int = 90, pattern: str = 'fidelity_*.{json,csv}'):
        """
        Delete old data files

        Args:
            keep_days: Number of days to keep
            pattern: Glob pattern for files to consider
        """
        cutoff_time = datetime.now().timestamp() - (keep_days * 24 * 60 * 60)
        deleted_count = 0

        for file_path in self.output_dir.glob(pattern):
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                deleted_count += 1
                logger.debug(f"Deleted old file: {file_path}")

        logger.info(f"Cleaned up {deleted_count} old files")
        return deleted_count

    def list_snapshots(self, file_type: str = 'json') -> List[Path]:
        """
        List available snapshot files

        Args:
            file_type: Type of files to list ('json', 'csv', or 'all')

        Returns:
            List of file paths sorted by modification time (newest first)
        """
        patterns = {
            'json': 'fidelity_data_*.json',
            'csv': 'fidelity_*.csv',
            'all': 'fidelity_*'
        }

        pattern = patterns.get(file_type, patterns['all'])
        files = sorted(
            self.output_dir.glob(pattern),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )

        return files
