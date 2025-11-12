"""
Pytest fixtures and configuration for test suite
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime
import json


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_db(temp_dir):
    """Create a temporary database file"""
    db_path = temp_dir / "test_portfolio.db"
    yield str(db_path)


@pytest.fixture
def sample_accounts_data():
    """Sample accounts data for testing"""
    return {
        "account1": {
            "account_id": "Z12345678",
            "nickname": "Individual Account",
            "account_type": "INDIVIDUAL",
            "balance": 100000.00,
            "holdings": [
                {
                    "symbol": "AAPL",
                    "quantity": 100,
                    "last_price": 150.00,
                    "value": 15000.00,
                    "cost_basis": 12000.00,
                    "gain_loss": 3000.00,
                    "gain_loss_percent": 25.0
                },
                {
                    "symbol": "GOOGL",
                    "quantity": 50,
                    "last_price": 140.00,
                    "value": 7000.00,
                    "cost_basis": 6500.00,
                    "gain_loss": 500.00,
                    "gain_loss_percent": 7.69
                }
            ]
        },
        "account2": {
            "account_id": "Z87654321",
            "nickname": "Roth IRA",
            "account_type": "ROTH_IRA",
            "balance": 50000.00,
            "holdings": [
                {
                    "symbol": "MSFT",
                    "quantity": 75,
                    "last_price": 380.00,
                    "value": 28500.00,
                    "cost_basis": 25000.00,
                    "gain_loss": 3500.00,
                    "gain_loss_percent": 14.0
                }
            ]
        }
    }


@pytest.fixture
def sample_portfolio_data(sample_accounts_data):
    """Complete portfolio data structure"""
    return {
        "timestamp": datetime.now().isoformat(),
        "accounts": sample_accounts_data,
        "total_value": 150000.00,
        "total_holdings": 3
    }


@pytest.fixture
def sample_enrichment_data():
    """Sample Yahoo Finance enrichment data"""
    return {
        "AAPL": {
            "company_name": "Apple Inc.",
            "sector": "Technology",
            "industry": "Consumer Electronics",
            "market_cap": 3000000000000,
            "pe_ratio": 29.5,
            "dividend_yield": 0.5,
            "fifty_two_week_high": 199.62,
            "fifty_two_week_low": 143.90
        },
        "GOOGL": {
            "company_name": "Alphabet Inc.",
            "sector": "Communication Services",
            "industry": "Internet Content & Information",
            "market_cap": 1800000000000,
            "pe_ratio": 27.3,
            "dividend_yield": 0.0,
            "fifty_two_week_high": 155.27,
            "fifty_two_week_low": 129.40
        },
        "MSFT": {
            "company_name": "Microsoft Corporation",
            "sector": "Technology",
            "industry": "Software—Infrastructure",
            "market_cap": 2800000000000,
            "pe_ratio": 35.8,
            "dividend_yield": 0.8,
            "fifty_two_week_high": 468.35,
            "fifty_two_week_low": 324.39
        }
    }


@pytest.fixture
def sample_config_dict():
    """Sample configuration dictionary"""
    return {
        "credentials": {
            "fidelity": {
                "username": "test_user",
                "password": "test_pass",
                "mfa_secret": "TESTMFASECRET123"
            }
        },
        "sync": {
            "schedule": "0 18 * * *",
            "enrichment_schedule": "0 19 * * 0",
            "headless": True
        },
        "enrichment": {
            "enabled": True,
            "delay_seconds": 3.0,
            "max_retries": 3
        },
        "storage": {
            "output_dir": ".",
            "retention_days": 90,
            "auto_cleanup": True,
            "formats": ["json", "csv", "sqlite"]
        },
        "database": {
            "path": "fidelity_portfolio.db"
        },
        "logging": {
            "level": "INFO",
            "file": "logs/portfolio-tracker.log",
            "rotation": "10 MB",
            "retention": "30 days"
        }
    }


@pytest.fixture
def temp_config_file(temp_dir, sample_config_dict):
    """Create a temporary config file"""
    import yaml
    config_path = temp_dir / "test_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(sample_config_dict, f)
    yield str(config_path)


@pytest.fixture
def temp_json_file(temp_dir, sample_portfolio_data):
    """Create a temporary JSON data file"""
    json_path = temp_dir / "test_data.json"
    with open(json_path, 'w') as f:
        json.dump(sample_portfolio_data, f, indent=2)
    yield str(json_path)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for credentials"""
    monkeypatch.setenv("FIDELITY_USERNAME", "test_user")
    monkeypatch.setenv("FIDELITY_PASSWORD", "test_pass")
    monkeypatch.setenv("FIDELITY_MFA_SECRET", "TESTMFASECRET123")
    yield


@pytest.fixture
def mock_fidelity_client(mocker):
    """Mock FidelityAutomation client"""
    mock_client = mocker.MagicMock()
    mock_client.get_account_info.return_value = {
        "Z12345678": {
            "nickname": "Individual Account",
            "type": "INDIVIDUAL",
            "balance": 100000.00
        }
    }
    return mock_client


@pytest.fixture
def mock_yfinance_ticker(mocker):
    """Mock yfinance Ticker object"""
    mock_ticker = mocker.MagicMock()
    mock_ticker.info = {
        "longName": "Apple Inc.",
        "sector": "Technology",
        "industry": "Consumer Electronics",
        "marketCap": 3000000000000,
        "trailingPE": 29.5,
        "dividendYield": 0.005,
        "fiftyTwoWeekHigh": 199.62,
        "fiftyTwoWeekLow": 143.90
    }
    return mock_ticker
