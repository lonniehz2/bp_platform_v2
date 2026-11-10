param([int]$Port = 8091)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
& (Join-Path $root 'platform-backend/scripts/verify-core.ps1') -BaseUrl "http://127.0.0.1:$Port"
