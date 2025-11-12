# Migration Guide: v1.0 → v2.0

## What's New in v2.0?

### Major Changes

✅ **Unified CLI** - Single `portfolio-tracker` command instead of separate scripts
✅ **Interactive Setup** - Wizard-guided configuration
✅ **YAML Configuration** - Flexible config system with environment variable support
✅ **Modular Architecture** - Clean, maintainable codebase
✅ **Better Error Handling** - Comprehensive logging and retry logic
✅ **Pip Installable** - Proper Python package with dependencies

### File Structure

**Old (v1.0):**
```
grok/
├── fid-import.py
├── enrich-data.py
├── .env
└── README.md
```

**New (v2.0):**
```
grok/
├── fidelity_tracker/          # Python package
│   ├── core/
│   ├── utils/
│   ├── cli/
│   └── scheduler/
├── config/
│   └── config.yaml.example
├── setup.py
├── requirements.txt
└── README_V2.md
```

## Migration Steps

### Step 1: Backup Existing Data

```bash
# Create backup directory
mkdir backup_v1

# Copy existing data files
cp fidelity_*.{json,csv} backup_v1/
cp fidelity_portfolio.db backup_v1/
cp .env backup_v1/
```

### Step 2: Install v2.0

```bash
# Install package
pip install -e .

# Or install dependencies only
pip install -r requirements.txt
```

### Step 3: Setup Configuration

**Option A: Use Setup Wizard (Recommended)**

```bash
portfolio-tracker setup
```

**Option B: Manual Configuration**

1. Copy example config:
   ```bash
   cp config/config.yaml.example config/config.yaml
   ```

2. Edit `config/config.yaml` with your credentials

3. Or keep using `.env` file (environment variables still work!)

### Step 4: Test New CLI

```bash
# Check status
portfolio-tracker status

# Run a sync
portfolio-tracker sync

# Enrich existing data
portfolio-tracker enrich backup_v1/fidelity_data_LATEST.json
```

## Command Mapping

| Old v1.0 | New v2.0 |
|----------|----------|
| `python3 fid-import.py` | `portfolio-tracker sync` |
| `python3 enrich-data.py` | `portfolio-tracker enrich` |
| N/A | `portfolio-tracker status` |
| N/A | `portfolio-tracker cleanup` |
| N/A | `portfolio-tracker setup` |

## Configuration Mapping

### Credentials

**Old (.env):**
```env
FIDELITY_USERNAME=587888
FIDELITY_PASSWORD=Rc514131!!
FIDELITY_MFA_SECRET=J3D5MFLR4DTASFIVAN4HN5ZC66MAKKOH
```

**New (config.yaml):**
```yaml
credentials:
  fidelity:
    username: ${FIDELITY_USERNAME}  # Still reads from .env!
    password: ${FIDELITY_PASSWORD}
    mfa_secret: ${FIDELITY_MFA_SECRET}
```

### Enrichment Settings

**New config options:**
```yaml
enrichment:
  enabled: true
  delay_seconds: 3.0  # Was hardcoded as 2-5 seconds
  max_retries: 3      # New feature!
```

### Storage Settings

```yaml
storage:
  output_dir: "."
  retention_days: 90  # Auto cleanup!
  auto_cleanup: true
```

## Data Compatibility

### ✅ Fully Compatible

- **CSV Files** - No changes, open as before
- **JSON Files** - Same format, can be enriched with v2.0
- **SQLite Database** - Automatically upgraded, all snapshots preserved

### 🔄 Enhanced in v2.0

- CSV files now have better column naming
- JSON files include timestamp in ISO format
- Database has additional indexes for faster queries

## Feature Comparison

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Data Collection | ✅ | ✅ |
| Yahoo Finance Enrichment | ✅ | ✅ |
| CSV Export | ✅ | ✅ |
| JSON Export | ✅ | ✅ |
| SQLite Database | ✅ | ✅ |
| Portfolio Weights | ✅ | ✅ |
| Unified CLI | ❌ | ✅ |
| Setup Wizard | ❌ | ✅ |
| Configuration System | ❌ | ✅ |
| Error Recovery | Partial | ✅ |
| Logging | Basic | Comprehensive |
| Auto Cleanup | ❌ | ✅ |
| Built-in Scheduler | ❌ | 🔜 Coming |
| Web Dashboard | ❌ | 🔜 Coming |

## Breaking Changes

### None! 🎉

v2.0 is designed to be backward compatible:

- Old `.env` file still works
- Old data files can be used
- Old database is automatically upgraded
- Old scripts (`fid-import.py`, `enrich-data.py`) still work (but deprecated)

## Recommended Workflow

### Daily Usage

**Old:**
```bash
python3 fid-import.py
# Wait...
# Check if rate limited
python3 enrich-data.py
# Enter delay
```

**New:**
```bash
portfolio-tracker sync
# Done! Enrichment happens automatically if configured
```

### Weekly Maintenance

```bash
# Check portfolio status
portfolio-tracker status

# Clean up old files (keeps last 90 days)
portfolio-tracker cleanup

# Re-enrich if Yahoo Finance failed
portfolio-tracker enrich
```

## Troubleshooting

### "portfolio-tracker: command not found"

```bash
# Reinstall package
pip install -e .

# Or run directly
python -m fidelity_tracker.cli.commands --help
```

### Config not found

```bash
# Create from example
cp config/config.yaml.example config/config.yaml

# Or run setup wizard
portfolio-tracker setup
```

### Import errors

```bash
# Install dependencies
pip install -r requirements.txt

# Check installation
pip show fidelity-portfolio-tracker
```

## Gradual Migration

You can use both versions side-by-side:

1. Keep v1.0 scripts for daily use
2. Test v2.0 CLI with `--config` flag
3. Once comfortable, switch to v2.0 fully
4. Archive old scripts

```bash
# Use v2.0 with custom config (test mode)
portfolio-tracker --config test-config.yaml sync

# Still use v1.0 for production
python3 fid-import.py
```

## Rollback Plan

If you need to go back to v1.0:

1. Restore backup:
   ```bash
   cp backup_v1/.env .
   cp backup_v1/*.db .
   ```

2. Uninstall v2.0:
   ```bash
   pip uninstall fidelity-portfolio-tracker
   ```

3. Use old scripts:
   ```bash
   python3 fid-import.py
   python3 enrich-data.py
   ```

## Getting Help

- See `README_V2.md` for full documentation
- Run `portfolio-tracker COMMAND --help` for command help
- Check logs in `logs/portfolio-tracker.log`

## Next Steps

After migrating to v2.0:

1. ✅ Run `portfolio-tracker setup` to configure
2. ✅ Test with `portfolio-tracker sync`
3. ✅ Set up daily cron job or wait for built-in scheduler
4. ✅ Try `portfolio-tracker status` to view history
5. 🔜 Launch web dashboard when available

---

**Questions?** Create an issue on GitHub or check the documentation.
