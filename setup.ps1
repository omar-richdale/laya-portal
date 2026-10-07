# Install into this project's environment; global Python packages are untouched.
param([switch]$SkipModels)
$ErrorActionPreference = 'Stop'
Push-Location $PSScriptRoot
try {
    if ((Get-PSDrive -Name ([IO.Path]::GetPathRoot($PSScriptRoot).Substring(0,1))).Free -lt 10GB) {
        throw 'Setup requires at least 10 GiB of free disk space.'
    }
    & uv sync --locked --python 3.12
    if ($LASTEXITCODE -ne 0) { throw 'Python environment installation failed.' }
    & '.\.venv\Scripts\python.exe' -c 'import torch; assert torch.cuda.is_available(), "CUDA is unavailable"; print(torch.__version__, torch.cuda.get_device_name(0))'
    if ($LASTEXITCODE -ne 0) { throw 'CUDA verification failed.' }
    if (-not $SkipModels) {
        & '.\.venv\Scripts\python.exe' '.\scripts\bootstrap.py'
        if ($LASTEXITCODE -ne 0) { throw 'Model download failed.' }
    }
    Push-Location frontend
    try {
        & npm.cmd ci
        if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
        & npm.cmd run build
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
    } finally { Pop-Location }
    Write-Host 'Setup complete. Run .\start.ps1. Your API key is stored in .env.'
} finally { Pop-Location }
