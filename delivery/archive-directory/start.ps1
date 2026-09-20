$ErrorActionPreference = 'Stop'
$archivePython = 'C:/Users/firas/AppData/Local/Programs/Python/Python311/python.exe'
$archiveServer = Join-Path $PSScriptRoot 'server.py'
$archiveUrl = 'http://127.0.0.1:8769/'
$archiveOnline = $false
try {
    $archiveStatus = Invoke-RestMethod -Uri ($archiveUrl + 'api/summary') -TimeoutSec 3
    $archiveOnline = [bool]$archiveStatus.published
} catch { }
if (-not $archiveOnline) {
    Start-Process -FilePath $archivePython -ArgumentList @(('"' + $archiveServer + '"'), '--serve') -WindowStyle Hidden -WorkingDirectory $PSScriptRoot
    for ($archiveAttempt = 0; $archiveAttempt -lt 20; $archiveAttempt++) {
        Start-Sleep -Milliseconds 300
        try {
            $archiveStatus = Invoke-RestMethod -Uri ($archiveUrl + 'api/summary') -TimeoutSec 2
            if ($archiveStatus.published) { $archiveOnline = $true; break }
        } catch { }
    }
}
if ($archiveOnline) { Start-Process $archiveUrl } else { throw 'Local directory did not start. See README.md.' }
