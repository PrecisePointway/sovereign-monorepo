[CmdletBinding()]
param(
  [int]$IntervalSeconds = 60
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path $PSScriptRoot
$logsDir = Join-Path $repoRoot "logs"
New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

Write-Host "Blade2AI Loop Launcher" -ForegroundColor Cyan
Write-Host ("UTC: " + [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")) -ForegroundColor Gray

$python = Join-Path $repoRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

# Launch Self-Heal Monitor
$monitorArgs = "scripts/ops/self_heal_monitor.py --interval $IntervalSeconds"
$monitor = Start-Process -FilePath $python -ArgumentList $monitorArgs -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
$monitor.Id | Out-File -FilePath (Join-Path $logsDir "heal.pid") -Encoding ascii
Write-Host "Self-Heal Monitor PID: $($monitor.Id)" -ForegroundColor Green

# Launch Watchdog
$watchdog = Start-Process -FilePath "pwsh" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File scripts/ops/watchdog_loops.ps1" -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
$watchdog.Id | Out-File -FilePath (Join-Path $logsDir "watchdog.pid") -Encoding ascii
Write-Host "Watchdog PID: $($watchdog.Id)" -ForegroundColor Green

Write-Host "DEFENSE LOOPS ACTIVE" -ForegroundColor Green
