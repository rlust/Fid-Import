# Quick Setup Guide - Get Your Loveable.ai App Running

## Current Status

✅ **Fidelity Tracker** - Running and collecting data
✅ **Export Scripts** - Created and tested  
✅ **Integration Code** - Complete and committed to GitHub
❌ **Loveable.ai Repo** - Needs to be cloned
❌ **Data Export** - Needs to be copied to Loveable repo

---

## Step 1: Clone Your Loveable.ai Repository

```bash
cd ~
git clone https://github.com/rlust/fidelity-portfolio-18884.git
cd fidelity-portfolio-18884
```

**If the repository doesn't exist yet:**

You need to create it on Loveable.ai first:
1. Go to https://loveable.ai
2. Create a new project named "fidelity-portfolio-18884"
3. Loveable.ai will create a GitHub repository for you
4. Then clone it with the command above

---

## Step 2: Run the Export Script

Once the repository is cloned:

```bash
cd ~/grok
LOVEABLE_REPO_PATH=~/fidelity-portfolio-18884 ./scripts/export_for_loveable.sh
```

This will:
- ✅ Export your portfolio data (232KB, 167 holdings, $2.16M)
- ✅ Copy to `~/fidelity-portfolio-18884/src/data/portfolio-latest.json`
- ✅ Auto-commit to Git
- ✅ Auto-push to GitHub

---

## Step 3: Copy Integration Files

```bash
cd ~/grok/loveable-integration
./quickstart.sh
```

This automated script will:
- ✅ Copy all React components
- ✅ Copy TypeScript services and hooks
- ✅ Copy dashboard page
- ✅ Install dependencies
- ✅ Setup automated daily exports

---

## Step 4: Test Locally

```bash
cd ~/fidelity-portfolio-18884
npm install
npm run dev
```

Open http://localhost:5173 (or the URL shown)

You should see:
- Portfolio summary cards
- Top 10 holdings chart
- Sector allocation
- Complete holdings table

---

## Step 5: Deploy to Loveable.ai

```bash
cd ~/fidelity-portfolio-18884
git push origin main
```

Loveable.ai will automatically:
- ✅ Detect the push
- ✅ Build your React app
- ✅ Deploy to production
- ✅ Make it live at your Loveable.ai URL

---

## Alternative: Manual Export (Without Cloning)

If you want to get the data ready before cloning:

```bash
# Create a temporary data package
cd ~/grok
mkdir -p loveable-data-package/src/data
cp exports/portfolio-latest.json loveable-data-package/src/data/

# Create a zip file
tar -czf loveable-data-package.tar.gz loveable-data-package/

echo "✅ Data package created: loveable-data-package.tar.gz"
echo "Copy this to your Loveable.ai project's src/data/ directory"
```

---

## What Data is Available Right Now

Your exported data (as of Nov 12, 15:01):

```json
{
  "id": 3,
  "timestamp": "2025-11-12T12:47:47.308970",
  "total_value": 2160622.72,
  "holdings": [
    // 167 holdings with full details
  ]
}
```

**Files ready:**
- ✅ `exports/portfolio-latest.json` (232KB)
- ✅ `exports/portfolio-latest.csv` (68KB)
- ✅ `exports/portfolio-history.json` (90-day history)

---

## Automated Daily Updates

Once setup is complete, the system will automatically:

```
Daily at 6:00 PM:
1. Portfolio data syncs from Fidelity
2. Export script runs
3. Data copied to Loveable.ai repo
4. Git commit and push
5. Loveable.ai auto-deploys
6. Users see fresh data
```

**Setup automation:**

```bash
# Run quickstart script (it will offer to setup cron/LaunchAgent)
cd ~/grok/loveable-integration
./quickstart.sh

# Or manually add to crontab:
crontab -e
# Add: 0 18 * * * LOVEABLE_REPO_PATH=/Users/randylust/fidelity-portfolio-18884 ./scripts/export_for_loveable.sh >> logs/export.log 2>&1
```

---

## Troubleshooting

### Repository doesn't exist?

Create it on Loveable.ai first:
- Go to https://loveable.ai
- Create new project
- It will create GitHub repo automatically

### Can't push to GitHub?

Check authentication:
```bash
cd ~/fidelity-portfolio-18884
git remote -v
git config user.name
git config user.email
```

### Data file not found?

Run export manually:
```bash
cd ~/grok
./scripts/export_for_loveable.sh
```

### Dependencies missing?

```bash
cd ~/fidelity-portfolio-18884
npm install @tanstack/react-query lucide-react
```

---

## Quick Test Without Loveable.ai

Want to test the dashboard locally first?

```bash
# Create a test React app
npx create-vite@latest portfolio-test --template react-ts
cd portfolio-test

# Copy the data
mkdir -p src/data
cp ~/grok/exports/portfolio-latest.json src/data/

# Copy integration files
cp -r ~/grok/loveable-integration/services src/
cp -r ~/grok/loveable-integration/hooks src/
cp -r ~/grok/loveable-integration/components src/
cp ~/grok/loveable-integration/pages/Dashboard.tsx src/

# Install dependencies
npm install @tanstack/react-query lucide-react

# Update App.tsx to use Dashboard
# Then run
npm run dev
```

---

## Summary

**To get your Loveable.ai app running:**

1. **Clone Loveable.ai repository:**
   ```bash
   git clone https://github.com/rlust/fidelity-portfolio-18884.git
   ```

2. **Run export script:**
   ```bash
   cd ~/grok
   LOVEABLE_REPO_PATH=~/fidelity-portfolio-18884 ./scripts/export_for_loveable.sh
   ```

3. **Run quickstart:**
   ```bash
   cd ~/grok/loveable-integration
   ./quickstart.sh
   ```

4. **Deploy:**
   ```bash
   cd ~/fidelity-portfolio-18884
   git push origin main
   ```

**Your data is ready - just needs the Loveable.ai repo to receive it!**
