# 构建 Windows/Linux 可发布包
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$repo = Split-Path -Parent $root
$version = Get-Date -Format 'yyyyMMdd-HHmmss'
$commit = (& git -C $repo rev-parse --short HEAD).Trim()
$out = Join-Path $root 'release'
$stage = Join-Path $env:TEMP "bp-platform-$version"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Force $stage, (Join-Path $stage 'web') | Out-Null

Push-Location (Join-Path $repo 'platform-backend')
try { & mvn -q -DskipTests package } finally { Pop-Location }
Push-Location (Join-Path $repo 'platform-frontend')
try { & npm run build } finally { Pop-Location }

Copy-Item (Join-Path $repo 'platform-backend/target/multi-scene-platform.jar') (Join-Path $stage 'app.jar')
Copy-Item (Join-Path $repo 'platform-frontend/dist/*') (Join-Path $stage 'web') -Recurse
Copy-Item (Join-Path $repo 'platform-sql') (Join-Path $stage 'platform-sql') -Recurse
New-Item -ItemType Directory -Force (Join-Path $stage 'platform-deploy') | Out-Null
foreach ($name in @('README.md','env.example')) { Copy-Item (Join-Path $repo "platform-deploy/$name") (Join-Path $stage 'platform-deploy') }
foreach ($name in @('scripts','nginx','systemd')) { Copy-Item (Join-Path $repo "platform-deploy/$name") (Join-Path $stage 'platform-deploy') -Recurse }
$manifest = @(
  "version=$version",
  "commit=$commit",
  "builtAt=$(Get-Date -Format o)",
  "jarSha256=$((Get-FileHash (Join-Path $stage 'app.jar') -Algorithm SHA256).Hash.ToLower())"
) -join "`n"
Set-Content -Path (Join-Path $stage 'version.txt') -Value $manifest -Encoding UTF8
$zip = Join-Path $out "bp-platform-$version.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
New-Item -ItemType Directory -Force $out | Out-Null
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip
Remove-Item $stage -Recurse -Force
"release=$zip"
"version=$version"
"commit=$commit"
"sha256=$((Get-FileHash $zip -Algorithm SHA256).Hash.ToLower())"
