<#
.SYNOPSIS
    Sovereign Sanctuary Elite - Multi-Source Discovery Script
    
.DESCRIPTION
    Comprehensive discovery script for OneDrive, local drives, and NAS.
    Scans for AI-related files and creates legal search index.
    
.PARAMETER Targets
    Comma-separated list of paths to scan (default: OneDrive, Documents, NAS)
    
.PARAMETER OutputPath
    Path for output files (default: Desktop\SovereignDiscovery)
    
.PARAMETER IncludeNAS
    Include NAS paths in scan
    
.PARAMETER NASPath
    UNC path to NAS (e.g., \\NASNAME\share)

.EXAMPLE
    .\discovery_elite.ps1 -IncludeNAS -NASPath "\\MYNAS\data"
    
.EXAMPLE
    .\discovery_elite.ps1 -Targets "C:\Projects,D:\Archive"

.NOTES
    Version: 2.0.0
    Author: Manus AI for Architect
#>

param(
    [string]$Targets = "",
    [string]$OutputPath = "$env:USERPROFILE\Desktop\SovereignDiscovery",
    [switch]$IncludeNAS,
    [string]$NASPath = "",
    [switch]$Quick
)

# ═══════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════

$LegalKeywords = @(
    "sovereign", "sanctuary", "fortress", "mycelial", "swarm",
    "agent", "llm", "gpt", "model", "truth", "evidence", "ledger",
    "governance", "policy", "compliance", "contract", "nda",
    "trading", "capital", "allocator", "proof", "manifest"
)

$FileExtensions = @(
    "*.py", "*.ts", "*.js", "*.md", "*.json", "*.yaml", "*.yml",
    "*.txt", "*.pdf", "*.docx", "*.doc", "*.xlsx", "*.csv"
)

$ExcludePaths = @(
    "*\node_modules\*", "*\.git\*", "*\__pycache__\*",
    "*\AppData\*", "*\Windows\*", "*\Program Files*"
)

# ═══════════════════════════════════════════════════════════════════
# FUNCTIONS
# ═══════════════════════════════════════════════════════════════════

function Write-Banner {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  SOVEREIGN SANCTUARY ELITE - DISCOVERY SCANNER v2.0.0" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
}

function Get-DefaultTargets {
    $targets = @()
    
    # OneDrive paths
    $oneDrivePaths = @(
        "$env:USERPROFILE\OneDrive",
        "$env:USERPROFILE\OneDrive - Personal",
        "$env:OneDrive",
        "$env:OneDriveConsumer",
        "$env:OneDriveCommercial"
    )
    
    foreach ($path in $oneDrivePaths) {
        if ($path -and (Test-Path $path)) {
            $targets += $path
            Write-Host "  [+] OneDrive: $path" -ForegroundColor Green
        }
    }
    
    # Documents
    $docsPath = [Environment]::GetFolderPath("MyDocuments")
    if (Test-Path $docsPath) {
        $targets += $docsPath
        Write-Host "  [+] Documents: $docsPath" -ForegroundColor Green
    }
    
    # Desktop
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    if (Test-Path $desktopPath) {
        $targets += $desktopPath
        Write-Host "  [+] Desktop: $desktopPath" -ForegroundColor Green
    }
    
    # Downloads
    $downloadsPath = "$env:USERPROFILE\Downloads"
    if (Test-Path $downloadsPath) {
        $targets += $downloadsPath
        Write-Host "  [+] Downloads: $downloadsPath" -ForegroundColor Green
    }
    
    return $targets
}

function Test-LegalRelevance {
    param([string]$FilePath)
    
    $pathLower = $FilePath.ToLower()
    foreach ($keyword in $LegalKeywords) {
        if ($pathLower -match $keyword) {
            return $true
        }
    }
    return $false
}

function Get-FileCategory {
    param([string]$FilePath)
    
    $pathLower = $FilePath.ToLower()
    
    if ($pathLower -match "evidence|ledger|proof|manifest") { return "EVIDENCE" }
    if ($pathLower -match "contract|nda|agreement|legal") { return "LEGAL" }
    if ($pathLower -match "governance|policy|compliance") { return "GOVERNANCE" }
    if ($pathLower -match "sovereign|fortress|sanctuary") { return "CORE_SYSTEM" }
    if ($pathLower -match "agent|swarm|llm|gpt|model") { return "AI_AGENT" }
    if ($pathLower -match "trading|capital|allocator") { return "TRADING" }
    if ($pathLower -match "config|settings") { return "CONFIG" }
    if ($pathLower -match "\.md$|\.pdf$|\.docx?$") { return "DOCUMENTATION" }
    
    return "OTHER"
}

function Get-FilePriority {
    param([string]$Category)
    
    switch ($Category) {
        "EVIDENCE" { return 1 }
        "LEGAL" { return 1 }
        "GOVERNANCE" { return 2 }
        "CORE_SYSTEM" { return 3 }
        "AI_AGENT" { return 4 }
        "TRADING" { return 4 }
        "CONFIG" { return 5 }
        "DOCUMENTATION" { return 6 }
        default { return 9 }
    }
}

function Scan-Directory {
    param(
        [string]$Path,
        [ref]$Results
    )
    
    Write-Host "  Scanning: $Path" -ForegroundColor Yellow
    
    try {
        $files = Get-ChildItem -Path $Path -Recurse -File -Include $FileExtensions -ErrorAction SilentlyContinue |
            Where-Object { 
                $exclude = $false
                foreach ($pattern in $ExcludePaths) {
                    if ($_.FullName -like $pattern) {
                        $exclude = $true
                        break
                    }
                }
                -not $exclude
            }
        
        $count = 0
        foreach ($file in $files) {
            $isRelevant = Test-LegalRelevance -FilePath $file.FullName
            
            if ($isRelevant -or -not $Quick) {
                $category = Get-FileCategory -FilePath $file.FullName
                $priority = Get-FilePriority -Category $category
                
                $fileInfo = @{
                    Path = $file.FullName
                    Name = $file.Name
                    Extension = $file.Extension
                    Size = $file.Length
                    Modified = $file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
                    Category = $category
                    Priority = $priority
                    LegalRelevant = $isRelevant
                }
                
                $Results.Value += $fileInfo
                $count++
            }
        }
        
        Write-Host "    Found: $count files" -ForegroundColor Gray
    }
    catch {
        Write-Host "    Error scanning: $_" -ForegroundColor Red
    }
}

function Export-Results {
    param(
        [array]$Results,
        [string]$OutputPath
    )
    
    # Create output directory
    if (-not (Test-Path $OutputPath)) {
        New-Item -ItemType Directory -Path $OutputPath -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $hostname = $env:COMPUTERNAME
    
    # Export JSON index
    $jsonPath = Join-Path $OutputPath "discovery_${hostname}_${timestamp}.json"
    $index = @{
        metadata = @{
            hostname = $hostname
            scanned_at = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ssZ")
            total_files = $Results.Count
            legal_relevant = ($Results | Where-Object { $_.LegalRelevant }).Count
        }
        files = $Results
        summary = @{
            by_category = $Results | Group-Object Category | ForEach-Object { @{ $_.Name = $_.Count } }
            by_priority = $Results | Group-Object Priority | ForEach-Object { @{ $_.Name = $_.Count } }
            by_extension = $Results | Group-Object Extension | ForEach-Object { @{ $_.Name = $_.Count } }
        }
    }
    
    $index | ConvertTo-Json -Depth 10 | Out-File -FilePath $jsonPath -Encoding UTF8
    Write-Host "  JSON Index: $jsonPath" -ForegroundColor Green
    
    # Export CSV for Excel
    $csvPath = Join-Path $OutputPath "discovery_${hostname}_${timestamp}.csv"
    $Results | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8
    Write-Host "  CSV Export: $csvPath" -ForegroundColor Green
    
    # Export priority 1 files list
    $priorityPath = Join-Path $OutputPath "priority1_${hostname}_${timestamp}.txt"
    $Results | Where-Object { $_.Priority -eq 1 } | ForEach-Object { $_.Path } | Out-File -FilePath $priorityPath -Encoding UTF8
    Write-Host "  Priority 1: $priorityPath" -ForegroundColor Green
    
    return $jsonPath
}

# ═══════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════

Write-Banner

Write-Host "Initializing discovery targets..." -ForegroundColor Cyan

# Build target list
$scanTargets = @()

if ($Targets) {
    $scanTargets = $Targets -split ","
    foreach ($t in $scanTargets) {
        Write-Host "  [+] Custom: $t" -ForegroundColor Green
    }
} else {
    $scanTargets = Get-DefaultTargets
}

# Add NAS if specified
if ($IncludeNAS -and $NASPath) {
    if (Test-Path $NASPath) {
        $scanTargets += $NASPath
        Write-Host "  [+] NAS: $NASPath" -ForegroundColor Green
    } else {
        Write-Host "  [!] NAS not accessible: $NASPath" -ForegroundColor Yellow
    }
}

if ($scanTargets.Count -eq 0) {
    Write-Host "No valid targets found!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting scan..." -ForegroundColor Cyan
Write-Host ""

$allResults = @()

foreach ($target in $scanTargets) {
    if (Test-Path $target) {
        Scan-Directory -Path $target -Results ([ref]$allResults)
    }
}

Write-Host ""
Write-Host "Exporting results..." -ForegroundColor Cyan

$outputFile = Export-Results -Results $allResults -OutputPath $OutputPath

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  DISCOVERY COMPLETE" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Total Files Scanned: $($allResults.Count)" -ForegroundColor White
Write-Host "  Legal Relevant:      $(($allResults | Where-Object { $_.LegalRelevant }).Count)" -ForegroundColor White
Write-Host "  Priority 1 Files:    $(($allResults | Where-Object { $_.Priority -eq 1 }).Count)" -ForegroundColor Yellow
Write-Host ""
Write-Host "  Output Directory: $OutputPath" -ForegroundColor Green
Write-Host ""

# Category summary
Write-Host "Category Summary:" -ForegroundColor Cyan
$allResults | Group-Object Category | Sort-Object Count -Descending | ForEach-Object {
    Write-Host "  $($_.Name): $($_.Count)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Next: Copy $outputFile to your central index location" -ForegroundColor Yellow
Write-Host ""
