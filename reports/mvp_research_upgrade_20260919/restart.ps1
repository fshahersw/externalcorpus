$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\firas\Downloads\SCRAPE'
$taskPython = 'C:\Users\firas\AppData\Local\Programs\Python\Python311\python.exe'
$taskServer = Join-Path $taskRoot 'delivery\archive-directory\server.py'
$taskReport = Join-Path $taskRoot 'reports\mvp_research_upgrade_20260919'
$taskState = Get-Content (Join-Path $taskRoot 'delivery\archive-directory\server.json') -Raw | ConvertFrom-Json
$taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($taskState.pid)"
if (-not $taskProcess -or $taskProcess.ExecutablePath -ne $taskPython -or -not $taskProcess.CommandLine.Contains($taskServer) -or -not $taskProcess.CommandLine.Contains('--serve')) {
    throw 'The recorded process is not the verified local archive server; nothing stopped.'
}
$taskStamp = Get-Date -Format 'yyyyMMddTHHmmss'
Stop-Process -Id $taskProcess.ProcessId
$taskArguments = '"' + $taskServer + '" --serve'
$taskNewServer = Start-Process -FilePath $taskPython -ArgumentList $taskArguments -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskReport ($taskStamp+'.stdout.log')) -RedirectStandardError (Join-Path $taskReport ($taskStamp+'.stderr.log')) -PassThru
[pscustomobject]@{old_pid=$taskProcess.ProcessId;new_pid=$taskNewServer.Id;url='http://127.0.0.1:8769';main_catalog_rebuilt=$false} | ConvertTo-Json | Set-Content (Join-Path $taskReport 'deployment.json')
Get-Content (Join-Path $taskReport 'deployment.json')
