# Changelog

All notable changes to the Fidelity Portfolio Tracker will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.0.0] - 2026-01-04

### Added

#### Fidelity CSV Import Feature
- **New CLI Command**: `portfolio-tracker import-fidelity-csv <csv_file>`
  - Import sector, industry, and company data from Fidelity portfolio CSV exports
  - Prepopulates ticker metadata cache to speed up enrichment
  - Automatically handles cash/money market funds
  - Parses market cap, P/E ratio, and dividend yield from CSV

- **Persistent Ticker Metadata Cache** (Database Migration v3)
  - New `ticker_metadata` table for persistent caching
  - Stores: ticker, company_name, sector, industry, market_cap, pe_ratio, dividend_yield
  - Tracks data source (fidelity_csv vs yahoo_finance)
  - Tracks update count and last updated timestamp
  - Indexed by ticker, sector, and last_updated for fast queries

- **Cache Age Tracking**
  - Stores last Fidelity CSV import timestamp in `user_preferences` table
  - Automatic alerts when cache data is >30 days old
  - Alerts shown during `sync` and `cache` commands

- **Enhanced Cache Command**: `portfolio-tracker cache`
  - Shows persistent cache statistics (not just in-memory)
  - Displays tickers by sector breakdown
  - Displays data sources breakdown (fidelity_csv vs yahoo_finance)
  - Shows last import date and days since import
  - Warns when cache needs updating

- **Import Alerts in Sync Command**
  - Warns users during sync if CSV cache is >30 days old
  - Suggests importing CSV if no Fidelity data in cache
  - Non-intrusive, helpful reminders

#### Documentation
- **New**: [docs/FIDELITY_CSV_IMPORT.md](docs/FIDELITY_CSV_IMPORT.md)
  - Complete guide to Fidelity CSV import feature
  - Instructions for exporting CSV from Fidelity
  - Database schema documentation
  - Troubleshooting guide
  - FAQ section
  - Automation examples

- **Updated**: [README.md](README.md)
  - Added "Fidelity CSV Import (NEW!)" section
  - Quick start guide for CSV import
  - Benefits list
  - Updated version history

- **New**: [CHANGELOG.md](CHANGELOG.md) (this file)
  - Track all changes going forward

#### Scripts
- **New**: [import_fidelity_csv.py](import_fidelity_csv.py)
  - Standalone Python script for CSV import
  - Can be run independently or via CLI command
  - Supports custom database paths
  - Detailed logging and progress reporting

- **New**: [view_cache_stats.py](view_cache_stats.py)
  - View cache statistics from command line
  - Shows sample tickers with sector data
  - Useful for verifying imports

### Changed

#### Database
- **Migration to v3**: Added `ticker_metadata` table
- Enhanced `DatabaseManager` class:
  - `get_ticker_metadata(ticker)`: Retrieve cached ticker data
  - `save_ticker_metadata(ticker, data)`: Save/update ticker cache
  - `is_metadata_stale(metadata, max_age_days)`: Check cache freshness
  - `get_metadata_stats()`: Get cache statistics

#### Data Enrichment
- **DataEnricher** now uses persistent cache:
  - Checks in-memory cache first (fastest)
  - Falls back to database cache (from CSV imports)
  - Only calls Yahoo Finance API if not cached
  - Saves Yahoo Finance data back to persistent cache

- **Enrichment Performance**:
  - Instant lookups for cached tickers
  - No API delays for known tickers
  - Reduced Yahoo Finance API calls = less rate limiting

### Fixed
- Improved error handling for empty CSV rows
- Better handling of "Unknown" sector assignments for ETFs
- Robust parsing of market cap values from Fidelity format

### Technical Details

#### Database Schema Changes (v3 Migration)

```sql
CREATE TABLE ticker_metadata (
    ticker TEXT PRIMARY KEY,
    company_name TEXT,
    sector TEXT,
    industry TEXT,
    market_cap REAL,
    pe_ratio REAL,
    dividend_yield REAL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    update_count INTEGER DEFAULT 1,
    data_source TEXT DEFAULT 'yahoo_finance'
);

CREATE INDEX idx_ticker_metadata_updated ON ticker_metadata(last_updated);
CREATE INDEX idx_ticker_metadata_sector ON ticker_metadata(sector);
```

#### User Preferences Table Usage

```sql
-- Tracking last CSV import
INSERT INTO user_preferences (key, value, updated_at)
VALUES ('last_fidelity_csv_import', '"2026-01-04T10:30:00.123456"', CURRENT_TIMESTAMP);
```

### Performance Improvements

- **Before CSV Import**:
  - 100 tickers × 3 seconds = 5 minutes enrichment time
  - High risk of Yahoo Finance rate limiting

- **After CSV Import**:
  - 100 cached tickers = instant enrichment
  - 0 API calls for cached data
  - 0% risk of rate limiting for known tickers

### Backward Compatibility

- **Fully backward compatible** with v2.x databases
- Automatic migration to v3 when first running CSV import
- Existing data is preserved during migration
- No breaking changes to existing commands or workflows

### Migration Path

For users upgrading from v2.x:

```bash
# Option 1: Automatic migration during first import
portfolio-tracker import-fidelity-csv ~/Downloads/Portfolio.csv

# Option 2: Manual migration
portfolio-tracker migrate --version 3
```

## [2.0.0] - Earlier

### Added
- CLI tool with Click framework
- Performance tracking features
- Database migrations support
- Transaction tracking
- Cost basis calculations
- Benchmark comparison

## [1.3.0] - Earlier

### Changed
- Split into fast import + optional enrichment
- Separated fid-import.py and enrich-data.py

## [1.2.0] - Earlier

### Added
- Yahoo Finance enrichment
- Rate limiting with exponential backoff

## [1.1.0] - Earlier

### Added
- Portfolio weights calculation
- Account weights calculation

## [1.0.0] - Earlier

### Added
- Initial release
- Basic data collection from Fidelity
- JSON and CSV export
- SQLite database storage

---

## Legend

- **Added**: New features
- **Changed**: Changes in existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Vulnerability fixes

## Links

- [Latest Release](https://github.com/yourusername/fidelity-portfolio-tracker/releases/latest)
- [Issue Tracker](https://github.com/yourusername/fidelity-portfolio-tracker/issues)
- [Documentation](docs/)
