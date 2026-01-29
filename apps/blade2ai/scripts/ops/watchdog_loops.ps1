[CmdletBinding()]
param(
  [int]$SleepSeconds = 300
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$logsDir = Join-Path $repoRoot "logs"
$pidPath = Join-Path $logsDir "heal.pid"
$logPath = Join-Path $logsDir "self_heal.log"

New-Item -ItemType Directory -Force -Path $logsDir | Out-Null

while ($true) {
  try {
    if (Test-Path $pidPath) {
      $pidVal = (Get-Content $pidPath -ErrorAction SilentlyContinue | Select-Object -First 1)
      if ($pidVal -and ($pidVal -as [int])) {
        $proc = Get-Process -Id ([int]$pidVal) -ErrorAction SilentlyContinue
        if (-not $proc) {
          Add-Content -Path $logPath -Value ("[WATCHDOG] {0} Monitor died. Restarting..." -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"))
          $python = Join-Path $repoRoot ".venv\Scripts\python.exe"
          if (-not (Test-Path $python)) { $python = "python" }
          $args = "scripts/ops/self_heal_monitor.py --interval 60"
          $p = Start-Process -FilePath $python -ArgumentList $args -WorkingDirectory $repoRoot -WindowStyle Hidden -PassThru
          $p.Id | Out-File -FilePath $pidPath -Encoding ascii
        }
      }
    }
  } catch {
    Add-Content -Path $logPath -Value ("[WATCHDOG] {0} Error: {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $_.Exception.Message)
  }

  Start-Sleep -Seconds $SleepSeconds
}
