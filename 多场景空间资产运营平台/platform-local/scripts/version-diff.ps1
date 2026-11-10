$ErrorActionPreference = 'Stop'
$base = Split-Path -Parent $PSScriptRoot
$root = Split-Path -Parent $base
$state = Get-Content (Join-Path $base 'remote-version.json') -Raw | ConvertFrom-Json
Write-Host "远程最后部署: $($state.remoteCommit)  $($state.remoteDeployedAt)"
Write-Host "远程验证: $($state.verified)"
Write-Host ""
Write-Host "运行时待部署差异（frontend/backend/sql）："
$range = "{0}..HEAD" -f $state.remoteCommit
git -C $root log --oneline $range -- platform-frontend platform-backend platform-sql
Write-Host ""
Write-Host "差异统计："
git -C $root diff --stat $range -- platform-frontend platform-backend platform-sql
