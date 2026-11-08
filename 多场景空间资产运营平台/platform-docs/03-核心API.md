# 平台核心 API（Phase 0）

> Base URL：`http://127.0.0.1:8090`  
> 前缀：`/api/v1/platform`  
> 租户头：`X-Tenant-Id: 350600`

---

## 1. 场景

### GET /scenes

返回场景包及租户启用状态。

### GET /scenes/{sceneCode}/business-modes

返回场景下的经营模式。

---

## 2. 空间模板

### GET /space-templates?sceneCode=GUARANTEE

返回模板，`levels` 已解析为数组。

### POST /space-templates

```json
{
  "sceneCode": "GUARANTEE",
  "templateCode": "GUARANTEE_BASE",
  "templateName": "保障房基础",
  "baseLevelCount": 5,
  "allowedSubModes": "NONE,BED,INNER_ROOM,INNER_ROOM_BED",
  "levels": [
    {"level": 1, "name": "小区", "required": true},
    {"level": 2, "name": "楼栋", "required": true},
    {"level": 3, "name": "单元", "required": false},
    {"level": 4, "name": "楼层", "required": true},
    {"level": 5, "name": "房屋", "required": true}
  ]
}
```

校验：

```text
基础层级 2-6
层级数不少于基础层级
场景存在
模板编码唯一
```

---

## 3. 资产类型

### GET /asset-types?sceneCode=GUARANTEE

### POST /asset-types

```json
{
  "sceneCode": "GUARANTEE",
  "typeCode": "PUBLIC_RENTAL",
  "typeName": "公租房",
  "typeCategory": "HOUSE",
  "sortNo": 1
}
```

---

## 4. 项目

### GET /projects

### POST /projects

```json
{
  "orgCode": "GUA_DEMO",
  "orgName": "保障房示范项目",
  "sceneCode": "GUARANTEE",
  "businessMode": "PUBLIC_RENTAL",
  "spaceTemplateId": 910000000000003001,
  "defaultAssetTypeCode": "PUBLIC_RENTAL"
}
```

校验：

```text
租户启用场景
经营模式属于场景
模板属于场景且可用
项目编码唯一
```

---

## 5. 空间

### GET /projects/{projectId}/spaces

### POST /projects/{projectId}/spaces

```json
{
  "parentId": null,
  "spaceCode": "XQ",
  "spaceName": "示范小区",
  "spaceType": "AREA",
  "assetTypeCode": "PUBLIC_RENTAL",
  "rentable": false,
  "area": 0
}
```

空间类型：

```text
AREA
BUILDING
UNIT
FLOOR
ROOM
INNER_ROOM
BED
SITE
PARKING
```

规则：

```text
层级从 1 开始
基础层级内可创建
超出基础层级只能是 INNER_ROOM/BED
出租单元 rentable=true
```

---

## 6. 房源

### GET /projects/{projectId}/houses

空间创建时：

```text
spaceType = ROOM/INNER_ROOM/BED
rentable = true
```

自动生成 `bp_house`。

---

## 7. 人员与关系

### GET /persons?keyword=&personType=

### POST /persons

```json
{
  "personCode": "P0001",
  "personName": "张三",
  "phone": "13800000000",
  "idCardMask": "330***********1234",
  "personType": "GUARANTEE_TENANT"
}
```

### GET /persons/{personId}/relations

### POST /persons/{personId}/relations

```json
{
  "projectId": 1,
  "targetType": "HOUSE",
  "targetId": 2,
  "relationType": "TENANT",
  "isPrimary": true,
  "startDate": "2026-11-08",
  "endDate": null
}
```

关联对象：

```text
PROJECT
SPACE
HOUSE
```

---

## 8. 保障房合同与账单

### GET /guarantee/contracts?projectId=

### POST /guarantee/contracts

```json
{
  "projectId": 1,
  "contractNo": "HT2026001",
  "houseId": 2,
  "personId": 3,
  "startDate": "2026-11-01",
  "endDate": "2027-10-31",
  "rentAmount": 1200.00,
  "depositAmount": 1200.00,
  "billingCycle": "MONTH",
  "billDay": 1
}
```

### POST /guarantee/contracts/{contractId}/bills

```json
{
  "periodStart": "2026-11-01",
  "periodEnd": "2026-11-30",
  "amount": 1200.00,
  "dueDate": "2026-11-30"
}
```

### GET /billing/bills?projectId=&status=

### POST /billing/bills/{billId}/pay

```json
{
  "amount": 1200.00,
  "paymentMethod": "CASH"
}
```

### GET /billing/payments?projectId=

### GET /billing/payments/{paymentId}/receipt

闭环：

```text
合同
→ 租金账单
→ 收款
→ 分摊
→ 收据
→ 账单 PAID
```

---

## 9. 审批/工作流

### GET /workflows?sceneCode=&bizType=

### POST /workflows

```json
{
  "sceneCode": "GUARANTEE",
  "bizType": "GUARANTEE_CONTRACT_CHANGE",
  "flowName": "保障房合同变更审批
申请/轮候/配租/配租转合同
押金收取/退还
退租释放房屋",
  "nodes": [
    {"nodeName": "客服初审", "approverRole": "PROPERTY_STEWARD"},
    {"nodeName": "经理终审", "approverRole": "PROPERTY_MANAGER"}
  ]
}
```

### POST /workflows/{flowId}/submit

```json
{
  "projectId": 1,
  "bizType": "GUARANTEE_CONTRACT_CHANGE",
  "bizId": 2,
  "submitterName": "客服A",
  "amount": 0,
  "summary": "合同变更"
}
```

### GET /workflow-tasks?status=APPROVING

### POST /workflow-tasks/{taskId}/approve

```json
{"approverName": "客服A", "comment": "同意"}
```

### POST /workflow-tasks/{taskId}/reject

### GET /workflow-tasks/{taskId}/records

当前支持：

```text
串行多级审批
合同变更审批
申请/轮候/配租/配租转合同
押金收取/退还
退租释放房屋
通过/驳回
审批记录
```

---

## 10. 合同变更/退租

### GET /guarantee/contracts/{contractId}/changes

### POST /guarantee/contracts/{contractId}/changes

```json
{
  "changeType": "RENT_CHANGE",
  "after": {"rentAmount": 1500.00},
  "effectiveDate": "2026-12-01",
  "reason": "租金调整"
}
```

变更类型：

```text
RENT_CHANGE
TERM_CHANGE
ROOM_CHANGE
TERMINATION
```

### POST /guarantee/contract-changes/{changeId}/submit

自动查找 `GUARANTEE_CONTRACT_CHANGE` 审批流程并提交。

### POST /guarantee/contract-changes/{changeId}/approve

### POST /guarantee/contract-changes/{changeId}/reject

审批通过后：

```text
RENT_CHANGE → 更新租金
TERM_CHANGE → 更新结束日期
ROOM_CHANGE → 更新房屋
TERMINATION → 合同终止
```

---

## 11. 保障房申请/轮候/配租/配租转合同
押金收取/退还
退租释放房屋

### GET /guarantee/applications?projectId=

### POST /guarantee/applications

```json
{
  "projectId": 1,
  "applicationNo": "APP2026001",
  "applicantPersonId": 2,
  "applicationType": "PUBLIC_RENTAL",
  "familySize": 2
}
```

### POST /guarantee/applications/{id}/submit

### POST /guarantee/applications/{id}/approve

```json
{"comment": "资格通过"}
```

### POST /guarantee/applications/{id}/waitlist

### GET /guarantee/waitlist?projectId=

### POST /guarantee/waitlist/{waitlistId}/allocate

```json
{"houseId": 3}
```

### POST /guarantee/allocations/{allocationId}/contract

```json
{
  "contractNo": "HT2026002",
  "startDate": "2026-12-01",
  "endDate": "2027-11-30",
  "rentAmount": 1000.00,
  "depositAmount": 1000.00,
  "billingCycle": "MONTH",
  "billDay": 1
}
```

配租转合同后：

```text
配租状态 ALLOCATED → CONTRACTED
生成保障房合同
```

### GET /guarantee/contracts/{contractId}/deposit

### POST /guarantee/contracts/{contractId}/deposit/pay

```json
{"amount": 1200.00, "operatorName": "收费员A", "remark": "收取押金"}
```

### POST /guarantee/deposits/{depositId}/refund

```json
{"amount": 1200.00, "operatorName": "收费员A", "reason": "退租退押"}
```

押金状态：

```text
PENDING → HELD → REFUNDED
```

### GET /guarantee/allocations?projectId=

状态：

```text
DRAFT → SUBMITTED → APPROVED
WAITING → ALLOCATED
房屋 VACANT → ALLOCATED
```

---

## 12. 验证脚本

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify-core.ps1
```

预期：

```text
54 个断言通过
保障房 7 级空间树
3 个房源
人员
人员房屋关系
保障房合同
租金账单
收款
收据
串行多级审批
合同变更审批
申请/轮候/配租/配租转合同
押金收取/退还
退租释放房屋
```
