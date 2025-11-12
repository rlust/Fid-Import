# Fidelity Portfolio Tracker v2.0

**Standalone application for automated Fidelity portfolio data collection and analysis**

## Features

- ✅ Automated data collection from Fidelity with 2FA support
- ✅ Yahoo Finance enrichment (company names, sectors, PE ratios, etc.)
- ✅ Multiple export formats (JSON, CSV, SQLite)
- ✅ Unified CLI with intuitive commands
- ✅ Interactive setup wizard
- ✅ Built-in scheduler for automatic updates
- ✅ Historical tracking and analytics
- ✅ Web dashboard (coming soon)
- ✅ Encrypted credential storage
- ✅ Comprehensive logging

## Quick Start

### Installation

```bash
# Clone or download the repository
cd fidelity-portfolio-tracker

# Install in development mode
pip install -e .

# Or install from requirements.txt
pip install -r requirements.txt
```

### Setup

Run the interactive setup wizard:

```bash
portfolio-tracker setup
```

The wizard will guide you through:
1. Entering Fidelity credentials
2. Configuring sync schedules
3. Setting up enrichment options
4. Testing your connection
5. Running your first sync

## Usage

### Commands

#### Sync Portfolio Data

```bash
# Pull data from Fidelity
portfolio-tracker sync

# Sync without enrichment
portfolio-tracker sync --no-enrich

# Sync with enrichment (default if enabled in config)
portfolio-tracker sync --enrich
```

#### Enrich Existing Data

```bash
# Enrich the most recent data file
portfolio-tracker enrich

# Enrich a specific file
portfolio-tracker enrich fidelity_data_20241112_111740.json
```

#### Check Status

```bash
# Show latest snapshot and recent history
portfolio-tracker status

# Show more snapshots
portfolio-tracker status --limit 20
```

#### Cleanup Old Data

```bash
# Clean up files and database snapshots older than 90 days
portfolio-tracker cleanup

# Keep only last 30 days
portfolio-tracker cleanup --days 30

# Clean only files (not database)
portfolio-tracker cleanup --no-database
```

#### Launch Dashboard

```bash
# Start web dashboard (opens in browser)
portfolio-tracker dashboard
```

### Configuration

Configuration is stored in `config/config.yaml`. See `config/config.yaml.example` for all options.

**Key settings:**

```yaml
credentials:
  fidelity:
    username: ${FIDELITY_USERNAME}  # Or hardcode (not recommended)
    password: ${FIDELITY_PASSWORD}
    mfa_secret: ${FIDELITY_MFA_SECRET}

sync:
  schedule: "0 18 * * *"  # Daily at 6 PM
  enrichment_schedule: "0 19 * * 0"  # Weekly Sunday 7 PM

enrichment:
  enabled: true
  delay_seconds: 3.0  # Avoid rate limits

storage:
  retention_days: 90  # Keep data for 90 days
  auto_cleanup: true
```

### Environment Variables

For better security, use environment variables:

```bash
export FIDELITY_USERNAME="your_username"
export FIDELITY_PASSWORD="your_password"
export FIDELITY_MFA_SECRET="your_totp_secret"
```

Or create a `.env` file:

```env
FIDELITY_USERNAME=your_username
FIDELITY_PASSWORD=your_password
FIDELITY_MFA_SECRET=your_totp_secret
```

## Output Files

The application generates several types of files:

### CSV Files

**`fidelity_accounts_TIMESTAMP.csv`**
- Account summaries with balances

**`fidelity_holdings_TIMESTAMP.csv`**
- Complete holdings data with:
  - Account info, ticker, quantity, value
  - Company name, sector, industry
  - Market cap, PE ratio, dividend yield
  - Portfolio weight, account weight

### JSON Files

**`fidelity_data_TIMESTAMP.json`**
- Complete data backup in JSON format
- Contains all accounts, holdings, and metadata

### SQLite Database

**`fidelity_portfolio.db`**
- Historical tracking database
- Three tables: `snapshots`, `accounts`, `holdings`
- Enables time-series analysis and comparisons

## Data Analysis

### Using CSV Files

Open in Excel, Google Sheets, or any spreadsheet software:

- Sort by portfolio weight to see largest holdings
- Filter by sector for diversification analysis
- Create pivot tables for summaries
- Generate charts and visualizations

### Using SQLite

Query the database with SQL:

```sql
-- Get latest portfolio value
SELECT * FROM snapshots ORDER BY id DESC LIMIT 1;

-- View all holdings from latest snapshot
SELECT h.*, a.nickname
FROM holdings h
JOIN accounts a ON h.account_id = a.account_id
WHERE h.snapshot_id = (SELECT MAX(id) FROM snapshots)
ORDER BY h.value DESC;

-- Analyze by sector
SELECT sector, SUM(value) as total, SUM(portfolio_weight) as weight
FROM holdings
WHERE snapshot_id = (SELECT MAX(id) FROM snapshots)
GROUP BY sector
ORDER BY total DESC;

-- Track portfolio over time
SELECT timestamp, total_value
FROM snapshots
ORDER BY timestamp;
```

## Scheduling

### Manual Scheduling (Cron)

Add to crontab (`crontab -e`):

```cron
# Daily sync at 6 PM
0 18 * * * cd /path/to/fidelity-tracker && portfolio-tracker sync

# Weekly enrichment on Sunday at 7 PM
0 19 * * 0 cd /path/to/fidelity-tracker && portfolio-tracker enrich

# Weekly cleanup on Monday at 1 AM
0 1 * * 1 cd /path/to/fidelity-tracker && portfolio-tracker cleanup
```

### Automatic Scheduling (Coming Soon)

Built-in scheduler will be activated with:

```bash
portfolio-tracker schedule start
portfolio-tracker schedule stop
portfolio-tracker schedule status
```

## Project Structure

```
fidelity-portfolio-tracker/
├── fidelity_tracker/           # Main package
│   ├── core/                   # Core functionality
│   │   ├── collector.py        # Fidelity data collection
│   │   ├── enricher.py         # Yahoo Finance enrichment
│   │   ├── database.py         # SQLite operations
│   │   └── storage.py          # File operations
│   ├── utils/                  # Utilities
│   │   ├── config.py           # Configuration management
│   │   └── logger.py           # Logging setup
│   ├── cli/                    # Command-line interface
│   │   └── commands.py         # CLI commands
│   └── scheduler/              # Task scheduling (coming soon)
├── web/                        # Web dashboard (coming soon)
│   └── app.py
├── tests/                      # Unit tests
├── config/                     # Configuration
│   └── config.yaml.example     # Example configuration
├── logs/                       # Log files
├── setup.py                    # Package setup
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

## Troubleshooting

### Import Errors

```bash
# Reinstall in development mode
pip install -e .

# Or ensure you're in the right directory
cd /path/to/fidelity-portfolio-tracker
python -m fidelity_tracker.cli.commands
```

### Missing Credentials

```bash
# Check environment variables
echo $FIDELITY_USERNAME

# Or check config file
cat config/config.yaml

# Run setup again
portfolio-tracker setup
```

### Rate Limiting (Yahoo Finance)

If you hit rate limits:
- Increase delay in config: `enrichment.delay_seconds: 5.0`
- Wait 1 hour before retrying
- Run enrichment separately: `portfolio-tracker enrich`

### Connection Errors

- Verify credentials are correct
- Check MFA secret (remove spaces)
- Ensure Fidelity account is accessible
- Check network connection

## Migration from v1.0

If you were using the old scripts (`fid-import.py`, `enrich-data.py`):

1. **Install new version:**
   ```bash
   pip install -e .
   ```

2. **Run setup:**
   ```bash
   portfolio-tracker setup
   ```

3. **Your existing data files are compatible!**
   - CSV files can still be opened normally
   - SQLite database will be upgraded automatically
   - JSON files can be enriched: `portfolio-tracker enrich old_file.json`

4. **Old scripts still work** but are deprecated
   - Consider using new CLI commands instead

## Development

### Running Tests

```bash
pytest tests/
pytest --cov=fidelity_tracker tests/
```

### Code Style

```bash
black fidelity_tracker/
flake8 fidelity_tracker/
mypy fidelity_tracker/
```

## Roadmap

- [ ] Built-in scheduler with APScheduler
- [ ] Web dashboard with Streamlit
- [ ] Docker container
- [ ] Windows/Mac standalone executables
- [ ] Plugin system for other brokerages
- [ ] Mobile app integration
- [ ] Tax reporting features

## Security

- ⚠️ Never commit `.env` or `config/config.yaml` to version control
- 🔒 Use environment variables for credentials
- 🔐 Consider using system keyring for credential storage (coming soon)
- 📝 Keep logs secure (may contain sensitive data)

## License

MIT License - See LICENSE file for details

## Support

- **Issues**: https://github.com/yourusername/fidelity-portfolio-tracker/issues
- **Discussions**: https://github.com/yourusername/fidelity-portfolio-tracker/discussions
- **Documentation**: https://docs.example.com

## Acknowledgments

- Built with [fidelity-api](https://github.com/MaxxRK/fidelity-api)
- Data enrichment via [yfinance](https://github.com/ranaroussi/yfinance)
- CLI powered by [Click](https://click.palletsprojects.com/)

---

**Version 2.0.0** - Standalone Application Release
