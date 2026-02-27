#!/bin/bash
# deploy.sh - Quick deployment script for updates

set -e
cd "$(dirname "$0")"

echo "🚀 Deploying to HuggingFace Spaces..."

# Add changes
git add .

# Commit with timestamp
git commit -m "Update: $(date '+%Y-%m-%d %H:%M:%S')" --allow-empty

# Push to HuggingFace (use 'space' remote - update if you use different name)
git push space main

echo "✅ Deployed! Check build status at:"
echo "   https://huggingface.co/spaces/YOUR_USERNAME/auditshield-live"
