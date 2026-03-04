#!/usr/bin/env pwsh
# Repository Reorganization Script v2 (Parameterized)
# Moves files to Artifacts/ folder, keeps only README.md in root
# Based on AuditShield Live success - reusable for any repo
# Author: Robert Reichert
# Date: March 2026
# Usage: .\reorganize_github_robust_v2.ps1 -RepoUrl "..." -RepoName "repo-name"
#    or: Edit config below and run .\reorganize_github_robust_v2.ps1

param(
    [string]$RepoUrl = "https://github.com/reichert-science-intelligence/REPO_NAME.git",
    [string]$RepoName = "REPO_NAME",
    [switch]$MoveAllExceptReadme = $true,
    [array]$FilesToMove = $null,
    [switch]$NoPush = $false
)

$ErrorActionPreference = "Stop"
$NeverMove = @("README.md", ".git", "Artifacts")

function Write-Banner {
    param([string]$Title, [string]$Subtitle)
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "  $Title" -ForegroundColor Cyan
    Write-Host "  $Subtitle" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Info { param($Msg) Write-Host "[i]  $Msg" -ForegroundColor DarkGray }
function Write-Success { param($Msg) Write-Host "[OK] $Msg" -ForegroundColor Green }
function Write-Skip { param($Msg) Write-Host "[-]  $Msg" -ForegroundColor Yellow }
function Write-Fail { param($Msg) Write-Host "[X]  $Msg" -ForegroundColor Red }

Write-Banner -Title "$RepoName - Repository Reorganization" -Subtitle "Moving files to Artifacts/ for cleaner root view"

# Detect working directory
$WorkDir = $PWD.Path
$IsInRepo = $false
$RepoRoot = $null

# Check if we're in the target repo (remote URL contains repo name)
if (Test-Path ".git") {
    try {
        $RemoteUrl = & git remote get-url origin 2>$null
        if ($RemoteUrl -and $RemoteUrl -like "*$RepoName*") {
            $IsInRepo = $true
            $RepoRoot = $WorkDir
            Write-Info "Using existing repository at: $RepoRoot"
        }
    } catch { }
}

# If not in repo, check if repo folder exists in current directory
if (-not $IsInRepo -and (Test-Path "$RepoName\.git")) {
    $IsInRepo = $true
    $RepoRoot = Join-Path $WorkDir $RepoName
    Write-Info "Found $RepoName in current directory"
}

# Clone if needed
if (-not $IsInRepo) {
    Write-Info "Cloning repository..."
    try {
        & git clone $RepoUrl
        if ($LASTEXITCODE -ne 0) { throw "Clone failed" }
        Set-Location $RepoName
        $RepoRoot = (Get-Location).Path
        Write-Success "Repository cloned successfully"
    } catch {
        Write-Fail "Failed to clone: $_"
        exit 1
    }
} else {
    Set-Location $RepoRoot
}

# Pull latest
Write-Info "Pulling latest changes from GitHub..."
try { & git pull origin main 2>$null } catch { }

# Check Git credentials
Write-Info "Checking Git credentials..."
$GitName = & git config user.name 2>$null
$GitEmail = & git config user.email 2>$null
$CredentialsWereSet = $false

if ([string]::IsNullOrWhiteSpace($GitName)) {
    Write-Host "  [!] Git user.name not set. Setting it now..." -ForegroundColor Yellow
    $GitName = Read-Host "  Enter your name (e.g., Robert Reichert)"
    if ([string]::IsNullOrWhiteSpace($GitName)) {
        Write-Fail "Git user.name is required for commits."
        exit 1
    }
    & git config --global user.name $GitName
    $CredentialsWereSet = $true
}
if ([string]::IsNullOrWhiteSpace($GitEmail)) {
    Write-Host "  [!] Git user.email not set. Setting it now..." -ForegroundColor Yellow
    $GitEmail = Read-Host "  Enter your email"
    if ([string]::IsNullOrWhiteSpace($GitEmail)) {
        Write-Fail "Git user.email is required for commits."
        exit 1
    }
    & git config --global user.email $GitEmail
    $CredentialsWereSet = $true
}
if ($CredentialsWereSet) {
    Write-Success "Git credentials set successfully"
} elseif ($GitName -and $GitEmail) {
    Write-Success "Git credentials OK ($GitName <$GitEmail>)"
}

# Build file list: explicit or dynamic
if ($MoveAllExceptReadme -and ((-not $FilesToMove) -or $FilesToMove.Count -eq 0)) {
    Write-Info "Discovering files to move (all except README.md)..."
    $RootItems = Get-ChildItem -Path $RepoRoot -Force -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notin $NeverMove }
    $FilesToMove = @($RootItems | ForEach-Object { $_.Name })
    Write-Info "Found $($FilesToMove.Count) items to move"
} elseif (-not $FilesToMove -or $FilesToMove.Count -eq 0) {
    Write-Fail "No files to move. Set either FilesToMove or MoveAllExceptReadme."
    exit 1
}

# Create Artifacts folder
$ArtifactsPath = Join-Path $RepoRoot "Artifacts"
if (-not (Test-Path $ArtifactsPath)) {
    New-Item -ItemType Directory -Path $ArtifactsPath | Out-Null
    Write-Success "Artifacts/ folder created"
} else {
    Write-Info "Artifacts/ folder already exists"
}

# Move files
Write-Info "Moving $($FilesToMove.Count) items to Artifacts/..."
$Moved = 0
$Skipped = 0
$Failed = 0

foreach ($File in $FilesToMove) {
    if ([string]::IsNullOrWhiteSpace($File) -or $File -in $NeverMove) { continue }

    $SrcPath = Join-Path $RepoRoot $File
    $DstPath = Join-Path $ArtifactsPath $File

    if (Test-Path $DstPath) {
        Write-Skip "Already in Artifacts: $File"
        $Skipped++
        continue
    }

    if (-not (Test-Path $SrcPath)) {
        Write-Skip "Not found (skipping): $File"
        $Skipped++
        continue
    }

    try {
        $MovedResult = & git mv $File "Artifacts/$File" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  + Moved: $File" -ForegroundColor Green
            $Moved++
        } else {
            Move-Item $SrcPath $DstPath -Force -ErrorAction Stop
            & git add "Artifacts/$File"
            & git add "-u" $File 2>$null
            Write-Host "  + Moved: $File" -ForegroundColor Green
            $Moved++
        }
    } catch {
        Write-Fail "Failed: $File - $_"
        $Failed++
    }
}

# Summary
Write-Host ""
Write-Info "Summary:"
Write-Host "  - Files moved: $Moved" -ForegroundColor White
Write-Host "  - Files skipped: $Skipped" -ForegroundColor White
Write-Host "  - Files failed: $Failed" -ForegroundColor White
Write-Host ""

# Commit if we moved anything
if ($Moved -gt 0) {
    Write-Info "Committing changes..."
    try {
        & git add -A
        & git status --short
        & git commit -m "Organize repository: Move $Moved files to Artifacts folder for cleaner root view"
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Changes committed successfully"
        } else {
            Write-Fail "Commit failed (nothing to commit?)"
        }
    } catch {
        Write-Fail "Commit failed: $_"
    }
} else {
    Write-Info "No files to move - nothing to commit"
}

# Push (unless -NoPush)
if ($NoPush) {
    Write-Info "Skipping push (-NoPush). Run push_both_starguard.ps1 with your token to push."
} else {
    Write-Info "Pushing to GitHub..."
    Write-Host ""
    Write-Host "  [!] This will require GitHub authentication." -ForegroundColor Yellow
    Write-Host "  [i] Options: 1) Personal Access Token  2) SSH key  3) gh auth login" -ForegroundColor DarkGray
    Write-Host ""
    Read-Host "  Press Enter to continue with push, or Ctrl+C to cancel"
    Write-Host ""
    try {
        & git push origin main
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Successfully pushed to GitHub!"
        } else {
            Write-Fail "Push failed. Use Personal Access Token as password."
            exit 1
        }
    } catch {
        Write-Fail "Push failed: $_"
        exit 1
    }
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Success "Repository reorganization complete!"
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Info "View your repository at:"
Write-Host "  https://github.com/reichert-science-intelligence/$RepoName" -ForegroundColor Cyan
Write-Host ""
Write-Info "New structure:"
Write-Host "  Root: README.md" -ForegroundColor White
Write-Host "  Artifacts/: [$Moved+ files]" -ForegroundColor White
Write-Host ""
Write-Success "Script completed!"
