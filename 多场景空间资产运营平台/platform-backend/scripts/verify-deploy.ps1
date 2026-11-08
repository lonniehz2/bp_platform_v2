param(
    [string]$BaseUrl = "http://192.168.31.11:8090",
    [string]$Username = "admin",
    [string]$Password = "admin123",
    [string]$TenantId = "350600"
)

$ErrorActionPreference = "Stop"

function Json-Get([string]$Path, [string]$Token = "") {
    $headers = @{}
    if ($Token) { $headers["Authorization"] = "Bearer $Token" }
    return Invoke-RestMethod -Uri "$BaseUrl$Path" -Headers $headers -Method Get -TimeoutSec 15
}

Write-Host "== health =="
$health = Json-Get "/actuator/health"
if ($health.status -ne "UP") { throw "health not UP: $($health.status)" }
if ($health.components.db.status -ne "UP") { throw "database not UP" }
Write-Host "health UP / db UP"

Write-Host "== login =="
$body = @{ username = $Username; password = $Password; tenantId = $TenantId } | ConvertTo-Json
$login = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 15
if ($login.code -ne "BP00000") { throw "login failed" }
$token = $login.data.token
Write-Host "login OK"

Write-Host "== permissions =="
$permissions = Json-Get "/api/v1/auth/permissions" $token
if ($permissions.data -notcontains "*") { throw "admin permission missing" }
Write-Host "admin permission OK"

Write-Host "== menus =="
$menus = Json-Get "/api/v1/auth/menus?sceneCode=GUARANTEE" $token
if (@($menus.data).Count -lt 1) { throw "menus empty" }
Write-Host "menus: $(@($menus.data).Count)"

Write-Host "== core pages API =="
$projects = Json-Get "/api/v1/platform/projects" $token
if (@($projects.data).Count -lt 1) { throw "projects empty" }
$projectId = $projects.data[0].id
$listings = Json-Get "/api/v1/platform/guarantee/listings?projectId=$projectId" $token
Write-Host "listings: $(@($listings.data).Count)"

$audit = Json-Get "/api/v1/platform/audit-logs?limit=1" $token
Write-Host "audit logs: $(@($audit.data).Count)"

Write-Host ""
Write-Host "DEPLOY OK"
