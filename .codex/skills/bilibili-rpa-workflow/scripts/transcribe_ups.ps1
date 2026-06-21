# Batch transcribe Bilibili videos from the queue/MySQL export.
# Usage: .\transcribe_ups.ps1 [-SkipSync] [-DryRun] [-IncludeDone] [-Mids "403375255","15741969"]
param(
    [switch]$SkipSync,
    [switch]$DryRun,
    [switch]$IncludeDone,
    [string[]]$Mids
)

$ErrorActionPreference = "Stop"
$Root = "X:\RPA"
$Py = "E:\anaconda\envs\wechatapp\python.exe"
$Script = Join-Path $Root "bili2text\batch_process_ups.py"

$scriptArgs = @($Script)
if ($SkipSync)     { $scriptArgs += "--skip-sync" }
if ($DryRun)       { $scriptArgs += "--dry-run" }
if ($IncludeDone)  { $scriptArgs += "--include-done" }
if ($Mids)         { $scriptArgs += "--mids"; $scriptArgs += $Mids }

Write-Host "[TRANSCRIBE] $Py $scriptArgs" -ForegroundColor Cyan
& $Py @scriptArgs
