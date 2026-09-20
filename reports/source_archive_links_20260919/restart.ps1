$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\firas\Downloads\SCRAPE'
$taskPython = 'C:\Users\firas\AppData\Local\Programs\Python\Python311\python.exe'
$taskServer = Join-Path $taskRoot 'delivery\archive-directory\server.py'
$taskReport = Join-Path $taskRoot 'reports\source_archive_links_20260919'
$taskState = Get-Content (Join-Path $taskRoot 'delivery\archive-directory\server.json') -Raw | ConvertFrom-Json
$taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($taskState.pid)"
# Compare with a single separator style: an earlier launcher used forward slashes for the same files.
$taskExecutable = if ($taskProcess) { ($taskProcess.ExecutablePath -replace '/', '\') } else { '' }
$taskCommand = if ($taskProcess) { ($taskProcess.CommandLine -replace '/', '\') } else { '' }
if (-not $taskProcess -or $taskExecutable -ne $taskPython -or -not $taskCommand.Contains($taskServer) -or -not $taskCommand.Contains('--serve')) {
    throw 'The recorded process is not the verified local archive server; nothing stopped.'
}
$taskStamp = Get-Date -Format 'yyyyMMddTHHmmss'
Stop-Process -Id $taskProcess.ProcessId
Start-Sleep -Milliseconds 500
$taskArguments = '"' + $taskServer + '" --serve'
$taskNewServer = Start-Process -FilePath $taskPython -ArgumentList $taskArguments -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskReport ($taskStamp + '.stdout.log')) -RedirectStandardError (Join-Path $taskReport ($taskStamp + '.stderr.log')) -PassThru
$taskOnline = $false
for ($taskAttempt = 0; $taskAttempt -lt 40; $taskAttempt++) {
    Start-Sleep -Milliseconds 500
    try { $taskStatus = Invoke-RestMethod -Uri 'http://127.0.0.1:8769/api/summary' -TimeoutSec 3; if ($taskStatus.published) { $taskOnline = $true; break } } catch { }
}
[pscustomobject]@{ old_pid = $taskProcess.ProcessId; new_pid = $taskNewServer.Id; online = $taskOnline; url = 'http://127.0.0.1:8769'; restarted_at = (Get-Date).ToUniversalTime().ToString('o'); main_catalog_rebuilt = $false; directory_rebuilt = $false } | ConvertTo-Json | Set-Content (Join-Path $taskReport 'deployment.json')
Get-Content (Join-Path $taskReport 'deployment.json')
