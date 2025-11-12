# GitHub Storage Configuration

Your portfolio data is **already stored on GitHub** and accessible from anywhere. This guide explains how it works and how to configure different data loading strategies.

---

## Current Setup ✅

Data is automatically stored on GitHub via this workflow:

```
1. Export Script Runs (6 PM daily)
   ↓
2. portfolio-latest.json created
   ↓
3. Copied to ~/fidelity-portfolio-18884/src/data/
   ↓
4. Git commit: "Update portfolio data YYYY-MM-DD HH:MM"
   ↓
5. Git push to GitHub
   ↓
6. Loveable.ai reads from GitHub and deploys
```

**Your data location:**
```
https://github.com/rlust/fidelity-portfolio-18884/blob/main/src/data/portfolio-latest.json
```

---

## Data Loading Strategies

### Strategy 1: Bundled (Current - Recommended) ⭐

**How it works:**
- Data file imported directly into app
- Bundled during build process
- No network requests needed

**Pros:**
- ⚡ Instant loading (no API calls)
- 📦 Works offline
- 🔒 No CORS issues
- 💰 No rate limits

**Cons:**
- Data only updates when app rebuilds/redeploys
- Loveable.ai redeploys on every Git push anyway, so this works perfectly!

**Configuration:**
```typescript
// Default - no config needed
import portfolioData from '@/data/portfolio-latest.json';
```

### Strategy 2: GitHub Raw URL (Always Fresh)

**How it works:**
- Fetches data directly from GitHub on page load
- Always gets the latest committed version

**Pros:**
- 🔄 Always up-to-date
- 🌐 Works from anywhere
- 📡 No build needed for data updates

**Cons:**
- Requires public repository
- Network request on every load
- Subject to GitHub rate limits (60 req/hour without auth)

**Configuration:**

**Step 1:** Create `.env` file in your Loveable.ai project:

```env
# Use GitHub raw URL for data
VITE_DATA_SOURCE=github-raw
VITE_GITHUB_REPO=rlust/fidelity-portfolio-18884
VITE_GITHUB_BRANCH=main
VITE_GITHUB_PATH=src/data/portfolio-latest.json
```

**Step 2:** Use enhanced service:

```typescript
// Use the enhanced version
import { portfolioService } from '@/services/portfolioServiceEnhanced';

// Initialize (loads from GitHub)
await portfolioService.initialize();

// Use normally
const summary = portfolioService.getSummary();
```

### Strategy 3: GitHub API (Private Repos)

**How it works:**
- Uses GitHub API to fetch file contents
- Works with private repositories

**Pros:**
- 🔒 Works with private repos
- 🔄 Always fresh data
- 📊 Higher rate limits with token (5000 req/hour)

**Cons:**
- Requires GitHub personal access token
- Token must be stored securely

**Configuration:**

**Step 1:** Create GitHub Personal Access Token:
1. Go to https://github.com/settings/tokens
2. Generate new token (classic)
3. Select scope: `repo` (for private repos) or `public_repo` (for public)
4. Copy the token

**Step 2:** Add to `.env`:

```env
VITE_DATA_SOURCE=github-api
VITE_GITHUB_REPO=rlust/fidelity-portfolio-18884
VITE_GITHUB_BRANCH=main
VITE_GITHUB_PATH=src/data/portfolio-latest.json
VITE_GITHUB_TOKEN=ghp_your_token_here
```

**⚠️ Security Note:**
- Never commit `.env` file to Git
- Add `.env` to `.gitignore`
- Use environment variables in Loveable.ai dashboard for production

---

## Comparison Table

| Feature | Bundled | GitHub Raw | GitHub API |
|---------|---------|------------|------------|
| Speed | ⚡⚡⚡ Instant | ⚡ Network call | ⚡ Network call |
| Freshness | On deploy | Always | Always |
| Public repos | ✅ | ✅ | ✅ |
| Private repos | ✅ | ❌ | ✅ |
| Rate limits | None | 60/hour | 5000/hour |
| Token needed | ❌ | ❌ | ✅ |
| CORS issues | ❌ | ❌ | ❌ |
| Offline support | ✅ | ❌ | ❌ |

---

## Recommended Configuration

### For Most Users (Current Setup) ✅

**Use: Bundled (Strategy 1)**

Since Loveable.ai auto-deploys on every Git push:
- Data gets updated in GitHub at 6 PM
- Loveable.ai deploys with fresh data
- Users see new data immediately after deploy
- No additional configuration needed

### For Immediate Updates

**Use: GitHub Raw (Strategy 2)**

If you need data to update without redeploying:

```env
VITE_DATA_SOURCE=github-raw
```

### For Private Repositories

**Use: GitHub API (Strategy 3)**

```env
VITE_DATA_SOURCE=github-api
VITE_GITHUB_TOKEN=your_token
```

---

## Implementation

### Option A: Keep Current Setup (Recommended)

No changes needed! Your data is already on GitHub and the app reads it correctly.

### Option B: Switch to GitHub Raw/API

**Step 1:** Copy enhanced files:

```bash
cd ~/grok/loveable-integration

# Copy to your Loveable.ai project
cp services/portfolioDataSource.ts ~/fidelity-portfolio-18884/src/services/
cp services/portfolioServiceEnhanced.ts ~/fidelity-portfolio-18884/src/services/
```

**Step 2:** Create `.env` file:

```bash
cd ~/fidelity-portfolio-18884

cat > .env << EOF
VITE_DATA_SOURCE=github-raw
VITE_GITHUB_REPO=rlust/fidelity-portfolio-18884
VITE_GITHUB_BRANCH=main
VITE_GITHUB_PATH=src/data/portfolio-latest.json
EOF
```

**Step 3:** Update hooks to use enhanced service:

```typescript
// In hooks/usePortfolio.ts
import { portfolioService } from '@/services/portfolioServiceEnhanced';

export function usePortfolioSummary() {
  return useQuery({
    queryKey: ['portfolio', 'summary'],
    queryFn: async () => {
      await portfolioService.initialize();
      return portfolioService.getSummary();
    },
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
```

**Step 4:** Add `.env` to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

---

## Testing Different Strategies

### Test Bundled (Current):

```bash
cd ~/fidelity-portfolio-18884
npm run dev
# Check Network tab - should see no GitHub requests
```

### Test GitHub Raw:

```bash
# Set environment variable
VITE_DATA_SOURCE=github-raw npm run dev

# Check Network tab - should see:
# GET https://raw.githubusercontent.com/rlust/fidelity-portfolio-18884/main/src/data/portfolio-latest.json
```

### Test GitHub API:

```bash
# Set all environment variables
VITE_DATA_SOURCE=github-api \
VITE_GITHUB_TOKEN=your_token \
npm run dev

# Check Network tab - should see:
# GET https://api.github.com/repos/rlust/fidelity-portfolio-18884/contents/...
```

---

## Verify Data on GitHub

### Via Web Browser:

**Raw file:**
```
https://raw.githubusercontent.com/rlust/fidelity-portfolio-18884/main/src/data/portfolio-latest.json
```

**GitHub UI:**
```
https://github.com/rlust/fidelity-portfolio-18884/blob/main/src/data/portfolio-latest.json
```

### Via Command Line:

```bash
# Check last commit
cd ~/fidelity-portfolio-18884
git log -1 src/data/portfolio-latest.json

# View file
cat src/data/portfolio-latest.json | jq '.[0] | {id, timestamp, total_value}'

# Check if pushed to GitHub
git status
```

---

## Monitoring & Debugging

### Check Data Freshness:

```typescript
const freshness = portfolioService.getDataFreshness();
console.log('Data age:', freshness.ageFormatted);
console.log('Is stale?', freshness.isStale);
```

### Check Cache Status:

```typescript
const cacheStatus = dataSource.getCacheStatus();
console.log('Is cached?', cacheStatus.isCached);
console.log('Cache age:', cacheStatus.age);
```

### Force Refresh:

```typescript
// Clear cache and reload
await portfolioService.refresh();
```

### Add Refresh Button:

```tsx
import { portfolioService } from '@/services/portfolioServiceEnhanced';

function RefreshButton() {
  const [loading, setLoading] = useState(false);

  const handleRefresh = async () => {
    setLoading(true);
    try {
      await portfolioService.refresh();
      // Invalidate React Query cache
      queryClient.invalidateQueries();
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button onClick={handleRefresh} disabled={loading}>
      {loading ? 'Refreshing...' : 'Refresh from GitHub'}
    </Button>
  );
}
```

---

## Git History

Your portfolio data history is automatically tracked in Git:

```bash
# View all updates
cd ~/fidelity-portfolio-18884
git log --oneline src/data/portfolio-latest.json

# See what changed
git diff HEAD~1 HEAD src/data/portfolio-latest.json

# Restore previous version
git checkout HEAD~1 src/data/portfolio-latest.json
```

---

## Best Practices

### 1. Use Bundled for Production ✅

Fastest, most reliable, works offline.

### 2. Use GitHub Raw for Development

Get latest data without redeploying.

### 3. Monitor Data Age

Alert users if data is stale:

```tsx
const freshness = portfolioService.getDataFreshness();

{freshness.isStale && (
  <Alert>
    <AlertCircle className="h-4 w-4" />
    <AlertTitle>Data may be outdated</AlertTitle>
    <AlertDescription>
      Last updated {freshness.ageFormatted}
    </AlertDescription>
  </Alert>
)}
```

### 4. Implement Error Boundaries

Handle GitHub API failures gracefully.

### 5. Use Environment Variables

Different configs for dev/prod:

```typescript
// .env.development
VITE_DATA_SOURCE=github-raw

// .env.production
VITE_DATA_SOURCE=local
```

---

## Troubleshooting

### Data not updating?

```bash
# Check if export ran
tail -f ~/grok/logs/export.log

# Check if committed to Git
cd ~/fidelity-portfolio-18884
git log -1 src/data/portfolio-latest.json

# Check if pushed
git status
```

### GitHub rate limit exceeded?

Use GitHub API with token:
```env
VITE_DATA_SOURCE=github-api
VITE_GITHUB_TOKEN=your_token
```

### CORS errors?

Only affects GitHub Raw strategy. Switch to bundled or GitHub API.

### Private repo not accessible?

Make repo public OR use GitHub API with token.

---

## Summary

✅ **Your data is already on GitHub!**

The current setup (bundled) is perfect because:
- Data updates daily at 6 PM
- Pushed to GitHub automatically
- Loveable.ai deploys with fresh data
- No configuration needed

**Want always-fresh data?** Use the enhanced service with GitHub Raw strategy.

**Need help?** See [SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md)
