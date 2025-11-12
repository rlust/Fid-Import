"""
Portfolio data collector from Fidelity
Handles authentication, data retrieval, and basic metrics calculation
"""

import os
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger

from fidelity.fidelity import FidelityAutomation


class PortfolioCollector:
    """Collects portfolio data from Fidelity"""

    def __init__(self, username: Optional[str] = None, password: Optional[str] = None,
                 mfa_secret: Optional[str] = None, headless: bool = True):
        """
        Initialize the collector

        Args:
            username: Fidelity username (if None, reads from config)
            password: Fidelity password (if None, reads from config)
            mfa_secret: TOTP secret for 2FA (if None, reads from config)
            headless: Run browser in headless mode
        """
        self.username = username or os.getenv('FIDELITY_USERNAME')
        self.password = password or os.getenv('FIDELITY_PASSWORD')
        self.mfa_secret = mfa_secret or os.getenv('FIDELITY_MFA_SECRET')
        self.headless = headless
        self.fidelity = None

        if not all([self.username, self.password, self.mfa_secret]):
            raise ValueError("Fidelity credentials not provided. Set environment variables or pass to constructor.")

    def connect(self) -> None:
        """Connect to Fidelity and authenticate"""
        logger.info("Connecting to Fidelity...")
        try:
            self.fidelity = FidelityAutomation(headless=self.headless)
            logger.info("Logging in...")
            self.fidelity.login(
                username=self.username,
                password=self.password,
                totp_secret=self.mfa_secret
            )
            logger.success("Successfully authenticated with Fidelity")
        except Exception as e:
            logger.error(f"Failed to connect to Fidelity: {e}")
            raise

    def collect_data(self) -> Dict[str, Any]:
        """
        Collect all account and holdings data

        Returns:
            Dictionary containing account_info, accounts, and holdings
        """
        if not self.fidelity:
            raise RuntimeError("Not connected. Call connect() first.")

        logger.info("Fetching account data...")
        try:
            account_info = self.fidelity.getAccountInfo()
            accounts = self.fidelity.get_list_of_accounts()
            holdings = self.fidelity.summary_holdings()

            logger.success(f"Retrieved data for {len(accounts)} accounts")

            return {
                'account_info': account_info,
                'accounts': accounts,
                'holdings': holdings,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to collect data: {e}")
            raise

    def calculate_weights(self, accounts: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate portfolio and account weights for all holdings

        Args:
            accounts: Dictionary of account data

        Returns:
            Enhanced accounts dictionary with calculated weights
        """
        logger.info("Calculating portfolio weights...")

        # Calculate total portfolio value
        total_portfolio_value = sum(account.get('balance', 0) for account in accounts.values())

        # Add weights to each holding
        for account_id, account_data in accounts.items():
            for stock in account_data.get('stocks', []):
                stock['portfolio_weight'] = (
                    (stock.get('value', 0) / total_portfolio_value * 100)
                    if total_portfolio_value > 0 else 0
                )
                stock['account_weight'] = (
                    (stock.get('value', 0) / account_data.get('balance', 1) * 100)
                    if account_data.get('balance', 0) > 0 else 0
                )

                # Set default empty values for enrichment fields
                stock.setdefault('company_name', stock.get('ticker', ''))
                stock.setdefault('sector', '')
                stock.setdefault('industry', '')
                stock.setdefault('market_cap', None)
                stock.setdefault('pe_ratio', None)
                stock.setdefault('dividend_yield', None)

        logger.success(f"Calculated weights for portfolio value: ${total_portfolio_value:,.2f}")
        return accounts

    def disconnect(self) -> None:
        """Close the browser connection"""
        if self.fidelity:
            logger.info("Closing browser connection...")
            self.fidelity.close_browser()
            self.fidelity = None

    def run(self) -> Dict[str, Any]:
        """
        Run complete data collection workflow

        Returns:
            Dictionary with all collected and processed data
        """
        try:
            self.connect()
            data = self.collect_data()
            data['accounts'] = self.calculate_weights(data['accounts'])
            return data
        finally:
            self.disconnect()

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
