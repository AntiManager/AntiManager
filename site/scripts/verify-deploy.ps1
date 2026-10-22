# Verify the deployed genome section is live. Exit non-zero on any failure.
# Usage: .\scripts\verify-deploy.ps1
$ErrorActionPreference = "Stop"

$base = "https://antimanager.pro"
$indexNowKey = (Get-Content (Join-Path $PSScriptRoot "..\src\indexnow-key.txt") -Raw).Trim()
$checks = @(
  @{ Url = "$base/genome/";        Match = 'hero-gen' },
  @{ Url = "$base/genome/role/";   Match = 'doc-doc' },
  @{ Url = "$base/sitemap.xml";    Match = '/genome/role/' },
  @{ Url = "$base/sitemap.xml";    Match = '/articles/practice/' },
  @{ Url = "$base/articles/practice/5s-na-proizvodstve/"; Match = 'article-faq' },
  @{ Url = "$base/$indexNowKey.txt"; Match = $indexNowKey }
)

$failed = $false
foreach ($c in $checks) {
  try {
    $r = Invoke-WebRequest -Uri $c.Url -UseBasicParsing -TimeoutSec 20
    $matched = $r.Content.Contains($c.Match)
    if ($r.StatusCode -eq 200 -and $matched) {
      Write-Host ("[OK]   {0}  (200, match '{1}')" -f $c.Url, $c.Match) -ForegroundColor Green
    } else {
      Write-Host ("[FAIL] {0}  status={1} match={2}" -f $c.Url, $r.StatusCode, $matched) -ForegroundColor Red
      $failed = $true
    }
  } catch {
    Write-Host ("[FAIL] {0}  {1}" -f $c.Url, $_.Exception.Message) -ForegroundColor Red
    $failed = $true
  }
}

if ($failed) { Write-Host "Deploy verification FAILED." -ForegroundColor Red; exit 1 }
Write-Host "Deploy verification passed: genome section is live." -ForegroundColor Green
