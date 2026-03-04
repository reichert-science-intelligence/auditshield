#!/usr/bin/env pwsh
# AuditShield Live - Repository Reorganization Script (PowerShell)
# Moves 18 files to Artifacts/ folder, keeps README.md in root
# Author: Robert Reichert
# Date: February 25, 2026
# Usage: .\reorganize_github_robust.ps1

$ErrorActionPreference = "Stop"
$RepoUrl = "https://github.com/reichert-science-intelligence/auditshield-live.git"
$RepoName = "auditshield-live"

# Files to move (18 total)
$FilesToMove = @(
    "LICENSE",
    ".gitignore",
    "requirements.txt",
    "GITHUB_UPLOAD_GUIDE.md",
    "PHASE_1_COMPLETE.md",
    "PHASE_2_COMPLETE.md",
    "PHASE_3_COMPLETE.md",
    "PHASE_4_COMPLETE.md",
    "DEPLOYMENT_GUIDE.md",
    "synthetic_chart_generator.py",
    "ncqa_specification_builder.py",
    "validation_engine.py",
    "layer1_document_intelligence.py",
    "layer3_self_correction.py",
    "compound_pipeline.py",
    "agentic_rag_coordinator.py",
    "AuditShieldMobile.jsx",
    "AuditShieldLive_Demo.html"
)

function Write-Banner {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "  AuditShield Live - Repository Reorganization Script         " -ForegroundColor Cyan
    Write-Host "  Moving 18 files to Artifacts/ folder                        " -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Info { param($Msg) Write-Host "[i]  $Msg" -ForegroundColor DarkGray }
function Write-Success { param($Msg) Write-Host "[OK] $Msg" -ForegroundColor Green }
function Write-Skip { param($Msg) Write-Host "[-]  $Msg" -ForegroundColor Yellow }
function Write-Fail { param($Msg) Write-Host "[X]  $Msg" -ForegroundColor Red }

Write-Banner

# Detect working directory
$WorkDir = $PWD.Path
$IsInRepo = $false
$RepoRoot = $null

# Check if we're in auditshield-live repo (must have origin -> auditshield-live)
if (Test-Path ".git") {
    try {
        $RemoteUrl = & git remote get-url origin 2>$null
        if ($RemoteUrl -and $RemoteUrl -like "*auditshield-live*") {
            $IsInRepo = $true
            $RepoRoot = $WorkDir
            Write-Info "Using existing repository at: $RepoRoot"
        }
    } catch {
        # No origin or other git error - not the auditshield-live repo, will clone
    }
}

# If not in repo, check if we're in a parent dir with auditshield-live
if (-not $IsInRepo -and (Test-Path "auditshield-live\.git")) {
    $IsInRepo = $true
    $RepoRoot = Join-Path $WorkDir "auditshield-live"
    Write-Info "Found auditshield-live in current directory"
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
try {
    & git pull origin main 2>$null
} catch { }
# Ignore pull errors (e.g., no remote changes)

# Check Git credentials
Write-Info "Checking Git credentials..."
$GitName = & git config user.name 2>$null
$GitEmail = & git config user.email 2>$null
$CredentialsWereSet = $false

if ([string]::IsNullOrWhiteSpace($GitName)) {
    Write-Host "  [!] Git user.name not set. Setting it now..." -ForegroundColor Yellow
    $GitName = Read-Host "  Enter your name (e.g., Robert Reichert)"
    if ([string]::IsNullOrWhiteSpace($GitName)) {
        Write-Fail "Git user.name is required for commits. Run: git config --global user.name 'Your Name'"
        exit 1
    }
    & git config --global user.name $GitName
    $CredentialsWereSet = $true
}
if ([string]::IsNullOrWhiteSpace($GitEmail)) {
    Write-Host "  [!] Git user.email not set. Setting it now..." -ForegroundColor Yellow
    $GitEmail = Read-Host "  Enter your email (e.g., you@example.com)"
    if ([string]::IsNullOrWhiteSpace($GitEmail)) {
        Write-Fail "Git user.email is required for commits. Run: git config --global user.email 'you@example.com'"
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

# Create Artifacts folder
$ArtifactsPath = Join-Path $RepoRoot "Artifacts"
if (-not (Test-Path $ArtifactsPath)) {
    New-Item -ItemType Directory -Path $ArtifactsPath | Out-Null
    Write-Success "Artifacts/ folder created"
} else {
    Write-Info "Artifacts/ folder already exists"
}

# Move files
Write-Info "Moving files to Artifacts/..."
$Moved = 0
$Skipped = 0
$Failed = 0

foreach ($File in $FilesToMove) {
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
        & git mv $File "Artifacts/$File" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  + Moved: $File" -ForegroundColor Green
            $Moved++
        } else {
            # Fallback: regular move + git add
            Move-Item $SrcPath $DstPath -Force
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

# Push
Write-Info "Pushing to GitHub..."
Write-Host ""
Write-Host "  [!] This will require GitHub authentication." -ForegroundColor Yellow
Write-Host "  [i] Options:" -ForegroundColor DarkGray
Write-Host "     1. Personal Access Token (recommended)" -ForegroundColor DarkGray
Write-Host "     2. SSH key" -ForegroundColor DarkGray
Write-Host "     3. GitHub CLI (gh auth login)" -ForegroundColor DarkGray
Write-Host ""
Read-Host "  Press Enter to continue with push, or Ctrl+C to cancel"
Write-Host ""
try {
    & git push origin main
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Successfully pushed to GitHub!"
    } else {
        Write-Fail "Push failed. Please authenticate with GitHub:"
        Write-Host "  - Option 1: gh auth login" -ForegroundColor Yellow
        Write-Host "  - Option 2: Use Personal Access Token as password" -ForegroundColor Yellow
        Write-Host "  • See QUICK_START for details" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Fail "Push failed: $_"
    exit 1
}

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Success "Repository reorganization complete!"
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Info "View your repository at:"
Write-Host "  https://github.com/reichert-science-intelligence/auditshield-live" -ForegroundColor Cyan
Write-Host ""
Write-Info "New structure:"
Write-Host "  Root: README.md" -ForegroundColor White
Write-Host "  Artifacts/: [18 files]" -ForegroundColor White
Write-Host ""
Write-Success "Script completed!"
