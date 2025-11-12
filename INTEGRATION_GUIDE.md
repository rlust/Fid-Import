# Integration Guide for Loveable.ai Application

This guide explains how to expose your Fidelity Portfolio Tracker data for consumption by external applications like your Loveable.ai app at `https://github.com/rlust/fidelity-portfolio-18884`.

---

## Integration Options (Recommended Order)

### Option 1: REST API (RECOMMENDED) ⭐

**Best for:** Web applications, mobile apps, real-time dashboards

The portfolio tracker includes a FastAPI server that provides real-time data access via HTTP endpoints.

#### Setup

1. **Start the API Server:**
   ```bash
   # Local development
   python -m fidelity_tracker.api.server

   # Or with uvicorn
   uvicorn fidelity_tracker.api.server:app --host 0.0.0.0 --port 8000

   # Or via Docker
   docker-compose up api
   ```

2. **API Documentation:**
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

#### Available Endpoints

```
GET /health
    → Health check: {"status": "healthy", "timestamp": "..."}

GET /api/v1/portfolio/summary
    → Portfolio overview with total value, holdings count, gain/loss

GET /api/v1/portfolio/holdings?limit=10
    → All holdings with optional limit

GET /api/v1/portfolio/top-holdings?limit=10
    → Top N holdings by value

GET /api/v1/portfolio/sectors
    → Sector allocation breakdown

GET /api/v1/portfolio/history?days=90
    → Historical portfolio value over time

GET /api/v1/snapshots?limit=10&days=30
    → Historical snapshots

GET /api/v1/snapshots/{id}
    → Specific snapshot details

GET /api/v1/snapshots/{id}/holdings
    → Holdings for a specific snapshot
```

#### Example: Fetch Portfolio Data

**JavaScript/TypeScript (for Loveable.ai React app):**

```typescript
// services/portfolioApi.ts
const API_BASE = process.env.VITE_PORTFOLIO_API_URL || 'http://localhost:8000';

export interface PortfolioSummary {
  total_value: number;
  total_holdings: number;
  total_gain_loss?: number;
  total_return_percent?: number;
  last_updated: string;
}

export interface Holding {
  symbol: string;
  company_name?: string;
  quantity: number;
  last_price: number;
  value: number;
  portfolio_weight?: number;
  sector?: string;
  industry?: string;
}

export const portfolioApi = {
  async getSummary(): Promise<PortfolioSummary> {
    const response = await fetch(`${API_BASE}/api/v1/portfolio/summary`);
    if (!response.ok) throw new Error('Failed to fetch summary');
    return response.json();
  },

  async getHoldings(limit?: number): Promise<Holding[]> {
    const url = limit
      ? `${API_BASE}/api/v1/portfolio/holdings?limit=${limit}`
      : `${API_BASE}/api/v1/portfolio/holdings`;
    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch holdings');
    return response.json();
  },

  async getHistory(days: number = 90): Promise<any> {
    const response = await fetch(`${API_BASE}/api/v1/portfolio/history?days=${days}`);
    if (!response.ok) throw new Error('Failed to fetch history');
    return response.json();
  }
};
```

**React Component Example:**

```tsx
// components/PortfolioSummary.tsx
import { useEffect, useState } from 'react';
import { portfolioApi, PortfolioSummary } from '@/services/portfolioApi';

export const PortfolioSummaryCard = () => {
  const [summary, setSummary] = useState<PortfolioSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await portfolioApi.getSummary();
        setSummary(data);
      } catch (error) {
        console.error('Error fetching portfolio:', error);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (!summary) return <div>No data available</div>;

  return (
    <div className="portfolio-summary">
      <h2>Portfolio Value</h2>
      <p className="value">${summary.total_value.toLocaleString()}</p>
      <p className="holdings">{summary.total_holdings} positions</p>
      {summary.total_gain_loss && (
        <p className={summary.total_gain_loss >= 0 ? 'gain' : 'loss'}>
          {summary.total_gain_loss >= 0 ? '+' : ''}
          ${summary.total_gain_loss.toLocaleString()}
          ({summary.total_return_percent?.toFixed(2)}%)
        </p>
      )}
    </div>
  );
};
```

#### CORS Configuration

The API is configured with CORS enabled for all origins (development). For production:

```python
# In fidelity_tracker/api/server.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-loveable-app.com"],  # Update this
    allow_credentials=True,
    allow_methods=["GET"],  # Only allow GET for security
    allow_headers=["*"],
)
```

#### Deploying the API

**Option A: Local Network (Same Machine)**
```bash
# Start API server accessible on local network
uvicorn fidelity_tracker.api.server:app --host 0.0.0.0 --port 8000
```

**Option B: Cloud Deployment (Railway, Render, Fly.io)**

Create `Procfile`:
```
web: uvicorn fidelity_tracker.api.server:app --host 0.0.0.0 --port $PORT
```

**Option C: Docker + Nginx Reverse Proxy**
```yaml
# docker-compose.yml
services:
  api:
    build: .
    command: python -m fidelity_tracker.api.server
    ports:
      - "8000:8000"
    volumes:
      - ./fidelity_portfolio.db:/app/fidelity_portfolio.db:ro
```

---

### Option 2: JSON File Export + GitHub Actions ⭐

**Best for:** Static sites, JAMstack apps, applications that don't need real-time data

Export portfolio data as JSON and automatically sync it to your Loveable.ai repository.

#### Setup Automated Export

**1. Export latest snapshot to JSON:**

```bash
# Export current portfolio to JSON
portfolio-tracker export data/portfolio-latest.json --format json

# Or export specific snapshot
portfolio-tracker export data/portfolio-latest.json --snapshot-id 3 --format json
```

**2. Create scheduled export script:**

Create `scripts/export_for_loveable.sh`:

```bash
#!/bin/bash
# Export portfolio data for Loveable.ai integration

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXPORT_DIR="$PROJECT_ROOT/exports"
LOVEABLE_REPO="$HOME/fidelity-portfolio-18884"  # Update path

# Create exports directory
mkdir -p "$EXPORT_DIR"

# Export latest snapshot as JSON
portfolio-tracker export "$EXPORT_DIR/portfolio-latest.json" --format json

# Also export CSV for reference
portfolio-tracker export "$EXPORT_DIR/portfolio-latest.csv" --format csv

# Export historical data (last 90 days)
portfolio-tracker export "$EXPORT_DIR/portfolio-history.json" --format json --days 90

# If Loveable repo exists, copy data there
if [ -d "$LOVEABLE_REPO" ]; then
    echo "Copying to Loveable.ai repo..."
    mkdir -p "$LOVEABLE_REPO/data"
    cp "$EXPORT_DIR/portfolio-latest.json" "$LOVEABLE_REPO/data/"

    # Optionally commit and push
    cd "$LOVEABLE_REPO"
    git add data/portfolio-latest.json
    git commit -m "Update portfolio data $(date '+%Y-%m-%d %H:%M')"
    git push origin main

    echo "✅ Data exported and pushed to Loveable.ai repo"
else
    echo "⚠️ Loveable repo not found at $LOVEABLE_REPO"
    echo "Data exported to $EXPORT_DIR"
fi
```

Make it executable:
```bash
chmod +x scripts/export_for_loveable.sh
```

**3. Schedule with cron:**

```bash
# Run export daily at 6 PM
crontab -e

# Add this line:
0 18 * * * cd /Users/randylust/grok && ./scripts/export_for_loveable.sh >> logs/export.log 2>&1
```

**4. Access in Loveable.ai app:**

```typescript
// In your Loveable.ai React app
import portfolioData from './data/portfolio-latest.json';

export const usePortfolioData = () => {
  return {
    summary: {
      totalValue: portfolioData.total_value,
      timestamp: portfolioData.timestamp,
      holdingsCount: portfolioData.total_holdings
    },
    holdings: portfolioData.accounts ?
      Object.values(portfolioData.accounts)
        .flatMap(account => account.holdings || [])
      : []
  };
};
```

#### JSON Data Structure

The exported JSON has this structure:

```json
{
  "timestamp": "2025-11-12T14:30:00.123456",
  "total_value": 2160622.72,
  "total_holdings": 167,
  "accounts": {
    "X12345678": {
      "account_id": "X12345678",
      "nickname": "Individual",
      "balance": 1250000.00,
      "holdings": [
        {
          "ticker": "QQQ",
          "company_name": "QQQ",
          "quantity": 350.0,
          "last_price": 369.32,
          "value": 129262.64,
          "sector": "Technology",
          "industry": "Exchange Traded Fund",
          "portfolio_weight": 5.98,
          "account_weight": 10.34
        }
      ]
    }
  }
}
```

---

### Option 3: Direct Database Access

**Best for:** Applications running on same machine, read-only access needed

The portfolio tracker uses SQLite, which can be read by multiple applications simultaneously (read-only).

#### Setup

**1. Copy database to shared location:**

```bash
# Copy database to a shared read-only location
cp fidelity_portfolio.db /path/to/shared/portfolio.db
chmod 444 /path/to/shared/portfolio.db  # Read-only
```

**2. Access from Loveable.ai app:**

If your Loveable.ai app has a backend (Node.js, Python):

**Node.js/TypeScript:**

```bash
npm install better-sqlite3
```

```typescript
// services/portfolioDb.ts
import Database from 'better-sqlite3';

const db = new Database('/path/to/shared/portfolio.db', { readonly: true });

export interface Holding {
  ticker: string;
  company_name: string;
  quantity: number;
  last_price: number;
  value: number;
  sector: string;
  portfolio_weight: number;
}

export const portfolioDb = {
  getLatestSnapshot() {
    return db.prepare(`
      SELECT id, timestamp, total_value
      FROM snapshots
      ORDER BY id DESC
      LIMIT 1
    `).get();
  },

  getHoldings(snapshotId: number): Holding[] {
    return db.prepare(`
      SELECT ticker, company_name, quantity, last_price, value,
             sector, industry, portfolio_weight
      FROM holdings
      WHERE snapshot_id = ?
      ORDER BY value DESC
    `).all(snapshotId);
  },

  getPortfolioHistory(days: number = 90) {
    return db.prepare(`
      SELECT id, timestamp, total_value
      FROM snapshots
      WHERE datetime(timestamp) >= datetime('now', '-${days} days')
      ORDER BY timestamp DESC
    `).all();
  }
};
```

**Python Backend:**

```python
import sqlite3
from typing import List, Dict

class PortfolioReader:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_latest_snapshot(self) -> Dict:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, timestamp, total_value
                FROM snapshots
                ORDER BY id DESC
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_holdings(self, snapshot_id: int) -> List[Dict]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT ticker, company_name, quantity, last_price,
                       value, sector, portfolio_weight
                FROM holdings
                WHERE snapshot_id = ?
                ORDER BY value DESC
            """, (snapshot_id,))
            return [dict(row) for row in cursor.fetchall()]
```

---

### Option 4: Webhook/Push Notifications

**Best for:** Real-time updates when portfolio changes

Set up the portfolio tracker to push updates to your Loveable.ai app when new data is available.

#### Implementation

**1. Create webhook notifier:**

Create `fidelity_tracker/utils/webhook.py`:

```python
import requests
from typing import Dict, Any
from loguru import logger

class WebhookNotifier:
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def notify_update(self, snapshot_data: Dict[str, Any]):
        """Send portfolio update to webhook endpoint"""
        try:
            response = requests.post(
                self.webhook_url,
                json={
                    "event": "portfolio_updated",
                    "timestamp": snapshot_data.get("timestamp"),
                    "total_value": snapshot_data.get("total_value"),
                    "holdings_count": snapshot_data.get("total_holdings")
                },
                timeout=10
            )
            response.raise_for_status()
            logger.success(f"Webhook notification sent successfully")
        except Exception as e:
            logger.error(f"Failed to send webhook: {e}")
```

**2. Configure webhook URL:**

```yaml
# config/config.yaml
webhook:
  enabled: true
  url: "https://your-loveable-app.com/api/webhooks/portfolio"
  secret: "your-webhook-secret"
```

**3. Add to sync command:**

Modify sync to call webhook after successful update.

**4. Loveable.ai webhook endpoint:**

```typescript
// pages/api/webhooks/portfolio.ts
import type { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { event, timestamp, total_value, holdings_count } = req.body;

  if (event === 'portfolio_updated') {
    // Trigger data refresh in your app
    console.log('Portfolio updated:', { timestamp, total_value, holdings_count });

    // Optionally store in your database or trigger revalidation

    return res.status(200).json({ received: true });
  }

  res.status(400).json({ error: 'Invalid event' });
}
```

---

## Recommended Setup for Loveable.ai Integration

Based on typical Loveable.ai app structure (React/Next.js), here's the recommended approach:

### Architecture

```
┌─────────────────────┐
│ Fidelity Tracker    │
│ (Local Machine)     │
│                     │
│ - Syncs portfolio   │
│ - Stores in SQLite  │
│ - Runs API server   │
└──────────┬──────────┘
           │
           │ Option A: Direct API calls (local dev)
           │ Option B: Export JSON → Git → Deploy
           │
┌──────────▼──────────┐
│ Loveable.ai App     │
│ (loveable.dev)      │
│                     │
│ - React/Next.js UI  │
│ - Charts/Dashboard  │
│ - Hosted on cloud   │
└─────────────────────┘
```

### Implementation Steps

**Step 1: Choose integration method**

For Loveable.ai hosted apps, use **Option 2 (JSON Export + Git)** because:
- ✅ Works with hosted static sites
- ✅ No need for server deployment
- ✅ Simple and reliable
- ✅ Version controlled data

**Step 2: Set up automated export**

```bash
# Create export script
./scripts/export_for_loveable.sh

# Test it
./scripts/export_for_loveable.sh

# Schedule it (cron or launchd on macOS)
crontab -e
0 18 * * * cd /Users/randylust/grok && ./scripts/export_for_loveable.sh
```

**Step 3: Configure Loveable.ai app**

1. Add data directory to your repo
2. Import JSON in components
3. Use React Query for data management

Example:

```tsx
// hooks/usePortfolio.ts
import { useQuery } from '@tanstack/react-query';
import portfolioData from '@/data/portfolio-latest.json';

export const usePortfolio = () => {
  return useQuery({
    queryKey: ['portfolio'],
    queryFn: () => Promise.resolve(portfolioData),
    staleTime: 1000 * 60 * 60, // 1 hour
  });
};
```

**Step 4: Build dashboard**

```tsx
// components/Dashboard.tsx
import { usePortfolio } from '@/hooks/usePortfolio';
import { Card } from '@/components/ui/card';

export const Dashboard = () => {
  const { data: portfolio, isLoading } = usePortfolio();

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="grid grid-cols-3 gap-4">
      <Card>
        <h3>Total Value</h3>
        <p className="text-3xl font-bold">
          ${portfolio.total_value.toLocaleString()}
        </p>
      </Card>

      <Card>
        <h3>Holdings</h3>
        <p className="text-3xl font-bold">{portfolio.total_holdings}</p>
      </Card>

      <Card>
        <h3>Last Updated</h3>
        <p>{new Date(portfolio.timestamp).toLocaleDateString()}</p>
      </Card>
    </div>
  );
};
```

---

## Data Formats

### JSON Export Format

```json
{
  "timestamp": "2025-11-12T14:30:00",
  "total_value": 2160622.72,
  "total_holdings": 167,
  "accounts": {
    "X12345678": {
      "account_id": "X12345678",
      "nickname": "Individual",
      "balance": 1250000.00,
      "holdings": [...]
    }
  }
}
```

### CSV Export Format

```csv
Account ID,Account Nickname,Ticker,Company Name,Quantity,Last Price,Value,Sector,Industry,Portfolio Weight (%)
X12345678,Individual,QQQ,QQQ,350.0,369.32,129262.64,Technology,ETF,5.98
```

---

## Security Considerations

1. **API Authentication** (if using REST API):
   ```python
   # Add API key authentication
   from fastapi import Header, HTTPException

   async def verify_api_key(x_api_key: str = Header(...)):
       if x_api_key != os.getenv("API_KEY"):
           raise HTTPException(status_code=401, detail="Invalid API key")

   @app.get("/api/v1/portfolio/summary", dependencies=[Depends(verify_api_key)])
   ```

2. **Read-only database access** - Never give write access to external apps

3. **HTTPS only** - Use SSL/TLS for API calls in production

4. **Rate limiting** - Implement if API is publicly accessible

---

## Testing the Integration

```bash
# Test JSON export
portfolio-tracker export exports/test.json --format json
cat exports/test.json | jq .total_value

# Test API endpoint
curl http://localhost:8000/api/v1/portfolio/summary | jq .

# Test database access
sqlite3 fidelity_portfolio.db "SELECT COUNT(*) FROM holdings WHERE snapshot_id = (SELECT MAX(id) FROM snapshots)"
```

---

## Troubleshooting

### Issue: Loveable.ai app can't access local API

**Solution:** Use ngrok for temporary public URL:
```bash
ngrok http 8000
# Use the ngrok URL in your Loveable app
```

### Issue: JSON file too large for Git

**Solution:** Use Git LFS or host on cloud storage:
```bash
git lfs track "*.json"
git lfs push origin main
```

### Issue: Data not updating in Loveable app

**Solution:** Check export script logs and Git push status:
```bash
tail -f logs/export.log
```

---

## Next Steps

1. ✅ Choose integration method (API or JSON export)
2. ✅ Set up automated export script if using JSON
3. ✅ Configure Loveable.ai app to consume data
4. ✅ Build dashboard components
5. ✅ Schedule regular syncs (cron job)
6. ✅ Monitor and test integration

Need help with a specific integration method? Let me know!
