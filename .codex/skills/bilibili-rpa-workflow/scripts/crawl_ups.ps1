# Crawl all unfinished UP spaces from bili_up_queue.xlsx.
# Usage: .\crawl_ups.ps1 [-Attach] [-KeepOpen] [-NoWriteDb]
param(
    [switch]$Attach,
    [switch]$KeepOpen,
    [switch]$NoWriteDb
)

$ErrorActionPreference = "Stop"
$Root = "X:\RPA"
$Py = "E:\anaconda\envs\wechatapp\python.exe"
$Script = Join-Path $Root "src\tools_browser\bilibili_browser_roll_runner.py"

$scriptArgs = @($Script, "--only-unfinished")
if ($Attach)    { $scriptArgs += "--attach" }
if ($KeepOpen)  { $scriptArgs += "--keep-open" }
if ($NoWriteDb) { $scriptArgs += "--no-write-db" }

Write-Host "[CRAWL] $Py $scriptArgs" -ForegroundColor Cyan
& $Py @scriptArgs
