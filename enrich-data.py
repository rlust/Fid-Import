#!/usr/bin/env python3
"""
Slow enrichment script to add Yahoo Finance data to holdings
Runs with longer delays to avoid rate limiting
"""

import json
import csv
import sqlite3
import yfinance as yf
from time import sleep
from datetime import datetime
import sys

def enrich_ticker_data(ticker, delay=3, max_retries=3):
    """Fetch data for a single ticker with delay and retry logic"""
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

    for attempt in range(max_retries):
        try:
            print(f"Fetching data for {ticker_clean}...", end=' ')
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
            print("✓")
            sleep(delay)
            return stock_info

        except Exception as e:
            error_msg = str(e)
            if 'Rate limit' in error_msg or '429' in error_msg:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                print(f"⚠ Rate limited. Waiting {wait_time}s...")
                sleep(wait_time)
                if attempt < max_retries - 1:
                    continue
            else:
                print(f"⚠ Error: {error_msg}")
                break

    # If all retries failed
    return {
        'company_name': ticker_clean,
        'sector': 'Unknown',
        'industry': 'Unknown',
        'market_cap': None,
        'pe_ratio': None,
        'dividend_yield': None
    }

def enrich_from_json(json_file, delay=2):
    """Enrich data from a JSON file"""
    print(f"\n{'='*60}")
    print(f"Enriching data from: {json_file}")
    print(f"{'='*60}\n")

    # Load JSON
    with open(json_file, 'r') as f:
        data = json.load(f)

    accounts = data.get('accounts', {})
    total_portfolio_value = sum(account.get('balance', 0) for account in accounts.values())

    # Get unique tickers
    unique_tickers = set()
    for account_data in accounts.values():
        for stock in account_data.get('stocks', []):
            ticker = stock.get('ticker', '').replace('**', '').strip()
            if ticker and ticker not in ['N/A', 'FZDXX', 'FDRXX', 'SPAXX', 'SPRXX', 'FDLXX', 'FZFXX']:
                unique_tickers.add(ticker)

    print(f"Found {len(unique_tickers)} unique tickers to enrich\n")

    # Fetch data for each unique ticker
    ticker_data_cache = {}
    for i, ticker in enumerate(sorted(unique_tickers), 1):
        print(f"[{i}/{len(unique_tickers)}] ", end='')
        ticker_data_cache[ticker] = enrich_ticker_data(ticker, delay)

    # Update accounts with enriched data
    for account_id, account_data in accounts.items():
        enriched_stocks = []
        for stock in account_data.get('stocks', []):
            ticker = stock.get('ticker', '').replace('**', '').strip()

            enriched_stock = stock.copy()

            # Add enrichment data
            if ticker in ticker_data_cache:
                enriched_stock.update(ticker_data_cache[ticker])
            elif not ticker or ticker in ['N/A', 'FZDXX', 'FDRXX', 'SPAXX', 'SPRXX', 'FDLXX', 'FZFXX']:
                enriched_stock.update({
                    'company_name': 'Cash/Money Market',
                    'sector': 'Cash',
                    'industry': 'Money Market',
                    'market_cap': None,
                    'pe_ratio': None,
                    'dividend_yield': None
                })

            # Add calculated weights
            enriched_stock['portfolio_weight'] = (stock.get('value', 0) / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
            enriched_stock['account_weight'] = (stock.get('value', 0) / account_data.get('balance', 1) * 100) if account_data.get('balance', 0) > 0 else 0

            enriched_stocks.append(enriched_stock)

        accounts[account_id]['stocks'] = enriched_stocks

    # Save enriched data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save to JSON
    enriched_json = f'fidelity_data_enriched_{timestamp}.json'
    with open(enriched_json, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"\n✓ Saved enriched JSON: {enriched_json}")

    # Save to CSV
    csv_file = f'fidelity_holdings_enriched_{timestamp}.csv'
    with open(csv_file, 'w', newline='') as f:
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
    print(f"✓ Saved enriched CSV: {csv_file}")

    # Update database
    db_name = 'fidelity_portfolio.db'
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Insert new snapshot
    cursor.execute('INSERT INTO snapshots (timestamp, total_value) VALUES (?, ?)',
                   (timestamp, total_portfolio_value))
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
    print(f"✓ Updated database: {db_name}")

    print(f"\n{'='*60}")
    print("✓ Enrichment complete!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    # Get the most recent JSON file
    import glob
    json_files = glob.glob('fidelity_data_*.json')

    if not json_files:
        print("Error: No fidelity data JSON files found!")
        print("Please run fid-import.py first to generate data.")
        sys.exit(1)

    # Sort by filename (timestamp) and get the most recent
    latest_json = sorted(json_files)[-1]

    print(f"\nUsing most recent data file: {latest_json}")
    print("This will take several minutes due to API rate limiting...")
    print("You can adjust the delay between requests if needed.\n")

    # Ask for delay
    try:
        delay = input("Enter delay between API calls in seconds [default: 3]: ").strip()
        delay = float(delay) if delay else 3.0
    except:
        delay = 3.0

    print(f"\nStarting enrichment with {delay}s delay between requests...")
    print("The script will automatically handle rate limits with exponential backoff.\n")

    enrich_from_json(latest_json, delay)
