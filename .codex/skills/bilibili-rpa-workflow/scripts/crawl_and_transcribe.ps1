# One-shot Bilibili flow: crawl UP spaces, then transcribe videos.
# Usage: .\crawl_and_transcribe.ps1 [-Attach] [-KeepOpen] [-CrawlOnly] [-TextOnly] [-SkipSync] [-DryRun] [-IncludeDone]
# Note: -Mids is supported only with -TextOnly; crawling by mid needs runner queue filtering.
param(
    [switch]$Attach,
    [switch]$KeepOpen,
    [switch]$CrawlOnly,
    [switch]$TextOnly,
    [switch]$SkipSync,
    [switch]$DryRun,
    [switch]$IncludeDone,
    [string[]]$Mids
)

$ErrorActionPreference = "Stop"
$Root = "X:\RPA"
$Py = "E:\anaconda\envs\wechatapp\python.exe"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Mids -and -not $TextOnly) {
    Write-Host "[ERROR] -Mids is currently supported only with -TextOnly. Use transcribe_ups.ps1 -Mids ... or add crawl queue filtering first." -ForegroundColor Red
    exit 2
}

if ($TextOnly) {
    $textOnlyParams = @{}
    if ($SkipSync)    { $textOnlyParams.SkipSync = $true }
    if ($DryRun)      { $textOnlyParams.DryRun = $true }
    if ($IncludeDone) { $textOnlyParams.IncludeDone = $true }
    if ($Mids)        { $textOnlyParams.Mids = $Mids }
    & (Join-Path $ScriptDir "transcribe_ups.ps1") @textOnlyParams
    exit $LASTEXITCODE
}

# Step 1: crawl
$crawlArgs = @()
if ($Attach)   { $crawlArgs += "-Attach" }
if ($KeepOpen) { $crawlArgs += "-KeepOpen" }
& (Join-Path $ScriptDir "crawl_ups.ps1") @crawlArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host "[EXIT] crawl failed" -ForegroundColor Red
    exit $LASTEXITCODE
}

if ($CrawlOnly) {
    Write-Host "[EXIT] CrawlOnly mode" -ForegroundColor Yellow
    exit 0
}

# Step 2: transcribe
$textParams = @{}
if ($SkipSync)    { $textParams.SkipSync = $true }
if ($DryRun)      { $textParams.DryRun = $true }
if ($IncludeDone) { $textParams.IncludeDone = $true }
if ($Mids)        { $textParams.Mids = $Mids }
& (Join-Path $ScriptDir "transcribe_ups.ps1") @textParams
exit $LASTEXITCODE
