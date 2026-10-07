# Start a hidden worker owned by this project, then show its connection addresses.
param([switch]$Foreground, [switch]$OpenBrowser)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    $pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath '.env')) { throw 'Run setup.ps1 before starting the service.' }
    if (-not (Test-Path -LiteralPath 'frontend\dist\index.html')) { throw 'Build the frontend using setup.ps1.' }
    $servicePort = 8000
    $portLine = Get-Content -LiteralPath '.env' | Where-Object { $_ -match '^LAYA_PORT=' } | Select-Object -First 1
    if ($portLine) { $servicePort = [int]($portLine.Split('=',2)[1]) }
    if (Get-NetTCPConnection -State Listen -LocalPort $servicePort -ErrorAction SilentlyContinue) {
        throw "Port $servicePort is already in use. Check the existing service before starting another."
    }
    New-Item -ItemType Directory -Force -Path 'data','logs' | Out-Null
    if ($Foreground) {
        & $pythonPath -m laya_portal
        exit $LASTEXITCODE
    }
    $worker = Start-Process -FilePath $pythonPath -ArgumentList @('-m','laya_portal') -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'logs\service.out.log') -RedirectStandardError (Join-Path $PSScriptRoot 'logs\service.err.log')
    @{ pid=$worker.Id; python=$pythonPath; workspace=$PSScriptRoot } | ConvertTo-Json | Set-Content -LiteralPath 'data\service.json'
    $ready = $false
    for ($attempt=0; $attempt -lt 90; $attempt++) {
        if ($worker.HasExited) { throw 'Service exited. Read logs\service.err.log.' }
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:$servicePort/health" -TimeoutSec 1
            if ($health.status -eq 'ok') { $ready = $true; break }
        } catch { }
        Start-Sleep -Seconds 1
    }
    if (-not $ready) { throw 'Startup is taking longer than expected. Read logs\service.err.log.' }
    Write-Host "Portal: http://localhost:$servicePort"
    Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.IPAddress -notmatch '^(127\.|169\.254\.)' } | ForEach-Object { Write-Host "LAN: http://$($_.IPAddress):$servicePort" }
    Write-Host 'API key: .env | Stop: .\stop.ps1 | Logs: logs\service.err.log'
    if ($OpenBrowser) { Start-Process "http://localhost:$servicePort" }
} finally { Pop-Location }
