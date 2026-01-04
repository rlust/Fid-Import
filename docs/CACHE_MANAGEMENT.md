# Cache Management Guide

## Overview

The Fidelity Portfolio Tracker uses a two-tier caching system to optimize data enrichment:

1. **In-Memory Cache**: Fast, temporary cache (cleared between runs)
2. **Persistent Database Cache**: Permanent cache in SQLite (survives restarts)

## Cache Architecture

```
Enrichment Request for Ticker "AAPL"
    ↓
┌─────────────────────────────┐
│  1. In-Memory Cache         │  ← Fastest (microseconds)
│     (Python dict)           │
└─────────────────────────────┘
    ↓ Not found
┌─────────────────────────────┐
│  2. Database Cache          │  ← Fast (milliseconds)
│     (ticker_metadata table) │  ← CSV imports stored here
└─────────────────────────────┘
    ↓ Not found
┌─────────────────────────────┐
│  3. Yahoo Finance API       │  ← Slow (3+ seconds)
│     (External API call)     │  ← Risk of rate limiting
└─────────────────────────────┘
    ↓ Cache result
[Save to both caches for future use]
```

## Viewing Cache Status

### CLI Command

```bash
# View comprehensive cache statistics
portfolio-tracker cache
```

**Output includes:**
- Total tickers in persistent cache
- Average update count per ticker
- Breakdown by sector
- Breakdown by data source (fidelity_csv vs yahoo_finance)
- Last Fidelity CSV import date
- Days since last import
- Warnings if cache is stale (>30 days)

### Example Output

```
Ticker Metadata Cache

Persistent Cache Statistics
  Total Tickers: 114
  Average Updates: 2.01

Tickers by Sector
  Unknown                                52
  Cash                                   21
  Energy                                  7
  Financials                              7
  Information technology                  7
  Consumer discretionary                  6

Data Sources
  fidelity_csv                          114

Last Fidelity CSV Import
  Date: 2026-01-04T09:34:14.176000
  ✓ 0 days ago
```

## Populating the Cache

### Method 1: Fidelity CSV Import (Recommended)

**Best for:** Initial setup, regular updates

```bash
# Import latest Fidelity export
portfolio-tracker import-fidelity-csv ~/Downloads/Portfolio_Positions_Jan-04-2026.csv
```

**Imports:**
- All tickers from your portfolio
- Sector and industry data
- Company names
- Market cap, P/E ratio, dividend yield

**Benefits:**
- Pre-populates cache with accurate data
- Avoids Yahoo Finance API calls
- One-time import benefits all future enrichments

### Method 2: Enrichment with Yahoo Finance

**Best for:** Filling gaps, updating stale data

```bash
# Enrich latest snapshot (auto-caches results)
portfolio-tracker enrich

# Enrich specific file
portfolio-tracker enrich fidelity_data_20260104.json
```

**What happens:**
1. Checks persistent cache for each ticker
2. If not cached, fetches from Yahoo Finance
3. Saves Yahoo Finance data to persistent cache
4. Future enrichments use cached data

### Method 3: Sync with Enrichment

**Best for:** Regular automated updates

```bash
# Sync and enrich in one command
portfolio-tracker sync --enrich
```

**Process:**
1. Pulls latest data from Fidelity
2. Enriches using cache + Yahoo Finance
3. Updates cache with new data
4. Saves enriched snapshot

## Cache Update Strategy

### Recommended Schedule

```
Daily:    portfolio-tracker sync
Weekly:   portfolio-tracker enrich (refresh prices)
Monthly:  portfolio-tracker import-fidelity-csv (refresh sectors/data)
```

### Update Triggers

**Import new CSV when:**
- ✅ Monthly routine maintenance
- ✅ After adding new holdings to portfolio
- ✅ After 30 days (automatic alert)
- ✅ When you notice incorrect sector data
- ✅ After major portfolio rebalancing

**Run enrichment when:**
- ✅ Daily sync (to get latest prices)
- ✅ Want to add tickers not in CSV
- ✅ Need to update stale Yahoo Finance data
- ✅ Adding external data sources

## Cache Maintenance

### Checking Cache Freshness

```bash
# View cache status with freshness warnings
portfolio-tracker cache
```

### Re-importing CSV (Safe)

```bash
# Re-import is safe - updates existing entries
portfolio-tracker import-fidelity-csv ~/Downloads/Latest_Portfolio.csv
```

**What happens:**
- Existing tickers: Updated with new data, `update_count++`
- New tickers: Added to cache
- Old tickers: Remain unchanged (not deleted)

### Manual Cache Cleanup (Advanced)

#### Remove specific ticker

```bash
sqlite3 fidelity_portfolio.db "DELETE FROM ticker_metadata WHERE ticker = 'AAPL';"
```

#### Remove all Fidelity CSV data

```bash
sqlite3 fidelity_portfolio.db "DELETE FROM ticker_metadata WHERE data_source = 'fidelity_csv';"
```

#### Clear entire cache

```bash
sqlite3 fidelity_portfolio.db "DELETE FROM ticker_metadata;"
```

#### Vacuum database after cleanup

```bash
sqlite3 fidelity_portfolio.db "VACUUM;"
```

## Cache Performance Metrics

### Before Persistent Cache (v2.x)

```
Enrichment of 100 tickers:
  API Calls: 100
  Time: 100 × 3 seconds = 5 minutes
  Risk: High chance of rate limiting
  Cache: Lost on exit (in-memory only)
```

### After Persistent Cache (v3.0+)

```
First enrichment (with CSV import):
  API Calls: 0 (all cached)
  Time: < 1 second
  Risk: No rate limiting
  Cache: Permanent (survives restarts)

Second enrichment:
  API Calls: 0 (still cached)
  Time: < 1 second
  Cache: Still there!
```

### Performance Comparison

| Operation | Without Cache | With Fidelity CSV |
|-----------|---------------|-------------------|
| Enrich 100 tickers | 5 minutes | < 1 second |
| API calls | 100 | 0 |
| Rate limit risk | High | None |
| Data accuracy | Variable | From Fidelity |

## Cache Alerts

### Automatic Warnings

The system automatically warns you when cache needs attention:

#### During Sync

```bash
portfolio-tracker sync
```

**If cache is old (>30 days):**
```
⚠ Cache notice: Fidelity CSV data is 45 days old
  Consider re-importing: portfolio-tracker import-fidelity-csv <csv_file>
```

**If no CSV imported:**
```
💡 Tip: Import Fidelity CSV to pre-populate sector data and speed up enrichment
   Use: portfolio-tracker import-fidelity-csv <csv_file>
```

#### When Viewing Cache

```bash
portfolio-tracker cache
```

**If stale:**
```
Last Fidelity CSV Import
  Date: 2025-12-05T10:30:00.123456
  ⚠ 30 days ago - Consider re-importing
```

## Database Schema Reference

### ticker_metadata Table

```sql
CREATE TABLE ticker_metadata (
    ticker TEXT PRIMARY KEY,           -- Stock ticker (e.g., 'AAPL')
    company_name TEXT,                 -- Full company name
    sector TEXT,                       -- Sector (e.g., 'Information technology')
    industry TEXT,                     -- Industry (e.g., 'Software')
    market_cap REAL,                   -- Market cap in USD
    pe_ratio REAL,                     -- Price-to-earnings ratio
    dividend_yield REAL,               -- Dividend yield (decimal, not %)
    last_updated TIMESTAMP,            -- Last update timestamp
    update_count INTEGER DEFAULT 1,    -- Times updated
    data_source TEXT                   -- 'fidelity_csv' or 'yahoo_finance'
);
```

### Example Queries

#### View all cached tickers

```sql
SELECT ticker, company_name, sector, data_source, last_updated
FROM ticker_metadata
ORDER BY ticker;
```

#### Count by data source

```sql
SELECT data_source, COUNT(*) as count
FROM ticker_metadata
GROUP BY data_source;
```

#### Find stale data (>30 days)

```sql
SELECT ticker, company_name,
       julianday('now') - julianday(last_updated) as days_old
FROM ticker_metadata
WHERE julianday('now') - julianday(last_updated) > 30
ORDER BY days_old DESC;
```

#### Sector breakdown

```sql
SELECT sector, COUNT(*) as count,
       GROUP_CONCAT(ticker, ', ') as tickers
FROM ticker_metadata
GROUP BY sector
ORDER BY count DESC;
```

## Troubleshooting

### Cache Not Used During Enrichment

**Symptom:** Enrichment still takes 3+ seconds per ticker

**Causes:**
1. Tickers not in cache
2. Cache marked as stale (>30 days for some implementations)
3. Wrong database path

**Solutions:**
```bash
# Verify cache contents
portfolio-tracker cache

# Re-import CSV
portfolio-tracker import-fidelity-csv <csv_file>

# Check database path in config
cat config.yaml | grep database.path
```

### Import Doesn't Improve Performance

**Symptom:** No speed improvement after importing CSV

**Causes:**
1. Tickers in portfolio don't match CSV
2. Cache query failing silently
3. Different ticker symbols

**Solutions:**
```bash
# Check what was imported
sqlite3 fidelity_portfolio.db "SELECT COUNT(*) FROM ticker_metadata WHERE data_source='fidelity_csv';"

# Verify specific ticker
sqlite3 fidelity_portfolio.db "SELECT * FROM ticker_metadata WHERE ticker='AAPL';"

# Enable debug logging
portfolio-tracker --verbose enrich
```

### Database Locked Errors

**Symptom:** `sqlite3.OperationalError: database is locked`

**Causes:**
1. Multiple processes accessing database
2. Long-running transaction

**Solutions:**
```bash
# Close other processes
pkill -f portfolio-tracker

# Wait and retry
sleep 5 && portfolio-tracker cache
```

## Best Practices

### ✅ Do

1. **Import CSV monthly** to keep data fresh
2. **Run sync daily** for up-to-date portfolio values
3. **Use cache command** to verify import success
4. **Enable enrichment** during sync for best results
5. **Keep backups** of database file

### ❌ Don't

1. **Don't delete database** without backup
2. **Don't ignore 30-day warnings** - re-import CSV
3. **Don't manually edit** ticker_metadata table (use import)
4. **Don't run multiple** imports/enrichments simultaneously
5. **Don't share database** file (contains your portfolio data)

## Advanced Topics

### Custom Cache Expiration

You can modify the cache staleness check by editing the DatabaseManager:

```python
# In fidelity_tracker/database/manager.py
def is_metadata_stale(self, metadata: Dict[str, Any], max_age_days: int = 30):
    # Change 30 to your preferred days
```

### Selective Cache Refresh

Refresh specific sectors only:

```sql
-- Delete only Energy sector to force refresh
DELETE FROM ticker_metadata WHERE sector = 'Energy';
```

Then run enrichment to refetch just those tickers.

### Cache Export for Backup

```bash
# Export cache to CSV for backup
sqlite3 -header -csv fidelity_portfolio.db \
  "SELECT * FROM ticker_metadata;" > cache_backup.csv

# Import from backup
sqlite3 fidelity_portfolio.db <<EOF
DELETE FROM ticker_metadata;
.mode csv
.import cache_backup.csv ticker_metadata
EOF
```

## See Also

- [Fidelity CSV Import Guide](FIDELITY_CSV_IMPORT.md)
- [Database Schema Documentation](DATABASE_SCHEMA.md)
- [CLI Commands Reference](CLI_COMMANDS.md)
