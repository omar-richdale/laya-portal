# Check the recorded executable and workspace before terminating a project worker.
$ErrorActionPreference = 'Stop'
$recordPath = Join-Path $PSScriptRoot 'data\service.json'
if (-not (Test-Path -LiteralPath $recordPath)) { Write-Host 'No managed Laya process is recorded.'; return }
$record = Get-Content -LiteralPath $recordPath | ConvertFrom-Json
$worker = Get-CimInstance Win32_Process -Filter "ProcessId = $($record.pid)"
if ($worker) {
    if ($worker.ExecutablePath -ne $record.python -or $record.workspace -ne $PSScriptRoot -or $worker.CommandLine -notmatch '-m laya_portal') {
        throw 'The PID no longer belongs to this project. Refusing to stop it.'
    }
    $settings = @{}
    Get-Content -LiteralPath (Join-Path $PSScriptRoot '.env') | Where-Object { $_ -match '^LAYA_(API_KEY|PORT)=' } | ForEach-Object {
        $parts = $_.Split('=',2); $settings[$parts[0]] = $parts[1]
    }
    $servicePort = if ($settings['LAYA_PORT']) { [int]$settings['LAYA_PORT'] } else { 8000 }
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:$servicePort/api/v1/shutdown" -Method Post -ContentType 'application/json' -Body '{}' -Headers @{ Authorization = "Bearer $($settings['LAYA_API_KEY'])" } -TimeoutSec 10 | Out-Null
        Wait-Process -Id $record.pid -Timeout 60 -ErrorAction Stop
    } catch {
        throw 'Graceful shutdown did not finish. Inspect logs and the recorded PID before stopping the process manually.'
    }
}
Remove-Item -LiteralPath $recordPath
Write-Host 'Laya stopped; Windows releases its GPU allocations.'
