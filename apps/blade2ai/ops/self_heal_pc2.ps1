[CmdletBinding(SupportsShouldProcess=$true)]
param(
  [Parameter(Mandatory=$false)]
  [string]$TargetIp = "100.94.217.82",

  [switch]$PingOnly,
  [switch]$RestartExplorer,
  [switch]$ForceReboot,

  # Fallback path if WinRM isn't available; requires remote shutdown rights.
  [switch]$UseShutdownExe
)

$ErrorActionPreference = "Stop"

function Write-Section([string]$Title) {
  Write-Host "" 
  Write-Host "=== $Title ===" -ForegroundColor Cyan
}

Write-Section "PC2 Self-Heal"
Write-Host "Target: $TargetIp" -ForegroundColor Gray

Write-Section "Connectivity"
$reachable = $false
try {
  $reachable = Test-Connection -ComputerName $TargetIp -Count 1 -Quiet -TimeoutSeconds 2
} catch {
  $reachable = $false
}

if (-not $reachable) {
  Write-Host "UNREACHABLE: $TargetIp" -ForegroundColor Red
  if ($PingOnly -or (-not $RestartExplorer -and -not $ForceReboot)) {
    exit 2
  }
} else {
  Write-Host "Reachable: $TargetIp" -ForegroundColor Green
  if ($PingOnly) { exit 0 }
}

if ($RestartExplorer) {
  Write-Section "Restart Explorer (WinRM)"
  $scriptBlock = {
    try {
      Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue
    } catch {}
    Start-Process explorer
  }

  if ($PSCmdlet.ShouldProcess($TargetIp, "Restart Explorer")) {
    try {
      Invoke-Command -ComputerName $TargetIp -ScriptBlock $scriptBlock -ErrorAction Stop
      Write-Host "Explorer restarted via WinRM." -ForegroundColor Green
      exit 0
    } catch {
      Write-Host "WinRM restart failed: $($_.Exception.Message)" -ForegroundColor Yellow
      Write-Host "Tip: enable WinRM on the target, or use -UseShutdownExe (requires permissions)." -ForegroundColor Gray
    }
  }
}

if ($ForceReboot) {
  Write-Section "Force Reboot"

  if ($PSCmdlet.ShouldProcess($TargetIp, "Restart-Computer -Force")) {
    try {
      Restart-Computer -ComputerName $TargetIp -Force -ErrorAction Stop
      Write-Host "Reboot issued via WinRM." -ForegroundColor Green
      exit 0
    } catch {
      Write-Host "WinRM reboot failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
  }

  if ($UseShutdownExe) {
    Write-Section "Fallback: shutdown.exe"
    $cmd = "shutdown.exe /r /m \\$TargetIp /t 0 /f"
    if ($PSCmdlet.ShouldProcess($TargetIp, $cmd)) {
      try {
        cmd.exe /c $cmd | Out-Null
        Write-Host "shutdown.exe reboot attempted." -ForegroundColor Green
        exit 0
      } catch {
        Write-Host "shutdown.exe failed: $($_.Exception.Message)" -ForegroundColor Red
        exit 3
      }
    }
  }
}

Write-Host "No action taken (safe default). Use -RestartExplorer or -ForceReboot." -ForegroundColor Gray
exit 0
