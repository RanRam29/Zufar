$ErrorActionPreference = 'Stop'
Write-Host '=== Boot ==='
# Move to repo root
Set-Location (Split-Path $MyInvocation.MyCommand.Path) | Out-Null
Set-Location ..

# Activate venv if exists
if (Test-Path ".venv\Scripts\Activate.ps1") {
    . ".\.venv\Scripts\Activate.ps1"
}

# Load .env (simple parser: KEY=VALUE per line)
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match "^\s*#") { return }
        if ($_ -match "^\s*$") { return }
        $kv = $_ -split '=', 2
        if ($kv.Length -eq 2) { [System.Environment]::SetEnvironmentVariable($kv[0], $kv[1]) }
    }
}

Write-Host '=== Running Alembic migrations ==='
python -m alembic upgrade head

Write-Host '=== Starting API ==='
$port = if ($env:PORT) { $env:PORT } else { 8000 }
uvicorn backend.app:app --host 0.0.0.0 --port $port
