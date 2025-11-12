# Loveable.ai Portfolio Dashboard Integration

Complete setup guide and code examples for integrating Fidelity Portfolio Tracker with your Loveable.ai application.

## Quick Start

### 1. Setup Data Export

```bash
# From your fidelity tracker directory
cd ~/grok

# Run the export script to generate data files
./scripts/export_for_loveable.sh

# This creates:
# - exports/portfolio-latest.json (latest snapshot)
# - exports/portfolio-latest.csv (CSV format)
# - exports/portfolio-history.json (90-day history)
```

### 2. Copy Files to Loveable.ai Project

```bash
# Option A: Manual copy
cp exports/portfolio-latest.json ~/fidelity-portfolio-18884/src/data/

# Option B: Set environment variable for auto-sync
export LOVEABLE_REPO_PATH=~/fidelity-portfolio-18884
./scripts/export_for_loveable.sh
```

### 3. Install in Loveable.ai Project

Copy the files from `loveable-integration/` to your Loveable.ai project:

```
fidelity-portfolio-18884/
├── src/
│   ├── data/
│   │   └── portfolio-latest.json      # Copied from exports/
│   ├── services/
│   │   └── portfolioService.ts        # Copy from loveable-integration/
│   ├── hooks/
│   │   └── usePortfolio.ts            # Copy from loveable-integration/
│   ├── components/
│   │   ├── PortfolioSummary.tsx       # Copy from loveable-integration/
│   │   ├── HoldingsTable.tsx          # Copy from loveable-integration/
│   │   ├── PortfolioChart.tsx         # Copy from loveable-integration/
│   │   └── SectorAllocation.tsx       # Copy from loveable-integration/
│   └── pages/
│       └── Dashboard.tsx              # Copy from loveable-integration/
```

## Automated Daily Updates

### Setup Cron Job (macOS/Linux)

```bash
# Edit crontab
crontab -e

# Add this line to run export daily at 6 PM
0 18 * * * cd /Users/randylust/grok && LOVEABLE_REPO_PATH=/Users/randylust/fidelity-portfolio-18884 ./scripts/export_for_loveable.sh >> logs/export.log 2>&1

# Verify cron job
crontab -l
```

### Setup LaunchAgent (macOS - Better than cron)

Create `~/Library/LaunchAgents/com.portfolio.export.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.portfolio.export</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/randylust/grok/scripts/export_for_loveable.sh</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>LOVEABLE_REPO_PATH</key>
        <string>/Users/randylust/fidelity-portfolio-18884</string>
    </dict>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/randylust/grok/logs/export.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/randylust/grok/logs/export-error.log</string>
</dict>
</plist>
```

Load the agent:
```bash
launchctl load ~/Library/LaunchAgents/com.portfolio.export.plist
launchctl start com.portfolio.export
```

## Data Structure

The `portfolio-latest.json` contains an array of snapshots:

```typescript
interface Snapshot {
  id: number;
  timestamp: string;
  total_value: number;
  holdings: Holding[];
}

interface Holding {
  id: number;
  snapshot_id: number;
  account_id: string;
  ticker: string;
  company_name: string;
  quantity: number;
  last_price: number;
  value: number;
  sector: string;
  industry: string;
  market_cap: number | null;
  pe_ratio: number | null;
  dividend_yield: number | null;
  portfolio_weight: number;
  account_weight: number;
}
```

## Testing

```bash
# Test data export
./scripts/export_for_loveable.sh

# Verify JSON structure
cat exports/portfolio-latest.json | jq '.[0] | {id, timestamp, total_value, holdings_count: (.holdings | length)}'

# Test in Loveable.ai
cd ~/fidelity-portfolio-18884
npm run dev
```

## Troubleshooting

### Data not updating?
```bash
# Check export logs
tail -f ~/grok/logs/export.log

# Manual export
cd ~/grok
./scripts/export_for_loveable.sh

# Verify Git status in Loveable repo
cd ~/fidelity-portfolio-18884
git status
git log -1
```

### LaunchAgent not running?
```bash
# Check status
launchctl list | grep portfolio

# View logs
cat ~/grok/logs/export.log
cat ~/grok/logs/export-error.log

# Restart agent
launchctl unload ~/Library/LaunchAgents/com.portfolio.export.plist
launchctl load ~/Library/LaunchAgents/com.portfolio.export.plist
```

## Next Steps

1. ✅ Run export script to generate data
2. ✅ Copy code files to Loveable.ai project
3. ✅ Test components locally
4. ✅ Setup automated daily exports
5. ✅ Deploy to Loveable.ai
6. ✅ Verify automatic updates

## Support

- Integration Guide: See `../INTEGRATION_GUIDE.md`
- Testing Report: See `../TESTING_REPORT.md`
- Export Script: `../scripts/export_for_loveable.sh`
