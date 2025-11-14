#!/bin/bash
# Export portfolio data for Loveable.ai integration
# This script exports the latest portfolio data to JSON/CSV and optionally
# copies it to your Loveable.ai repository for automatic deployment

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
EXPORT_DIR="$PROJECT_ROOT/exports"
LOVEABLE_REPO="${LOVEABLE_REPO_PATH:-$HOME/fidelity-portfolio-18884}"  # Override with env var

# Change to project root directory (critical for portfolio-tracker to work)
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "========================================="
echo "Portfolio Data Export for Loveable.ai"
echo "========================================="
echo ""

# Create exports directory
mkdir -p "$EXPORT_DIR"
echo "📁 Export directory: $EXPORT_DIR"

# Export latest snapshot as JSON
echo "📊 Exporting latest portfolio data to JSON..."
if portfolio-tracker export "$EXPORT_DIR/portfolio-latest.json" --format json; then
    echo -e "${GREEN}✓${NC} JSON export complete"
else
    echo -e "${RED}✗${NC} JSON export failed"
    exit 1
fi

# Also export CSV for reference
echo "📊 Exporting latest portfolio data to CSV..."
if portfolio-tracker export "$EXPORT_DIR/portfolio-latest.csv" --format csv; then
    echo -e "${GREEN}✓${NC} CSV export complete"
else
    echo -e "${YELLOW}⚠${NC} CSV export failed (continuing...)"
fi

# Export historical data (last 90 days)
echo "📈 Exporting historical data (90 days)..."
if portfolio-tracker export "$EXPORT_DIR/portfolio-history.json" --format json --days 90; then
    echo -e "${GREEN}✓${NC} Historical export complete"
else
    echo -e "${YELLOW}⚠${NC} Historical export failed (continuing...)"
fi

# Display file info
echo ""
echo "📋 Export Summary:"
if [ -f "$EXPORT_DIR/portfolio-latest.json" ]; then
    SIZE=$(du -h "$EXPORT_DIR/portfolio-latest.json" | cut -f1)
    TIMESTAMP=$(date -r "$EXPORT_DIR/portfolio-latest.json" "+%Y-%m-%d %H:%M:%S")
    echo "  - portfolio-latest.json: $SIZE (modified: $TIMESTAMP)"
fi

# Check if Loveable repo exists
if [ -d "$LOVEABLE_REPO" ]; then
    echo ""
    echo "🔗 Copying to Loveable.ai repository..."
    echo "  Location: $LOVEABLE_REPO"

    # Create data directory in Loveable repo
    mkdir -p "$LOVEABLE_REPO/data"

    # Copy JSON file
    cp "$EXPORT_DIR/portfolio-latest.json" "$LOVEABLE_REPO/data/portfolio-latest.json"
    echo -e "${GREEN}✓${NC} Copied portfolio-latest.json"

    # Optionally copy CSV
    if [ -f "$EXPORT_DIR/portfolio-latest.csv" ]; then
        cp "$EXPORT_DIR/portfolio-latest.csv" "$LOVEABLE_REPO/data/portfolio-latest.csv"
        echo -e "${GREEN}✓${NC} Copied portfolio-latest.csv"
    fi

    # Check if we should commit and push
    if [ "${AUTO_COMMIT:-true}" = "true" ]; then
        echo ""
        echo "📤 Committing and pushing to Git..."

        cd "$LOVEABLE_REPO"

        # Check if there are changes
        if git diff --quiet data/portfolio-latest.json 2>/dev/null; then
            echo -e "${YELLOW}⚠${NC} No changes detected, skipping commit"
        else
            # Configure git if needed
            if [ -z "$(git config user.email)" ]; then
                git config user.email "portfolio-tracker@local"
                git config user.name "Portfolio Tracker"
            fi

            # Add, commit, and push
            git add data/portfolio-latest.json data/portfolio-latest.csv 2>/dev/null || true

            COMMIT_MSG="Update portfolio data $(date '+%Y-%m-%d %H:%M')"
            if git commit -m "$COMMIT_MSG"; then
                echo -e "${GREEN}✓${NC} Changes committed: $COMMIT_MSG"

                if git push origin main 2>/dev/null || git push origin master 2>/dev/null; then
                    echo -e "${GREEN}✓${NC} Pushed to remote repository"
                else
                    echo -e "${RED}✗${NC} Failed to push (check remote configuration)"
                fi
            else
                echo -e "${YELLOW}⚠${NC} Commit failed (may be nothing to commit)"
            fi
        fi

        cd "$PROJECT_ROOT"
    else
        echo ""
        echo "ℹ️  Auto-commit disabled (set AUTO_COMMIT=true to enable)"
    fi

    echo ""
    echo -e "${GREEN}✅ Data exported and synced to Loveable.ai repo${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  Loveable.ai repository not found${NC}"
    echo "  Expected location: $LOVEABLE_REPO"
    echo "  Set LOVEABLE_REPO_PATH environment variable to specify location"
    echo ""
    echo "  Example:"
    echo "    export LOVEABLE_REPO_PATH=/path/to/fidelity-portfolio-18884"
    echo "    $0"
    echo ""
    echo "✅ Data exported to: $EXPORT_DIR"
fi

echo ""
echo "========================================="
echo "Export complete!"
echo "========================================="
