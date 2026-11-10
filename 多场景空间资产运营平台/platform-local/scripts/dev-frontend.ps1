$ErrorActionPreference = 'Stop'
$frontend = Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'platform-frontend'
$env:VITE_API_TARGET = 'http://127.0.0.1:8091'
Push-Location $frontend
try { npm run dev } finally { Pop-Location }
