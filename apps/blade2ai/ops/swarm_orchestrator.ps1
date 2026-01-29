[CmdletBinding()]
param(
  [Parameter(Mandatory=$false)]
  [hashtable]$Nodes = @{
    PC1_blade = @{ ip = "100.94.217.81"; role = "primary" }
    PC2_echo  = @{ ip = "100.94.217.82"; role = "compute" }
    PC4_local = @{ ip = "127.0.0.1";     role = "controller" }
  },

  [switch]$AttemptPc2Recovery
)

$ErrorActionPreference = "Stop"

Write-Host "Swarm Orchestrator" -ForegroundColor Cyan
Write-Host ("UTC: " + [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")) -ForegroundColor Gray

$results = @()
foreach ($name in $Nodes.Keys) {
  $node = $Nodes[$name]
  $ip = $node.ip
  $role = $node.role

  $ok = $false
  try {
    $ok = Test-Connection -ComputerName $ip -Count 1 -Quiet -TimeoutSeconds 2
  } catch {
    $ok = $false
  }

  $results += [pscustomobject]@{
    name = $name
    ip = $ip
    role = $role
    reachable = $ok
  }
}

$results | Format-Table -AutoSize

$pc2 = $results | Where-Object { $_.name -eq "PC2_echo" }
if ($AttemptPc2Recovery -and $pc2 -and -not $pc2.reachable) {
  Write-Host "PC2 unreachable; attempting recovery..." -ForegroundColor Yellow
  $script = Join-Path $PSScriptRoot "self_heal_pc2.ps1"
  if (Test-Path $script) {
    & $script -TargetIp $pc2.ip -RestartExplorer
  } else {
    Write-Host "Missing: $script" -ForegroundColor Red
  }
}
