#!/usr/bin/env pwsh
# StarGuard Desktop - Repository Reorganization Script
# Moves all 200+ files to Artifacts/, keeps only README.md in root
# Same process as AuditShield Live - professional recruit-ready structure
# Usage: cd "Artifacts\project\auditshield" then: .\reorganize_starguard_desktop.ps1

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$V2Path = Join-Path $ScriptDir "reorganize_github_robust_v2.ps1"
& $V2Path -RepoUrl "https://github.com/reichert-science-intelligence/starguard-desktop.git" -RepoName "starguard-desktop" -MoveAllExceptReadme:$true @args
