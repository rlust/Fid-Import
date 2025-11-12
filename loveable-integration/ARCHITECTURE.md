# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Fidelity Portfolio Tracker                   │
│                     (Local Machine - macOS)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐        │
│  │   Fidelity   │──▶│  Portfolio   │──▶│   SQLite     │        │
│  │     API      │   │  Collector   │   │   Database   │        │
│  └──────────────┘   └──────────────┘   └──────────────┘        │
│                                               │                  │
│                                               ▼                  │
│                                      ┌──────────────────┐        │
│                                      │  Data Enricher   │        │
│                                      │  (Yahoo Finance) │        │
│                                      └──────────────────┘        │
│                                               │                  │
│                                               ▼                  │
│                              ┌────────────────────────────┐      │
│                              │   Export Script            │      │
│                              │   (runs daily at 6 PM)     │      │
│                              └────────────────────────────┘      │
│                                               │                  │
└───────────────────────────────────────────────┼──────────────────┘
                                                │
                           Exports portfolio-latest.json
                                                │
                                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Git Repository (GitHub)                        │
│                   fidelity-portfolio-18884                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  src/                                                             │
│  ├── data/                                                        │
│  │   └── portfolio-latest.json ◀── Updated daily                │
│  ├── services/                                                    │
│  │   └── portfolioService.ts                                    │
│  ├── hooks/                                                       │
│  │   └── usePortfolio.ts                                        │
│  ├── components/portfolio/                                       │
│  │   ├── PortfolioSummary.tsx                                   │
│  │   ├── HoldingsTable.tsx                                      │
│  │   ├── PortfolioChart.tsx                                     │
│  │   └── SectorAllocation.tsx                                   │
│  └── pages/                                                       │
│      └── Dashboard.tsx                                           │
│                                                                   │
└────────────────────────────────┬────────────────────────────────┘
                                 │
                          Auto-deploy on push
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Loveable.ai Hosting                             │
│                  (Production Website)                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────┐        │
│  │          React Application (Built)                   │        │
│  │  ┌─────────────────────────────────────────────┐    │        │
│  │  │         Portfolio Dashboard                  │    │        │
│  │  │  ┌──────────────┐  ┌──────────────┐        │    │        │
│  │  │  │   Summary    │  │    Charts    │        │    │        │
│  │  │  │    Cards     │  │  & Graphs    │        │    │        │
│  │  │  └──────────────┘  └──────────────┘        │    │        │
│  │  │  ┌──────────────────────────────────┐      │    │        │
│  │  │  │     Holdings Table               │      │    │        │
│  │  │  │  (Sortable, Searchable)          │      │    │        │
│  │  │  └──────────────────────────────────┘      │    │        │
│  │  └─────────────────────────────────────────────┘    │        │
│  └─────────────────────────────────────────────────────┘        │
│                              │                                    │
│                              ▼                                    │
│                       ┌──────────────┐                           │
│                       │  End Users   │                           │
│                       │  (Browsers)  │                           │
│                       └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Daily Update Cycle

```
1. 6:00 PM Daily
   ├── LaunchAgent/Cron triggers export script
   │
2. Export Script Runs
   ├── portfolio-tracker export (JSON)
   ├── Saves to exports/ directory
   └── Copies to Loveable.ai repo
   │
3. Git Operations
   ├── git add data/portfolio-latest.json
   ├── git commit -m "Update portfolio data YYYY-MM-DD HH:MM"
   └── git push origin main
   │
4. Loveable.ai Auto-Deploy
   ├── Detects new commit
   ├── Builds React application
   └── Deploys to production
   │
5. Users See Updated Data
   └── Next page load shows new portfolio values
```

## Component Architecture

### Service Layer

```typescript
portfolioService
├── Data Loading
│   ├── Import JSON file
│   └── Type casting
├── Data Access
│   ├── getSummary()
│   ├── getHoldings()
│   ├── getTopHoldings()
│   └── getSectorAllocation()
├── Data Processing
│   ├── Filtering
│   ├── Sorting
│   └── Aggregation
└── Export
    ├── exportToCSV()
    └── downloadCSV()
```

### Hooks Layer

```typescript
usePortfolio hooks (React Query)
├── usePortfolioSummary()
├── useHoldings()
├── useTopHoldings()
├── useSectorAllocation()
├── usePortfolioStatistics()
└── useDashboardData()
    └── Combines all above hooks
```

### Component Layer

```
Dashboard (Page)
├── PortfolioSummary
│   ├── Total Value Card
│   ├── Total Holdings Card
│   └── Last Updated Card
│
├── PortfolioChart
│   └── Top 10 Holdings Bar Chart
│
├── SectorAllocation
│   ├── Visual Bar
│   └── Sector Breakdown List
│
└── HoldingsTable
    ├── Search Bar
    ├── Sort Functionality
    ├── Data Table
    └── CSV Export Button
```

## Technology Stack

### Backend (Fidelity Tracker)
- **Language**: Python 3.12
- **Database**: SQLite
- **API**: FastAPI (optional, for real-time access)
- **Data Collection**: Playwright (fidelity-api)
- **Data Enrichment**: yfinance
- **Automation**: LaunchAgent/Cron

### Frontend (Loveable.ai)
- **Framework**: React 18
- **Build Tool**: Vite
- **Language**: TypeScript
- **State Management**: React Query (TanStack Query v5)
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui
- **Icons**: Lucide React

## Data Schema

### Snapshot
```typescript
{
  id: number;
  timestamp: string;          // ISO 8601 format
  total_value: number;        // Total portfolio value
  holdings: Holding[];        // Array of all holdings
}
```

### Holding
```typescript
{
  id: number;
  snapshot_id: number;
  account_id: string;
  ticker: string;             // Stock symbol
  company_name: string;
  quantity: number;
  last_price: number;
  value: number;              // quantity × last_price
  sector: string;
  industry: string;
  market_cap: number | null;
  pe_ratio: number | null;
  dividend_yield: number | null;
  portfolio_weight: number;   // % of total portfolio
  account_weight: number;     // % of account
}
```

## Security Considerations

### Data Security
- ✅ JSON files are read-only in production
- ✅ No API keys or credentials in frontend code
- ✅ Git repository is private (recommended)
- ✅ Fidelity credentials stored locally only

### Access Control
- ✅ Loveable.ai handles authentication
- ✅ Data is static (no database queries from frontend)
- ✅ No write operations from web interface

## Performance

### Caching Strategy
- React Query caches data for 1 hour
- Data updates only once daily (at 6 PM)
- No API calls after initial load
- Fast page loads (data bundled with app)

### Bundle Size
- portfolio-latest.json: ~200-300KB
- Gzipped: ~30-50KB
- Minimal impact on load time

## Monitoring

### Health Checks
```bash
# Check export logs
tail -f ~/grok/logs/export.log

# Verify data freshness
stat ~/fidelity-portfolio-18884/src/data/portfolio-latest.json

# Check LaunchAgent status
launchctl list | grep portfolio

# View last Git commit
cd ~/fidelity-portfolio-18884
git log -1 --oneline
```

### Error Handling
- Export script logs all errors
- LaunchAgent logs to separate error file
- React Query handles loading/error states
- UI shows fallback messages on failure

## Scalability

### Current Limitations
- Updates once per day only
- Static data (no real-time updates)
- Single user focus

### Possible Enhancements
1. **Real-Time Updates**: Add WebSocket or SSE
2. **Multiple Users**: Add authentication
3. **More Frequent Updates**: Adjust schedule
4. **Historical Charts**: Add time-series data
5. **Notifications**: Alert on portfolio changes

## Deployment

### Development
```bash
cd ~/fidelity-portfolio-18884
npm run dev
# Access at http://localhost:5173
```

### Production
```bash
git push origin main
# Loveable.ai auto-deploys
# Access at https://your-app.loveable.app
```

## Maintenance

### Regular Tasks
- **Daily**: Automatic data exports (no action needed)
- **Weekly**: Check export logs for errors
- **Monthly**: Verify Git repository size
- **Quarterly**: Review and update dependencies

### Troubleshooting Checklist
- [ ] Export script running? (check launchctl)
- [ ] Data file updated? (check timestamp)
- [ ] Git commits happening? (check git log)
- [ ] Loveable.ai deploying? (check site)
- [ ] Components rendering? (check browser console)

## Future Architecture Options

### Option 1: Hybrid (Static + API)
```
React App
├── Load static JSON (fast initial render)
└── Fetch from API (real-time updates)
```

### Option 2: Serverless
```
AWS Lambda / Vercel Functions
├── Scheduled function runs export
└── Stores in S3 / Database
```

### Option 3: Full Stack
```
Next.js Application
├── Backend API routes
├── Server-side rendering
└── Incremental Static Regeneration
```
