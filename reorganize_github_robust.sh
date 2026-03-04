#!/bin/bash
# AuditShield Live - Repository Reorganization Script (Bash)
# Moves 18 files to Artifacts/ folder, keeps README.md in root
# Author: Robert Reichert
# Date: February 25, 2026
# Usage: ./reorganize_github_robust.sh

set -e

REPO_URL="https://github.com/reichert-science-intelligence/auditshield-live.git"
REPO_NAME="auditshield-live"

# Files to move (18 total)
FILES_TO_MOVE=(
    "LICENSE"
    ".gitignore"
    "requirements.txt"
    "GITHUB_UPLOAD_GUIDE.md"
    "PHASE_1_COMPLETE.md"
    "PHASE_2_COMPLETE.md"
    "PHASE_3_COMPLETE.md"
    "PHASE_4_COMPLETE.md"
    "DEPLOYMENT_GUIDE.md"
    "synthetic_chart_generator.py"
    "ncqa_specification_builder.py"
    "validation_engine.py"
    "layer1_document_intelligence.py"
    "layer3_self_correction.py"
    "compound_pipeline.py"
    "agentic_rag_coordinator.py"
    "AuditShieldMobile.jsx"
    "AuditShieldLive_Demo.html"
)

info()  { echo "ℹ️  $*"; }
success() { echo "✅ $*"; }
skip() { echo "⏭️  $*"; }
fail() { echo "❌ $*"; exit 1; }

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║  AuditShield Live - Repository Reorganization Script      ║"
echo "║  Moving 18 files to Artifacts/ folder                     ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Detect working directory - are we in auditshield-live or have it as subdir?
REPO_ROOT=""
if [ -d ".git" ] && git remote get-url origin 2>/dev/null | grep -q "auditshield-live"; then
    REPO_ROOT="$(pwd)"
    info "Using existing repository at: $REPO_ROOT"
elif [ -d "auditshield-live/.git" ]; then
    REPO_ROOT="$(pwd)/auditshield-live"
    info "Found auditshield-live in current directory"
fi

# Clone if needed
if [ -z "$REPO_ROOT" ]; then
    info "Cloning repository..."
    if ! git clone "$REPO_URL"; then
        fail "Failed to clone repository"
    fi
    cd "$REPO_NAME"
    REPO_ROOT="$(pwd)"
    success "Repository cloned successfully"
else
    cd "$REPO_ROOT"
fi

# Pull latest
info "Pulling latest changes from GitHub..."
git pull origin main 2>/dev/null || true

# Check Git credentials
info "Checking Git credentials..."
GIT_NAME=$(git config user.name 2>/dev/null || true)
GIT_EMAIL=$(git config user.email 2>/dev/null || true)
CREDENTIALS_WERE_SET=false

if [ -z "$GIT_NAME" ]; then
    echo "  ⚠️  Git user.name not set. Setting it now..."
    read -p "  Enter your name (e.g., Robert Reichert): " GIT_NAME
    if [ -z "$GIT_NAME" ]; then
        fail "Git user.name is required for commits. Run: git config --global user.name 'Your Name'"
    fi
    git config --global user.name "$GIT_NAME"
    CREDENTIALS_WERE_SET=true
fi
if [ -z "$GIT_EMAIL" ]; then
    echo "  ⚠️  Git user.email not set. Setting it now..."
    read -p "  Enter your email (e.g., you@example.com): " GIT_EMAIL
    if [ -z "$GIT_EMAIL" ]; then
        fail "Git user.email is required for commits. Run: git config --global user.email 'you@example.com'"
    fi
    git config --global user.email "$GIT_EMAIL"
    CREDENTIALS_WERE_SET=true
fi
if [ "$CREDENTIALS_WERE_SET" = true ]; then
    success "Git credentials set successfully"
elif [ -n "$GIT_NAME" ] && [ -n "$GIT_EMAIL" ]; then
    success "Git credentials OK ($GIT_NAME <$GIT_EMAIL>)"
fi

# Create Artifacts folder
if [ ! -d "Artifacts" ]; then
    mkdir -p Artifacts
    success "Artifacts/ folder created"
else
    info "Artifacts/ folder already exists"
fi

# Move files
info "Moving files to Artifacts/..."
MOVED=0
SKIPPED=0
FAILED=0

for FILE in "${FILES_TO_MOVE[@]}"; do
    if [ -f "Artifacts/$FILE" ]; then
        skip "Already in Artifacts: $FILE"
        ((SKIPPED++)) || true
        continue
    fi

    if [ ! -e "$FILE" ]; then
        skip "Not found (skipping): $FILE"
        ((SKIPPED++)) || true
        continue
    fi

    if git mv "$FILE" "Artifacts/$FILE" 2>/dev/null; then
        echo "  ✓ Moved: $FILE"
        ((MOVED++)) || true
    else
        # Fallback: mv + git add
        if mv "$FILE" "Artifacts/$FILE" 2>/dev/null; then
            git add "Artifacts/$FILE"
            git add -u "$FILE" 2>/dev/null || true
            echo "  ✓ Moved: $FILE"
            ((MOVED++)) || true
        else
            echo "  ✗ Failed: $FILE"
            ((FAILED++)) || true
        fi
    fi
done

# Summary
echo ""
info "Summary:"
echo "  • Files moved: $MOVED"
echo "  • Files skipped: $SKIPPED"
echo "  • Files failed: $FAILED"
echo ""

# Commit if we moved anything
if [ "$MOVED" -gt 0 ]; then
    info "Committing changes..."
    git add -A
    git status --short
    if git commit -m "Organize repository: Move $MOVED files to Artifacts folder for cleaner root view"; then
        success "Changes committed successfully"
    else
        fail "Commit failed"
    fi
else
    info "No files to move - nothing to commit"
fi

# Push
info "Pushing to GitHub..."
echo ""
echo "  ⚠️  This will require GitHub authentication."
echo "  ℹ️  Options:"
echo "     1. Personal Access Token (recommended)"
echo "     2. SSH key"
echo "     3. GitHub CLI (gh auth login)"
echo ""
read -p "  Press Enter to continue with push, or Ctrl+C to cancel: " _
echo ""
if git push origin main; then
    success "Successfully pushed to GitHub!"
else
    fail "Push failed. Please authenticate with GitHub:
  • Option 1: gh auth login
  • Option 2: Use Personal Access Token as password
  • See QUICK_START for details"
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
success "Repository reorganization complete!"
echo "═══════════════════════════════════════════════════════════"
echo ""
info "View your repository at:"
echo "  🌐 https://github.com/reichert-science-intelligence/auditshield-live"
echo ""
info "New structure:"
echo "  📂 Root: README.md"
echo "  📂 Artifacts/: [18 files]"
echo ""
success "Script completed!"
