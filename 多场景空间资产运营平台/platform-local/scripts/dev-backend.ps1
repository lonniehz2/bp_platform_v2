param(
    [string]$Jar = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) 'platform-backend/target/multi-scene-platform.jar'),
    [int]$Port = 8091,
    [int]$DbPort = 3306,
    [string]$DbPassword = 'local123'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $Jar)) { throw "未找到 jar：$Jar，请先执行 platform-backend/scripts/package-with-web.ps1" }
$env:SPRING_PROFILES_ACTIVE = 'local'
$env:SERVER_PORT = "$Port"
$env:DB_URL = "jdbc:mysql://127.0.0.1:$DbPort/bp_platform_v2?useUnicode=true&characterEncoding=utf8&serverTimezone=Asia/Shanghai&allowPublicKeyRetrieval=true&useSSL=false"
$env:DB_USER = 'root'
$env:DB_PASSWORD = $DbPassword
Write-Host "启动本地后端：http://127.0.0.1:$Port（DB 127.0.0.1:$DbPort）"
java -Xms512m -Xmx1024m -Dfile.encoding=UTF-8 -jar $Jar
