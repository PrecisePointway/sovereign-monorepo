[CmdletBinding(SupportsShouldProcess=$true)]
param(
  [Parameter(Mandatory=$false)]
  [string]$TargetIp = "100.77.189.96"
)

# Compat wrapper for Phase 4 file layout.
# Canonical implementation lives at repo-root: ops/self_heal_pc2.ps1

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$canonical = Join-Path $repoRoot "ops\self_heal_pc2.ps1"

if (-not (Test-Path $canonical)) {
  Write-Host "Missing canonical script: $canonical" -ForegroundColor Red
  exit 2
}

& $canonical -TargetIp $TargetIp -RestartExplorer
