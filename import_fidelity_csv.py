"""
Import Fidelity portfolio CSV data to prepopulate ticker metadata cache

This script reads a Fidelity portfolio CSV export and extracts:
- Ticker symbols
- Company names (Description field)
- Sector information
- Industry information
- Market cap
- P/E ratio
- Dividend yield
- Current price

The data is saved to the ticker_metadata cache table to avoid
unnecessary Yahoo Finance API calls.
"""

import csv
import sys
from pathlib import Path
from loguru import logger
from fidelity_tracker.database.manager import DatabaseManager
from fidelity_tracker.database.migrations import MigrationManager


def parse_market_cap(market_cap_str: str) -> float:
    """
    Parse market cap string like 'Large cap ($174.12B)' to a float

    Args:
        market_cap_str: Market cap string from Fidelity

    Returns:
        Market cap as float (in dollars)
    """
    if not market_cap_str or market_cap_str.strip() == '--':
        return None

    try:
        # Extract the value inside parentheses
        if '($' in market_cap_str and ')' in market_cap_str:
            value_str = market_cap_str.split('($')[1].split(')')[0]

            # Remove $ and commas
            value_str = value_str.replace('$', '').replace(',', '')

            # Handle B (billions), M (millions), K (thousands)
            multiplier = 1
            if value_str.endswith('B'):
                multiplier = 1_000_000_000
                value_str = value_str[:-1]
            elif value_str.endswith('M'):
                multiplier = 1_000_000
                value_str = value_str[:-1]
            elif value_str.endswith('K'):
                multiplier = 1_000
                value_str = value_str[:-1]

            return float(value_str) * multiplier
    except (ValueError, IndexError):
        pass

    return None


def parse_float(value: str) -> float:
    """Parse a float value, handling '--' and empty strings"""
    if not value or value.strip() in ['--', '']:
        return None
    try:
        # Remove $ and commas
        clean_value = value.replace('$', '').replace(',', '').strip()
        return float(clean_value)
    except ValueError:
        return None


def import_fidelity_csv(csv_path: str, db_path: str = 'fidelity_portfolio.db'):
    """
    Import Fidelity CSV data to populate ticker metadata cache

    Args:
        csv_path: Path to Fidelity CSV file
        db_path: Path to database file
    """
    csv_file = Path(csv_path)

    if not csv_file.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return

    logger.info(f"Reading CSV file: {csv_file}")

    # Ensure database is migrated to v3 (has ticker_metadata table)
    logger.info("Checking database schema...")
    migrator = MigrationManager(db_path)
    current_version = migrator.get_current_version()

    if current_version < 3:
        logger.info(f"Database at version {current_version}, migrating to v3...")
        migrator.migrate(target_version=3)
    else:
        logger.info(f"Database at version {current_version} ✓")

    # Initialize database manager
    db = DatabaseManager(db_path)

    # Track statistics
    stats = {
        'total_rows': 0,
        'tickers_processed': 0,
        'tickers_saved': 0,
        'skipped': 0,
        'errors': 0,
        'unique_tickers': set()
    }

    # Read CSV file
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        # Use DictReader to parse CSV with headers
        reader = csv.DictReader(f)

        for row in reader:
            # Skip None or empty rows
            if not row:
                continue

            stats['total_rows'] += 1

            # Extract ticker symbol
            ticker = row.get('Symbol', '').strip() if row.get('Symbol') else ''

            # Skip rows without ticker or special cases
            if not ticker or ticker == 'N/A':
                stats['skipped'] += 1
                continue

            # Skip if already processed this ticker in this import
            if ticker in stats['unique_tickers']:
                continue

            stats['unique_tickers'].add(ticker)
            stats['tickers_processed'] += 1

            try:
                # Extract data from CSV
                description = row.get('Description', '').strip()
                sector = row.get('Sector', '').strip()
                industry = row.get('Industry', '').strip()
                market_cap_str = row.get('Market cap', '').strip()
                pe_ratio_str = row.get('P/E ratio', '').strip()
                last_price_str = row.get('Last price', '').strip()

                # Determine if this is a cash/money market fund
                security_type = row.get('Security type', '').strip()
                is_cash = security_type in ['Core', 'Mutual Fund', 'Annuity'] or \
                         ticker in ['FZDXX', 'FDRXX', 'SPAXX', 'SPRXX', 'FDLXX', 'FZFXX']

                # Override sector/industry for cash equivalents
                if is_cash and (not sector or sector == '--'):
                    sector = 'Cash'
                    industry = 'Money Market'

                # Parse numeric values
                market_cap = parse_market_cap(market_cap_str)
                pe_ratio = parse_float(pe_ratio_str)

                # Calculate dividend yield from SEC yield or Dist. yield
                dividend_yield = None
                sec_yield = row.get('SEC yield', '').strip()
                dist_yield = row.get('Dist. yield', '').strip()

                if sec_yield and sec_yield != '--':
                    # SEC yield is already in percentage, convert to decimal
                    try:
                        dividend_yield = float(sec_yield.replace('%', '')) / 100
                    except ValueError:
                        pass
                elif dist_yield and dist_yield != '--':
                    try:
                        dividend_yield = float(dist_yield.replace('%', '')) / 100
                    except ValueError:
                        pass

                # Prepare metadata dictionary
                metadata = {
                    'company_name': description or ticker,
                    'sector': sector if sector and sector != '--' else 'Unknown',
                    'industry': industry if industry and industry != '--' else 'Unknown',
                    'market_cap': market_cap,
                    'pe_ratio': pe_ratio,
                    'dividend_yield': dividend_yield,
                    'data_source': 'fidelity_csv'
                }

                # Save to database
                db.save_ticker_metadata(ticker, metadata)
                stats['tickers_saved'] += 1

                logger.info(f"✓ {ticker}: {metadata['company_name']} | {metadata['sector']} | {metadata['industry']}")

            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
                stats['errors'] += 1

    # Print summary
    logger.info("\n" + "="*60)
    logger.success("Import Complete!")
    logger.info(f"Total rows in CSV: {stats['total_rows']}")
    logger.info(f"Unique tickers found: {len(stats['unique_tickers'])}")
    logger.info(f"Tickers processed: {stats['tickers_processed']}")
    logger.info(f"Tickers saved to cache: {stats['tickers_saved']}")
    logger.info(f"Skipped (no ticker): {stats['skipped']}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info("="*60)

    # Show cache statistics
    cache_stats = db.get_metadata_stats()
    logger.info("\nTicker Metadata Cache Statistics:")
    logger.info(f"Total tickers in cache: {cache_stats['total_tickers']}")
    logger.info(f"\nTickers by sector:")
    for sector, count in sorted(cache_stats['by_sector'].items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {sector}: {count}")
    logger.info(f"\nData sources:")
    for source, count in cache_stats['by_data_source'].items():
        logger.info(f"  {source}: {count}")


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        logger.error("Usage: python import_fidelity_csv.py <path_to_csv>")
        logger.info("Example: python import_fidelity_csv.py ~/Downloads/Portfolio_Positions_Jan-04-2026.csv")
        sys.exit(1)

    csv_path = sys.argv[1]

    # Optional: specify custom database path
    db_path = sys.argv[2] if len(sys.argv) > 2 else 'fidelity_portfolio.db'

    import_fidelity_csv(csv_path, db_path)


if __name__ == '__main__':
    main()
