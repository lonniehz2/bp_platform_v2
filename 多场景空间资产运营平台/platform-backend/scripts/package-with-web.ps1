param(
    [string]$JdkHome = "D:\Work\tools\jdk-17.0.20.1+1",
    [string]$Maven = "D:\Work\tools\apache-maven-3.9.9\bin\mvn.cmd",
    [string]$Settings = "D:\Work\tools\m2-settings.xml"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$frontend = Join-Path $root "platform-frontend"
$backend = Join-Path $root "platform-backend"
$static = Join-Path $backend "src\main\resources\static"

Push-Location $frontend
try {
    node node_modules\vite\bin\vite.js build
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Standard build failed; retrying without esbuild/minify'
        node node_modules\vite\bin\vite.js build --config vite.config.noesbuild.js
        if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed' }
    }
} finally {
    Pop-Location
}

if (Test-Path $static) { Remove-Item $static -Recurse -Force }
New-Item -ItemType Directory -Path $static | Out-Null
Copy-Item (Join-Path $frontend "dist\*") $static -Recurse

Push-Location $backend
try {
    $env:JAVA_HOME = $JdkHome
    & $Maven -B -q -DskipTests package -s $Settings
    if ($LASTEXITCODE -ne 0) { throw "Maven build failed: $LASTEXITCODE" }
} finally {
    Pop-Location
}


Add-Type -AssemblyName System.IO.Compression.FileSystem
$jarPath = Join-Path $backend "target\multi-scene-platform.jar"
$zip = [System.IO.Compression.ZipFile]::OpenRead($jarPath)
try {
    $hasLogback = $zip.Entries | Where-Object { $_.FullName -like 'BOOT-INF/lib/logback-classic-*' }
    if (-not $hasLogback) { throw "Invalid jar: missing BOOT-INF/lib/logback-classic (not a Spring Boot fat jar)" }
} finally { $zip.Dispose() }

Write-Host "Built: $backend\target\multi-scene-platform.jar"
