# Loveable.ai Setup Instructions

Step-by-step guide to integrate the Fidelity Portfolio Tracker with your Loveable.ai application.

## Prerequisites

- Your Loveable.ai project cloned locally
- Node.js and npm installed
- Git configured
- Portfolio tracker set up and running

## Step 1: Install Dependencies

In your Loveable.ai project directory:

```bash
cd ~/fidelity-portfolio-18884

# Install React Query (if not already installed)
npm install @tanstack/react-query

# Install UI components (if using shadcn/ui)
# If you're using Loveable.ai, these may already be installed
npm install lucide-react
npm install class-variance-authority clsx tailwind-merge

# If using TypeScript (recommended)
npm install --save-dev @types/node
```

## Step 2: Copy Integration Files

Copy all files from `loveable-integration/` to your Loveable.ai project:

```bash
# From the fidelity tracker directory
cd ~/grok

# Create necessary directories in Loveable.ai project
mkdir -p ~/fidelity-portfolio-18884/src/data
mkdir -p ~/fidelity-portfolio-18884/src/services
mkdir -p ~/fidelity-portfolio-18884/src/hooks
mkdir -p ~/fidelity-portfolio-18884/src/components/portfolio
mkdir -p ~/fidelity-portfolio-18884/src/pages

# Copy service layer
cp loveable-integration/services/portfolioService.ts ~/fidelity-portfolio-18884/src/services/

# Copy hooks
cp loveable-integration/hooks/usePortfolio.ts ~/fidelity-portfolio-18884/src/hooks/

# Copy components
cp loveable-integration/components/*.tsx ~/fidelity-portfolio-18884/src/components/portfolio/

# Copy page
cp loveable-integration/pages/Dashboard.tsx ~/fidelity-portfolio-18884/src/pages/
```

## Step 3: Export Portfolio Data

```bash
cd ~/grok

# Set the Loveable repo path
export LOVEABLE_REPO_PATH=~/fidelity-portfolio-18884

# Run the export script
./scripts/export_for_loveable.sh

# This will:
# 1. Export portfolio data to JSON
# 2. Copy it to ~/fidelity-portfolio-18884/src/data/
# 3. Commit and push the changes (if AUTO_COMMIT=true)
```

## Step 4: Configure Import Paths

Update the import paths in the copied files to match your project structure.

### Check your project's path aliases

Look at your `tsconfig.json`:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]  // Common alias
    }
  }
}
```

If your project uses different aliases, update the imports in:
- `services/portfolioService.ts`
- `hooks/usePortfolio.ts`
- `components/*.tsx`
- `pages/Dashboard.tsx`

## Step 5: Add Dashboard to Your App

### Option A: Replace existing page

In your `src/App.tsx` or main routing file:

```typescript
import { Dashboard } from './pages/Dashboard';

function App() {
  return <Dashboard />;
}

export default App;
```

### Option B: Add as a route (if using React Router)

```typescript
import { Dashboard } from './pages/Dashboard';

<Route path="/portfolio" element={<Dashboard />} />
```

### Option C: Use components individually

```typescript
import { PortfolioSummary } from './components/portfolio/PortfolioSummary';
import { HoldingsTable } from './components/portfolio/HoldingsTable';

function MyPage() {
  return (
    <div>
      <PortfolioSummary />
      <HoldingsTable />
    </div>
  );
}
```

## Step 6: Setup Automated Data Updates

### Option A: Cron Job (Simple)

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 6 PM)
0 18 * * * cd /Users/randylust/grok && LOVEABLE_REPO_PATH=/Users/randylust/fidelity-portfolio-18884 AUTO_COMMIT=true ./scripts/export_for_loveable.sh >> logs/export.log 2>&1
```

### Option B: LaunchAgent (Recommended for macOS)

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
        <key>AUTO_COMMIT</key>
        <string>true</string>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
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
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
```

Load the agent:

```bash
launchctl load ~/Library/LaunchAgents/com.portfolio.export.plist

# Test it manually
launchctl start com.portfolio.export

# Check status
launchctl list | grep portfolio
```

## Step 7: Test the Integration

```bash
cd ~/fidelity-portfolio-18884

# Start development server
npm run dev

# Open in browser (usually http://localhost:3000 or http://localhost:5173)
```

### What to check:

1. ✅ Portfolio summary cards display correct total value
2. ✅ Holdings table shows all positions
3. ✅ Top holdings chart displays correctly
4. ✅ Sector allocation shows percentages
5. ✅ Search and sort functionality works
6. ✅ CSV export downloads file
7. ✅ Refresh button reloads data

## Step 8: Deploy to Loveable.ai

```bash
cd ~/fidelity-portfolio-18884

# Commit any customizations you made
git add .
git commit -m "Add portfolio dashboard integration"

# Push to Loveable.ai
git push origin main
```

Loveable.ai will automatically deploy your changes.

## Troubleshooting

### Data file not found

```bash
# Check if data file exists
ls -lh ~/fidelity-portfolio-18884/src/data/portfolio-latest.json

# If not, run export manually
cd ~/grok
./scripts/export_for_loveable.sh
```

### Import errors

Check that your `tsconfig.json` has the correct path mappings:

```json
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"],
      "@/components/*": ["./src/components/*"],
      "@/services/*": ["./src/services/*"],
      "@/hooks/*": ["./src/hooks/*"],
      "@/data/*": ["./src/data/*"]
    }
  }
}
```

### UI components not found

If using shadcn/ui and components are missing:

```bash
# Install missing components
npx shadcn-ui@latest add card
npx shadcn-ui@latest add button
npx shadcn-ui@latest add table
npx shadcn-ui@latest add input
npx shadcn-ui@latest add skeleton
```

### TypeScript errors

```bash
# Check TypeScript configuration
npm run type-check

# Or ignore for now (not recommended)
# Add // @ts-nocheck at the top of files
```

### Data not updating automatically

```bash
# Check export logs
tail -f ~/grok/logs/export.log

# Check if launchagent is running
launchctl list | grep portfolio

# Test manual export
cd ~/grok
LOVEABLE_REPO_PATH=~/fidelity-portfolio-18884 ./scripts/export_for_loveable.sh

# Check if changes were pushed
cd ~/fidelity-portfolio-18884
git log -1
git status
```

### Styling issues

The components use Tailwind CSS. Ensure your `tailwind.config.js` includes:

```js
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

## Customization

### Change update schedule

Edit the LaunchAgent plist or crontab to run at different times:

```xml
<!-- For 8 AM daily -->
<key>StartCalendarInterval</key>
<dict>
    <key>Hour</key>
    <integer>8</integer>
    <key>Minute</key>
    <integer>0</integer>
</dict>
```

### Add more charts

The service layer provides these additional methods you can use:

```typescript
import { portfolioService } from '@/services/portfolioService';

// Get statistics
const stats = portfolioService.getStatistics();

// Search holdings
const results = portfolioService.searchHoldings('AAPL');

// Get holdings by sector
const techHoldings = portfolioService.getHoldingsBySector('Technology');

// Get historical comparison
const comparison = portfolioService.getHistoricalComparison();
```

### Customize styling

All components use Tailwind CSS and shadcn/ui. You can customize:

- Colors: Update your theme in `tailwind.config.js`
- Spacing: Modify the className props
- Layout: Change the grid layouts in `Dashboard.tsx`

## Next Steps

1. ✅ Customize the dashboard layout
2. ✅ Add additional charts or metrics
3. ✅ Set up monitoring for automated exports
4. ✅ Add error boundaries for better error handling
5. ✅ Implement data caching strategies
6. ✅ Add loading states and skeletons
7. ✅ Create mobile-responsive layouts

## Support

- Main Integration Guide: `../INTEGRATION_GUIDE.md`
- Export Script: `../scripts/export_for_loveable.sh`
- Testing Report: `../TESTING_REPORT.md`

## Quick Commands Reference

```bash
# Export data manually
cd ~/grok && ./scripts/export_for_loveable.sh

# Check export logs
tail -f ~/grok/logs/export.log

# Test Loveable.ai app locally
cd ~/fidelity-portfolio-18884 && npm run dev

# Deploy to Loveable.ai
cd ~/fidelity-portfolio-18884 && git push origin main

# Restart LaunchAgent
launchctl unload ~/Library/LaunchAgents/com.portfolio.export.plist
launchctl load ~/Library/LaunchAgents/com.portfolio.export.plist
```
