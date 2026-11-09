# 设备授权策略与 IoT 同步任务设计

> 任务编号：T-DEVICE-AUTH-01  
> 优先级：P0  
> 状态：设计稿，未编码  
> 依赖：IoT 平台设备权限接口、手机中继同步能力、合同/收款现有流程

---

## 1. 任务目标

在业务系统与 IoT 之间建立一层**设备授权策略**，解决：

```text
合同生效时，应该转移管理权、设二级管理员，还是只给使用权？
授权什么时候开始、什么时候结束？
欠费后冻结还是撤销？
短租和长租策略如何区分？
设备离线、手机中继同步时如何保持授权一致？
```

目标不是重写 IoT 四级权限，而是：

```text
业务系统输出授权策略和目标计划
IoT 执行四级权限和凭证
APP/小程序继续负责住户操作
```

---

## 2. 任务范围

### 包含

```text
项目级设备授权策略配置
合同级策略快照
三种租赁授权模式
合同期授权 + 欠费冻结
短租退房到期
离线租期（仅长租）
手机中继在线判定
二级管理员委派单
临时人员设备授权单
IoT 账号/设备/组织映射
同步任务、重试、对账
设备授权状态只读展示
```

### 不包含

```text
重新实现 IoT 四级权限
设备凭证下发
开门指令
车位模型
批量导入（另立任务）
资产交易流程本身（只接授权转移）
```

---

## 3. 已确认的默认值

| 项目 | 默认值 | 说明 |
|---|---|---|
| 长租默认模式 | 项目管理员配置 | TRANSFER_MANAGEMENT / SECONDARY_MANAGER / USE_ONLY |
| 短租默认模式 | USE_ONLY | 不产生管理员 |
| 提前期 | 7 天 | 授权早于账期开始 |
| 宽容期 | 3 天 | 账期结束后的欠费宽限 |
| 长租离线租期 | 30 天 | 项目可配，仅长租 |
| 短租离线租期 | 不启用 | 退房后到期 |
| 短租退房宽限 | 2 小时 | 项目可配 |
| 常连接心跳 | 60 秒 | 丢失 3 次判离线 |
| 门锁唤醒 | 24 小时 | 连续 3 个周期判离线 |
| 表计上报 | 24 小时 | 连续 3 个周期判离线 |
| 手机中继 | 连接平台即在线 | 空心跳也刷新 |
| 手机中继审计 | 记录操作账号 | 不强制绑定工单 |
| 策略变更 | 只影响新合同 | 老合同保留快照 |
| 资产转让授权 | 默认清空 | 可显式保留 |

---

## 4. 核心模型

### 4.1 三种租赁授权模式

#### TRANSFER_MANAGEMENT

```text
组织管理员保留所有权
承租人成为主管理员
承租人可创建二级管理员
同住人获得使用权
```

#### SECONDARY_MANAGER

```text
组织管理员保留所有权和主管理员
承租人成为二级管理员
承租人不能再创建管理员
同住人获得使用权
```

#### USE_ONLY

```text
组织管理员保留所有权和主管理员
承租人和同住人只有使用权
不产生管理员
```

### 4.2 设备侧三种主体

```text
所有者：唯一
主管理员：唯一
二级管理员：多个
通行授权：一张共享表
```

### 4.3 授权共享原则

```text
主管理员和二级管理员共同维护同一张授权表
授权属于设备，不属于管理员
granted_by 只做审计
撤销管理员不撤销其授出的使用权/访客权
```

---

## 5. 授权时间规则

### 5.1 长租

```text
authFrom = 合同开始日 - 7 天
authTo = 合同结束日 + 3 天
```

合同期内不按月延期。

支付只更新：

```text
paidThroughDate
欠费状态
冻结状态
```

### 5.2 短租

```text
authFrom = 入住时间 - 提前期
authTo = 退房时间 + 2 小时
```

不启用离线租期。

### 5.3 临时授权

```text
authFrom / authTo 由临时授权单决定
起止日期必填
不叠加离线租期
```

---

## 6. 欠费冻结

状态：

```text
ACTIVE
GRACE
SUSPENDED
EXPIRED
REVOKED
```

规则：

```text
账期结束 + 3 天宽容期
  ↓
SUSPENDED
  ↓
下发冻结
  ↓
补缴后恢复 ACTIVE
```

冻结时：

```text
使用权暂停
访客权暂停
管理员不能新增授权
开门拒绝
```

不删除授权，补缴后恢复。

---

## 7. 离线与在线

### 7.1 在线定义

```text
lastOnlineAt = 平台最近一次收到设备认证连接/心跳
```

不论：

```text
设备直连
手机中继
是否有业务数据
```

都算上线。

### 7.2 设备连接模式

| 模式 | 判定 |
|---|---|
| ALWAYS_ON | 60 秒心跳，丢失 3 次 |
| LOW_POWER_LOCK | 24 小时唤醒，连续 3 个周期未连接 |
| LOW_POWER_METER | 24 小时上报，连续 3 个周期未连接 |
| MANUAL | 最后一次平台连接 |

门锁状态：

```text
SLEEPING   1 个周期内
DELAYED    1~3 个周期
OFFLINE    超过 3 个周期
```

### 7.3 离线租期

仅长租：

```text
offlineValidUntil = min(authTo, lastOnlineAt + 30 天)
```

校验：

```text
offlineLeaseDays 必须大于
唤醒周期 × 离线判定周期 + 安全余量
```

短租：

```text
不使用离线租期
```

### 7.4 手机中继

```text
手机连接平台 → 记录 lastOnlineAt → 下发签名心跳包 → 设备更新时间/租期/冻结状态
```

空心跳也刷新在线时间和离线租期。

---

## 8. 策略配置

### 8.1 项目级

```text
devicePolicy
  longRentMode
  shortRentMode
  advanceDays
  graceDays
  offlineLeaseEnabled
  offlineLeaseDays
  shortRentCheckoutGraceHours
  phoneSyncEnabled
```

### 8.2 合同快照

合同签订时保存：

```text
policyCode
policyVersion
longRentMode / shortRentMode
advanceDays
graceDays
offlineLeaseEnabled
offlineLeaseDays
```

老合同不随项目配置变化。

---

## 9. 业务系统表结构建议

```text
bp_project_device_policy
  project_id
  long_rent_mode
  short_rent_mode
  advance_days
  grace_days
  offline_lease_enabled
  offline_lease_days
  short_rent_checkout_grace_hours
  phone_sync_enabled
  version

bp_contract_device_policy
  contract_id
  policy_snapshot_json
  policy_version
  auth_status
  paid_through_date
  last_sync_at
  sync_status
  last_error

bp_iot_account_mapping
  person_id
  iot_user_id
  phone
  status

bp_iot_device_mapping
  device_id
  iot_device_id
  iot_space_id
  model
  firmware
  offline_lease_supported
  phone_relay_supported

bp_iot_entitlement_snapshot
  device_id
  iot_device_id
  holder_iot_user_id
  level
  valid_from
  valid_to
  grant_id
  synced_at

bp_entitlement_sync_job
  id
  contract_id
  scope
  desired_state_json
  status
  retry_count
  last_error

bp_device_manager_delegation
  id
  device_id
  grantee_person_id
  manager_tier
  parent_grant_id
  created_by
  valid_from
  valid_to
  iot_grant_id
  status
```

现有 `bp_grant_entitlement`：

```text
停止新增设备四级授权写入
保留历史只读
新授权以 IoT 为准
```

---

## 10. IoT 接口清单

```text
transferOwnership(deviceId, newOwner)
transferPrimaryManager(deviceId, newManager)
returnPrimaryManager(deviceId, reason)
createSecondaryManager(deviceId, manager, validFrom, validTo, creator)
revokeSecondaryManager(grantId, reason)
grantUser(deviceId, userId, validFrom, validTo)
grantVisitor(deviceId, userId, validFrom, validTo, singleUse)
revokeGrant(grantId, reason)
setFreezeState(scope, FROZEN/ACTIVE, reason)
provisionContractEntitlement(scope, plan)
getDeviceEntitlements(deviceId)
getDeviceOnlineStatus(deviceId)
```

---

## 11. 业务流程

### 11.1 合同生效

```text
合同签订
  ↓
读取项目策略
  ↓
保存合同快照
  ↓
等待收款
  ↓
收款成功
  ↓
计算 Desired Plan
  ↓
调用 IoT
  ↓
记录同步结果
```

### 11.2 长租转移管理权

```text
owner = 组织管理员
primaryManager = 承租人
users = 同住人
```

### 11.3 长租二级管理员

```text
owner = 组织管理员
primaryManager = 组织管理员
secondaryManager = 承租人
```

### 11.4 短租

```text
owner = 组织管理员
primaryManager = 组织管理员
users = 承租人/同住人
authTo = 退房时间 + 2 小时
```

### 11.5 欠费

```text
账期结束 + 3 天
  ↓
SUSPENDED
  ↓
冻结
  ↓
补缴恢复
```

### 11.6 资产转让

```text
转移所有权
转移主管理员
撤销原二级管理员
默认清空使用权/访客权
```

---

## 12. 前端页面

### 项目设置

```text
设备授权策略
  长租模式
  短租模式
  提前期/宽容期
  离线租期
  短租退房宽限
  手机中继开关
```

### 合同详情

```text
设备授权策略快照
授权状态
同步状态
待同步原因
```

### 设备详情

```text
所有者（只读）
主管理员（转移/归还）
二级管理员（新增/撤销）
通行授权（只读或临时授权）
在线状态
最后在线时间
离线租期到期
```

### 设备列表

```text
筛选：在线 / 休眠 / 离线 / 待同步 / 离线租期即将到期
```

---

## 13. 验收标准

```text
合同生效后按策略生成 Desired Plan
长租不按月调用延期
三种租赁模式都正确
短租不使用离线租期
短租退房后 2 小时到期
欠费 3 天后冻结
补缴后解冻
合同结束本地到期
门锁连续 3 个周期未连接才判离线
单次联网失败不判离线
手机中继空心跳也刷新在线时间和离线租期
手机中继记录操作账号
所有者唯一
主管理员唯一
二级管理员多个
撤销二级管理员不撤销其授权
资产转让默认清空授权
同步失败可重试
同步记录可审计
```

---

## 14. 实施步骤

### 第 1 步：模型与配置

```text
项目策略表
合同策略快照
IoT 映射表
同步任务表
```

### 第 2 步：只读接入

```text
设备授权查询
在线状态查询
同步状态展示
```

### 第 3 步：合同授权

```text
三种模式
Desired Plan
IoT 调用
Outbox 重试
```

### 第 4 步：冻结/解冻

```text
欠费任务
补缴恢复
短租到期
```

### 第 5 步：二级管理员和临时授权

```text
委派单
临时授权单
撤销
```

### 第 6 步：手机中继

```text
会话记录
空心跳
离线租期刷新
审计
```

---

## 15. 风险与依赖

```text
IoT 接口是否已具备全部能力
设备固件是否支持签名时间/离线租期
手机中继协议是否支持空心跳
账号映射是否完整
混合设备能力差异
老合同策略迁移
同步失败的业务兜底
```

---

## 16. 结论

```text
业务系统负责策略和计划
IoT 负责四级权限和凭证
APP/小程序负责住户操作

长租：合同期授权 + 欠费冻结 + 30 天离线租期
短租：退房 + 2 小时到期，不使用离线租期
临时：按授权单期限，不使用离线租期
门锁：24 小时唤醒，连续 3 个周期判离线
手机中继：连接平台即在线，空心跳也刷新
```
