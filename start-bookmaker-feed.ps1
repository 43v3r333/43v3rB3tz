[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$collectorPython = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'tools/dots/.venv/Scripts/python.exe')).Path
$collectorScript = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'tools/collect_bookmaker_data.py')).Path
$existing = Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" |
    Where-Object { $_.CommandLine -match 'collect_bookmaker_data\.py' }
if ($existing) {
    Write-Output "Bookmaker collector already running (PID: $($existing.ProcessId -join ', '))."
    return
}
$collectorArguments = @('"' + $collectorScript + '"', '--interval', '300')
$process = Start-Process -FilePath $collectorPython -ArgumentList $collectorArguments `
    -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru
Write-Output "Bookmaker collector started (PID: $($process.Id)); refreshes every five minutes."
Write-Output 'Celery imports eligible observations on its existing fifteen-minute schedule.'
Write-Output 'This process does not automatically restart after Windows reboots.'
