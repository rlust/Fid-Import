# Fidelity CSV Import Feature

## Overview

The Fidelity CSV Import feature allows you to prepopulate the ticker metadata cache with sector, industry, and company data directly from Fidelity portfolio export files. This significantly speeds up enrichment operations by avoiding Yahoo Finance API calls for tickers that are already in your portfolio.

## Benefits

1. **Faster Enrichment**: Skip Yahoo Finance API calls for known tickers
2. **Accurate Sector Data**: Use Fidelity's sector classifications
3. **Reduced API Rate Limiting**: Fewer external API calls means less chance of hitting rate limits
4. **Persistent Cache**: Data is stored in the database and used across all future operations
5. **One-Time Setup**: Import once, benefit from it on every subsequent enrichment

## How to Export CSV from Fidelity

1. Log into your Fidelity account at https://www.fidelity.com
2. Navigate to **Accounts & Trade** → **Portfolio**
3. Click on **Positions** tab
4. Click the **Download** button (usually in top right)
5. Select **Export to CSV** or **Download Positions**
6. Save the file to your Downloads folder
   - Example: `Portfolio_Positions_Jan-04-2026.csv`

## Importing the CSV

### Using CLI Command (Recommended)

```bash
# Basic import
portfolio-tracker import-fidelity-csv ~/Downloads/Portfolio_Positions_Jan-04-2026.csv

# Import without showing statistics
portfolio-tracker import-fidelity-csv ~/Downloads/Portfolio_Positions_Jan-04-2026.csv --no-stats
```

### Using Standalone Script

```bash
# Direct script execution
python3 import_fidelity_csv.py ~/Downloads/Portfolio_Positions_Jan-04-2026.csv

# With custom database path
python3 import_fidelity_csv.py ~/Downloads/Portfolio_Positions_Jan-04-2026.csv custom_database.db
```

## What Gets Imported

The import process extracts the following data for each ticker:

- **Ticker Symbol**: The stock/ETF ticker (e.g., QQQ, AAPL, MSFT)
- **Company Name**: From the Description field
- **Sector**: Industry sector classification
- **Industry**: Specific industry within sector
- **Market Cap**: Company market capitalization (parsed from format like "Large cap ($174.12B)")
- **P/E Ratio**: Price-to-earnings ratio
- **Dividend Yield**: SEC yield or distribution yield (converted to decimal)

### Data Source Tagging

All imported data is tagged with `data_source = 'fidelity_csv'` to distinguish it from data fetched via Yahoo Finance API.

## Cache Statistics

After importing, you can view cache statistics:

```bash
# View cache information
portfolio-tracker cache
```

This shows:
- Total number of tickers cached
- Breakdown by sector
- Breakdown by data source (fidelity_csv vs yahoo_finance)
- Last import date and days since import

## Tracking and Alerts

### Last Import Timestamp

The system automatically tracks when you last imported a Fidelity CSV file. This timestamp is stored in the `user_preferences` table:

```sql
SELECT * FROM user_preferences WHERE key = 'last_fidelity_csv_import';
```

### Automatic Alerts

The CLI will automatically alert you when:

1. **During Sync**: If CSV data is >30 days old
   ```
   ⚠ Cache notice: Fidelity CSV data is 45 days old
   Consider re-importing: portfolio-tracker import-fidelity-csv <csv_file>
   ```

2. **During Sync**: If no Fidelity CSV has been imported
   ```
   💡 Tip: Import Fidelity CSV to pre-populate sector data and speed up enrichment
   Use: portfolio-tracker import-fidelity-csv <csv_file>
   ```

3. **When Viewing Cache**: Shows warning if >30 days old
   ```
   Last Fidelity CSV Import
   Date: 2025-12-05T10:30:00.123456
   ⚠ 30 days ago - Consider re-importing
   ```

## Re-importing CSV Files

### When to Re-import

You should re-import your Fidelity CSV when:

- **Monthly** (recommended): Keep sector data fresh
- **After major portfolio changes**: Added new holdings
- **After 30 days**: Automatic alerts will remind you
- **When market cap or metrics change significantly**

### Re-import Process

When you re-import:
1. Existing ticker data is **updated** (not duplicated)
2. The `update_count` field is incremented
3. The `last_updated` timestamp is refreshed
4. New tickers are added to the cache

This means re-importing is safe and won't create duplicate entries.

## Database Schema

### ticker_metadata Table

```sql
CREATE TABLE ticker_metadata (
    ticker TEXT PRIMARY KEY,           -- Ticker symbol (uppercase)
    company_name TEXT,                 -- Company/fund name
    sector TEXT,                       -- Sector classification
    industry TEXT,                     -- Industry within sector
    market_cap REAL,                   -- Market capitalization in dollars
    pe_ratio REAL,                     -- Price-to-earnings ratio
    dividend_yield REAL,               -- Dividend yield (decimal, not %)
    last_updated TIMESTAMP,            -- Last update timestamp
    update_count INTEGER DEFAULT 1,    -- Number of times updated
    data_source TEXT                   -- 'fidelity_csv' or 'yahoo_finance'
);
```

### Indexes

```sql
CREATE INDEX idx_ticker_metadata_updated ON ticker_metadata(last_updated);
CREATE INDEX idx_ticker_metadata_sector ON ticker_metadata(sector);
```

## Special Handling

### Cash and Money Market Funds

The import automatically identifies and tags cash/money market funds:

- **Tickers**: FZDXX, FDRXX, SPAXX, SPRXX, FDLXX, FZFXX
- **Security Types**: Core, Mutual Fund, Annuity (when sector is empty)

These are assigned:
- `sector = 'Cash'`
- `industry = 'Money Market'`

### ETFs Without Sector Data

Many ETFs don't have sector classifications in Fidelity exports. These are marked as:
- `sector = 'Unknown'`
- `industry = 'Unknown'`

This is expected and normal. Yahoo Finance enrichment can fill in additional data for these.

## Integration with Enrichment

### Priority Order

When enriching portfolio data, the DataEnricher checks caches in this order:

1. **In-memory cache** (fastest, cleared between runs)
2. **Persistent database cache** (this is where Fidelity CSV data lives)
3. **Yahoo Finance API** (slowest, only if not in cache)

### Example Flow

```python
# Enriching a ticker
ticker = "AAPL"

# 1. Check in-memory cache - not found (first run)
# 2. Check persistent cache - FOUND! (from Fidelity CSV import)
#    Returns: sector="Information technology", industry="Technology hardware..."
# 3. Yahoo Finance API - SKIPPED (data already in cache)
```

### Performance Benefit

**Without CSV Import:**
- 100 tickers × 3 seconds delay = 5 minutes
- Risk of rate limiting

**With CSV Import:**
- 100 tickers cached = instant
- 0 API calls
- 0 risk of rate limiting

## Automation

### Monthly Import via Cron

Set up automatic monthly imports:

```bash
crontab -e
```

Add this line to import on the 1st of each month at 9 AM:
```
0 9 1 * * cd /Users/randylust/grok && /usr/local/bin/python3 import_fidelity_csv.py ~/Downloads/Portfolio_Positions_Latest.csv
```

### Script for Latest Export

Create a script to always import the most recent CSV:

```bash
#!/bin/bash
# import_latest_fidelity_csv.sh

DOWNLOADS_DIR=~/Downloads
LATEST_CSV=$(ls -t $DOWNLOADS_DIR/Portfolio_Positions*.csv | head -1)

if [ -f "$LATEST_CSV" ]; then
    echo "Importing: $LATEST_CSV"
    cd /Users/randylust/grok
    python3 import_fidelity_csv.py "$LATEST_CSV"
else
    echo "No Fidelity CSV found in Downloads"
    exit 1
fi
```

Make it executable:
```bash
chmod +x import_latest_fidelity_csv.sh
```

## Troubleshooting

### Import Errors

**Problem**: `AttributeError: 'NoneType' object has no attribute 'strip'`
- **Cause**: Empty rows in CSV file
- **Solution**: Already handled in current version, but if you see this, file a bug report

**Problem**: Tickers showing as "Unknown" sector
- **Cause**: Fidelity export doesn't include sector data for some securities (especially ETFs)
- **Solution**: This is normal. Yahoo Finance enrichment can fill in additional data.

### Database Issues

**Problem**: `sqlite3.OperationalError: no such table: ticker_metadata`
- **Cause**: Database not migrated to v3
- **Solution**: Run `portfolio-tracker migrate` first

**Problem**: Duplicate ticker warnings
- **Cause**: Ticker appears multiple times in CSV (different accounts)
- **Solution**: This is normal. Only the first occurrence is imported.

### Performance

**Problem**: Import is slow
- **Cause**: Large CSV file with many tickers
- **Expected**: ~1-2 seconds per 100 tickers
- **Solution**: This is normal. Be patient.

## FAQ

**Q: How often should I re-import?**
A: Monthly is recommended. The system will alert you after 30 days.

**Q: Will re-importing create duplicates?**
A: No. Existing tickers are updated, not duplicated.

**Q: Can I import multiple CSV files?**
A: Yes, but they'll overwrite each other for the same tickers. Use the most recent export.

**Q: What if my CSV has different columns?**
A: The script is designed for Fidelity's standard export format. Other formats may not work.

**Q: Does this work with joint accounts?**
A: Yes. All tickers from all accounts in the CSV are imported.

**Q: How do I clear the cache?**
A: You can delete rows from the `ticker_metadata` table or delete the entire database and start fresh.

## Version History

- **v3.0.0** (2026-01-04)
  - Added Fidelity CSV import feature
  - Added persistent ticker metadata cache
  - Added last import timestamp tracking
  - Added automatic cache age alerts

## See Also

- [Database Schema Documentation](DATABASE_SCHEMA.md)
- [CLI Commands Reference](CLI_COMMANDS.md)
- [Enrichment Guide](ENRICHMENT.md)
