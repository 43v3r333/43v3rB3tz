<#
  Self-healing Cloudflare quick tunnel for the 43v3rB3tz backend (Windows PowerShell 5.1+).

  - Starts `cloudflared tunnel --url http://localhost:8001` and restarts it if it ever stops.
  - Each time the tunnel gets a new https://*.trycloudflare.com address, it waits until the backend answers
    through it, then updates every env var on the Vercel project "43v3rb3tz" that still points at an old
    trycloudflare address (INTERNAL_API_URL, and NEXT_PUBLIC_API_URL if it does too) and redeploys production,
    so the site and LifeOS find the backend again within about 2 minutes.
  - Needs VERCEL_TOKEN in prophitbet-saas\.env (never printed). Log: prophitbet-saas\logs\tunnel.log

  Run once by hand:   powershell -ExecutionPolicy Bypass -File .\start-tunnel.ps1
  Start at logon:     powershell -ExecutionPolicy Bypass -File .\start-tunnel.ps1 -Install
#>
param([switch]$Install)

$ErrorActionPreference = "Stop"
$Here      = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir    = Join-Path $Here "logs"
$Log       = Join-Path $LogDir "tunnel.log"
$CfLog     = Join-Path $LogDir "cloudflared.log"
$ProjectId = "prj_h8HQ2aN0DKRBAh532mKYiAFlefK4"
$TeamId    = "team_5JdQBY7Zjx3rb7dtTeoGzJMk"
$Local     = "http://localhost:8001"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Write-Log($msg) { $line = "$(Get-Date -Format s)  $msg"; Add-Content -Path $Log -Value $line; Write-Host $line }

if ($Install) {
  $action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$($MyInvocation.MyCommand.Path)`"" -WorkingDirectory $Here
  $trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
  $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero)
  Register-ScheduledTask -TaskName "43v3rB3tz tunnel" -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
  Write-Host "Installed: the tunnel now starts at every logon (Task Scheduler > '43v3rB3tz tunnel'). Starting it now..."
  Start-ScheduledTask -TaskName "43v3rB3tz tunnel"
  exit 0
}

# --- settings -------------------------------------------------------------------------------
$envFile = Join-Path $Here ".env"
$token = $null
if (Test-Path $envFile) {
  $m = Select-String -Path $envFile -Pattern '^\s*VERCEL_TOKEN\s*=\s*"?([^"\s]+)"?' | Select-Object -First 1
  if ($m) { $token = $m.Matches[0].Groups[1].Value }
}
if (-not $token) { Write-Log "ERROR: add VERCEL_TOKEN=... to $envFile (see the comment at the top of this script)"; exit 1 }

$cf = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $cf) {
  Write-Log "cloudflared not found: installing with winget..."
  winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements | Out-Null
  $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
  $cf = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
  if (-not $cf) { Write-Log "ERROR: cloudflared install failed. Install it from https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/"; exit 1 }
}

$headers = @{ Authorization = "Bearer $token"; "Content-Type" = "application/json" }
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

function Wait-Url($url, $seconds) {
  $deadline = (Get-Date).AddSeconds($seconds)
  while ((Get-Date) -lt $deadline) {
    try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 10; if ($r.StatusCode -eq 200) { return $true } } catch { }
    Start-Sleep -Seconds 5
  }
  return $false
}

function Update-Vercel($newUrl) {
  $envs = (Invoke-RestMethod -Uri "https://api.vercel.com/v9/projects/$ProjectId/env?teamId=$TeamId&decrypt=true" -Headers $headers).envs
  $changed = 0
  foreach ($e in $envs) {
    $val = [string]$e.value
    if ($val -match 'https://[a-z0-9-]+\.trycloudflare\.com') {
      $updated = $val -replace 'https://[a-z0-9-]+\.trycloudflare\.com', $newUrl
      if ($updated -ne $val) {
        $body = @{ value = $updated } | ConvertTo-Json
        Invoke-RestMethod -Method Patch -Uri "https://api.vercel.com/v9/projects/$ProjectId/env/$($e.id)?teamId=$TeamId" -Headers $headers -Body $body | Out-Null
        Write-Log "Vercel: $($e.key) now points at the new tunnel"
        $changed++
      }
    }
  }
  if ($changed -eq 0) { Write-Log "Vercel already points at $newUrl"; return }
  $latest = (Invoke-RestMethod -Uri "https://api.vercel.com/v6/deployments?projectId=$ProjectId&teamId=$TeamId&target=production&state=READY&limit=1" -Headers $headers).deployments[0]
  $body = @{ name = "43v3rb3tz"; project = $ProjectId; deploymentId = $latest.uid; target = "production" } | ConvertTo-Json
  $dep = Invoke-RestMethod -Method Post -Uri "https://api.vercel.com/v13/deployments?teamId=$TeamId&forceNew=1" -Headers $headers -Body $body
  Write-Log "Vercel: production redeploy started ($($dep.id)); live in about 1-2 min"
}

# --- main loop: run the tunnel forever --------------------------------------------------------
Write-Log "Tunnel watchdog started"
while ($true) {
  if (-not (Wait-Url "$Local/health" 600)) { Write-Log "Backend not answering on $Local/health (is Docker running?). Retrying..."; continue }

  if (Test-Path $CfLog) { Remove-Item $CfLog -Force }
  $proc = Start-Process -FilePath $cf -ArgumentList @("tunnel", "--no-autoupdate", "--url", $Local, "--logfile", $CfLog) -WindowStyle Hidden -PassThru
  Write-Log "cloudflared started (pid $($proc.Id))"

  $url = $null
  for ($i = 0; $i -lt 60 -and -not $url -and -not $proc.HasExited; $i++) {
    Start-Sleep -Seconds 2
    if (Test-Path $CfLog) {
      $hit = Select-String -Path $CfLog -Pattern 'https://[a-z0-9-]+\.trycloudflare\.com' | Select-Object -First 1
      if ($hit) { $url = $hit.Matches[0].Value }
    }
  }

  if ($url) {
    Write-Log "Tunnel address: $url"
    if (Wait-Url "$url/health" 120) {
      try { Update-Vercel $url } catch { Write-Log "ERROR updating Vercel: $($_.Exception.Message)" }
    } else { Write-Log "Tunnel not reachable yet; Vercel left unchanged" }
  } else { Write-Log "No tunnel address found; restarting cloudflared" }

  while (-not $proc.HasExited) {
    Start-Sleep -Seconds 30
    if ($url -and -not (Wait-Url "$url/health" 90)) { Write-Log "Tunnel stopped answering: restarting"; try { $proc.Kill() } catch { }; break }
  }
  Write-Log "cloudflared exited; restarting in 10 s"
  Start-Sleep -Seconds 10
}
