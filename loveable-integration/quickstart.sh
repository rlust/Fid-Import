#!/bin/bash
# Quick Start Script for Loveable.ai Integration
# This script automates the setup process

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}Loveable.ai Integration Quick Start${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Configuration
GROK_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." && pwd )"
LOVEABLE_REPO="${LOVEABLE_REPO_PATH:-$HOME/fidelity-portfolio-18884}"

echo -e "${BLUE}Configuration:${NC}"
echo "  Grok directory: $GROK_DIR"
echo "  Loveable repo: $LOVEABLE_REPO"
echo ""

# Check if Loveable repo exists
if [ ! -d "$LOVEABLE_REPO" ]; then
    echo -e "${YELLOW}⚠️  Loveable.ai repository not found at: $LOVEABLE_REPO${NC}"
    echo ""
    read -p "Enter the path to your Loveable.ai repository: " USER_REPO
    LOVEABLE_REPO="$USER_REPO"

    if [ ! -d "$LOVEABLE_REPO" ]; then
        echo -e "${RED}✗ Directory not found. Exiting.${NC}"
        exit 1
    fi
fi

echo -e "${GREEN}✓${NC} Found Loveable.ai repository"
echo ""

# Step 1: Export portfolio data
echo -e "${BLUE}Step 1: Exporting portfolio data...${NC}"
cd "$GROK_DIR"
LOVEABLE_REPO_PATH="$LOVEABLE_REPO" ./scripts/export_for_loveable.sh
echo ""

# Step 2: Create directories
echo -e "${BLUE}Step 2: Creating directories in Loveable.ai project...${NC}"
mkdir -p "$LOVEABLE_REPO/src/data"
mkdir -p "$LOVEABLE_REPO/src/services"
mkdir -p "$LOVEABLE_REPO/src/hooks"
mkdir -p "$LOVEABLE_REPO/src/components/portfolio"
mkdir -p "$LOVEABLE_REPO/src/pages"
echo -e "${GREEN}✓${NC} Directories created"
echo ""

# Step 3: Copy integration files
echo -e "${BLUE}Step 3: Copying integration files...${NC}"

# Service layer
if [ ! -f "$LOVEABLE_REPO/src/services/portfolioService.ts" ]; then
    cp "$GROK_DIR/loveable-integration/services/portfolioService.ts" "$LOVEABLE_REPO/src/services/"
    echo -e "${GREEN}✓${NC} Copied portfolioService.ts"
else
    echo -e "${YELLOW}⚠${NC}  portfolioService.ts already exists, skipping"
fi

# Hooks
if [ ! -f "$LOVEABLE_REPO/src/hooks/usePortfolio.ts" ]; then
    cp "$GROK_DIR/loveable-integration/hooks/usePortfolio.ts" "$LOVEABLE_REPO/src/hooks/"
    echo -e "${GREEN}✓${NC} Copied usePortfolio.ts"
else
    echo -e "${YELLOW}⚠${NC}  usePortfolio.ts already exists, skipping"
fi

# Components
for component in PortfolioSummary HoldingsTable PortfolioChart SectorAllocation; do
    if [ ! -f "$LOVEABLE_REPO/src/components/portfolio/${component}.tsx" ]; then
        cp "$GROK_DIR/loveable-integration/components/${component}.tsx" "$LOVEABLE_REPO/src/components/portfolio/"
        echo -e "${GREEN}✓${NC} Copied ${component}.tsx"
    else
        echo -e "${YELLOW}⚠${NC}  ${component}.tsx already exists, skipping"
    fi
done

# Dashboard page
if [ ! -f "$LOVEABLE_REPO/src/pages/Dashboard.tsx" ]; then
    cp "$GROK_DIR/loveable-integration/pages/Dashboard.tsx" "$LOVEABLE_REPO/src/pages/"
    echo -e "${GREEN}✓${NC} Copied Dashboard.tsx"
else
    echo -e "${YELLOW}⚠${NC}  Dashboard.tsx already exists, skipping"
fi

echo ""

# Step 4: Check dependencies
echo -e "${BLUE}Step 4: Checking dependencies...${NC}"

cd "$LOVEABLE_REPO"

if [ -f "package.json" ]; then
    echo "Checking for required packages..."

    MISSING_DEPS=()

    if ! grep -q "@tanstack/react-query" package.json; then
        MISSING_DEPS+=("@tanstack/react-query")
    fi

    if ! grep -q "lucide-react" package.json; then
        MISSING_DEPS+=("lucide-react")
    fi

    if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
        echo -e "${YELLOW}⚠${NC}  Missing dependencies: ${MISSING_DEPS[*]}"
        echo ""
        read -p "Install missing dependencies? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            npm install "${MISSING_DEPS[@]}"
            echo -e "${GREEN}✓${NC} Dependencies installed"
        else
            echo -e "${YELLOW}⚠${NC}  Skipping dependency installation"
            echo "  Run manually: npm install ${MISSING_DEPS[*]}"
        fi
    else
        echo -e "${GREEN}✓${NC} All required dependencies present"
    fi
else
    echo -e "${YELLOW}⚠${NC}  No package.json found"
fi

echo ""

# Step 5: Setup automated exports
echo -e "${BLUE}Step 5: Setup automated data exports${NC}"
echo ""
echo "Would you like to setup automated daily exports?"
echo "  1) Cron job (simple)"
echo "  2) LaunchAgent (recommended for macOS)"
echo "  3) Skip (setup manually later)"
echo ""
read -p "Choose option (1-3): " -n 1 -r
echo

case $REPLY in
    1)
        echo ""
        echo "Adding cron job..."
        CRON_CMD="0 18 * * * cd $GROK_DIR && LOVEABLE_REPO_PATH=$LOVEABLE_REPO AUTO_COMMIT=true ./scripts/export_for_loveable.sh >> $GROK_DIR/logs/export.log 2>&1"

        # Check if already exists
        if crontab -l 2>/dev/null | grep -q "export_for_loveable.sh"; then
            echo -e "${YELLOW}⚠${NC}  Cron job already exists"
        else
            (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
            echo -e "${GREEN}✓${NC} Cron job added (runs daily at 6 PM)"
        fi
        ;;
    2)
        echo ""
        echo "Creating LaunchAgent..."

        PLIST_PATH="$HOME/Library/LaunchAgents/com.portfolio.export.plist"

        cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.portfolio.export</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$GROK_DIR/scripts/export_for_loveable.sh</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>LOVEABLE_REPO_PATH</key>
        <string>$LOVEABLE_REPO</string>
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
    <string>$GROK_DIR/logs/export.log</string>
    <key>StandardErrorPath</key>
    <string>$GROK_DIR/logs/export-error.log</string>
</dict>
</plist>
EOF

        launchctl load "$PLIST_PATH" 2>/dev/null || true
        echo -e "${GREEN}✓${NC} LaunchAgent created and loaded (runs daily at 6 PM)"
        echo "  Plist: $PLIST_PATH"
        ;;
    3)
        echo -e "${YELLOW}⚠${NC}  Skipping automated setup"
        echo "  See SETUP_INSTRUCTIONS.md for manual setup"
        ;;
    *)
        echo -e "${YELLOW}⚠${NC}  Invalid option, skipping"
        ;;
esac

echo ""

# Summary
echo -e "${BLUE}=========================================${NC}"
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Test the integration:"
echo "   cd $LOVEABLE_REPO"
echo "   npm run dev"
echo ""
echo "2. View the documentation:"
echo "   cat $GROK_DIR/loveable-integration/SETUP_INSTRUCTIONS.md"
echo ""
echo "3. Check export logs:"
echo "   tail -f $GROK_DIR/logs/export.log"
echo ""
echo "4. Deploy to Loveable.ai:"
echo "   cd $LOVEABLE_REPO"
echo "   git push origin main"
echo ""
echo -e "${GREEN}Data will be exported automatically at 6 PM daily${NC}"
echo ""
