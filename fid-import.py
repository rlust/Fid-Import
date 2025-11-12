from fidelity.fidelity import FidelityAutomation
import os
import json
import csv
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
import yfinance as yf
from time import sleep

# Load environment variables from .env file
load_dotenv()

def enrich_holdings_data(accounts, total_portfolio_value):
    """Enrich holdings with additional data from Yahoo Finance"""
    print("\nEnriching holdings with additional data...")

    enriched_accounts = {}
    processed_tickers = {}  # Cache to avoid duplicate API calls

    for account_id, account_data in accounts.items():
        enriched_accounts[account_id] = account_data.copy()
        enriched_stocks = []

        for stock in account_data.get('stocks', []):
            ticker = stock.get('ticker', '').replace('**', '').strip()

            # Skip if no valid ticker or is cash/special position
            if not ticker or ticker in ['N/A', 'FZDXX', 'FDRXX', 'SPAXX', 'SPRXX', 'FDLXX', 'FZFXX']:
                enriched_stock = stock.copy()
                enriched_stock.update({
                    'company_name': 'Cash/Money Market',
                    'sector': 'Cash',
                    'industry': 'Money Market',
                    'market_cap': None,
                    'pe_ratio': None,
                    'dividend_yield': None,
                    'portfolio_weight': (stock.get('value', 0) / total_portfolio_value * 100) if total_portfolio_value > 0 else 0,
                    'account_weight': (stock.get('value', 0) / account_data.get('balance', 1) * 100) if account_data.get('balance', 0) > 0 else 0
                })
                enriched_stocks.append(enriched_stock)
                continue

            # Check cache first
            if ticker in processed_tickers:
                stock_info = processed_tickers[ticker]
            else:
                try:
                    print(f"  Fetching data for {ticker}...")
                    yf_ticker = yf.Ticker(ticker)
                    info = yf_ticker.info

                    stock_info = {
                        'company_name': info.get('longName', info.get('shortName', ticker)),
                        'sector': info.get('sector', 'Unknown'),
                        'industry': info.get('industry', 'Unknown'),
                        'market_cap': info.get('marketCap'),
                        'pe_ratio': info.get('trailingPE'),
                        'dividend_yield': info.get('dividendYield')
                    }
                    processed_tickers[ticker] = stock_info
                    sleep(0.1)  # Small delay to avoid rate limiting

                except Exception as e:
                    print(f"  Warning: Could not fetch data for {ticker}: {e}")
                    stock_info = {
                        'company_name': ticker,
                        'sector': 'Unknown',
                        'industry': 'Unknown',
                        'market_cap': None,
                        'pe_ratio': None,
                        'dividend_yield': None
                    }
                    processed_tickers[ticker] = stock_info

            # Create enriched stock entry
            enriched_stock = stock.copy()
            enriched_stock.update(stock_info)
            enriched_stock['portfolio_weight'] = (stock.get('value', 0) / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
            enriched_stock['account_weight'] = (stock.get('value', 0) / account_data.get('balance', 1) * 100) if account_data.get('balance', 0) > 0 else 0

            enriched_stocks.append(enriched_stock)

        enriched_accounts[account_id]['stocks'] = enriched_stocks

    print("✓ Holdings enrichment complete!")
    return enriched_accounts

def save_to_json(account_info, accounts, holdings, timestamp):
    """Save data to JSON file"""
    data = {
        'timestamp': timestamp,
        'account_info': account_info,
        'accounts': accounts,
        'holdings': holdings
    }

    filename = f'fidelity_data_{timestamp}.json'
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n✓ Saved to JSON: {filename}")
    return filename

def save_to_csv(accounts, timestamp):
    """Save holdings to CSV files"""
    # Save account summary
    accounts_file = f'fidelity_accounts_{timestamp}.csv'
    with open(accounts_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Account ID', 'Nickname', 'Balance', 'Withdrawal Balance'])
        for account_id, account_data in accounts.items():
            writer.writerow([
                account_id,
                account_data.get('nickname', ''),
                account_data.get('balance', 0),
                account_data.get('withdrawal_balance', 0)
            ])
    print(f"✓ Saved accounts to CSV: {accounts_file}")

    # Save all holdings to a single CSV with enriched data
    holdings_file = f'fidelity_holdings_{timestamp}.csv'
    with open(holdings_file, 'w', newline='') as f:
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
    print(f"✓ Saved holdings to CSV: {holdings_file}")

    return accounts_file, holdings_file

def save_to_database(account_info, accounts, holdings, timestamp):
    """Save data to SQLite database"""
    db_name = 'fidelity_portfolio.db'
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            total_value REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            account_id TEXT,
            nickname TEXT,
            balance REAL,
            withdrawal_balance REAL,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS holdings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER,
            account_id TEXT,
            ticker TEXT,
            company_name TEXT,
            quantity REAL,
            last_price REAL,
            value REAL,
            sector TEXT,
            industry TEXT,
            market_cap REAL,
            pe_ratio REAL,
            dividend_yield REAL,
            portfolio_weight REAL,
            account_weight REAL,
            FOREIGN KEY (snapshot_id) REFERENCES snapshots(id)
        )
    ''')

    # Calculate total portfolio value
    total_value = sum(account.get('balance', 0) for account in accounts.values())

    # Insert snapshot
    cursor.execute('INSERT INTO snapshots (timestamp, total_value) VALUES (?, ?)',
                   (timestamp, total_value))
    snapshot_id = cursor.lastrowid

    # Insert accounts
    for account_id, account_data in accounts.items():
        cursor.execute('''
            INSERT INTO accounts (snapshot_id, account_id, nickname, balance, withdrawal_balance)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            snapshot_id,
            account_id,
            account_data.get('nickname', ''),
            account_data.get('balance', 0),
            account_data.get('withdrawal_balance', 0)
        ))

    # Insert holdings
    for account_id, account_data in accounts.items():
        for stock in account_data.get('stocks', []):
            cursor.execute('''
                INSERT INTO holdings (
                    snapshot_id, account_id, ticker, company_name, quantity, last_price, value,
                    sector, industry, market_cap, pe_ratio, dividend_yield, portfolio_weight, account_weight
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot_id,
                account_id,
                stock.get('ticker', ''),
                stock.get('company_name', ''),
                stock.get('quantity', 0),
                stock.get('last_price', 0),
                stock.get('value', 0),
                stock.get('sector', ''),
                stock.get('industry', ''),
                stock.get('market_cap'),
                stock.get('pe_ratio'),
                stock.get('dividend_yield'),
                stock.get('portfolio_weight', 0),
                stock.get('account_weight', 0)
            ))

    conn.commit()
    conn.close()
    print(f"✓ Saved to database: {db_name}")
    print(f"  Snapshot ID: {snapshot_id}, Total Portfolio Value: ${total_value:,.2f}")

    return db_name

def pull_account_data():
    # Initialize FidelityAutomation (headless browser)
    print("Connecting to Fidelity...")
    fidelity = FidelityAutomation(headless=True)

    # Login with credentials from environment variables
    print("Logging in...")
    fidelity.login(
        username=os.getenv('FIDELITY_USERNAME'),
        password=os.getenv('FIDELITY_PASSWORD'),
        totp_secret=os.getenv('FIDELITY_MFA_SECRET')
    )

    # Get account information
    print("Fetching account data...")
    account_info = fidelity.getAccountInfo()
    accounts = fidelity.get_list_of_accounts()
    holdings = fidelity.summary_holdings()

    # Close the browser
    fidelity.close_browser()

    # Calculate total portfolio value
    total_portfolio_value = sum(account.get('balance', 0) for account in accounts.values())

    # Add basic calculated fields (weights) without Yahoo Finance data
    for account_id, account_data in accounts.items():
        for stock in account_data.get('stocks', []):
            stock['portfolio_weight'] = (stock.get('value', 0) / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
            stock['account_weight'] = (stock.get('value', 0) / account_data.get('balance', 1) * 100) if account_data.get('balance', 0) > 0 else 0
            # Set default empty values for enrichment fields
            stock['company_name'] = stock.get('ticker', '')
            stock['sector'] = ''
            stock['industry'] = ''
            stock['market_cap'] = None
            stock['pe_ratio'] = None
            stock['dividend_yield'] = None

    # Generate timestamp for filenames
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    print("\n" + "="*50)
    print("SAVING DATA TO MULTIPLE FORMATS")
    print("="*50)

    # Save to JSON
    save_to_json(account_info, accounts, holdings, timestamp)

    # Save to CSV
    save_to_csv(accounts, timestamp)

    # Save to SQLite database
    save_to_database(account_info, accounts, holdings, timestamp)

    print("\n" + "="*50)
    print("✓ All data saved successfully!")
    print("="*50)

    # Print summary
    total_value = sum(account.get('balance', 0) for account in accounts.values())
    print(f"\nPortfolio Summary:")
    print(f"  Total Accounts: {len(accounts)}")
    print(f"  Total Value: ${total_value:,.2f}")

pull_account_data()