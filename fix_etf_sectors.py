#!/usr/bin/env python3
"""
Manually fix sector classifications for common ETFs that Fidelity doesn't provide sector data for.
This is a workaround for when Yahoo Finance rate limits prevent automatic enrichment.
"""

import sqlite3
from datetime import datetime

# Manual ETF sector classifications for well-known ETFs
ETF_SECTORS = {
    # Broad Market ETFs
    'QQQ': ('ETF - Technology', 'Large Cap Tech'),
    'VOO': ('ETF - Broad Market', 'S&P 500'),
    'IVV': ('ETF - Broad Market', 'S&P 500'),
    'VTI': ('ETF - Broad Market', 'Total Stock Market'),
    'SPY': ('ETF - Broad Market', 'S&P 500'),

    # Dividend ETFs
    'SCHD': ('ETF - Dividend', 'High Dividend Yield'),
    'DGRO': ('ETF - Dividend', 'Dividend Growth'),
    'VYM': ('ETF - Dividend', 'High Dividend Yield'),
    'RDIV': ('ETF - Dividend', 'Rising Dividends'),

    # Sector ETFs
    'XLF': ('ETF - Financials', 'Financial Sector'),
    'XLU': ('ETF - Utilities', 'Utilities Sector'),
    'VHT': ('ETF - Healthcare', 'Healthcare Sector'),
    'FHLC': ('ETF - Healthcare', 'Healthcare Sector'),
    'IGV': ('ETF - Technology', 'Software & Services'),
    'FNCL': ('ETF - Financials', 'Financial Sector'),

    # Bond ETFs
    'BND': ('ETF - Bonds', 'Total Bond Market'),
    'BIV': ('ETF - Bonds', 'Intermediate-Term Bonds'),
    'BSV': ('ETF - Bonds', 'Short-Term Bonds'),
    'VCLT': ('ETF - Bonds', 'Long-Term Corporate Bonds'),
    'SCHP': ('ETF - Bonds', 'TIPS'),

    # International ETFs
    'SCHF': ('ETF - International', 'Developed Markets'),
    'IEFA': ('ETF - International', 'Developed Markets'),
    'SCHC': ('ETF - International', 'Small Cap International'),
    'VWO': ('ETF - International', 'Emerging Markets'),
    'SCHE': ('ETF - International', 'Emerging Markets'),

    # Commodity ETFs
    'GLD': ('ETF - Commodities', 'Gold'),
    'IAU': ('ETF - Commodities', 'Gold'),
    'SLV': ('ETF - Commodities', 'Silver'),

    # Crypto ETFs
    'BITO': ('ETF - Cryptocurrency', 'Bitcoin Strategy'),
    'GBTC': ('ETF - Cryptocurrency', 'Bitcoin'),
    'IBIT': ('ETF - Cryptocurrency', 'Bitcoin'),

    # Thematic ETFs
    'LIT': ('ETF - Thematic', 'Lithium & Battery Tech'),
    'ARGT': ('ETF - Thematic', 'Global X Silver Miners'),

    # Small Cap ETFs
    'SCHA': ('ETF - Small Cap', 'Small Cap Blend'),
    'SCHX': ('ETF - Broad Market', 'Large Cap Blend'),

    # Value ETFs
    'IUSV': ('ETF - Value', 'Large Cap Value'),
    'SPYV': ('ETF - Value', 'Large Cap Value'),

    # Income ETFs
    'JEPI': ('ETF - Income', 'Equity Premium Income'),

    # Sector Specific
    'ONEQ': ('ETF - Technology', 'NASDAQ Composite'),

    # Leveraged ETFs
    'TQQQ': ('ETF - Leveraged', '3x Long NASDAQ-100'),

    # Real Estate
    'SCHH': ('ETF - Real Estate', 'REIT'),

    # Fidelity Sector ETFs
    'FNDA': ('ETF - Blend', 'Fundamental Alpha'),
    'FNDC': ('ETF - International', 'Developed Markets'),
    'FNDE': ('ETF - International', 'Emerging Markets'),
    'FNDF': ('ETF - Blend', 'Fundamental International'),
    'FNDX': ('ETF - Broad Market', 'Fundamental Index'),
    'FELV': ('ETF - Value', 'Enhanced Large Cap Value'),
    'FYEE': ('ETF - High Yield', 'High Yield'),

    # Other Schwab ETFs
    'DJD': ('ETF - Dividend', 'Dow Jones Dividend'),
}

def fix_etf_sectors(db_path='fidelity_portfolio.db'):
    """Update ticker_metadata with manual ETF sector classifications"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    updated_count = 0
    not_found = []

    for ticker, (sector, industry) in ETF_SECTORS.items():
        # Check if ticker exists in cache
        cursor.execute("SELECT ticker FROM ticker_metadata WHERE ticker = ?", (ticker,))
        if cursor.fetchone():
            # Update the sector and industry
            cursor.execute("""
                UPDATE ticker_metadata
                SET sector = ?,
                    industry = ?,
                    data_source = 'manual_classification',
                    last_updated = ?,
                    update_count = update_count + 1
                WHERE ticker = ?
            """, (sector, industry, datetime.now().isoformat(), ticker))
            updated_count += 1
            print(f"✓ Updated {ticker:8} → {sector:30} / {industry}")
        else:
            not_found.append(ticker)

    conn.commit()
    conn.close()

    print(f"\nUpdated {updated_count} ETF sector classifications")
    if not_found:
        print(f"Note: {len(not_found)} tickers not in cache (not in portfolio): {', '.join(not_found)}")

    return updated_count

if __name__ == '__main__':
    print("Manually fixing ETF sector classifications...")
    print("=" * 80)
    count = fix_etf_sectors()
    print("=" * 80)
    print(f"\n✓ Complete! Updated {count} ETFs")
    print("\nNext steps:")
    print("1. Run: portfolio-tracker sync --enrich")
    print("2. Restart your dashboard to see updated sectors")
