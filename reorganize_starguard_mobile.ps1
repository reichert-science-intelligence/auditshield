#!/usr/bin/env pwsh
# StarGuard Mobile - Repository Reorganization Script
# Moves all files to Artifacts/, keeps only README.md in root
# Same process as AuditShield Live - professional recruit-ready structure
# Usage: cd "Artifacts\project\auditshield" then: .\reorganize_starguard_mobile.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$V2Path = Join-Path $ScriptDir "reorganize_github_robust_v2.ps1"
& $V2Path -RepoUrl "https://github.com/reichert-science-intelligence/starguard-mobile.git" -RepoName "starguard-mobile" -MoveAllExceptReadme:$true @args
