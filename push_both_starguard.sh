#!/usr/bin/env bash
# Push both StarGuard repos to GitHub using token
# Usage: ./push_both_starguard.sh YOUR_GITHUB_TOKEN
# Token is used inline only - never stored

set -e
TOKEN="${1:?Usage: ./push_both_starguard.sh YOUR_GITHUB_TOKEN}"
BASEDIR="$(cd "$(dirname "$0")" && pwd)"
ORG="reichert-science-intelligence"

push_repo() {
    local name="$1"
    local path="$BASEDIR/$name"
    if [[ ! -d "$path" ]]; then
        echo "[SKIP] $name - not found. Run reorganize script first."
        return
    fi
    cd "$path"
    if [[ -n "$(git status --porcelain)" ]]; then
        echo "[i] Committing changes in $name..."
        git add -A
        git commit -m "Organize repository: Move files to Artifacts folder for cleaner root view" || true
    fi
    echo "[i] Pushing $name..."
    if git push "https://${TOKEN}@github.com/${ORG}/${name}.git" main; then
        echo "[OK] $name pushed successfully!"
    else
        echo "[X] $name push failed"
    fi
}

echo ""
echo "========================================"
echo "  StarGuard Push - Both Repositories"
echo "========================================"
echo ""

push_repo "starguard-desktop"
push_repo "starguard-mobile"

echo ""
echo "========================================"
echo "  Push complete! Verify at:"
echo "  https://github.com/${ORG}/starguard-desktop"
echo "  https://github.com/${ORG}/starguard-mobile"
echo "========================================"
echo ""
echo "[i] Token was used inline only - not stored in config."
