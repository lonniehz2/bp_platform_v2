param([string]$ComposeFile = (Join-Path (Split-Path -Parent $PSScriptRoot) 'docker-compose.yml'))
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$sql = Get-Content -Raw (Join-Path $root 'init/00-run-all.sql')
$sql | docker compose -f $ComposeFile exec -T mysql sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"'
if ($LASTEXITCODE -ne 0) { throw '本地 SQL 初始化失败' }
Write-Host '本地 SQL 初始化完成'
