# Sync .cursorrules, Phase2-to-Hardening-Sprint-Checklist.md, INSTALL-REFERENCE.md,
# and app-specific CURSORRULES-*.md to all five portfolio repo roots.
# Run from auditshield root. Keeps Engineering Standards identical across repos.
# Usage: .\sync-cursorrules.ps1
#
# Targets:
#   Artifacts/project/auditshield (AuditShield Live — source and live app root)
#   Artifacts/project/auditshield/starguard-desktop
#   Artifacts/project/auditshield/starguard-mobile
#   Artifacts/project/sovereignshield
#   Artifacts/project/sovereignshield-mobile

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$parent = Split-Path $root -Parent

# Target paths: flat repos under Artifacts/project/, StarGuard under auditshield/
$repoPaths = @{
    "auditshield-live"       = $root   # auditshield is source and live app root — sync in place
    "starguard-desktop"      = Join-Path $root "starguard-desktop"
    "starguard-mobile"       = Join-Path $root "starguard-mobile"
    "sovereignshield"        = Join-Path $parent "sovereignshield"
    "sovereignshield-mobile" = Join-Path $parent "sovereignshield-mobile"
}

# App-specific CURSORRULES mapping: source file -> target repo key
$appRules = @{
    "CURSORRULES-AUDITSHIELD-LIVE.md"       = "auditshield-live"
    "CURSORRULES-STARGUARD-DESKTOP.md"      = "starguard-desktop"
    "CURSORRULES-STARGUARD-MOBILE.md"       = "starguard-mobile"
    "CURSORRULES-SOVEREIGNSHIELD-DESKTOP.md" = "sovereignshield"
    "CURSORRULES-SOVEREIGNSHIELD-MOBILE.md"  = "sovereignshield-mobile"
}

# Shared files copied to ALL five repos
$sharedFiles = @(".cursorrules", "Phase2-to-Hardening-Sprint-Checklist.md", "INSTALL-REFERENCE.md")

$results = @()

# 1. Copy shared files (.cursorrules, Phase2, INSTALL-REFERENCE) to all five repos
foreach ($file in $sharedFiles) {
    $source = Join-Path $root $file
    foreach ($repoKey in $repoPaths.Keys) {
        $destDir = $repoPaths[$repoKey]
        $dest = Join-Path $destDir $file
        $status = "Failed"
        if (Test-Path $source) {
            if (Test-Path $destDir) {
                try {
                    Copy-Item $source $dest -Force
                    $status = "Copied"
                } catch { $status = "Failed" }
            } else {
                $status = "Failed (dest missing)"
            }
        } else {
            $status = "Failed (source missing)"
        }
        $results += [PSCustomObject]@{
            File       = $file
            Source     = $source
            Destination = $dest
            Status     = $status
        }
    }
}

# 2. Copy each app's CURSORRULES-*.md to its correct repo only
foreach ($kv in $appRules.GetEnumerator()) {
    $file = $kv.Key
    $repoKey = $kv.Value
    $source = Join-Path $root $file
    $destDir = $repoPaths[$repoKey]
    $dest = Join-Path $destDir $file
    $status = "Failed"
    if (Test-Path $source) {
        if (Test-Path $destDir) {
            try {
                Copy-Item $source $dest -Force
                $status = "Copied"
            } catch { $status = "Failed" }
        } else {
            $status = "Failed (dest missing)"
        }
    } else {
        $status = "Failed (source missing)"
    }
    $results += [PSCustomObject]@{
        File        = $file
        Source      = $source
        Destination = $dest
        Status      = $status
    }
}

# 3. Print confirmation table
Write-Host ""
$results | Format-Table -Property File, Source, Destination, Status -AutoSize -Wrap
Write-Host ""

# 4. Timestamp
Write-Host "Sync complete: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""
