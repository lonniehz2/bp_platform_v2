param([string]$ComposeFile = (Join-Path (Split-Path -Parent $PSScriptRoot) 'docker-compose.yml'))
$ErrorActionPreference = 'Stop'
docker compose -f $ComposeFile up -d
if ($LASTEXITCODE -ne 0) { throw 'docker compose up 失败' }
Write-Host '等待 MySQL 就绪...'
for ($i = 0; $i -lt 60; $i++) {
    $state = (docker inspect -f '{{.State.Health.Status}}' bp-mysql-local 2>$null)
    if ($state -eq 'healthy') { Write-Host 'MySQL 已就绪：127.0.0.1:3306 / bp_platform_v2'; exit 0 }
    Start-Sleep -Seconds 2
}
throw 'MySQL 未在 120 秒内就绪，请查看 docker logs bp-mysql-local'
