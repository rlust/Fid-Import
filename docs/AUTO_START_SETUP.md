# Auto-Start Setup for Portfolio Tracker

This document explains the automated startup configuration for the Portfolio Tracker system.

## Overview

Four launchd agents have been configured to maintain system functionality:

1. **Backend API** - FastAPI server on port 8000
2. **Frontend Dashboard** - Next.js app on port 3000
3. **Daily Sync** - Automated portfolio synchronization
4. **Transaction Inference** - Automated transaction detection from snapshots

## LaunchAgent Files

Located in `~/Library/LaunchAgents/`:

### 1. Backend API (`com.portfolio.backend.plist`)
- **Service**: FastAPI/Uvicorn server
- **Port**: 8000
- **Auto-start**: On login
- **Auto-restart**: If crashes
- **Logs**: `~/grok/logs/backend.log` and `backend.error.log`

### 2. Dashboard (`com.portfolio.dashboard.plist`)
- **Service**: Next.js development server
- **Port**: 3000
- **Auto-start**: On login
- **Auto-restart**: If crashes
- **Logs**: `~/grok/logs/dashboard.log` and `dashboard.error.log`
- **Environment**: NODE_ENV cleared to avoid production mode issues

### 3. Daily Sync (`com.portfolio.sync.plist`)
- **Service**: Portfolio data synchronization
- **Schedule**: Daily at 6:00 PM
- **Command**: `portfolio-tracker sync`
- **Logs**: `~/grok/logs/sync.log` and `sync.error.log`

### 4. Transaction Inference (`com.portfolio.infer.plist`)
- **Service**: Automatic transaction detection from snapshot changes
- **Schedule**: Daily at 6:15 PM (15 minutes after sync)
- **Command**: `curl -X POST http://localhost:8000/api/v1/transactions/infer?save=true&skip_existing=true`
- **Logs**: `~/grok/logs/infer.log` and `infer.error.log`
- **Purpose**: Automatically creates transaction records when holdings change between snapshots

## Management Commands

### Check Status
```bash
launchctl list | grep portfolio
```

### View Logs
```bash
# Backend logs
tail -f ~/grok/logs/backend.log

# Dashboard logs
tail -f ~/grok/logs/dashboard.log

# Sync logs
tail -f ~/grok/logs/sync.log
```

### Restart Services
```bash
# Restart backend
launchctl kickstart -k gui/$(id -u)/com.portfolio.backend

# Restart dashboard
launchctl kickstart -k gui/$(id -u)/com.portfolio.dashboard

# Run sync manually
launchctl kickstart gui/$(id -u)/com.portfolio.sync
```

### Stop Services
```bash
launchctl stop com.portfolio.backend
launchctl stop com.portfolio.dashboard
```

### Unload Agents (disable auto-start)
```bash
launchctl unload ~/Library/LaunchAgents/com.portfolio.backend.plist
launchctl unload ~/Library/LaunchAgents/com.portfolio.dashboard.plist
launchctl unload ~/Library/LaunchAgents/com.portfolio.sync.plist
```

### Reload Agents (re-enable auto-start)
```bash
launchctl load ~/Library/LaunchAgents/com.portfolio.backend.plist
launchctl load ~/Library/LaunchAgents/com.portfolio.dashboard.plist
launchctl load ~/Library/LaunchAgents/com.portfolio.sync.plist
```

## Accessing the Services

After login, services will automatically start. Access them at:

- **Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Sync Schedule

The portfolio sync runs automatically every day at 6:00 PM. This:
- Fetches latest prices from Yahoo Finance
- Creates a new snapshot
- Updates holdings with current values
- Enriches ticker metadata (sector, industry, etc.)

## Troubleshooting

### Services not starting
1. Check logs for errors
2. Verify paths in plist files are correct
3. Ensure Python and npm are in PATH
4. Check file permissions

### Backend fails to start
```bash
# Check if port 8000 is in use
lsof -ti:8000

# Check Python/uvicorn installation
which python3
python3 -m uvicorn --version
```

### Dashboard fails to start
```bash
# Check if port 3000 is in use
lsof -ti:3000

# Verify npm and dependencies
cd ~/grok/dashboard
npm list
```

### Sync not running
```bash
# Check when next sync is scheduled
launchctl print gui/$(id -u)/com.portfolio.sync

# Run manually to test
cd ~/grok
python3 -m fidelity_tracker.cli sync
```

## Disabling Auto-Start

If you prefer to run services manually:

```bash
# Unload all agents
launchctl unload ~/Library/LaunchAgents/com.portfolio.*.plist

# Remove plist files (optional)
rm ~/Library/LaunchAgents/com.portfolio.*.plist
```

## Notes

- Logs are rotated automatically by the system
- Services will restart automatically if they crash
- Sync only runs if network is available
- All services use absolute paths to avoid PATH issues
