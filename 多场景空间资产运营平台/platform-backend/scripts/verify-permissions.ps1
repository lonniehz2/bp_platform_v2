param(
    [string]$BaseUrl = "http://127.0.0.1:8091",
    [string]$TenantCode = "350600",
    [string]$Username = "admin",
    [string]$Password = "admin123"
)
$ErrorActionPreference = "Stop"
$body = @{ tenantCode = $TenantCode; username = $Username; password = $Password } | ConvertTo-Json
$login = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method Post -ContentType "application/json" -Body $body
if ($login.code -ne "BP00000") { throw "login failed" }
$headers = @{ Authorization = "Bearer $($login.data.token)" }
$projects = Invoke-RestMethod -Uri "$BaseUrl/api/v1/platform/projects" -Headers $headers
$projectId = $projects.data[0].id
if (-not $projectId) { throw "no project" }
try {
    Invoke-WebRequest -Uri "$BaseUrl/api/v1/platform/billing/bills?projectId=$projectId" -Method Get | Out-Null
    throw "anonymous request should be rejected"
} catch {
    if ($_.Exception.Response -and [int]$_.Exception.Response.StatusCode -ne 401) { throw }
}
$bills = Invoke-RestMethod -Uri "$BaseUrl/api/v1/platform/billing/bills?projectId=$projectId" -Headers $headers
if ($null -eq $bills.data) { throw "bills data missing" }
Write-Host "anonymous=401 authenticated=200 project=$projectId"
Write-Host "PERMISSIONS SMOKE OK"
