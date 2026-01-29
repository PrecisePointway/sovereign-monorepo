<#
.SYNOPSIS
  Deterministically merge patent node bundles into a closeout pack.

.DESCRIPTION
  Reads node bundles under -InRoot (typically .../NODE_BUNDLES) and writes a merged pack under -OutRoot.

  Output layout (under OutRoot):
    BLOBS/<sha256>
    INDEX/BUNDLES.csv
    INDEX/NODES.csv
    FILES.csv
    README_PACK.md
    MANIFEST_SHA256.txt

  Plus *.sha256.txt receipts for the key pack files.

.PARAMETER InRoot
  Root containing one or more node bundle folders (<Node>-<timestampZ>).

.PARAMETER OutRoot
  Pack root directory (sibling of NODE_BUNDLES).
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string]$InRoot,

  [Parameter(Mandatory = $true)]
  [string]$OutRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function _ToPosix([string]$p) {
  return ($p -replace '\\', '/').Trim()
}

function _Fail([string]$msg) {
  throw "PATENT_MERGE_FAIL: $msg"
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
    # best-effort
  }

  Set-Content -LiteralPath $receiptPath -Value ($lines -join "`n") -Encoding UTF8 -NoNewline
  Add-Content -LiteralPath $receiptPath -Value "" -Encoding UTF8
}

$inAbs = (Resolve-Path -LiteralPath $InRoot).Path
if (-not (Test-Path -LiteralPath $inAbs -PathType Container)) {
  _Fail "InRoot is not a directory: $InRoot"
}

$packAbs = (Resolve-Path -LiteralPath $OutRoot -ErrorAction SilentlyContinue)?.Path
if (-not $packAbs) {
  _EnsureDir $OutRoot
  $packAbs = (Resolve-Path -LiteralPath $OutRoot).Path
}

$blobsDir = Join-Path $packAbs 'BLOBS'
$indexDir = Join-Path $packAbs 'INDEX'
_EnsureDir $blobsDir
_EnsureDir $indexDir

$bundleDirs = Get-ChildItem -LiteralPath $inAbs -Directory | Sort-Object Name
if (-not $bundleDirs -or $bundleDirs.Count -eq 0) {
  _Fail "No node bundles found under: $inAbs"
}

# Read all bundle FILES.csv from INDEX
$entries = New-Object System.Collections.Generic.List[object]
$bundleRows = New-Object System.Collections.Generic.List[string]
$bundleRows.Add('bundle_dir,node,files_csv_path,manifest_path') | Out-Null

foreach ($b in $bundleDirs) {
  $idx = Join-Path $b.FullName 'INDEX'
  $filesCsv = Join-Path $idx 'FILES.csv'
  $manifest = Join-Path $idx 'MANIFEST_SHA256.txt'

  if (-not (Test-Path -LiteralPath $filesCsv -PathType Leaf)) {
    _Fail "Bundle missing INDEX/FILES.csv: $($b.FullName)"
  }
  if (-not (Test-Path -LiteralPath (Join-Path $b.FullName 'BLOBS') -PathType Container)) {
    _Fail "Bundle missing BLOBS/: $($b.FullName)"
  }

  # Infer node from bundle dir name prefix <node>-<timestampZ>
  $node = ($b.Name -split '-', 2)[0]

  $bundleRows.Add("$(_ToPosix $b.FullName),$node,$(_ToPosix $filesCsv),$(_ToPosix $manifest)") | Out-Null

  $lines = Get-Content -LiteralPath $filesCsv -ErrorAction Stop
  if (-not $lines -or $lines.Count -lt 2) { continue }

  foreach ($line in $lines | Select-Object -Skip 1) {
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    $parts = $line -split ',', 4
    if ($parts.Count -lt 4) { _Fail "Bad CSV line in ${filesCsv}: $line" }
    $entries.Add([PSCustomObject]@{
      bundle = $b.Name
      node = $parts[0]
      source_relpath = $parts[1]
      bytes = [int64]$parts[2]
      sha256 = $parts[3]
    }) | Out-Null
  }
}

if ($entries.Count -eq 0) {
  _Fail "No entries found in any bundle INDEX/FILES.csv under: $inAbs"
}

# Copy blobs into merged BLOBS/ (dedupe by sha256)
$blobSet = @{}
foreach ($e in ($entries | Sort-Object sha256 -Unique)) {
  $sha = [string]$e.sha256
  if ($sha -notmatch '^[0-9a-f]{64}$') { _Fail "Invalid sha256: $sha" }

  if ($blobSet.ContainsKey($sha)) { continue }

  # locate the blob within any bundle
  $src = $null
  foreach ($b in $bundleDirs) {
    $p = Join-Path (Join-Path $b.FullName 'BLOBS') $sha
    if (Test-Path -LiteralPath $p -PathType Leaf) { $src = $p; break }
  }
  if (-not $src) { _Fail "Blob missing in bundles for sha256: $sha" }

  $dst = Join-Path $blobsDir $sha
  if (-not (Test-Path -LiteralPath $dst -PathType Leaf)) {
    Copy-Item -LiteralPath $src -Destination $dst -Force
  }
  $blobSet[$sha] = $true
}

# Write pack FILES.csv (stable ordering)
$filesOut = Join-Path $packAbs 'FILES.csv'
$rows = New-Object System.Collections.Generic.List[string]
$rows.Add('bundle,node,source_relpath,bytes,sha256') | Out-Null
foreach ($e in ($entries | Sort-Object bundle, node, source_relpath, sha256)) {
  $rows.Add("$($e.bundle),$($e.node),$($e.source_relpath),$($e.bytes),$($e.sha256)") | Out-Null
}
Set-Content -LiteralPath $filesOut -Value ($rows -join "`n") -Encoding UTF8 -NoNewline
Add-Content -LiteralPath $filesOut -Value "" -Encoding UTF8

# Bundle + node summaries
$bundlesCsv = Join-Path $indexDir 'BUNDLES.csv'
Set-Content -LiteralPath $bundlesCsv -Value ($bundleRows -join "`n") -Encoding UTF8 -NoNewline
Add-Content -LiteralPath $bundlesCsv -Value "" -Encoding UTF8

$nodesCsv = Join-Path $indexDir 'NODES.csv'
$nodeRows = New-Object System.Collections.Generic.List[string]
$nodeRows.Add('node,entries,unique_blobs') | Out-Null
foreach ($g in ($entries | Group-Object node | Sort-Object Name)) {
  $uniq = ($g.Group | Select-Object -ExpandProperty sha256 | Sort-Object -Unique).Count
  $nodeRows.Add("$($g.Name),$($g.Count),$uniq") | Out-Null
}
Set-Content -LiteralPath $nodesCsv -Value ($nodeRows -join "`n") -Encoding UTF8 -NoNewline
Add-Content -LiteralPath $nodesCsv -Value "" -Encoding UTF8

# README
$readme = Join-Path $packAbs 'README_PACK.md'
$readmeLines = @(
  "# Patent Closeout Pack",
  "",
  "Generated: $((Get-Date).ToUniversalTime().ToString('o'))",
  "",
  "Contents:",
  "- NODE_BUNDLES/: raw node bundles (immutable inputs)",
  "- BLOBS/: merged content-addressed blobs (sha256 filenames)",
  "- FILES.csv: merged index of discovered files across bundles",
  "- INDEX/: bundle and node summaries",
  "- MANIFEST_SHA256.txt: sha256 manifest of pack files",
  ""
)
Set-Content -LiteralPath $readme -Value ($readmeLines -join "`n") -Encoding UTF8 -NoNewline
Add-Content -LiteralPath $readme -Value "" -Encoding UTF8

# Pack manifest (covers everything under pack except itself)
$manifestPath = Join-Path $packAbs 'MANIFEST_SHA256.txt'
$manifestLines = New-Object System.Collections.Generic.List[string]
Get-ChildItem -LiteralPath $packAbs -Recurse -File |
  Where-Object { $_.FullName -ne $manifestPath } |
  ForEach-Object {
    $rp = _ToPosix ([System.IO.Path]::GetRelativePath($packAbs, $_.FullName))
    $h = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash.ToLowerInvariant()
    $manifestLines.Add("$h  $rp") | Out-Null
  }

$manifestSorted = $manifestLines | Sort-Object
Set-Content -LiteralPath $manifestPath -Value ($manifestSorted -join "`n") -Encoding UTF8 -NoNewline
Add-Content -LiteralPath $manifestPath -Value "" -Encoding UTF8

# Seal key pack files
_WriteSeal -targetPath $filesOut -receiptPath (Join-Path $packAbs 'FILES.csv.sha256.txt')
_WriteSeal -targetPath $readme -receiptPath (Join-Path $packAbs 'README_PACK.md.sha256.txt')
_WriteSeal -targetPath $manifestPath -receiptPath (Join-Path $packAbs 'MANIFEST_SHA256.txt.sha256.txt')
_WriteSeal -targetPath $bundlesCsv -receiptPath (Join-Path $indexDir 'BUNDLES.csv.sha256.txt')
_WriteSeal -targetPath $nodesCsv -receiptPath (Join-Path $indexDir 'NODES.csv.sha256.txt')

Write-Host "OK: merged pack written: $packAbs" -ForegroundColor Green
Write-Host "OK: bundles: $($bundleDirs.Count)" -ForegroundColor Green
Write-Host "OK: entries:  $($entries.Count)" -ForegroundColor Green
Write-Host "OK: blobs:    $($blobSet.Keys.Count)" -ForegroundColor Green
