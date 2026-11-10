param([string]$ComposeFile = (Join-Path (Split-Path -Parent $PSScriptRoot) 'docker-compose.yml'))
$ErrorActionPreference = 'Stop'
Write-Host '警告：将删除本地 MySQL 数据卷并重新初始化。'
docker compose -f $ComposeFile down -v
if ($LASTEXITCODE -ne 0) { throw 'docker compose down 失败' }
& (Join-Path $PSScriptRoot 'db-local-up.ps1') -ComposeFile $ComposeFile
