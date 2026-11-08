param(
    [string]$BaseUrl = "http://127.0.0.1:8090",
    [string]$TenantId = "350600"
)

$ErrorActionPreference = "Stop"
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

$loginBody = @{ username = "admin"; password = "admin123"; tenantId = $TenantId } | ConvertTo-Json
$login = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/login" -Method Post `
    -ContentType "application/json; charset=utf-8" `
    -Body ([Text.Encoding]::UTF8.GetBytes($loginBody))
if ($login.code -ne "BP00000") { throw "login failed: $($login.message)" }
$Headers = @{ "X-Tenant-Id" = $TenantId; "Authorization" = "Bearer $($login.data.token)" }
Assert-True ($null -ne $login.data.token) "login token issued"


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

$person = Api "POST" "/api/v1/platform/persons" @{
    personCode = "VERIFY_PERSON_$suffix"
    personName = "验证保障对象"
    phone = "13800000000"
    personType = "GUARANTEE_TENANT"
}
Assert-True ($null -ne $person.id) "person created"

$roomHouse = @($houses | Where-Object { $_.houseCode -eq "101" })[0]
$relation = Api "POST" "/api/v1/platform/persons/$($person.id)/relations" @{
    projectId = $projectId
    targetType = "HOUSE"
    targetId = $roomHouse.id
    relationType = "TENANT"
    isPrimary = $true
    startDate = "2026-11-08"
}
Assert-True ($null -ne $relation.id) "person house relation created"

$relations = Api "GET" "/api/v1/platform/persons/$($person.id)/relations" $null
Assert-True (@($relations).Count -eq 1) "person relation listed"
Assert-True ($relations[0].targetId -eq $roomHouse.id) "person relation target id"

$contract = Api "POST" "/api/v1/platform/guarantee/contracts" @{
    projectId = $projectId
    contractNo = "VERIFY_HT_$suffix"
    houseId = $roomHouse.id
    personId = $person.id
    startDate = "2026-11-01"
    endDate = "2027-10-31"
    rentAmount = 1200.00
    depositAmount = 1200.00
    billingCycle = "MONTH"
    billDay = 1
}
Assert-True ($null -ne $contract.id) "guarantee contract created"


$subsidy = Api "POST" "/api/v1/platform/guarantee/contracts/$($contract.id)/subsidies" @{
    subsidyType = "RENT_SUBSIDY"
    amount = 300.00
    startDate = "2026-11-01"
    endDate = "2026-11-30"
    remark = "租金补贴验证"
}
Assert-True ($subsidy.subsidyStatus -eq "ACTIVE") "subsidy created"

$deposit = Api "GET" "/api/v1/platform/guarantee/contracts/$($contract.id)/deposit" $null
Assert-True ([decimal]$deposit.amount -eq 1200.00) "deposit created"
Assert-True ($deposit.depositStatus -eq "PENDING") "deposit pending"

$depositPay = Api "POST" "/api/v1/platform/guarantee/contracts/$($contract.id)/deposit/pay" @{
    amount = 1200.00
    operatorName = "收费员A"
    remark = "收取押金"
}
Assert-True ($depositPay.depositStatus -eq "HELD") "deposit held"

$depositRefund = Api "POST" "/api/v1/platform/guarantee/deposits/$($deposit.id)/refund" @{
    amount = 1200.00
    operatorName = "收费员A"
    reason = "退租退押"
}
Assert-True ($depositRefund.depositStatus -eq "REFUNDED") "deposit refunded"

$depositAfter = Api "GET" "/api/v1/platform/guarantee/contracts/$($contract.id)/deposit" $null
Assert-True (@($depositAfter.transactions).Count -eq 2) "deposit transactions created"

$bill = Api "POST" "/api/v1/platform/guarantee/contracts/$($contract.id)/bills" @{
    periodStart = "2026-11-01"
    periodEnd = "2026-11-30"
    amount = 1200.00
    dueDate = "2026-11-30"
}
Assert-True ($null -ne $bill.id) "rent bill generated"
Assert-True ($bill.billStatus -eq "UNPAID") "rent bill unpaid"
Assert-True ([decimal]$bill.discountAmount -eq 300.00) "subsidy applied to bill"
Assert-True ([decimal]$bill.payableAmount -eq 900.00) "bill payable after subsidy"

$payment = Api "POST" "/api/v1/platform/billing/bills/$($bill.id)/pay" @{
    amount = 900.00
    paymentMethod = "CASH"
}
Assert-True ($payment.billStatus -eq "PAID") "bill paid"
Assert-True ($null -ne $payment.receiptNo) "receipt generated"

$bills = Api "GET" "/api/v1/platform/billing/bills?projectId=$projectId" $null
Assert-True (@($bills).Count -eq 1) "bill listed"
Assert-True ($bills[0].billStatus -eq "PAID") "bill status persisted"
Assert-True ([decimal]$bills[0].paidAmount -eq 900.00) "bill paid amount persisted"

$payments = Api "GET" "/api/v1/platform/billing/payments?projectId=$projectId" $null
Assert-True (@($payments).Count -eq 1) "payment listed"
$receipt = Api "GET" "/api/v1/platform/billing/payments/$($payment.paymentId)/receipt" $null
Assert-True ($receipt.receiptNo -eq $payment.receiptNo) "receipt readable"


$flow = Api "POST" "/api/v1/platform/workflows" @{
    sceneCode = "GUARANTEE"
    bizType = "GUARANTEE_CONTRACT_CHANGE"
    flowName = "保障房合同变更审批_$suffix"
    nodes = @(
        @{ nodeName = "客服初审"; approverRole = "PROPERTY_STEWARD" },
        @{ nodeName = "经理终审"; approverRole = "PROPERTY_MANAGER" }
    )
}
Assert-True ($null -ne $flow.id) "workflow created"

$wfTask = Api "POST" "/api/v1/platform/workflows/$($flow.id)/submit" @{
    projectId = $projectId
    bizType = "GUARANTEE_CONTRACT_CHANGE"
    bizId = $contract.id
    submitterName = "客服A"
    amount = 0
    summary = "合同变更验证"
}
Assert-True ($wfTask.taskStatus -eq "APPROVING") "workflow submitted"

$step1 = Api "POST" "/api/v1/platform/workflow-tasks/$($wfTask.taskId)/approve" @{
    approverName = "客服A"
    comment = "同意"
}
Assert-True ($step1.taskStatus -eq "APPROVING") "workflow first node approved"

$step2 = Api "POST" "/api/v1/platform/workflow-tasks/$($wfTask.taskId)/approve" @{
    approverName = "经理B"
    comment = "通过"
}
Assert-True ($step2.taskStatus -eq "APPROVED") "workflow final approved"

$wfRecords = Api "GET" "/api/v1/platform/workflow-tasks/$($wfTask.taskId)/records" $null
Assert-True (@($wfRecords).Count -eq 2) "workflow records created"


$change = Api "POST" "/api/v1/platform/guarantee/contracts/$($contract.id)/changes" @{
    changeType = "RENT_CHANGE"
    after = @{ rentAmount = 1500.00 }
    effectiveDate = "2026-12-01"
    reason = "租金调整验证"
}
Assert-True ($null -ne $change.id) "contract change created"

$changeSubmit = Api "POST" "/api/v1/platform/guarantee/contract-changes/$($change.id)/submit" $null
Assert-True ($changeSubmit.changeStatus -eq "APPROVING") "contract change submitted"

$changeStep1 = Api "POST" "/api/v1/platform/guarantee/contract-changes/$($change.id)/approve" @{
    approverName = "客服A"
    comment = "同意变更"
}
Assert-True ($changeStep1.changeStatus -eq "APPROVING") "contract change first approved"

$changeStep2 = Api "POST" "/api/v1/platform/guarantee/contract-changes/$($change.id)/approve" @{
    approverName = "经理B"
    comment = "通过"
}
Assert-True ($changeStep2.changeStatus -eq "APPROVED") "contract change final approved"

$contracts = Api "GET" "/api/v1/platform/guarantee/contracts?projectId=$projectId" $null
Assert-True ([decimal]$contracts[0].rentAmount -eq 1500.00) "contract rent applied"


$application = Api "POST" "/api/v1/platform/guarantee/applications" @{
    projectId = $projectId
    applicationNo = "VERIFY_APP_$suffix"
    applicantPersonId = $person.id
    applicationType = "PUBLIC_RENTAL"
    familySize = 2
}
Assert-True ($application.applicationStatus -eq "DRAFT") "guarantee application created"

$appSubmitted = Api "POST" "/api/v1/platform/guarantee/applications/$($application.id)/submit" $null
Assert-True ($appSubmitted.applicationStatus -eq "SUBMITTED") "guarantee application submitted"

$appApproved = Api "POST" "/api/v1/platform/guarantee/applications/$($application.id)/approve" @{ comment = "资格通过" }
Assert-True ($appApproved.applicationStatus -eq "APPROVED") "guarantee application approved"

$wait = Api "POST" "/api/v1/platform/guarantee/applications/$($application.id)/waitlist" $null
Assert-True ($wait.waitlistStatus -eq "WAITING") "guarantee waitlist joined"

$innerHouse = @($houses | Where-Object { $_.houseCode -eq "101-1" })[0]
$allocation = Api "POST" "/api/v1/platform/guarantee/waitlist/$($wait.id)/allocate" @{ houseId = $innerHouse.id }
Assert-True ($allocation.allocationStatus -eq "ALLOCATED") "guarantee house allocated"

$housesAfter = Api "GET" "/api/v1/platform/projects/$projectId/houses" $null
$allocatedHouse = @($housesAfter | Where-Object { $_.id -eq $innerHouse.id })[0]
Assert-True ($allocatedHouse.houseStatus -eq "ALLOCATED") "house status allocated"


$allocContract = Api "POST" "/api/v1/platform/guarantee/allocations/$($allocation.allocationId)/contract" @{
    contractNo = "VERIFY_ALLOC_HT_$suffix"
    startDate = "2026-12-01"
    endDate = "2027-11-30"
    rentAmount = 1000.00
    depositAmount = 1000.00
    billingCycle = "MONTH"
    billDay = 1
}
Assert-True ($allocContract.allocationStatus -eq "CONTRACTED") "allocation contracted"
Assert-True ($null -ne $allocContract.contractId) "allocation contract created"

$allocations = Api "GET" "/api/v1/platform/guarantee/allocations?projectId=$projectId" $null
$allocationRow = @($allocations | Where-Object { $_.id -eq $allocation.allocationId })[0]
Assert-True ($allocationRow.allocationStatus -eq "CONTRACTED") "allocation status persisted"


$termination = Api "POST" "/api/v1/platform/guarantee/contracts/$($allocContract.contractId)/changes" @{
    changeType = "TERMINATION"
    after = @{}
    effectiveDate = "2027-11-30"
    reason = "退租验证"
}
$termSubmit = Api "POST" "/api/v1/platform/guarantee/contract-changes/$($termination.id)/submit" $null
Assert-True ($termSubmit.changeStatus -eq "APPROVING") "termination submitted"

$termStep1 = Api "POST" "/api/v1/platform/guarantee/contract-changes/$($termination.id)/approve" @{
    approverName = "客服A"
    comment = "同意退租"
}
$termStep2 = Api "POST" "/api/v1/platform/guarantee/contract-changes/$($termination.id)/approve" @{
    approverName = "经理B"
    comment = "通过"
}
Assert-True ($termStep2.changeStatus -eq "APPROVED") "termination approved"

$housesAfterTerm = Api "GET" "/api/v1/platform/projects/$projectId/houses" $null
$terminatedHouse = @($housesAfterTerm | Where-Object { $_.id -eq $innerHouse.id })[0]
Assert-True ($terminatedHouse.houseStatus -eq "VACANT") "termination released house"


$device = Api "POST" "/api/v1/platform/devices" @{
    projectId = $projectId
    spaceId = $roomHouse.spaceId
    deviceCode = "VERIFY_DEV_$suffix"
    deviceName = "验证门锁"
    deviceType = "LOCK"
    deviceModel = "TEST-LOCK"
    assetStatus = "ACTIVE"
    businessStatus = "IN_USE"
}
Assert-True ($null -ne $device.id) "device created"

$devices = Api "GET" "/api/v1/platform/devices?projectId=$projectId" $null
Assert-True (@($devices | Where-Object { $_.id -eq $device.id }).Count -eq 1) "device listed"

$grant = Api "POST" "/api/v1/platform/grants" @{
    projectId = $projectId
    personId = $person.id
    targetType = "SPACE"
    targetId = $roomHouse.spaceId
    grantLevel = "OPEN"
    validStart = "2026-11-08"
    validEnd = "2027-11-07"
    sourceType = "CONTRACT"
    sourceId = $contract.id
}
Assert-True ($grant.grantStatus -eq "ACTIVE") "grant created"

$keyring = Api "GET" "/api/v1/platform/persons/$($person.id)/keyring" $null
Assert-True (@($keyring).Count -eq 1) "keyring has grant"

$revoked = Api "POST" "/api/v1/platform/grants/$($grant.id)/revoke" @{ reason = "测试撤销" }
Assert-True ($revoked.grantStatus -eq "REVOKED") "grant revoked"

$keyringAfter = Api "GET" "/api/v1/platform/persons/$($person.id)/keyring" $null
Assert-True (@($keyringAfter).Count -eq 0) "keyring empty after revoke"


$menus = Api "GET" "/api/v1/platform/menus?sceneCode=GUARANTEE" $null
Assert-True (@($menus).Count -eq 9) "guarantee menu tree loaded"

$roles = Api "GET" "/api/v1/platform/roles?sceneCode=GUARANTEE" $null
Assert-True (@($roles).Count -eq 4) "guarantee role templates loaded"

$adminRole = @($roles | Where-Object { $_.roleCode -eq "GUARANTEE_ADMIN" })[0]
$adminMenus = Api "GET" "/api/v1/platform/roles/$($adminRole.id)/menus" $null
Assert-True (@($adminMenus).Count -ge 13) "admin role menus loaded"

Write-Host ""
Write-Host "VERIFY OK: $script:Pass assertions passed"
Write-Host "ProjectId=$projectId TemplateId=$($template.id)"
