# Deploy antimanager.pro to VPS
param(
  [switch]$SkipBuild = $false
)

$ErrorActionPreference = "Stop"
$remoteUser = "REMOTE_USER"
$remoteHost = "ANTIMANAGER_VPS_IP"
$remotePort = 2222
$remoteDir = "/home/REMOTE_USER/antimanager"
$sshOpts = "-p $remotePort -o StrictHostKeyChecking=accept-new"

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
& "ssh" $sshOpts "$remoteUser@$remoteHost" "grep -q 'antimanager.pro {' /home/REMOTE_USER/factory-system/.infra/caddy/Caddyfile || printf '\nantimanager.pro {\n    reverse_proxy antimanager-web:80\n    encode zstd gzip\n    header {\n        -Server\n        Strict-Transport-Security \"max-age=31536000; includeSubDomains\"\n        X-Content-Type-Options \"nosniff\"\n    }\n}\n' >> /home/REMOTE_USER/factory-system/.infra/caddy/Caddyfile"

Write-Host "🔄 Reloading Caddy..." -ForegroundColor Cyan
& "ssh" $sshOpts "$remoteUser@$remoteHost" "docker exec caddy caddy reload --config /etc/caddy/Caddyfile"

Write-Host "✅ Deploy complete! https://antimanager.pro" -ForegroundColor Green
