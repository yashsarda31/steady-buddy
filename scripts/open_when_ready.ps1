# Open only after the server is ready, without holding up its startup.
$taskScript = @'
for ($taskTry = 0; $taskTry -lt 60; $taskTry++) {
    try {
        $taskResponse = Invoke-WebRequest -Uri 'http://localhost:8765/health' -UseBasicParsing -TimeoutSec 2
        if ($taskResponse.StatusCode -eq 200) {
            Start-Process 'http://localhost:8765/'
            exit
        }
    } catch { }
    Start-Sleep -Seconds 1
}
'@
$taskEncoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($taskScript))
Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -ArgumentList @('-NoProfile', '-EncodedCommand', $taskEncoded)
