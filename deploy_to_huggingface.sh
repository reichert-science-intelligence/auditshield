#!/bin/bash
# deploy_to_huggingface.sh - Deploy AuditShield-Live to HuggingFace Spaces

set -e

# Change to script directory (auditshield folder)
cd "$(dirname "$0")"

echo "🚀 Deploying AuditShield-Live to HuggingFace Spaces"
echo "=================================================="

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit - AuditShield-Live complete system"
fi

# Prompt for HuggingFace username and space name
read -p "Enter your HuggingFace username: " HF_USERNAME
read -p "Enter your Space name (default: auditshield-live): " SPACE_NAME
SPACE_NAME=${SPACE_NAME:-auditshield-live}

# Add HuggingFace remote
echo "🔗 Adding HuggingFace remote..."
git remote remove hf 2>/dev/null || true
git remote add hf "https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"

# Create deployment branch
echo "🌿 Creating deployment branch..."
git checkout -b hf-deploy 2>/dev/null || git checkout hf-deploy

# Ensure all required files are present
echo "📋 Checking required files..."
required_files=(
    "Dockerfile"
    "requirements.txt"
    "app_complete.py"
    "app.py"
    "init_complete_system.py"
    "database.py"
    "README.md"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ All required files present"

# Add and commit all changes
echo "📝 Committing changes..."
git add .
git commit -m "Deploy to HuggingFace Spaces" --allow-empty

# Push to HuggingFace
echo "🚀 Pushing to HuggingFace..."
echo ""
echo "⚠️  You will be prompted for your HuggingFace credentials"
echo "    Username: $HF_USERNAME"
echo "    Password: Your HuggingFace Access Token (not your password!)"
echo ""
echo "    Get token at: https://huggingface.co/settings/tokens"
echo ""
read -p "Press Enter to continue..."

git push hf hf-deploy:main

echo ""
echo "============================================================"
echo "✅ Deployment initiated!"
echo "============================================================"
echo ""
echo "🔗 Your Space: https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME"
echo ""
echo "⏱️  Build will take 5-10 minutes"
echo "    - Docker image build: ~5 min"
echo "    - App initialization: ~1 min"
echo ""
echo "📊 Monitor build progress at:"
echo "    https://huggingface.co/spaces/$HF_USERNAME/$SPACE_NAME/settings"
echo ""
echo "🔐 Don't forget to add ANTHROPIC_API_KEY in Space settings!"
echo ""
