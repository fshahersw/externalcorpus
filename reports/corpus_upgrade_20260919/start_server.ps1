$ErrorActionPreference = 'Stop'
$taskRoot = 'C:\Users\firas\Downloads\SCRAPE'
$taskPython = 'C:\Users\firas\AppData\Local\Programs\Python\Python311\python.exe'
$taskServer = Join-Path $taskRoot 'delivery\archive-directory\server.py'
$taskReport = Join-Path $taskRoot 'reports\corpus_upgrade_20260919'
$taskStateFile = Join-Path $taskRoot 'delivery\archive-directory\server.json'
$taskState = Get-Content $taskStateFile -Raw | ConvertFrom-Json
$taskProcess = Get-CimInstance Win32_Process -Filter "ProcessId = $($taskState.pid)"
$taskCommand = if ($taskProcess) { ($taskProcess.CommandLine -replace '/', '\') } else { '' }
$taskIsOurs = $taskProcess -and $taskCommand.Contains($taskServer) -and $taskCommand.Contains('--serve')
$taskListening = $null -ne (Get-NetTCPConnection -LocalPort 8769 -State Listen -ErrorAction SilentlyContinue)
if ($taskIsOurs -and $taskListening) { [pscustomobject]@{ action = 'already_running'; pid = $taskProcess.ProcessId; url = 'http://127.0.0.1:8769' } | ConvertTo-Json; exit 0 }
if ($taskIsOurs -and -not $taskListening) { Stop-Process -Id $taskProcess.ProcessId; Start-Sleep -Milliseconds 500 }
if ($taskListening -and -not $taskIsOurs) { throw 'Port 8769 is held by a process that is not the verified archive server; nothing started.' }
$taskStamp = Get-Date -Format 'yyyyMMddTHHmmss'
$taskArguments = '"' + $taskServer + '" --serve'
$taskNew = Start-Process -FilePath $taskPython -ArgumentList $taskArguments -WorkingDirectory $taskRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $taskReport ($taskStamp + '.server.stdout.log')) -RedirectStandardError (Join-Path $taskReport ($taskStamp + '.server.stderr.log')) -PassThru
$taskOnline = $false
for ($i = 0; $i -lt 60; $i++) { Start-Sleep -Milliseconds 500; try { $s = Invoke-RestMethod -Uri 'http://127.0.0.1:8769/api/summary' -TimeoutSec 3; if ($s.published) { $taskOnline = $true; break } } catch { } }
[pscustomobject]@{ action = 'started'; old_pid = $taskState.pid; new_pid = $taskNew.Id; online = $taskOnline; url = 'http://127.0.0.1:8769'; started_at = (Get-Date).ToUniversalTime().ToString('o') } | ConvertTo-Json
