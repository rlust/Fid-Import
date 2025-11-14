#!/bin/bash
# Complete Automation: Sync from Fidelity + Export to Loveable.ai
# Runs daily to get fresh portfolio data and deploy to dashboard

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOVEABLE_REPO="${LOVEABLE_REPO_PATH:-$HOME/fidelity-portfolio-18884}"

# Change to project root
cd "$PROJECT_ROOT"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Complete Portfolio Update Automation${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Step 1: Sync from Fidelity
echo -e "${BLUE}📡 Step 1: Syncing portfolio from Fidelity...${NC}"
if portfolio-tracker sync; then
    echo -e "${GREEN}✓${NC} Portfolio sync complete"
else
    echo -e "${YELLOW}⚠${NC} Sync failed or no new data"
fi

echo ""

# Step 2: Export to Loveable.ai
echo -e "${BLUE}📦 Step 2: Exporting to Loveable.ai repository...${NC}"
if LOVEABLE_REPO_PATH="$LOVEABLE_REPO" AUTO_COMMIT=true "$SCRIPT_DIR/export_for_loveable.sh"; then
    echo -e "${GREEN}✓${NC} Export and deployment complete"
else
    echo -e "${YELLOW}⚠${NC} Export failed"
    exit 1
fi

echo ""
echo -e "${GREEN}=========================================${NC}"
echo -e "${GREEN}✅ Complete! Portfolio updated and deployed${NC}"
echo -e "${GREEN}=========================================${NC}"
echo ""
echo "Your Loveable.ai dashboard will update in 1-2 minutes"
echo ""
