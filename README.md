# Fidelity Portfolio Data Import Tool

Automated tool to pull Fidelity account and holdings data into multiple formats (JSON, CSV, SQLite) with optional enrichment from Yahoo Finance.

## Overview

This tool provides two scripts:
1. **fid-import.py** - Fast data collection from Fidelity (1-2 minutes)
2. **enrich-data.py** - Optional enrichment with Yahoo Finance data (5-10 minutes)

## Setup

### Prerequisites
```bash
pip install fidelity-api python-dotenv yfinance
```

### Configuration

Create a `.env` file in the project directory:
```env
FIDELITY_USERNAME=your_username
FIDELITY_PASSWORD=your_password
FIDELITY_MFA_SECRET=your_totp_secret
```

**Getting your MFA Secret:**
1. Log into Fidelity website
2. Go to Security Settings → Two-Factor Authentication
3. Choose "Set up authenticator app"
4. Click "Can't scan QR code?" to reveal the secret key
5. Copy the secret key (remove spaces) and add to `.env`

## Usage

### 1. Pull Fidelity Data (Main Script)

```bash
python3 fid-import.py
```

**What it does:**
- Connects to Fidelity and logs in with 2FA
- Pulls all account information and holdings
- Calculates portfolio weights and account weights
- Saves data to multiple formats:
  - `fidelity_data_TIMESTAMP.json` - Complete data backup
  - `fidelity_accounts_TIMESTAMP.csv` - Account summary
  - `fidelity_holdings_TIMESTAMP.csv` - All holdings with calculated metrics
  - `fidelity_portfolio.db` - SQLite database for historical tracking

**Output includes:**
- Account ID, Nickname, Balance
- Ticker, Quantity, Last Price, Value
- Portfolio Weight % (holding value / total portfolio)
- Account Weight % (holding value / account balance)

**Time:** ~1-2 minutes

### 2. Enrich with Yahoo Finance Data (Optional)

```bash
python3 enrich-data.py
```

**What it does:**
- Reads the most recent JSON data file
- Fetches additional data from Yahoo Finance for each ticker
- Adds: Company Name, Sector, Industry, Market Cap, PE Ratio, Dividend Yield
- Creates enriched files with suffix `_enriched_TIMESTAMP`
- Uses rate limiting with exponential backoff to avoid API limits

**Recommended delay:** 3-5 seconds between requests

**Time:** ~5-10 minutes (depends on number of unique tickers)

**Note:** Yahoo Finance has rate limits. If you hit limits, wait 1 hour and try again.

## Output Files

### CSV Format
```csv
Account ID, Account Nickname, Ticker, Company Name, Quantity, Last Price, Value,
Sector, Industry, Market Cap, PE Ratio, Dividend Yield (%),
Portfolio Weight (%), Account Weight (%)
```

### Database Schema

**snapshots table:**
- id, timestamp, total_value

**accounts table:**
- id, snapshot_id, account_id, nickname, balance, withdrawal_balance

**holdings table:**
- id, snapshot_id, account_id, ticker, company_name, quantity, last_price, value
- sector, industry, market_cap, pe_ratio, dividend_yield
- portfolio_weight, account_weight

## Portfolio Analysis

### Using CSV Files
Open in Excel, Google Sheets, or any spreadsheet application for:
- Sorting by portfolio weight
- Filtering by sector/industry
- Creating pivot tables
- Analyzing diversification

### Using SQLite Database

```sql
-- Get latest portfolio snapshot
SELECT * FROM snapshots ORDER BY timestamp DESC LIMIT 1;

-- View all holdings from latest snapshot
SELECT h.*, a.nickname
FROM holdings h
JOIN accounts a ON h.account_id = a.account_id
WHERE h.snapshot_id = (SELECT MAX(id) FROM snapshots)
ORDER BY h.value DESC;

-- Analyze by sector
SELECT sector, SUM(value) as total_value,
       SUM(portfolio_weight) as total_weight
FROM holdings
WHERE snapshot_id = (SELECT MAX(id) FROM snapshots)
GROUP BY sector
ORDER BY total_value DESC;

-- Compare portfolio over time
SELECT timestamp, total_value
FROM snapshots
ORDER BY timestamp;
```

## Scheduling

### Daily Updates (macOS/Linux)

Create a cron job:
```bash
crontab -e
```

Add line (runs daily at 6 PM):
```
0 18 * * * cd /Users/randylust/grok && /usr/local/bin/python3 fid-import.py
```

### Weekly Enrichment

Run enrichment weekly to update company data:
```
0 19 * * 0 cd /Users/randylust/grok && /usr/local/bin/python3 enrich-data.py <<< "5"
```

## Troubleshooting

### ModuleNotFoundError
```bash
pip install --user fidelity-api python-dotenv yfinance
```

### MFA Secret Invalid
Ensure you've removed all spaces from the secret key in `.env`

### Rate Limiting (Yahoo Finance)
- Increase delay in enrich-data.py (use 5+ seconds)
- Wait 1 hour before retrying
- The script will automatically retry with exponential backoff

### Python Command Not Found
Use `python3` instead of `python`:
```bash
python3 fid-import.py
```

## Security Notes

- `.env` file contains sensitive credentials - never commit to git
- Add `.env` to `.gitignore`
- Database and CSV files contain financial data - store securely
- Consider encrypting database file if sharing system with others

## Portfolio Metrics Explained

**Portfolio Weight (%):** What percentage of your total portfolio this holding represents
- Example: If QQQ value is $129,000 and total portfolio is $2,158,000, weight = 5.98%

**Account Weight (%):** What percentage of the specific account this holding represents
- Example: If QQQ value is $129,000 and account balance is $878,000, weight = 14.68%

**Use cases:**
- Portfolio Weight: Track overall diversification across all accounts
- Account Weight: Understand individual account allocation

## Files Structure

```
grok/
├── .env                              # Credentials (DO NOT COMMIT)
├── fid-import.py                     # Main data collection script
├── enrich-data.py                    # Yahoo Finance enrichment script
├── README.md                         # This file
├── fidelity_portfolio.db            # SQLite database
├── fidelity_data_*.json             # JSON backups
├── fidelity_accounts_*.csv          # Account summaries
├── fidelity_holdings_*.csv          # Holdings data
└── fidelity_holdings_enriched_*.csv # Enriched holdings
```

## Fidelity CSV Import (NEW!)

### What is it?

Import sector and company data directly from Fidelity portfolio CSV exports to prepopulate the ticker metadata cache. This makes enrichment **much faster** and avoids Yahoo Finance rate limiting.

### Quick Start

1. **Export CSV from Fidelity**: Accounts & Trade → Portfolio → Download
2. **Import the CSV**:

   ```bash
   portfolio-tracker import-fidelity-csv ~/Downloads/Portfolio_Positions_Jan-04-2026.csv
   ```

3. **Benefit**: Future enrichment operations will use cached data instead of Yahoo Finance API

### Benefits

- ✅ **Instant enrichment** for cached tickers (no 3-second API delays)
- ✅ **Avoid rate limiting** (fewer Yahoo Finance API calls)
- ✅ **Accurate sector data** from Fidelity
- ✅ **Automatic tracking** with alerts when cache needs updating

### Documentation

See [docs/FIDELITY_CSV_IMPORT.md](docs/FIDELITY_CSV_IMPORT.md) for detailed guide.

## Version History

- **v3.0** - Added Fidelity CSV import & persistent ticker metadata cache (2026-01-04)
- **v2.0** - Added CLI tool, performance tracking, database migrations
- **v1.3** - Split into fast import + optional enrichment
- **v1.2** - Added Yahoo Finance enrichment with rate limiting
- **v1.1** - Added portfolio weights and account weights
- **v1.0** - Initial release with basic data collection

## Support

For issues or questions:
- Check Troubleshooting section above
- Review fidelity-api documentation: https://github.com/MaxxRK/fidelity-api
- Check Yahoo Finance API status

## License

MIT License - Use at your own risk. Not affiliated with Fidelity Investments.
