#!/bin/bash
# ═══════════════════════════════════════════════════════════════════
# Sovereign Sanctuary Elite - GitHub Push Script
# ═══════════════════════════════════════════════════════════════════
#
# This script pushes the IDE handover pack to your GitHub repository.
#
# Prerequisites:
#   1. GitHub CLI (gh) installed and authenticated
#   2. Git configured with your credentials
#
# Usage:
#   ./github_push.sh [repo_name]
#
# Example:
#   ./github_push.sh sovereign-sanctuary-elite
#
# ═══════════════════════════════════════════════════════════════════

set -e

# Configuration
REPO_NAME="${1:-sovereign-sanctuary-elite}"
REPO_VISIBILITY="private"
BRANCH="main"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  SOVEREIGN SANCTUARY ELITE - GITHUB PUSH${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) not installed${NC}"
    echo "Install: https://cli.github.com/"
    exit 1
fi

if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: Git not installed${NC}"
    exit 1
fi

# Check gh auth status
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI not authenticated${NC}"
    echo "Run: gh auth login"
    exit 1
fi

echo -e "${GREEN}  ✓ GitHub CLI authenticated${NC}"
echo -e "${GREEN}  ✓ Git available${NC}"
echo ""

# Get current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACK_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${YELLOW}Pack directory: ${PACK_DIR}${NC}"
echo ""

# Check if we're in a git repo
cd "$PACK_DIR"

if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Initializing Git repository...${NC}"
    git init
    git config user.email "architect@sovereign.elite"
    git config user.name "Architect"
fi

# Ensure we're on main branch
git checkout -B "$BRANCH" 2>/dev/null || git checkout "$BRANCH"

# Stage all files
echo -e "${YELLOW}Staging files...${NC}"
git add -A

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo -e "${GREEN}No new changes to commit${NC}"
else
    echo -e "${YELLOW}Committing changes...${NC}"
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    git commit -m "Update: Sovereign Sanctuary Elite v2.0.0

Timestamp: ${TIMESTAMP}
- IDE Handover Pack complete
- Safety tools and protocols
- Legal search index
- PDCA cycles documented"
fi

# Check if remote exists
if git remote get-url origin &> /dev/null; then
    echo -e "${GREEN}Remote 'origin' already configured${NC}"
    REMOTE_URL=$(git remote get-url origin)
    echo -e "  URL: ${REMOTE_URL}"
else
    # Create repository
    echo -e "${YELLOW}Creating GitHub repository: ${REPO_NAME}${NC}"
    
    if gh repo view "$REPO_NAME" &> /dev/null; then
        echo -e "${GREEN}Repository already exists${NC}"
    else
        gh repo create "$REPO_NAME" \
            --"$REPO_VISIBILITY" \
            --description "Sovereign Sanctuary Elite - Zero-drift automation with cryptographic traceability" \
            --source=. \
            --remote=origin
        echo -e "${GREEN}  ✓ Repository created${NC}"
    fi
fi

# Push to GitHub
echo ""
echo -e "${YELLOW}Pushing to GitHub...${NC}"
git push -u origin "$BRANCH" --force

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  PUSH COMPLETE${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════${NC}"
echo ""

# Get repo URL
REPO_URL=$(gh repo view --json url -q '.url' 2>/dev/null || echo "")
if [ -n "$REPO_URL" ]; then
    echo -e "  Repository: ${CYAN}${REPO_URL}${NC}"
fi

echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Verify repository at GitHub"
echo "  2. Add collaborators if needed"
echo "  3. Enable branch protection rules"
echo ""
