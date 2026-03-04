#!/usr/bin/env pwsh
# Push both StarGuard repos to GitHub using token
# Usage: .\push_both_starguard.ps1 YOUR_GITHUB_TOKEN
# Token is used inline only - never stored

param([string]$Token)
if (-not $Token) { $Token = $env:GITHUB_TOKEN }
if (-not $Token) { $Token = $env:AUDITSHIELD_TOKEN }
if ([string]::IsNullOrWhiteSpace($Token)) {
    Write-Host "Usage: .\push_both_starguard.ps1 YOUR_GITHUB_TOKEN" -ForegroundColor Yellow
    Write-Host "  Or set env: `$env:GITHUB_TOKEN = 'your-token'" -ForegroundColor DarkGray
    exit 1
}

$ErrorActionPreference = "Stop"
$BaseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Org = "reichert-science-intelligence"

function Push-Repo {
    param([string]$RepoName, [string]$RepoPath)
    if (-not (Test-Path $RepoPath)) {
        Write-Host "[SKIP] $RepoName - not found. Run reorganize script first." -ForegroundColor Yellow
        return
    }
    Push-Location $RepoPath
    try {
        $status = & git status --porcelain 2>$null
        if ($status) {
            Write-Host "[i] Committing changes in $RepoName..." -ForegroundColor DarkGray
            & git add -A
            & git commit -m "Organize repository: Move files to Artifacts folder for cleaner root view" 2>$null
        }
        $remote = "https://${Token}@github.com/${Org}/${RepoName}.git"
        Write-Host "[i] Pushing $RepoName..." -ForegroundColor Cyan
        & git push $remote main 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] $RepoName pushed successfully!" -ForegroundColor Green
        } else {
            Write-Host "[X] $RepoName push failed" -ForegroundColor Red
        }
    } finally {
        Pop-Location
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  StarGuard Push - Both Repositories" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Push-Repo -RepoName "starguard-desktop" -RepoPath (Join-Path $BaseDir "starguard-desktop")
Push-Repo -RepoName "starguard-mobile" -RepoPath (Join-Path $BaseDir "starguard-mobile")

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Push complete! Verify at:" -ForegroundColor Green
Write-Host "  https://github.com/$Org/starguard-desktop" -ForegroundColor White
Write-Host "  https://github.com/$Org/starguard-mobile" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "[i] Token was used inline only - not stored in config." -ForegroundColor DarkGray
