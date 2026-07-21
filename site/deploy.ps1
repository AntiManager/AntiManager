# Deploy antimanager.pro to VPS
# Usage: .\deploy.ps1 [-SkipBuild]
# Config: .env file in repo root (copy .env.example → .env and fill in)
param(
  [switch]$SkipBuild = $false
)

$ErrorActionPreference = "Stop"

# --- Load .env from repo root ---
$envFile = Join-Path $PSScriptRoot ".." ".env"
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
$remoteDir    = if ($env:REMOTE_DIR)    { $env:REMOTE_DIR }    else { "/home/user/app" }
$sshOpts      = "-p $remotePort -o StrictHostKeyChecking=accept-new"

if (-not $SkipBuild) {
  Write-Host "🏗 Building..." -ForegroundColor Cyan
  Push-Location $PSScriptRoot
  node build.js
  Pop-Location
}

Write-Host "📦 Copying dist to VPS..." -ForegroundColor Cyan
& "ssh" $sshOpts "$remoteUser@$remoteHost" "mkdir -p $remoteDir/current"
& "scp" "-P$remotePort" -r "$PSScriptRoot\dist\*" "$remoteUser@$remoteHost`:$remoteDir/current/"
& "ssh" $sshOpts "$remoteUser@$remoteHost" "chmod -R 755 $remoteDir/current/ && find $remoteDir/current/ -type f -exec chmod 644 {} \;"

Write-Host "⚙️ Creating nginx config..." -ForegroundColor Cyan
& "scp" "-P$remotePort" "$PSScriptRoot\deploy\nginx.conf" "$remoteUser@$remoteHost`:$remoteDir/nginx.conf"

Write-Host "🐳 Restarting Docker container..." -ForegroundColor Cyan
& "ssh" $sshOpts "$remoteUser@$remoteHost" "docker rm -f antimanager-web 2>/dev/null; docker run -d --name antimanager-web --restart unless-stopped --network vps_shared -v $remoteDir/current:/usr/share/nginx/html:ro -v $remoteDir/nginx.conf:/etc/nginx/conf.d/default.conf:ro nginx:alpine"

Write-Host "📝 Adding Caddy config..." -ForegroundColor Cyan
& "ssh" $sshOpts "$remoteUser@$remoteHost" "grep -q 'antimanager.pro {' $remoteDir/../factory-system/.infra/caddy/Caddyfile || printf '\nantimanager.pro {\n    reverse_proxy antimanager-web:80\n    encode zstd gzip\n    header {\n        -Server\n        Strict-Transport-Security \"max-age=31536000; includeSubDomains\"\n        X-Content-Type-Options \"nosniff\"\n    }\n}\n' >> $remoteDir/../factory-system/.infra/caddy/Caddyfile"

Write-Host "🔄 Reloading Caddy..." -ForegroundColor Cyan
& "ssh" $sshOpts "$remoteUser@$remoteHost" "docker exec caddy caddy reload --config /etc/caddy/Caddyfile"

Write-Host "✅ Deploy complete! https://antimanager.pro" -ForegroundColor Green
