# Deploy the feedback microservice to the VPS (build image there, (re)run container).
$ErrorActionPreference = "Stop"

$envFile = Join-Path (Join-Path (Join-Path $PSScriptRoot "..") "..") ".env"
if (Test-Path $envFile) {
  Get-Content $envFile | ForEach-Object {
    if ($_ -match '^([^#=]+)=(.+)$') {
      [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
  }
}

$remoteUser = if ($env:REMOTE_USER) { $env:REMOTE_USER } else { "user" }
$remoteHost = if ($env:REMOTE_HOST) { $env:REMOTE_HOST } else { "host.local" }
$remotePort = if ($env:REMOTE_PORT) { [int]$env:REMOTE_PORT } else { 22 }
$remoteDir  = if ($env:REMOTE_DIR)  { $env:REMOTE_DIR }  else { "/home/user/app" }
$sshBase    = @("-p", "$remotePort", "-o", "StrictHostKeyChecking=accept-new")
$sshDst     = "${remoteUser}@${remoteHost}"

function Run-Ssh($cmd) {
  & "ssh" @sshBase "$sshDst" $cmd 2>&1
  if (-not $?) { throw "SSH command failed: $cmd" }
}

function Run-Scp($local, $remote) {
  & "scp" @("-P$remotePort", "-o", "StrictHostKeyChecking=accept-new", "-r") $local "${sshDst}:${remote}" 2>&1
  if (-not $?) { throw "SCP failed: $local -> $remote" }
}

Write-Host "Uploading service source..." -ForegroundColor Cyan
Run-Ssh "mkdir -p $remoteDir/feedback-src"
Run-Scp "$PSScriptRoot\." "$remoteDir/feedback-src/"

Write-Host "Checking server env file..." -ForegroundColor Cyan
try {
  Run-Ssh "test -f $remoteDir/feedback.env"
} catch {
  throw "Missing $remoteDir/feedback.env on the server. Create it from .env.example with TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, then chmod 600 and re-run."
}

Write-Host "Building image..." -ForegroundColor Cyan
Run-Ssh "cd $remoteDir/feedback-src && docker build -t antimanager-feedback:latest ."

Write-Host "Restarting container..." -ForegroundColor Cyan
Run-Ssh "docker rm -f antimanager-feedback 2>/dev/null; docker run -d --name antimanager-feedback --restart unless-stopped --network vps_shared --env-file $remoteDir/feedback.env antimanager-feedback:latest"

# A crash-loop (e.g. an empty token in feedback.env) still returns 0 from
# `docker run -d`, so confirm the process is actually up before reporting success.
Write-Host "Verifying container is running..." -ForegroundColor Cyan
Run-Ssh "sleep 2; docker inspect -f '{{.State.Running}}' antimanager-feedback | grep -qx true || { echo 'container is not running:'; docker logs --tail 20 antimanager-feedback 2>&1; exit 1; }"

Write-Host "Feedback service deployed (proxied by nginx at /api/feedback)." -ForegroundColor Green
