# Verify the deployed site is live and the legacy routes are single-hop 301s.
# Usage: .\scripts\verify-deploy.ps1
$ErrorActionPreference = "Stop"

$base = "https://antimanager.pro"
$indexNowKey = (Get-Content (Join-Path $PSScriptRoot "..\src\indexnow-key.txt") -Raw).Trim()
$checks = @(
  @{ Url = "$base/method/";        Match = 'hero-gen' },
  @{ Url = "$base/method/role/";   Match = 'doc-doc' },
  @{ Url = "$base/start/";         Match = 'start-page' },
  @{ Url = "$base/playbook/";      Match = 'weapon-grid' },
  @{ Url = "$base/sitemap.xml";    Match = '/method/role/' },
  @{ Url = "$base/sitemap.xml";    Match = '/articles/practice/' },
  @{ Url = "$base/articles/practice/5s-na-proizvodstve/"; Match = 'article-faq' },
  @{ Url = "$base/$indexNowKey.txt"; Match = $indexNowKey }
)

$redirects = @(
  @{ From = "/arsenal";               To = "/playbook/" },
  @{ From = "/arsenal/";              To = "/playbook/" },
  @{ From = "/weapons/antikrizis";    To = "/playbook/antikrizis/" },
  @{ From = "/weapons/antikrizis/";   To = "/playbook/antikrizis/" },
  @{ From = "/book/";                To = "/playbook/" },
  @{ From = "/book/antikrizis/";     To = "/playbook/antikrizis/" },
  @{ From = "/genome/";               To = "/method/" },
  @{ From = "/genome/role/";          To = "/method/role/" },
  @{ From = "/manifesto/";            To = "/about/manifesto/" },
  @{ From = "/archive/";              To = "/about/origins/" },
  @{ From = "/headquarters/";         To = "/contact/" },
  @{ From = "/about/headquarters/";   To = "/contact/" },
  @{ From = "/scenarios/";            To = "/start/" },
  @{ From = "/cases/";                To = "/" },
  @{ From = "/strategy/";             To = "/articles/strategy/" }
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

# Invoke-WebRequest writes a non-terminating "maximum redirects" error for a 3xx
# even with -SkipHttpErrorCheck, which becomes fatal under ErrorActionPreference=Stop.
# HttpClient with AllowAutoRedirect=false probes the status and Location cleanly.
$handler = [System.Net.Http.HttpClientHandler]::new()
$handler.AllowAutoRedirect = $false
$http = [System.Net.Http.HttpClient]::new($handler)
$http.Timeout = [TimeSpan]::FromSeconds(20)

foreach ($r in $redirects) {
  try {
    $resp = $http.GetAsync(("{0}{1}" -f $base, $r.From)).Result
    $location = [string]$resp.Headers.Location
    $ok = ($resp.StatusCode -eq 301) -and $location.EndsWith($r.To)
    if ($ok) {
      Write-Host ("[OK]   301 {0} -> {1}" -f $r.From, $location) -ForegroundColor Green
    } else {
      Write-Host ("[FAIL] 301 {0}  status={1} location={2}" -f $r.From, $resp.StatusCode, $location) -ForegroundColor Red
      $failed = $true
    }
  } catch {
    Write-Host ("[FAIL] 301 {0}  {1}" -f $r.From, $_.Exception.Message) -ForegroundColor Red
    $failed = $true
  }
}

$http.Dispose()

if ($failed) { Write-Host "Deploy verification FAILED." -ForegroundColor Red; exit 1 }
Write-Host "Deploy verification passed: new routes live and legacy routes 301." -ForegroundColor Green
