# Deploy antimanager.pro to VPS
param([switch]$SkipBuild = $false)

$ErrorActionPreference = "Stop"

$envFile = Join-Path (Join-Path $PSScriptRoot "..") ".env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.+)$') {
      [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
  }
}

$remoteUser   = if ($env:REMOTE_USER)   { $env:REMOTE_USER }   else { "user" }
$remoteHost   = if ($env:REMOTE_HOST)   { $env:REMOTE_HOST }   else { "host.local" }
$remotePort   = if ($env:REMOTE_PORT)   { [int]$env:REMOTE_PORT } else { 22 }
$remoteDir    = if ($env:REMOTE_DIR)   { $env:REMOTE_DIR }    else { "/home/user/app" }
$sshBase      = @("-p", "$remotePort", "-o", "StrictHostKeyChecking=accept-new")
$sshDst       = "${remoteUser}@${remoteHost}"

function Run-Ssh($cmd) {
  & "ssh" @sshBase "$sshDst" $cmd 2>&1
  if (-not $?) { throw "SSH command failed: $cmd" }
}

function Run-Scp($local, $remote) {
  & "scp" @("-P$remotePort", "-o", "StrictHostKeyChecking=accept-new", "-r") $local "${sshDst}:${remote}" 2>&1
  if (-not $?) { throw "SCP failed: $local -> $remote" }
}

if (-not $SkipBuild) {
  Write-Host "Building..." -ForegroundColor Cyan
  Push-Location $PSScriptRoot
  node build.js; if ($?) { Pop-Location } else { Pop-Location; exit 1 }
}

Write-Host "Copying dist to VPS..." -ForegroundColor Cyan
Run-Ssh "mkdir -p $remoteDir/current"
Run-Scp "$PSScriptRoot\dist\*" "$remoteDir/current/"
Run-Ssh "chmod -R 755 $remoteDir/current/; find $remoteDir/current/ -type f -exec chmod 644 {} \;"

Write-Host "Creating nginx config..." -ForegroundColor Cyan
Run-Scp "$PSScriptRoot\deploy\nginx.conf" "$remoteDir/nginx.conf"

Write-Host "Restarting Docker container..." -ForegroundColor Cyan
Run-Ssh "docker rm -f antimanager-web 2>/dev/null; docker run -d --name antimanager-web --restart unless-stopped --network vps_shared -v $remoteDir/current:/usr/share/nginx/html:ro -v $remoteDir/nginx.conf:/etc/nginx/conf.d/default.conf:ro nginx:alpine"

Write-Host "Reloading Caddy if configured..." -ForegroundColor Cyan
Run-Ssh "docker exec caddy caddy reload --config /etc/caddy/Caddyfile 2>/dev/null || true" 2>$null

Write-Host "Deploy complete! https://antimanager.pro" -ForegroundColor Green
