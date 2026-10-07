# Run elevated once. Access is limited to the local subnet without changing network profiles.
$ErrorActionPreference = 'Stop'
$servicePort = 8000
$portLine = Get-Content -LiteralPath (Join-Path $PSScriptRoot '.env') | Where-Object { $_ -match '^LAYA_PORT=' } | Select-Object -First 1
if ($portLine) { $servicePort = [int]($portLine.Split('=',2)[1]) }
$pythonPath = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
$ruleName = 'Laya Local GPU API'
Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $servicePort -Program $pythonPath -RemoteAddress LocalSubnet -Profile Any | Out-Null
Write-Host "Allowed TCP $servicePort from the local subnet only."
