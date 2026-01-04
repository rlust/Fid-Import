"""
View ticker metadata cache statistics
"""

from fidelity_tracker.database.manager import DatabaseManager
from loguru import logger


def view_cache_stats(db_path: str = 'fidelity_portfolio.db'):
    """View cache statistics"""
    db = DatabaseManager(db_path)

    # Get cache statistics
    stats = db.get_metadata_stats()

    logger.info("="*60)
    logger.info("TICKER METADATA CACHE STATISTICS")
    logger.info("="*60)
    logger.info(f"\nTotal tickers in cache: {stats['total_tickers']}")
    logger.info(f"Average update count: {stats['avg_update_count']}")

    logger.info(f"\n{'SECTOR':<40} {'COUNT':>10}")
    logger.info("-"*60)
    for sector, count in sorted(stats['by_sector'].items(), key=lambda x: x[1], reverse=True):
        logger.info(f"{sector:<40} {count:>10}")

    logger.info(f"\n{'DATA SOURCE':<40} {'COUNT':>10}")
    logger.info("-"*60)
    for source, count in stats['by_data_source'].items():
        logger.info(f"{source:<40} {count:>10}")

    logger.info("="*60)

    # Show some sample tickers
    import sqlite3
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    logger.info("\nSample tickers with sector data:")
    logger.info(f"{'TICKER':<10} {'COMPANY':<40} {'SECTOR':<30}")
    logger.info("-"*90)

    cursor.execute('''
        SELECT ticker, company_name, sector, industry
        FROM ticker_metadata
        WHERE data_source = 'fidelity_csv'
        AND sector != 'Unknown'
        AND sector != 'Cash'
        ORDER BY ticker
        LIMIT 20
    ''')

    for row in cursor.fetchall():
        logger.info(f"{row['ticker']:<10} {row['company_name'][:40]:<40} {row['sector']:<30}")

    conn.close()


if __name__ == '__main__':
    view_cache_stats()
