param(
    [string]$BaseUrl = "http://192.168.31.11:8090",
    [string]$TenantId = "350600",
    [string]$Password = "chk123456"
)

$ErrorActionPreference = "Stop"

function Login([string]$Username) {
    $body = @{ username = $Username; password = $Password; tenantId = $TenantId } | ConvertTo-Json
    $r = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 15
    if ($r.code -ne "BP00000") { throw "login failed: $Username" }
    return $r.data.token
}

function Get-Api([string]$Path, [string]$Token) {
    return Invoke-RestMethod -Uri "$BaseUrl$Path" -Headers @{ Authorization = "Bearer $Token" } -Method Get -TimeoutSec 15
}

function Get-Status([string]$Path, [string]$Token, [string]$Method = "POST") {
    try {
        $params = @{ Uri = "$BaseUrl$Path"; Headers = @{ Authorization = "Bearer $Token" }; Method = $Method; TimeoutSec = 15 }
        if ($Method -ne "GET") {
            $params.ContentType = "application/json"
            $params.Body = "{}"
        }
        $r = Invoke-WebRequest @params
        return [int]$r.StatusCode
    } catch {
        if ($_.Exception.Response) { return [int]$_.Exception.Response.StatusCode }
        return 0
    }
}

$projectId = "370988445033697280"

Write-Host "== auditor =="
$auditor = Login "UICHK_AUDITOR_2898"
$bills = Get-Api "/api/v1/platform/billing/bills?projectId=$projectId" $auditor
if ($null -eq $bills.data) { throw "auditor bills failed" }
$write = Get-Status "/api/v1/platform/guarantee/alerts" $auditor
if ($write -ne 403) { throw "auditor write expected 403, got $write" }
Write-Host "read OK / write 403"

Write-Host "== finance =="
$finance = Login "UICHK_GUARANTEE_FINANCE_1157"
$financeBills = Get-Api "/api/v1/platform/billing/bills?projectId=$projectId" $finance
if ($null -eq $financeBills.data) { throw "finance scoped bills failed" }
$other = Get-Status "/api/v1/platform/billing/bills?projectId=1000000000000000020" $finance "GET"
if ($other -ne 403) { throw "finance out-of-scope expected 403, got $other" }
Write-Host "in scope OK / out of scope 403"

Write-Host "== contract clerk =="
$contract = Login "UICHK_CONTRACT_CLERK_8136"
$contracts = Get-Api "/api/v1/platform/guarantee/contracts?projectId=$projectId" $contract
if ($null -eq $contracts.data) { throw "contract clerk failed" }
Write-Host "contract read OK"

Write-Host "== asset clerk =="
$asset = Login "UICHK_ASSET_CLERK_3437"
$devices = Get-Api "/api/v1/platform/devices?projectId=$projectId" $asset
if ($null -eq $devices.data) { throw "asset clerk failed" }
Write-Host "device read OK"

Write-Host ""
Write-Host "PERMISSIONS OK"
