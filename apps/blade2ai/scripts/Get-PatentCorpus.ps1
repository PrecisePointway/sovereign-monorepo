<#
.SYNOPSIS
  Deterministic patent corpus collector (node bundle).

.DESCRIPTION
  Scans -Root recursively and writes a node bundle under -OutRoot:
    <OutRoot>/<Node>-<timestampZ>/
      BLOBS/<sha256>
      INDEX/FILES.csv
      INDEX/MANIFEST_SHA256.txt
      INDEX/RUN_RECEIPT.json

  Design goals:
  - Deterministic ordering (sorted relpaths)
  - Content-addressed blobs (sha256)
  - Minimal index (node, relpath, bytes, sha256)
  - No zip/flattening

.PARAMETER Node
  Node identifier (e.g. COMPUTERNAME).

.PARAMETER Root
  Root directory to scan.

.PARAMETER OutRoot
  Output root directory (typically .../NODE_BUNDLES).

.PARAMETER IncludePatterns
  Optional filename patterns. Default: '*' (everything under Root).

.EXAMPLE
  pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\Get-PatentCorpus.ps1 -Node $env:COMPUTERNAME -Root C:\patents -OutRoot .\evidence\patents\...\NODE_BUNDLES
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$Node,

  [Parameter(Mandatory = $true)]
  [string]$Root,

  [Parameter(Mandatory = $true)]
  [string]$OutRoot,

  [string[]]$IncludePatterns = @('*')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function _ToPosix([string]$p) {
  return ($p -replace '\\', '/').Trim()
}

function _Fail([string]$msg) {
  throw "PATENT_CORPUS_FAIL: $msg"
}

function _EnsureDir([string]$path) {
  New-Item -ItemType Directory -Force -Path $path | Out-Null
}

function _ComputeSha256([string]$path) {
  return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToLowerInvariant()
}

function _WriteSeal([string]$targetPath, [string]$receiptPath) {
  $digest = (Get-FileHash -Algorithm SHA256 -LiteralPath $targetPath).Hash.ToLowerInvariant()
  $bytes = (Get-Item -LiteralPath $targetPath).Length
  $ts = (Get-Date).ToUniversalTime().ToString('yyyy-MM-ddTHH:mm:ssZ')

  $rel = _ToPosix ([System.IO.Path]::GetRelativePath((Get-Location).Path, (Resolve-Path -LiteralPath $targetPath).Path))

  $lines = @(
    "$digest  $rel",
    "bytes: $bytes",
    "timestamp_utc: $ts"
  )

  try {
    $head = (git rev-parse HEAD 2>$null)
    if ($head) { $lines += "git_head: $head" }
    $dirty = (git status --porcelain 2>$null)
    $lines += ("git_state: " + ($(if ($dirty) { 'dirty' } else { 'clean' })))
  } catch {
    # best-effort git metadata
  }

  Set-Content -LiteralPath $receiptPath -Value ($lines -join "`n") -Encoding UTF8 -NoNewline
  Add-Content -LiteralPath $receiptPath -Value "" -Encoding UTF8
}

$rootAbs = (Resolve-Path -LiteralPath $Root).Path
if (-not (Test-Path -LiteralPath $rootAbs -PathType Container)) {
  _Fail "Root is not a directory: $Root"
}

_EnsureDir $OutRoot

$tsFolder = (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$bundleDir = Join-Path (Resolve-Path -LiteralPath $OutRoot).Path ("{0}-{1}" -f $Node, $tsFolder)
$blobsDir = Join-Path $bundleDir 'BLOBS'
$indexDir = Join-Path $bundleDir 'INDEX'

_EnsureDir $blobsDir
_EnsureDir $indexDir

# Discover files with stable ordering
$allFiles = New-Object System.Collections.Generic.List[System.IO.FileInfo]
foreach ($pattern in $IncludePatterns) {
  Get-ChildItem -LiteralPath $rootAbs -Recurse -File -Filter $pattern -ErrorAction SilentlyContinue |
    ForEach-Object { $allFiles.Add($_) | Out-Null }
}

$files = $allFiles | Sort-Object FullName -Unique

$rows = New-Object System.Collections.Generic.List[string]
$rows.Add('node,source_relpath,bytes,sha256') | Out-Null

$seenBlobs = @{}
$included = 0

foreach ($f in $files) {
  $abs = $f.FullName

  # Relpath anchored to Root
  $rel = [System.IO.Path]::GetRelativePath($rootAbs, $abs)
  $relPosix = _ToPosix $rel

  $sha = _ComputeSha256 $abs
  $bytes = [int64]$f.Length

  $blobPath = Join-Path $blobsDir $sha
  if (-not $seenBlobs.ContainsKey($sha)) {
    # Content-addressed copy (idempotent)
    Copy-Item -LiteralPath $abs -Destination $blobPath -Force
    $seenBlobs[$sha] = $true
  }

  $rows.Add("$Node,$relPosix,$bytes,$sha") | Out-Null
  $included++
}

$filesCsv = Join-Path $indexDir 'FILES.csv'
Set-Content -LiteralPath $filesCsv -Value ($rows -join "`n") -Encoding UTF8 -NoNewline
Add-Content -LiteralPath $filesCsv -Value "" -Encoding UTF8

# Index-level manifest (covers bundle internals except itself)
$manifestLines = New-Object System.Collections.Generic.List[string]
Get-ChildItem -LiteralPath $bundleDir -Recurse -File |
  Where-Object { $_.FullName -ne (Join-Path $indexDir 'MANIFEST_SHA256.txt') } |
  ForEach-Object {
    $rp = _ToPosix ([System.IO.Path]::GetRelativePath($bundleDir, $_.FullName))
    $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
    $manifestLines.Add("$h  $rp") | Out-Null
  }

$manifestLinesSorted = $manifestLines | Sort-Object
$manifestPath = Join-Path $indexDir 'MANIFEST_SHA256.txt'
Set-Content -LiteralPath $manifestPath -Value ($manifestLinesSorted -join "`n") -Encoding UTF8 -NoNewline
Add-Content -LiteralPath $manifestPath -Value "" -Encoding UTF8

# Receipt
$receipt = [PSCustomObject]@{
  schema = 'patent-node-bundle.v1'
  node = $Node
  timestamp_utc = (Get-Date).ToUniversalTime().ToString('o')
  root = _ToPosix $rootAbs
  out_root = _ToPosix (Resolve-Path -LiteralPath $OutRoot).Path
  bundle_dir = _ToPosix $bundleDir
  include_patterns = $IncludePatterns
  files_included = $included
  unique_blobs = $seenBlobs.Keys.Count
}

$receiptPath = Join-Path $indexDir 'RUN_RECEIPT.json'
$receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding UTF8

# Seal key index files
_WriteSeal -targetPath $filesCsv -receiptPath (Join-Path $indexDir 'FILES.csv.sha256.txt')
_WriteSeal -targetPath $manifestPath -receiptPath (Join-Path $indexDir 'MANIFEST_SHA256.txt.sha256.txt')
_WriteSeal -targetPath $receiptPath -receiptPath (Join-Path $indexDir 'RUN_RECEIPT.json.sha256.txt')

Write-Host "OK: node bundle written: $bundleDir" -ForegroundColor Green
Write-Host "OK: files included: $included" -ForegroundColor Green
Write-Host "OK: unique blobs: $($seenBlobs.Keys.Count)" -ForegroundColor Green
