#requires -Version 5.1
# Agent Manager run script: build the static site and serve a local preview.
# The fixed port is intentional — no automatic port selection.
# Agent Manager sets WORKTREE_PATH to the checkout being run; otherwise fall back
# to the repository next to this script.

$ErrorActionPreference = 'Stop'

$root = if ($env:WORKTREE_PATH) { $env:WORKTREE_PATH } else { (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }
$siteDir = Join-Path $root 'site'

if (-not (Test-Path -LiteralPath (Join-Path $siteDir 'build.js'))) {
    Write-Output "build.js not found in $siteDir"
    exit 1
}

# Fail fast when the preview port is taken instead of silently picking another one.
$busy = @()
try { $busy = @(Get-NetTCPConnection -LocalPort 4173 -State Listen -ErrorAction Stop) } catch { $busy = @() }
if ($busy.Count -gt 0) {
    Write-Output 'PORT 4173 BUSY'
    exit 1
}

# Build the static site.
Push-Location $siteDir
try {
    & node build.js
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}

# Serve the build output for manual preview.
& npx --yes serve (Join-Path $siteDir 'dist') -l 4173
exit $LASTEXITCODE
