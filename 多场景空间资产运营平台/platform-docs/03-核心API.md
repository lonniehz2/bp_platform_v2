# 平台核心 API（Phase 0）

> Base URL：`http://127.0.0.1:8090`  
> 前缀：`/api/v1/platform`  
> 租户头：`X-Tenant-Id: 350600`

---

## 0. 登录

### POST /api/v1/auth/login

```json
{"username": "admin", "password": "admin123", "tenantId": "350600"}
```

返回：

```json
{"token": "...", "displayName": "平台管理员", "roles": ["GUARANTEE_ADMIN"]}
```

平台接口需要：

```text
Authorization: Bearer <token>
```

### GET /api/v1/auth/me

---

## 0.1 菜单权限

平台接口按菜单授权：

```text
项目/空间/模板 -> asset
人员 -> person
申请/轮候/配租 -> application
合同/变更/资格复核 -> contract
账单/收款/押金/补贴 -> billing
设备/授权 -> device
审批 -> audit
菜单/角色 -> config
迁移异常 -> system
```

无权限返回：

```text
403 BP40300
```

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
退租释放房屋
补贴抵扣租金
设备业务资产
授权/人员钥匙包
菜单/角色模板
登录鉴权
资格复核
迁移异常处理
附件上传
计量与能耗
服务工单
访客通行
投诉与申诉
计费项目
公示管理
风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码
菜单权限",
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
补贴抵扣租金
设备业务资产
授权/人员钥匙包
菜单/角色模板
登录鉴权
资格复核
迁移异常处理
附件上传
计量与能耗
服务工单
访客通行
投诉与申诉
计费项目
公示管理
风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码
菜单权限
通过/驳回
审批记录
```

---

## 10. 设备业务资产

### GET /devices?projectId=

### POST /devices

```json
{
  "projectId": 1,
  "spaceId": 2,
  "deviceCode": "LOCK-001",
  "deviceName": "101门锁",
  "deviceType": "LOCK",
  "deviceModel": "TEST-LOCK",
  "assetStatus": "ACTIVE",
  "businessStatus": "IN_USE"
}
```

业务平台只做设备资产，不做 IOT 控制。

---

## 11. 授权/人员钥匙包

### GET /grants?personId=&projectId=

### POST /grants

```json
{
  "projectId": 1,
  "personId": 2,
  "targetType": "SPACE",
  "targetId": 3,
  "grantLevel": "OPEN",
  "validStart": "2026-11-08",
  "validEnd": "2027-11-07",
  "sourceType": "CONTRACT",
  "sourceId": 4
}
```

授权对象：

```text
SPACE
DEVICE
```

### POST /grants/{grantId}/revoke

```json
{"reason": "退租撤销"}
```

### GET /persons/{personId}/keyring

返回当前有效授权，业务钥匙包只展示授权，不展示 IOT 凭证。

---

## 12. 合同变更/退租

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
补贴抵扣租金
设备业务资产
授权/人员钥匙包
菜单/角色模板
登录鉴权
资格复核
迁移异常处理
附件上传
计量与能耗
服务工单
访客通行
投诉与申诉
计费项目
公示管理
风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码
菜单权限

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

### POST /guarantee/contracts/{contractId}/subsidies

```json
{
  "subsidyType": "RENT_SUBSIDY",
  "amount": 300.00,
  "startDate": "2026-11-01",
  "endDate": "2026-11-30",
  "remark": "租金补贴"
}
```

### GET /guarantee/contracts/{contractId}/subsidies

账单生成时自动抵扣当期有效补贴：

```text
账单金额 = 租金
补贴金额 = 当期有效补贴合计
应付金额 = 账单金额 - 补贴金额
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

## 13. 资格复核
迁移异常处理
附件上传
计量与能耗
服务工单
访客通行
投诉与申诉
计费项目
公示管理
风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码
菜单权限

### GET /guarantee/contracts/{contractId}/qualification-reviews

### POST /guarantee/contracts/{contractId}/qualification-reviews

```json
{"reviewType": "ANNUAL", "reviewYear": 2026}
```

### POST /guarantee/qualification-reviews/{reviewId}/complete

```json
{
  "result": "PASSED",
  "reviewerName": "复核员A",
  "comment": "资格仍符合",
  "nextReviewDate": "2027-11-01"
}
```

状态：

```text
PENDING → PASSED / FAILED
```

---

## 14. 菜单/角色

### GET /menus?sceneCode=GUARANTEE

返回场景菜单树。

### GET /roles?sceneCode=GUARANTEE

返回角色模板和菜单数量。

### GET /roles/{roleId}/menus

返回角色菜单。

GUARANTEE 场景已预置：

```text
工作台
项目与资产
客户与人员
合同与租赁
收费与账务
审核中心
设备与授权
基础配置
系统与数据
```

种子文件：

```text
platform-sql/002_menu_seed.sql
```

---

## 15. 计量与能耗
服务工单
访客通行
投诉与申诉
计费项目
公示管理
风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码

### GET /guarantee/meters?projectId=

### POST /guarantee/meters

```json
{
  "projectId": 1,
  "houseId": 2,
  "meterType": "WATER",
  "meterNo": "WM-001",
  "initialReading": 0
}
```

### POST /guarantee/meters/{meterId}/readings

```json
{"readingDate": "2026-11-08", "readingValue": 100, "readerName": "抄表员A"}
```

### GET /guarantee/meters/{meterId}/readings

### GET /guarantee/meters/summary?projectId=

---

## 16. 服务工单
访客通行
投诉与申诉
计费项目
公示管理
风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码

### GET /guarantee/work-orders?projectId=

### POST /guarantee/work-orders

```json
{
  "projectId": 1,
  "orderType": "REPAIR",
  "title": "厨房漏水",
  "houseId": 2,
  "personId": 3,
  "priority": "NORMAL",
  "assigneeName": "维修班组"
}
```

### POST /guarantee/work-orders/{orderId}/update

```json
{"orderStatus": "DONE", "assigneeName": "维修班组"}
```

状态：

```text
PENDING → PROCESSING → DONE → CLOSED
```

---

## 17. 访客通行
投诉与申诉
计费项目
公示管理
风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码

### GET /guarantee/access-records?projectId=

### POST /guarantee/access-records

```json
{
  "projectId": 1,
  "houseId": 2,
  "personId": 3,
  "visitorName": "访客A",
  "visitorPhone": "13900000000",
  "purpose": "探访"
}
```

### POST /guarantee/access-records/{id}/approve

```json
{"status": "APPROVED"}
```

---

## 18. 投诉与申诉
计费项目
公示管理
风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码

### GET /guarantee/complaints?projectId=&type=

### POST /guarantee/complaints

```json
{
  "projectId": 1,
  "complaintType": "COMPLAINT",
  "title": "楼道噪音",
  "content": "夜间噪音",
  "houseId": 2,
  "personId": 3
}
```

### POST /guarantee/complaints/{id}/handle

```json
{"complaintStatus": "RESOLVED", "handlerName": "客服中心", "handleResult": "已协调"}
```

类型：

```text
COMPLAINT 投诉
APPEAL 申诉
VISIT 走访
```

---

## 19. 计费项目
公示管理
风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码

### GET /guarantee/fee-items?projectId=

### POST /guarantee/fee-items

```json
{
  "projectId": 1,
  "feeCode": "RENT_STD",
  "feeName": "标准租金",
  "feeType": "RENT",
  "billingCycle": "MONTHLY",
  "unitPrice": 1800,
  "unitName": "月",
  "taxRate": 0
}
```

### POST /guarantee/fee-items/{id}/toggle?enabled=

---

## 20. 公示管理
风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码

### GET /guarantee/publicities?projectId=

### POST /guarantee/publicities

```json
{
  "projectId": 1,
  "publicityType": "ALLOCATION",
  "title": "配租公示",
  "content": "公示内容",
  "startDate": "2026-11-08",
  "endDate": "2026-11-15"
}
```

### POST /guarantee/publicities/{id}/status

```json
{"status": "PUBLISHED"}
```

---

## 21. 风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码

### GET /guarantee/alerts?projectId=

### POST /guarantee/alerts

```json
{
  "projectId": 1,
  "alertType": "RISK",
  "alertLevel": "HIGH",
  "title": "连续欠费",
  "content": "风险提示",
  "houseId": 2,
  "personId": 3
}
```

### POST /guarantee/alerts/{id}/handle

```json
{"alertStatus": "RESOLVED", "handlerName": "运营中心", "handleResult": "已处理"}
```

---

## 22. 信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码

### GET /guarantee/credits?projectId=

### POST /guarantee/credits

```json
{
  "projectId": 1,
  "personId": 2,
  "creditType": "VIOLATION",
  "scoreChange": -5,
  "reason": "违规转租"
}
```

### POST /guarantee/credits/{id}/revoke

---

## 23. 短租订单
开放平台
消息中心
用户管理
修改密码

### GET /guarantee/short-rent-orders?projectId=

### POST /guarantee/short-rent-orders

```json
{
  "projectId": 1,
  "houseId": 2,
  "guestName": "短租客人A",
  "guestPhone": "13800000000",
  "startDate": "2026-11-10",
  "endDate": "2026-11-13",
  "amount": 900
}
```

### POST /guarantee/short-rent-orders/{id}/status

```json
{"status": "CONFIRMED"}
```

状态：

```text
PENDING → CONFIRMED → CHECKED_IN → COMPLETED / CANCELLED
```

---

## 24. 开放平台
消息中心
用户管理
修改密码

### GET /open-apps

### POST /open-apps

```json
{"appCode": "GOV_SYNC", "appName": "监管数据同步", "scopes": "project:read,bill:read"}
```

### POST /open-apps/{id}/toggle?enabled=

---

## 25. 消息中心
用户管理
修改密码

### GET /messages

### POST /messages

```json
{"title": "租金逾期提醒", "content": "请及时缴费", "bizType": "BILL", "bizId": "1"}
```

### POST /messages/{id}/read

### POST /messages/read-all

---

## 26. 用户管理
修改密码

### GET /users

### GET /users/roles

### POST /users

```json
{
  "username": "steward02",
  "password": "123456",
  "displayName": "管家02",
  "roleIds": [1]
}
```

### POST /users/{id}/update

```json
{"userStatus": "DISABLED", "displayName": "管家02", "password": "", "roleIds": [1]}
```

---

## 27. 修改密码

### POST /auth/password

```json
{"oldPassword": "start123", "newPassword": "newpass123"}
```

---

## 28. 附件

### POST /files

multipart/form-data：

```text
bizType=CONTRACT
bizId=<合同ID>
file=<文件>
```

### GET /files?bizType=CONTRACT&bizId=<合同ID>

### GET /files/{id}/download

限制：

```text
单文件 20MB
保存到 bp.file.root
按租户分目录
```

---

## 29. 迁移异常

### GET /migration/exceptions?status=PENDING

### POST /migration/exceptions/{id}/resolve

```json
{"resolution": "ACCEPT_SKIP"}
```

状态：

```text
PENDING → RESOLVED
```

---

## 30. 验证脚本

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\verify-core.ps1
```

预期：

```text
111 个断言通过
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
补贴抵扣租金
设备业务资产
授权/人员钥匙包
菜单/角色模板
登录鉴权
资格复核
迁移异常处理
附件上传
计量与能耗
服务工单
访客通行
投诉与申诉
计费项目
公示管理
风险告警
信用惩戒
短租订单
开放平台
消息中心
用户管理
修改密码
菜单权限
```
