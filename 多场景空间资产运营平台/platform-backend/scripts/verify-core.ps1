param(
    [string]$BaseUrl = "http://127.0.0.1:8090",
    [string]$TenantId = "350600"
)

$ErrorActionPreference = "Stop"
$Headers = @{ "X-Tenant-Id" = $TenantId }
$script:Pass = 0

function Assert-True($condition, $message) {
    if (-not $condition) { throw "ASSERT FAILED: $message" }
    $script:Pass++
    Write-Host "PASS $message"
}

function Api($method, $path, $body) {
    $params = @{
        Uri = "$BaseUrl$path"
        Method = $method
        Headers = $Headers
        ErrorAction = "Stop"
    }
    if ($null -ne $body) {
        $params.ContentType = "application/json; charset=utf-8"
        $params.Body = [Text.Encoding]::UTF8.GetBytes(($body | ConvertTo-Json -Depth 10))
    }
    $response = Invoke-RestMethod @params
    if ($response.code -ne "BP00000") {
        throw "API $path failed: $($response.code) $($response.message)"
    }
    return $response.data
}

$health = Invoke-RestMethod "$BaseUrl/actuator/health"
Assert-True ($health.status -eq "UP") "health is UP"

$scenes = Api "GET" "/api/v1/platform/scenes" $null
Assert-True (@($scenes | Where-Object { $_.sceneCode -eq "GUARANTEE" }).Count -eq 1) "GUARANTEE scene exists"

$modes = Api "GET" "/api/v1/platform/scenes/GUARANTEE/business-modes" $null
Assert-True (@($modes | Where-Object { $_.modeCode -eq "PUBLIC_RENTAL" }).Count -eq 1) "PUBLIC_RENTAL mode exists"

$suffix = Get-Date -Format "HHmmss"
$templateCode = "VERIFY_TPL_$suffix"
$template = Api "POST" "/api/v1/platform/space-templates" @{
    sceneCode = "GUARANTEE"
    templateCode = $templateCode
    templateName = "验证保障房模板"
    baseLevelCount = 5
    allowedSubModes = "NONE,BED,INNER_ROOM,INNER_ROOM_BED"
    levels = @(
        @{ level = 1; name = "小区"; required = $true },
        @{ level = 2; name = "楼栋"; required = $true },
        @{ level = 3; name = "单元"; required = $false },
        @{ level = 4; name = "楼层"; required = $true },
        @{ level = 5; name = "房屋"; required = $true }
    )
}
Assert-True ($null -ne $template.id) "template created"

$typeCode = "VERIFY_ASSET_$suffix"
$assetType = Api "POST" "/api/v1/platform/asset-types" @{
    sceneCode = "GUARANTEE"
    typeCode = $typeCode
    typeName = "验证公租房"
    typeCategory = "HOUSE"
    sortNo = 99
}
Assert-True ($null -ne $assetType.id) "asset type created"

$projectCode = "VERIFY_PROJ_$suffix"
$project = Api "POST" "/api/v1/platform/projects" @{
    orgCode = $projectCode
    orgName = "保障房验证项目"
    sceneCode = "GUARANTEE"
    businessMode = "PUBLIC_RENTAL"
    spaceTemplateId = $template.id
    defaultAssetTypeCode = $typeCode
}
Assert-True ($null -ne $project.id) "project created"
$projectId = $project.id

function NewSpace($parentId, $code, $name, $type, $rentable) {
    return Api "POST" "/api/v1/platform/projects/$projectId/spaces" @{
        parentId = $parentId
        spaceCode = $code
        spaceName = $name
        spaceType = $type
        assetTypeCode = $typeCode
        rentable = $rentable
        area = 88.5
    }
}

$area = NewSpace $null "XQ" "示范小区" "AREA" $false
$building = NewSpace $area.id "A" "A栋" "BUILDING" $false
$unit = NewSpace $building.id "1" "1单元" "UNIT" $false
$floor = NewSpace $unit.id "1F" "1层" "FLOOR" $false
$room = NewSpace $floor.id "101" "101室" "ROOM" $true
$innerRoom = NewSpace $room.id "101-1" "101室内房1" "INNER_ROOM" $true
$bed = NewSpace $innerRoom.id "101-1-B1" "内房1床位1" "BED" $true

$spaces = Api "GET" "/api/v1/platform/projects/$projectId/spaces" $null
Assert-True (@($spaces).Count -eq 7) "7-level guarantee space tree created"
Assert-True (@($spaces | Where-Object { $_.spaceType -eq "INNER_ROOM" }).Count -eq 1) "inner room exists"
Assert-True (@($spaces | Where-Object { $_.spaceType -eq "BED" }).Count -eq 1) "bed exists"

$houses = Api "GET" "/api/v1/platform/projects/$projectId/houses" $null
Assert-True (@($houses).Count -eq 3) "room/inner room/bed houses created"
Assert-True (@($houses | Where-Object { $_.houseCode -eq "101" }).Count -eq 1) "room house exists"
Assert-True (@($houses | Where-Object { $_.houseCode -eq "101-1" }).Count -eq 1) "inner room house exists"
Assert-True (@($houses | Where-Object { $_.houseCode -eq "101-1-B1" }).Count -eq 1) "bed house exists"

Write-Host ""
Write-Host "VERIFY OK: $script:Pass assertions passed"
Write-Host "ProjectId=$projectId TemplateId=$($template.id)"
