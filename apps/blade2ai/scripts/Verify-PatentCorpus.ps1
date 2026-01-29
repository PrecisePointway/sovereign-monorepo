<#
.SYNOPSIS
  Verifies a merged patent closeout pack (manifest + blob integrity).

.DESCRIPTION
  Verifies that MANIFEST_SHA256.txt entries all exist and match sha256.
  Also performs basic sanity checks for expected directories.

.PARAMETER PackDir
  Path to the pack root (e.g., evidence/patents/<packname>).
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$PackDir
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function _ToPosix([string]$p) {
  return ($p -replace '\\', '/').Trim()
}

function _Fail([string]$msg) {
  throw "PATENT_VERIFY_FAIL: $msg"
}

function _AssertSafeRelPath([string]$rel) {
  $rel2 = _ToPosix $rel
  if ([string]::IsNullOrWhiteSpace($rel2)) { _Fail "Empty manifest path entry." }
  if ([System.IO.Path]::IsPathRooted($rel2)) { _Fail "Manifest path is rooted: $rel2" }
  if ($rel2.StartsWith('/')) { _Fail "Manifest path starts with '/': $rel2" }
  if ($rel2 -match '^[A-Za-z]:' ) { _Fail "Manifest path looks drive-rooted: $rel2" }
  if ($rel2 -match '(^|/)\.\.(/|$)') { _Fail "Manifest path traversal '..' not allowed: $rel2" }
  if ($rel2 -match '(^|/)\./') { _Fail "Manifest path contains '/./' not allowed: $rel2" }
}

$pack = (Resolve-Path -LiteralPath $PackDir).Path
if (-not (Test-Path -LiteralPath $pack -PathType Container)) {
  _Fail "PackDir is not a directory: $PackDir"
}

$manifestPath = Join-Path $pack 'MANIFEST_SHA256.txt'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
  _Fail "Missing MANIFEST_SHA256.txt in $pack"
}

# Basic structure checks
foreach ($d in @('BLOBS','INDEX','NODE_BUNDLES')) {
  $p = Join-Path $pack $d
  if (-not (Test-Path -LiteralPath $p -PathType Container)) {
    Write-Warning "Missing expected directory: $d"
  }
}

$lines = Get-Content -LiteralPath $manifestPath -ErrorAction Stop
if (-not $lines -or $lines.Count -eq 0) {
  _Fail "MANIFEST_SHA256.txt is empty."
}

$ok = 0
foreach ($line in $lines) {
  $t = $line.Trim()
  if ([string]::IsNullOrWhiteSpace($t)) { continue }

  # Format: <sha256><spaces><relpath>
  $parts = $t -split '\s+', 2
  if ($parts.Count -ne 2) { _Fail "Bad manifest line: $t" }

  $shaExpected = $parts[0].ToLowerInvariant()
  $rel = $parts[1]

  if ($shaExpected -notmatch '^[0-9a-f]{64}$') { _Fail "Invalid sha256 in manifest: $shaExpected" }
  _AssertSafeRelPath $rel

  $relPosix = _ToPosix $rel
  $abs = Join-Path $pack $relPosix

  if (-not (Test-Path -LiteralPath $abs -PathType Leaf)) {
    _Fail "Missing file from manifest: $relPosix"
  }

  $shaActual = (Get-FileHash -Algorithm SHA256 -LiteralPath $abs).Hash.ToLowerInvariant()
  if ($shaActual -ne $shaExpected) {
    _Fail "SHA mismatch for $relPosix. expected=$shaExpected actual=$shaActual"
  }

  $ok++
}

Write-Host "VERIFY_OK: $ok files verified in $pack" -ForegroundColor Green
