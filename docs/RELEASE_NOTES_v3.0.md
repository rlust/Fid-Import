# Release Notes - Version 3.0.0

**Release Date:** January 4, 2026

## 🎉 What's New

### Fidelity CSV Import Feature

The headline feature of v3.0 is the ability to import sector and company data directly from Fidelity portfolio CSV exports. This dramatically speeds up enrichment and eliminates Yahoo Finance rate limiting issues.

## 🚀 Key Features

### 1. Import Command

```bash
portfolio-tracker import-fidelity-csv ~/Downloads/Portfolio_Positions_Jan-04-2026.csv
```

**What it does:**
- Reads Fidelity portfolio CSV export
- Extracts ticker, sector, industry, company name, market cap, P/E ratio, dividend yield
- Stores in persistent database cache
- Auto-detects cash/money market funds
- Tracks import timestamp for maintenance alerts

### 2. Persistent Metadata Cache

**New Database Table:** `ticker_metadata`
- Stores ticker information permanently
- Survives application restarts
- Used automatically during enrichment
- Eliminates redundant Yahoo Finance API calls

**Fields:**
- Ticker symbol, company name
- Sector, industry classification
- Market cap, P/E ratio, dividend yield
- Last updated timestamp
- Update count (tracks how many times updated)
- Data source (fidelity_csv vs yahoo_finance)

### 3. Cache Age Tracking & Alerts

**Automatic Monitoring:**
- Tracks last CSV import date
- Warns when cache is >30 days old
- Suggests re-import during sync operations
- Shows cache status in `cache` command

**Alert Examples:**
```
⚠ Cache notice: Fidelity CSV data is 45 days old
  Consider re-importing: portfolio-tracker import-fidelity-csv <csv_file>
```

### 4. Enhanced Cache Command

```bash
portfolio-tracker cache
```

**Now shows:**
- Total tickers in persistent cache
- Breakdown by sector
- Breakdown by data source
- Last import date and age
- Stale data warnings

## 📊 Performance Improvements

### Before v3.0 (No Persistent Cache)

```
Enriching 100 tickers:
  Time: ~5 minutes (100 × 3 seconds)
  API Calls: 100 to Yahoo Finance
  Rate Limiting: High risk
  Data Persistence: Lost on exit
```

### After v3.0 (With CSV Import)

```
Enriching 100 tickers:
  Time: <1 second
  API Calls: 0 (all cached)
  Rate Limiting: No risk
  Data Persistence: Permanent
```

**Speed Improvement:** ~300x faster for cached tickers!

## 🗂️ Files Added

### Scripts

1. **[import_fidelity_csv.py](../import_fidelity_csv.py)**
   - Standalone CSV import script
   - Can run independently or via CLI
   - Detailed progress reporting

2. **[view_cache_stats.py](../view_cache_stats.py)**
   - View cache statistics
   - Shows sample tickers with sectors
   - Useful for verification

### Documentation

1. **[docs/FIDELITY_CSV_IMPORT.md](FIDELITY_CSV_IMPORT.md)**
   - Complete CSV import guide
   - Export instructions from Fidelity
   - Troubleshooting section
   - FAQ

2. **[docs/CACHE_MANAGEMENT.md](CACHE_MANAGEMENT.md)**
   - Cache architecture overview
   - Performance metrics
   - Maintenance best practices
   - Advanced cache management

3. **[CHANGELOG.md](../CHANGELOG.md)**
   - Comprehensive change log
   - Tracks all version changes
   - Migration guides

4. **[docs/RELEASE_NOTES_v3.0.md](RELEASE_NOTES_v3.0.md)**
   - This file!

## 🔧 Technical Changes

### Database Migration v3

**New Table:**
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

**Automatic Migration:**
- Runs automatically on first CSV import
- Can run manually: `portfolio-tracker migrate --version 3`
- Preserves all existing data
- No breaking changes

### Enhanced DatabaseManager

**New Methods:**
- `get_ticker_metadata(ticker)` - Retrieve cached data
- `save_ticker_metadata(ticker, data)` - Save/update cache
- `is_metadata_stale(metadata, max_age_days)` - Check freshness
- `get_metadata_stats()` - Get statistics

### Enhanced DataEnricher

**Cache Strategy:**
1. Check in-memory cache (fastest)
2. Check persistent database cache (CSV imports)
3. Fall back to Yahoo Finance API
4. Save API results to persistent cache

## 📝 Updated Commands

### Modified Commands

**`portfolio-tracker cache`**
- Now shows persistent cache statistics
- Displays sector breakdown
- Shows data source breakdown
- Displays last import date
- Warns when cache is stale

**`portfolio-tracker sync`**
- Added cache age check at startup
- Warns if CSV data >30 days old
- Suggests CSV import for first-time users
- More informative about enrichment

### New Commands

**`portfolio-tracker import-fidelity-csv <csv_file>`**
- Import Fidelity portfolio CSV
- Populate persistent cache
- Track import timestamp
- Display statistics after import

## 🎓 Usage Examples

### First-Time Setup

```bash
# 1. Export CSV from Fidelity
#    (Accounts & Trade → Portfolio → Download)

# 2. Import CSV to populate cache
portfolio-tracker import-fidelity-csv ~/Downloads/Portfolio_Positions_Jan-04-2026.csv

# 3. Run sync with enrichment
portfolio-tracker sync --enrich

# Result: Lightning-fast enrichment, no rate limiting!
```

### Regular Maintenance

```bash
# Daily: Pull latest data
portfolio-tracker sync

# Weekly: Refresh enrichment
portfolio-tracker enrich

# Monthly: Update cache from new CSV export
portfolio-tracker import-fidelity-csv ~/Downloads/Latest_Portfolio.csv
```

### Checking Cache Status

```bash
# View cache statistics
portfolio-tracker cache

# Output shows:
# - Total tickers cached
# - Sector breakdown
# - Data sources
# - Last import date
# - Age warnings
```

## 🔄 Migration Guide

### From v2.x to v3.0

**Automatic Migration:**
```bash
# Simply import a CSV - migration happens automatically
portfolio-tracker import-fidelity-csv <csv_file>
```

**Manual Migration:**
```bash
# Run migration explicitly
portfolio-tracker migrate --version 3

# Verify migration
portfolio-tracker cache
```

**No Breaking Changes:**
- All v2.x commands still work
- Existing data is preserved
- No configuration changes required

### What Stays the Same

- All existing commands work identically
- Database schema is backward compatible
- Configuration files unchanged
- Enrichment behavior (just faster!)

### What's New

- Persistent cache capability
- CSV import feature
- Cache age tracking
- Enhanced statistics

## ⚠️ Important Notes

### Data Sources

**Two cache data sources:**
1. `fidelity_csv` - From CSV imports (preferred)
2. `yahoo_finance` - From API enrichment

Both are valid and work together seamlessly.

### Cache Staleness

- CSV data older than 30 days triggers warnings
- Re-import monthly for best results
- Warnings are suggestions, not requirements

### Backward Compatibility

- **100% backward compatible** with v2.x
- Existing databases upgrade automatically
- No action required for current users
- New features optional (but recommended!)

## 🐛 Bug Fixes

- Fixed error handling for empty CSV rows
- Improved sector assignment for ETFs
- Robust market cap parsing from Fidelity format
- Better handling of special characters in company names

## 🔮 Future Enhancements

Planned for future releases:
- Automatic CSV export integration (if Fidelity API supports)
- Smart cache refresh (only update changed tickers)
- Cache import/export between databases
- Web dashboard cache visualization

## 📖 Documentation

### New Documentation

- [Fidelity CSV Import Guide](FIDELITY_CSV_IMPORT.md) - Complete import guide
- [Cache Management Guide](CACHE_MANAGEMENT.md) - Cache best practices
- [Changelog](../CHANGELOG.md) - All version changes

### Updated Documentation

- [README.md](../README.md) - Added CSV import section
- Version history updated

## 🙏 Credits

This release focused on improving performance and user experience by reducing dependency on external APIs and providing faster, more reliable data enrichment.

## 📞 Support

- **Documentation**: See [docs/](.) folder
- **Issues**: File at GitHub repository
- **Questions**: See [FAQ in FIDELITY_CSV_IMPORT.md](FIDELITY_CSV_IMPORT.md#faq)

## 🎯 Next Steps

1. **Export CSV from Fidelity** (Accounts & Trade → Portfolio → Download)
2. **Import CSV**: `portfolio-tracker import-fidelity-csv <csv_file>`
3. **Enjoy faster enrichment** with no rate limiting!

---

**Happy Tracking! 📈**

*Fidelity Portfolio Tracker v3.0.0*
