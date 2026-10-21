# 云门道业务平台 —— API 契约（第三轮）

| 项目 | 内容 |
|---|---|
| 文档名称 | 云门道业务平台 · API 契约 |
| 文档版本 | V0.9（第三轮 · 待评审） |
| 交付轮次 | 第 3 / 3 轮（配套 `03_数据库设计_P1~P5.sql`） |
| 适用范围 | ① 管理后台/移动端 → 业务平台；② 业务平台 → 云门道 IoT 平台；③ 第三方 → 开放 API |
| 基础路径 | 内部 API：`/api/v1`；开放 API：`/open/v1`；**回调：`/api/callback/ymd/{env}/{appCode}`** |

---

## 1. 通用规范

### 1.1 协议与编码

| 项 | 约定 |
|---|---|
| 协议 | HTTPS（TLS 1.2+） |
| 方法 | `GET` 查询 / `POST` 新增与复杂查询 / `PUT` 全量更新 / `PATCH` 部分更新 / `DELETE` 删除（实际为逻辑删除） |
| 编码 | UTF-8 |
| 请求体 | `application/json`（文件上传除外，用 `multipart/form-data`） |
| 时间格式 | `yyyy-MM-dd HH:mm:ss`（日期 `yyyy-MM-dd`）；**时区统一 Asia/Shanghai** |
| 命名风格 | JSON 字段用 **camelCase**（与前端一致）；DB 列为 snake_case，由映射层转换 |
| 金额 | **字符串传输**（避免 JS 浮点精度丢失），如 `"1200.00"` |
| 大整数 ID | **字符串传输**（雪花 ID 超出 JS 安全整数范围），如 `"1856234123456789"` |

> ⚠️ **金额与 ID 用字符串**是硬性约定。JS 的 `Number.MAX_SAFE_INTEGER` 为 2^53-1，
> 雪花 ID 为 64 位，直接传数字会在前端**静默丢精度**。这是实际项目中最常见的坑之一。

### 1.2 认证

| 场景 | 方式 |
|---|---|
| 后台/移动端 | `Authorization: Bearer <JWT>`；登录接口返回 |
| 开放 API | `X-App-Key` + `X-Timestamp` + `X-Nonce` + `X-Sign`（HMAC-SHA256） |
| 回调（IoT → 平台） | IP 白名单 + 可选共享密钥（`X-Callback-Secret`） |

**JWT 载荷**
```json
{
  "sub": "1856234123456789",
  "tenantId": "350600",
  "orgId": "1856234123456790",
  "userId": "1856234123456789",
  "dataScope": "ORG_TREE",
  "scopes": ["asset:house:view", "grant:task:edit"],
  "deviceId": "web-abc123",
  "jti": "a1b2c3d4",
  "exp": 1792000000
}
```

**多租户传递**：JWT 中的 `tenantId` 为准；**禁止**从 URL 或请求体读取 `tenantId` 覆盖
（防止越权）。平台级角色跨租户操作时，用独立接口并强制审计。

### 1.3 统一响应体

**成功**
```json
{
  "code": "0",
  "message": "success",
  "data": { },
  "traceId": "B98BFCB3-73DC-4325-B1D7-7ECD2BA1D006",
  "timestamp": 1792000000000
}
```

**失败**
```json
{
  "code": "BP40001",
  "message": "房源状态不允许配租",
  "data": null,
  "traceId": "B98BFCB3-73DC-4325-B1D7-7ECD2BA1D006",
  "timestamp": 1792000000000,
  "errors": [
    { "field": "houseId", "message": "房源当前状态为 LOCKED，不可重复配租" }
  ]
}
```

| 字段 | 说明 |
|---|---|
| `code` | `"0"` 成功；其他为错误码（字符串） |
| `message` | 面向用户的提示（可直接展示） |
| `data` | 业务数据；查询列表时为 `PageResult` |
| `traceId` | 链路追踪 ID，**排查问题时必须提供** |
| `timestamp` | 服务端毫秒时间戳 |
| `errors` | 字段级校验错误（可选） |

### 1.4 分页

**请求**（`GET` 用 query，`POST` 查询用 body）
```json
{ "pageNum": 1, "pageSize": 20, "orderBy": "createTime", "orderDirection": "DESC" }
```

**响应**
```json
{
  "code": "0",
  "data": {
    "list": [ ],
    "pageNum": 1,
    "pageSize": 20,
    "total": 44148,
    "pages": 2208,
    "hasNextPage": true
  }
}
```

**约束**
1. `pageSize` 上限 **200**（超出按 200 处理）；
2. 深分页（`pageNum > 100`）走**游标模式**（`searchAfter` 参数）或强制加筛选条件；
3. **导出必须走异步**（`POST /api/v1/export/task`），不得用分页循环。

### 1.5 错误码规范

格式：`BP + HTTP 语义 + 业务序号`，共 5-7 位。

| 段 | 含义 |
|---|---|
| `BP` | 业务平台前缀 |
| 第 3 位 | 类别：`1` 参数 / `2` 认证授权 / `3` 业务规则 / `4` 资源 / `5` 系统 / `6` 外部依赖 |
| 后 3 位 | 序号 |

| 错误码 | HTTP | 说明 |
|---|---|---|
| `BP10001` | 400 | 参数校验失败 |
| `BP10002` | 400 | 参数格式错误 |
| `BP20001` | 401 | 未登录或令牌失效 |
| `BP20002` | 403 | 无权限访问 |
| `BP20003` | 403 | 数据权限越界 |
| `BP20004` | 403 | 单设备登录冲突（账号在别处登录） |
| `BP30001` | 409 | 业务状态不允许该操作 |
| `BP30002` | 409 | 幂等冲突（重复请求） |
| `BP30003` | 409 | 房源已被锁定 |
| `BP30004` | 409 | 合同状态不允许该操作 |
| `BP30005` | 409 | 权益已存在，无需重复授权 |
| `BP40001` | 404 | 资源不存在 |
| `BP40002` | 404 | 租户不存在或已停用 |
| `BP50001` | 500 | 系统内部错误 |
| `BP50002` | 500 | 数据一致性校验失败 |
| `BP60001` | 502 | **IoT 平台调用失败**（附 `iotErrorCode`） |
| `BP60002` | 502 | IoT 平台限流 |
| `BP60003` | 504 | IoT 平台超时 |
| `BP60004` | 502 | 外部系统（公安/公租房/财政等）调用失败 |
| `BP60005` | 500 | 加密算法配置错误（见第二轮 §4.3 阻塞项） |

> **IoT 错误码透传**：`BP60001` 的响应体必须携带 IoT 原始错误码（如 `99990001`），
> 便于运维直接定位（见 `_调研/接口能力清单-可用于集成设计.md` 错误码表）。

### 1.6 幂等

**需要幂等的接口**（写操作）：授权、缴费、账单生成、审批提交。

| 方式 | 适用 |
|---|---|
| `Idempotency-Key` 请求头 | 内部 API（推荐） |
| 请求体 `idempotentKey` | 开放 API |
| 业务唯一键 | 服务端兜底（如 `bp_grant_task.uk_idempotent`） |

**规则**：同一 `Idempotency-Key` 在 **24 小时**内重复请求，返回**首次结果**（HTTP 200），
不重复执行；冲突时返回 `BP30002` 并附首次的 `data`。

### 1.7 限流

| 接口类型 | 默认配额 | 超限响应 |
|---|---|---|
| 登录类 | 5 次/分钟/账号 | `BP20005`（429） |
| 查询类 | 100 QPS/租户 | 429 + `Retry-After` |
| 写操作类 | 20 QPS/租户 | 429 |
| 导出类 | 5 次/小时/用户 | `BP30006` |
| 开放 API | 按 `bp_open_app.qps_limit` | 429 |
| 回调接收 | 不限（但幂等去重） | — |

### 1.8 版本与兼容

1. 路径版本：`/api/v1`；破坏性变更升 `v2`；
2. **字段只增不删不改语义**；废弃字段保留并标注 `@deprecated`，**至少保留 2 个大版本**；
3. 响应体**禁止**依赖字段顺序；
4. 新增枚举值时，客户端必须能**容错处理未知值**。

---

## 2. 核心接口清单

> 完整清单见 OpenAPI 文档（开发阶段产出）。此处列出**关键契约**。

### 2.1 认证与租户

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/auth/login` | 账号密码登录 |
| POST | `/api/v1/auth/login/sms` | 短信登录 |
| POST | `/api/v1/auth/logout` | 登出 |
| POST | `/api/v1/auth/refresh` | 刷新令牌 |
| GET | `/api/v1/auth/userinfo` | 当前用户信息 + 权限 + 菜单 |
| POST | `/api/v1/auth/switch-org` | 切换组织（多组织用户） |

**`POST /api/v1/auth/login`**
```json
// Request
{ "username": "luoyi", "password": "******", "deviceId": "web-abc123", "captcha": "8f2a" }

// Response
{
  "code": "0",
  "data": {
    "accessToken": "eyJhbGciOi...",
    "refreshToken": "eyJhbGciOi...",
    "expiresIn": 7200,
    "userInfo": {
      "userId": "1856234123456789",
      "userName": "罗",
      "tenantId": "350600",
      "tenantName": "漳州市住房保障中心",
      "orgId": "1856234123456790",
      "orgName": "漳州安居智家",
      "userType": "GOV",
      "roles": [{ "roleCode": "QUALIFY_REVIEWER", "roleName": "资格审核员" }]
    }
  }
}
```

**错误场景**
| 场景 | 错误码 |
|---|---|
| 账号或密码错误 | `BP20001` |
| 账号被禁用 | `BP20001`（message 说明） |
| **单设备登录冲突** | `BP20004`（提示"账号已在其他设备登录"） |
| 触发验证码 | `BP10003`（需带验证码重试） |
| 登录频率超限 | `BP20005` |

---

### 2.2 空间与房源

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/spaces/tree` | 空间树（支持 `orgId`/`spaceType`/`maxLevel` 过滤） |
| GET | `/api/v1/spaces/{id}` | 空间详情 |
| POST | `/api/v1/spaces` | 新增空间 |
| PUT | `/api/v1/spaces/{id}` | 修改空间 |
| DELETE | `/api/v1/spaces/{id}` | 删除空间（需校验无子节点、无绑定） |
| POST | `/api/v1/spaces/batch-import` | 空间批量导入（**异步**） |
| GET | `/api/v1/houses` | 房源列表（**多维筛选**） |
| GET | `/api/v1/houses/{id}` | 房源详情 |
| POST | `/api/v1/houses` | 新增房源 |
| PATCH | `/api/v1/houses/{id}/status` | 变更房源状态 |
| GET | `/api/v1/houses/statistics` | 房源统计（大屏用，**走预聚合**） |

**`GET /api/v1/houses`（对应漳州标【指标17】多维条件查询）**

参数：
```
tenantId    （隐式，取 JWT）
orgId       组织和项目
spaceId     空间（含子空间，用 spacePath 前缀匹配）
houseCode   房源编号
houseName   房源名称（模糊）
houseType   PUBLIC_RENTAL / AFFORDABLE_RENTAL / TALENT / APARTMENT / ...
houseStatus PENDING_ALLOC / LOCKED / ALLOCATED / OCCUPIED / VACANT / MAINTENANCE / DISABLED
securityType
rentMin / rentMax
areaMin / areaMax
occupantName    承租人姓名（联表 person）
occupantIdCard  承租人身份证（**用 hash 精确匹配**）
occupantCount   入住人数
hasDevice       true/false（是否已绑定设备）
pageNum / pageSize
```

响应 `list` 项：
```json
{
  "houseId": "1856234123456789",
  "houseCode": "ZZ-2026-0001",
  "houseName": "金麓小区B9幢9单元401室",
  "houseType": "PUBLIC_RENTAL",
  "securityType": "PUBLIC",
  "houseStatus": "OCCUPIED",
  "houseStatusName": "已入住",
  "orgId": "1856234123456790",
  "orgName": "漳州安居智家",
  "spaceId": "1856234123456800",
  "spacePath": "/1/12/125/1250/",
  "spaceFullName": "金麓小区/B9幢/9单元/401室",
  "area": "169.61",
  "rentStandard": "12.00",
  "rentUnit": "AREA_MONTH",
  "monthlyRent": "2035.32",
  "maxCapacity": 4,
  "currentCapacity": 3,
  "occupants": [
    { "personId": "1856234123456810", "personName": "刘俊匣", "idCardMask": "1307********1027", "occupyType": "TENANT" }
  ],
  "contractId": "1856234123456820",
  "contractNo": "HT-2026-0001",
  "contractStatus": "EFFECTIVE",
  "leaseEnd": "2027-06-30",
  "lockCount": 2,
  "onlineLockCount": 2,
  "createTime": "2026-01-15 10:30:00"
}
```

> **性能要求**：列表默认只返回房源主表字段 + 承租人摘要；
> `occupants` 与合同信息**按需返回**（加 `include=occupants,contract` 参数），避免大列表拖垮查询。

---

### 2.3 人员与保障对象

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/persons` | 人员列表 |
| GET | `/api/v1/persons/{id}` | 人员详情（含档案、家庭、证件） |
| POST | `/api/v1/persons` | 新增人员 |
| PATCH | `/api/v1/persons/{id}` | 修改人员 |
| GET | `/api/v1/persons/{id}/keyring` | **我的钥匙包**（竞品/厂家方案核心） |
| POST | `/api/v1/persons/{id}/verify` | **触发实名认证**（转调 IoT §9） |
| GET | `/api/v1/persons/guarantee-profiles` | 保障对象档案列表 |
| PATCH | `/api/v1/persons/{id}/guarantee-profile` | 更新保障对象档案 |

**`POST /api/v1/persons/{id}/verify`**
```json
// Request
{ "verifyType": "PERSONAL", "faceImgBase64": "data:image/jpeg;base64,/9j/4AA..." }

// Response
{
  "code": "0",
  "data": {
    "verifyRecordId": "1856234123456900",
    "verifyStatus": "VERIFIED",
    "faceScore": "70.00",
    "faceResult": "1",
    "faceResultText": "系统判断为同一人",
    "citizenResult": "1",
    "citizenResultText": "一致",
    "verifyTime": "2026-10-16 10:30:00"
  }
}
```

**失败场景**
| 场景 | 错误码 | 说明 |
|---|---|---|
| 人照不一致 | `0`（业务成功）但 `verifyStatus=FAILED` | **认证失败不是接口错误**，用业务字段表达 |
| 库中无此身份证 | `0`，`citizenResult=3` | |
| IoT 实名接口不可用 | `BP60001` | 需重试或转人工 |
| 加密算法配置错误 | `BP60005` | 阻塞类错误 |

> **重要设计决策**：实名**认证失败**（人照不同/查无此人）返回 **HTTP 200 + `code=0`**，
> 通过 `verifyStatus` 表达业务结论。只有**调用链路失败**才返回错误码。
> 这样前端可区分"认证不通过"与"系统故障"——这是政务项目中容易被混淆的点。

---

### 2.4 权益与授权（★核心）

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/grants/entitlements` | 权益列表 |
| POST | `/api/v1/grants/entitlements` | 新增权益（含空间继承计算） |
| POST | `/api/v1/grants/entitlements/{id}/revoke` | 撤销权益 |
| POST | `/api/v1/grants/entitlements/{id}/freeze` | 冻结权益 |
| POST | `/api/v1/grants/entitlements/{id}/unfreeze` | 解冻 |
| POST | `/api/v1/grants/person-grant` | **按人授权**（自动匹配钥匙）★ |
| POST | `/api/v1/grants/batch-grant` | 批量授权（按空间/人群） |
| POST | `/api/v1/grants/batch-revoke` | 批量撤销 |
| GET | `/api/v1/grants/tasks` | 授权任务列表 |
| GET | `/api/v1/grants/tasks/{id}` | 授权任务详情（含逐锁结果） |
| POST | `/api/v1/grants/tasks/{id}/retry` | 重试失败任务 |
| GET | `/api/v1/grants/reconcile-diffs` | 对账差异列表 |

**`POST /api/v1/grants/person-grant`（以人为中心，不选钥匙）★**

```json
// Request
{
  "personId": "1856234123456810",
  "spaceId": "1856234123456800",
  "grantLevel": "USAGE",
  "validStart": "2026-11-01 00:00:00",
  "validEnd": "2027-10-31 23:59:59",
  "autoMatchKey": true,            // ★ true=自动匹配钥匙包（推荐）
  "keyringIds": [],                // autoMatchKey=false 时指定
  "sourceType": "CONTRACT",
  "sourceId": "1856234123456820",
  "idempotentKey": "sha1(personId+spaceId+level)"
}

// Response
{
  "code": "0",
  "data": {
    "entitlementId": "1856234123456910",
    "taskNo": "GRT20261016001",
    "taskStatus": "DISPATCHING",
    "lockCount": 3,
    "matchedKeys": [
      { "keyringId": "1", "keyType": "FACE", "keyClass": "PERSONAL_REAL", "keyAlias": "人脸" },
      { "keyringId": "2", "keyType": "FINGERPRINT", "keyClass": "PERSONAL_REAL", "keyAlias": "右手大拇指" }
    ],
    "skippedKeys": [
      { "keyringId": "3", "keyType": "IC_CARD", "keyClass": "PERSONAL_UNREAL", "reason": "该设备为实名工作模式，非实名钥匙不下发" }
    ]
  }
}
```

**关键语义**
1. **`autoMatchKey=true` 时，服务端按钥匙分类 × 设备实名模式自动匹配**（对应厂家方案核心卖点）；
2. **被跳过的钥匙必须返回并说明原因**——这是"合规匹配"的可解释性，不能静默丢弃；
3. 授权为**异步**：接口返回 `DISPATCHING`，客户端需轮询任务或订阅 Webhook；
4. 幂等键冲突返回 `BP30002` + 首次结果。

**`GET /api/v1/grants/tasks/{id}`（含逐锁结果）**
```json
{
  "code": "0",
  "data": {
    "taskNo": "GRT20261016001",
    "taskType": "GRANT",
    "taskStatus": "PARTIAL",
    "personId": "...", "personName": "刘俊匣",
    "lockCount": 3, "successCount": 2, "failCount": 1,
    "dispatchTime": "2026-10-16 10:30:05",
    "finishTime": "2026-10-16 10:30:18",
    "iotTaskId": "13D4A20261016...",
    "details": [
      { "deviceId": "13D4AFE181121149952237877", "deviceMac": "FF00FFE16751", "spaceId": "...", "spaceName": "B9幢9单元401室", "detailStatus": "SUCCESS", "durationMs": 820 },
      { "deviceId": "...", "detailStatus": "FAILED", "errorCode": "99990001", "errorMsg": "授权微服务不在线，或者网络超时" }
    ]
  }
}
```

> **设计要点**：`errorCode` 直接透传 IoT 错误码，运维可对照
> `_调研/接口能力清单-可用于集成设计.md` 的错误码表**立即定位**，无需二次排查。

---

### 2.5 业务办理（申请→审核→轮候→配租→合同→退出）

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/biz/applications` | 提交申请 |
| GET | `/api/v1/biz/applications` | 申请列表 |
| GET | `/api/v1/biz/applications/{id}` | 申请详情（含审核轨迹） |
| POST | `/api/v1/biz/applications/{id}/accept` | 受理 |
| POST | `/api/v1/biz/applications/{id}/review` | **审核（联审）** |
| POST | `/api/v1/biz/applications/{id}/supplement` | 补件 |
| GET | `/api/v1/biz/waiting-queue` | 轮候库 |
| GET | `/api/v1/biz/batches` | 配租批次 |
| POST | `/api/v1/biz/batches/{id}/lottery` | **执行摇号** |
| POST | `/api/v1/biz/batches/{id}/select-house` | 选房 |
| GET | `/api/v1/biz/lottery-results` | 摇号/选房结果 |
| POST | `/api/v1/biz/allocations` | 生成配租单 |
| GET | `/api/v1/biz/contracts` | 合同列表 |
| POST | `/api/v1/biz/contracts` | 生成合同 |
| POST | `/api/v1/biz/contracts/{id}/sign` | **发起签署**（电子签章） |
| POST | `/api/v1/biz/contracts/{id}/renew` | 续签 |
| POST | `/api/v1/biz/contracts/{id}/terminate` | 终止 |
| POST | `/api/v1/biz/terminations` | 退租申请 |
| POST | `/api/v1/biz/terminations/{id}/complete` | 完成退租（**释放房源 + 回收授权**） |
| GET | `/api/v1/biz/annual-reviews` | 年度复核列表 |
| POST | `/api/v1/biz/annual-reviews/{id}/submit` | 提交复核结论 |
| POST | `/api/v1/biz/exchanges` | 换房（**权限自动迁移**） |

**`POST /api/v1/biz/batches/{id}/lottery`（摇号，公证留痕）**
```json
// Request
{
  "participantIds": ["..."],       // 参与人员（留空则取轮候库符合条件者）
  "seed": "a3f8c1e2",              // ★ 随机种子（公证留痕，可由公证员现场生成）
  "algorithm": "FISHER_YATES_V1",
  "notaryInfo": { "office": "漳州市公证处", "notary": "张三", "certNo": "ZZ2026-1234" }
}

// Response
{
  "code": "0",
  "data": {
    "batchId": "...",
    "lotteryTime": "2026-10-20 09:00:00",
    "seed": "a3f8c1e2",
    "algorithm": "FISHER_YATES_V1",
    "participantCount": 500,
    "houseCount": 120,
    "wonCount": 120,
    "waitlistCount": 30,
    "resultFileUrl": "https://.../lottery-20261020.xlsx"
  }
}
```

> **公证留痕设计**：`seed` + `algorithm` + 参与名单 + 结果**全部落库**。
> 同一种子 + 同一算法 + 同一名单**可复现同一结果**，满足公证与审计要求。这是摇号功能的合规基础。

**`POST /api/v1/biz/terminations/{id}/complete`（退租完成，联动）**
```json
// Request
{
  "actualExitDate": "2026-10-31",
  "inspectResult": "PASSED",
  "damageAmount": "200.00",
  "depositRefund": "1800.00",
  "arrearsAmount": "0.00",
  "releaseHouse": true,        // 释放房源回可配池
  "revokeGrant": true          // ★ 回收全部授权
}

// Response
{
  "code": "0",
  "data": {
    "terminationNo": "TZ20261031001",
    "terminationStatus": "COMPLETED",
    "houseReleased": true,
    "houseStatus": "VACANT",
    "grantRevokeTaskNo": "GRT20261031009",
    "grantRevokeStatus": "DISPATCHING",
    "settleAmount": "1600.00",
    "refundId": "1856234123456999"
  }
}
```

> **关键**：退租完成 = **房源释放 + 授权回收 + 结算**三件事的编排。
> 授权回收是**异步**的，返回 `DISPATCHING`，需轮询或订阅事件确认最终结果——
> 不能假设"调用成功即回收成功"。

---

### 2.6 账单与缴费

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/fin/bills` | 账单列表 |
| POST | `/api/v1/fin/bills/generate` | 批量生成账单（**异步**） |
| GET | `/api/v1/fin/bills/{id}` | 账单详情 |
| POST | `/api/v1/fin/payments` | 收款登记 |
| POST | `/api/v1/fin/payments/{id}/allocate` | 收款核销 |
| POST | `/api/v1/fin/payments/unknown` | **未知款项挂账** |
| POST | `/api/v1/fin/payments/{id}/link` | **未知款项关联应收** |
| GET | `/api/v1/fin/payments/pay-url` | 获取支付链接/二维码 |
| POST | `/api/v1/fin/deposits/refund` | 押金退还 |
| POST | `/api/v1/fin/subsidies/generate` | 生成补贴发放清单 |
| POST | `/api/v1/fin/subsidies/{id}/issue` | 执行发放 |
| POST | `/api/v1/fin/dunning` | 催缴登记 |
| POST | `/api/v1/fin/arrears/action` | **欠费处置（冻结/通知）** |
| GET | `/api/v1/fin/reconcile` | 对账查询 |

**`POST /api/v1/fin/arrears/action`（欠费停权，含安全底线）**
```json
// Request
{
  "contractId": "1856234123456820",
  "actionType": "FREEZE",
  "freezeScope": "EXCLUDE_MAIN_DOOR",   // ★ 排除大门门禁（消防/安全底线）
  "triggerType": "AUTO",
  "reason": "欠费超过 30 天，系统自动冻结房门权限",
  "notifyChannels": ["SMS", "WECHAT", "INNER"]
}

// Response
{
  "code": "0",
  "data": {
    "actionNo": "ARS20261016001",
    "actionStatus": "EXECUTED",
    "arrearsAmount": "2035.32",
    "overdueDays": 35,
    "freezeScope": "EXCLUDE_MAIN_DOOR",
    "frozenDeviceCount": 1,
    "skippedDeviceCount": 2,
    "skippedReason": "大门门禁与单元门禁按安全策略排除",
    "grantTaskNo": "GRT20261016010"
  }
}
```

> ⭐ **`freezeScope` 是本设计的重点**：欠费停权**不应停掉大门门禁**
> （涉及消防疏散与基本出入权利），这是**安全底线**。
> 参数化设计让该策略可配置，且响应中**明确说明哪些设备被排除及原因**——
> 这是政务项目中被追责时的重要举证。

---

### 2.7 通行记录与告警

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/dev/access-records` | 通行记录查询（**多维**） |
| GET | `/api/v1/dev/access-records/track` | **行为轨迹**（人-空间-设备） |
| GET | `/api/v1/dev/devices` | 设备列表（含在线状态） |
| GET | `/api/v1/dev/devices/{id}` | 设备详情 |
| GET | `/api/v1/dev/devices/online-rate` | **在线率统计**（考核数据） |
| GET | `/api/v1/dev/availability` | **核心功能可用率**（考核数据） |
| GET | `/api/v1/ops/alerts` | 告警列表 |
| PATCH | `/api/v1/ops/alerts/{id}/handle` | 告警处置 |
| GET | `/api/v1/ops/alert-rules` | 告警规则列表 |
| PUT | `/api/v1/ops/alert-rules/{id}` | 修改告警规则（阈值可配） |
| GET | `/api/v1/ops/auto-inspections` | 自动巡查结果 |
| POST | `/api/v1/ops/house-visits` | 巡房/走访登记 |
| GET | `/api/v1/ops/workorders` | 工单列表 |
| POST | `/api/v1/ops/workorders` | 创建工单 |
| POST | `/api/v1/ops/workorders/{id}/assign` | 派单 |
| POST | `/api/v1/ops/workorders/{id}/finish` | 完工 |
| POST | `/api/v1/ops/workorders/{id}/close` | 闭环 |

**`GET /api/v1/dev/access-records`（对应漳州标"不可信开门占比"）**

参数：`personId` / `houseId` / `spaceId` / `deviceId` / `openType` / `isTrusted` / `isAbnormal`
/ `startTime` / `endTime` / `pageNum` / `pageSize`

```json
// Response list 项
{
  "id": "1856234123457001",
  "eventId": "202209011701",
  "deviceMac": "FF00FFE16751",
  "spaceName": "金麓小区B9幢9单元401室",
  "personName": "刘俊匣",
  "targetUserMobile": "13512100239",
  "openType": "1049",
  "openTypeName": "人脸开门",
  "isTrusted": true,
  "isAbnormal": false,
  "openTime": "2026-10-16 08:15:22",
  "source": "CALLBACK"
}
```

**`GET /api/v1/dev/access-records/track`（行为轨迹，对应"人-空间-设备"）**

参数：`personId` + `startTime`/`endTime`；可选 `deviceType`（只看向门锁/门禁/梯控/道闸）。

```json
{
  "code": "0",
  "data": {
    "personId": "...", "personName": "刘俊匣",
    "startTime": "2026-10-01 00:00:00", "endTime": "2026-10-16 23:59:59",
    "totalCount": 42,
    "tracks": [
      {
        "date": "2026-10-16",
        "events": [
          { "time": "08:15:22", "deviceType": "LOCK", "deviceName": "B9幢9单元401室门锁", "spaceName": "金麓小区/B9幢/9单元/401室", "openTypeName": "人脸开门", "result": "SUCCESS" },
          { "time": "08:16:10", "deviceType": "ELEVATOR", "deviceName": "9单元电梯", "spaceName": "金麓小区/B9幢/9单元", "openTypeName": "梯控呼梯", "result": "SUCCESS" },
          { "time": "18:42:05", "deviceType": "ACCESS", "deviceName": "小区大门门禁", "spaceName": "金麓小区", "openTypeName": "APP开门", "result": "SUCCESS" }
        ]
      }
    ]
  }
}
```

**`GET /api/v1/dev/devices/online-rate`（考核数据，可导出）**

参数：`orgId` / `period`（如 `2026-H1`）/ `startDate` / `endDate` / `deviceType`

```json
{
  "code": "0",
  "data": {
    "period": "2026-H1",
    "startDate": "2026-01-01", "endDate": "2026-06-30",
    "overall": { "totalCount": 5771, "onlineCount": 5702, "onlineRate": "0.9881", "pass": true, "threshold": "0.98" },
    "byOrg": [
      { "orgId": "...", "orgName": "芗城区", "totalCount": 2000, "onlineCount": 1980, "onlineRate": "0.9900", "pass": true }
    ],
    "byType": [ { "deviceType": "LOCK", "totalCount": 5771, "onlineCount": 5702, "onlineRate": "0.9881" } ]
  }
}
```

> **设计要点**：在线率的 `threshold` 与 `pass` 判定**由服务端计算并返回**，
> 避免客户端各自实现判定逻辑产生口径不一致。考核数据必须**可导出**（`POST /api/v1/export/task`）。

**`PATCH /api/v1/ops/alerts/{id}/handle`**
```json
// Request
{ "handleAction": "FREEZE", "handleResult": "已核实转租，已冻结房门权限并下发通知书", "workorderRequired": true }

// Response
{ "code": "0", "data": { "alertNo": "AL20261016001", "alertStatus": "HANDLED", "handleTime": "2026-10-16 11:00:00", "workorderNo": "WO20261016088" } }
```

---

### 2.8 报表与导出

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/v1/rpt/reports` | 报表列表 |
| POST | `/api/v1/rpt/reports/{code}/query` | 执行报表查询 |
| POST | `/api/v1/export/task` | **创建导出任务**（异步） |
| GET | `/api/v1/export/task/{taskNo}` | 查询导出进度 |
| GET | `/api/v1/rpt/metrics` | 指标查询（大屏用） |
| GET | `/api/v1/rpt/screens/{code}` | 获取大屏数据 |

**`POST /api/v1/export/task`（对应漳州标合同义务：Excel + 时间跨度自定义）**
```json
// Request
{
  "exportType": "WORKORDER",        // WORKORDER / ONLINE_RATE / FAULT_STAT / AVAILABILITY / ALERT / CUSTOM
  "queryParams": {
    "startTime": "2026-01-01 00:00:00",
    "endTime": "2026-06-30 23:59:59",
    "orgIds": ["..."],
    "fields": ["workorderNo", "reporterName", "reportTime", "closeTime", "isDeviceChanged"]
  },
  "fileName": "工单记录_2026H1.xlsx"
}

// Response（立即返回，异步生成）
{ "code": "0", "data": { "taskNo": "EXP20261016001", "taskStatus": "PENDING", "estimatedRows": 3381 } }
```

**约束**：导出为**异步任务**，结果落对象存储并返回签名 URL（有效期 7 天）。
**禁止**同步导出大数据集（会占满连接与内存）。

---

### 2.9 监管报送与开放平台

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/gov/report-tasks` | 创建报送任务 |
| GET | `/api/v1/gov/report-tasks/{taskNo}` | 查询报送进度 |
| GET | `/api/v1/gov/report-tasks` | 报送任务列表 |
| GET | `/api/v1/open/apps` | 开放应用管理 |
| POST | `/api/v1/open/apps` | 创建应用（生成 appKey/appSecret） |
| PUT | `/api/v1/open/apps/{id}` | 修改配额/权限 |
| GET | `/api/v1/open/webhooks` | Webhook 列表 |
| POST | `/api/v1/open/webhooks` | 创建 Webhook |

**开放 API（第三方 → 平台）**

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/open/v1/houses/query` | 房源查询 |
| POST | `/open/v1/houses/sync` | 房源同步（公租房系统 → 平台 / 反向） |
| POST | `/open/v1/persons/query` | 人员查询 |
| POST | `/open/v1/contracts/query` | 合同查询 |
| POST | `/open/v1/access-records/query` | 通行记录查询 |
| POST | `/open/v1/alerts/query` | 告警查询 |
| POST | `/open/v1/grants/apply` | 授权申请（第三方发起） |

**签名算法**（开放 API）
```
signStr = appKey + timestamp + nonce + requestBody(MD5) + appSecret
X-Sign  = HMAC-SHA256(signStr, appSecret) 的十六进制大写
```
| 请求头 | 说明 |
|---|---|
| `X-App-Key` | 应用标识 |
| `X-Timestamp` | 毫秒时间戳（**与服务端偏差 ≤5 分钟**，防重放） |
| `X-Nonce` | 随机串（**5 分钟内不可重复**，Redis 去重） |
| `X-Sign` | 签名 |

**Webhook 推送体**
```json
{
  "eventType": "access.record",
  "eventVersion": "1.0",
  "eventId": "202209011701",
  "occurredAt": "2026-10-16T08:15:22+08:00",
  "tenantId": "350600",
  "data": { "deviceMac": "FF00FFE16751", "openType": "1049", "openTime": "2026-10-16 08:15:22" },
  "sign": "HMAC-SHA256(...)"
}
```
**要求**：接收方需**幂等处理**（按 `eventId` 去重）；平台按 1m/5m/30m 指数退避重试 **3 次**。

---

## 3. 回调契约（IoT → 业务平台）

> 📌 **本章回调契约已按定稿更新**
>
> | 项 | 定稿 |
> |---|---|
> | **回调路径** | **`/api/callback/ymd/{env}/{appCode}`**（`env` ∈ `dev`/`test`/`prod`），支持多环境 + 多应用隔离 |
> | **授权结果回调** | **`/api/callback/ymd/{env}/{appCode}/grantResult`** |
> | **自检端点** | `/api/callback/ymd/_selftest`（供 IoT 方联调） |
> | **IoT 调用签名** | **`v2-hmac-sha256`** + AES-256-GCM 字段级加密（替代原 AES/MD5），见 [`02_架构与技术方案.md`](02_架构与技术方案.md) §15 |
> | 限流 / 批量 / 分页 | QPS 50 / 批量 ≤100 / 单页 ≤500，见同上 §17 |
> | 授权异步与结果回调 | 见同上 §18 |
>
> **不变的原则**：回调**永远返回 HTTP 200**（失败入 DLQ）、`lockId` 反查租户、幂等去重。


### 3.1 开门记录回调

**`POST /callback/ymd/bite`**

> 该地址需在 IoT 平台**线下配置**（见第二轮 §12-A3）。
> IoT 侧**不加密**，因此安全依赖 IP 白名单 + 可选共享密钥。

```json
// Request（IoT 推送，字段名以 IoT 文档为准）
{
  "msgType": "1",
  "eventId": "202209011701",
  "msgData": {
    "openType": 1005,
    "lockId": "13D4AFE181121149952237877",
    "targetUserMobile": "13512100239",
    "openTime": "2022-09-01 15:00:01"
  }
}
```

**必须返回**（IoT 文档定义的成功响应）
```json
{ "code": "0000", "msg": "成功", "data": null, "traceId": "..." }
```

**平台处理流程**
```
1. 校验来源 IP（白名单）
2. 校验共享密钥（若启用）
3. 按 lockId 反查租户 → 设置租户上下文 ★（关键，否则租户插件失效）
4. 以 eventId 幂等去重（唯一索引），重复则直接返回成功
5. 落库 bp_dev_access_record + bp_dev_callback_log
6. 发布领域事件 access.record（RabbitMQ）
7. 立即返回标准响应体
```

| 场景 | 返回 |
|---|---|
| 正常 | `code=0000` |
| 重复事件 | `code=0000`（幂等，不报错） |
| 未知 lockId | `code=0000` + 记录告警（**不能报错**，否则 IoT 会重推） |
| 内部异常 | `code=0000` + 落 `bp_sys_mq_dlq` 人工处置（**仍返回成功**，避免重推风暴） |

> ⚠️ **重要设计决策**：**回调一律返回成功**，即使内部处理失败。
> 原因：IoT 侧失败会**重复推送**，造成风暴；且无法保证重推一定成功。
> 正确做法是**先落库再异步处理**，失败进死信队列人工处置。
> 这条契约必须在与 IoT 平台方对接时明确。

### 3.2 其他回调（若后续 IoT 提供）

| 事件 | 路径 | 状态 |
|---|---|---|
| 授权结果回调 | `/callback/ymd/auth-result` | ⏳ **待确认 IoT 是否提供**（第二轮 §12-A5） |
| 设备状态变更 | `/callback/ymd/device-status` | ⏳ 待确认 |
| 告警上报 | `/callback/ymd/alert` | ⏳ 待确认 |

**若无回调**，则走**对账拉取兜底**（第二轮 §4.6），本契约预留路径不做实现。

---

## 4. 与 IoT 平台的调用契约（业务平台 → IoT）

> 完整设计见第二轮 §4 集成层。此处列**契约要点**。

### 4.1 公共请求参数

| 参数 | 必填 | 说明 |
|---|---|---|
| `appKey` | 是 | 应用 KEY |
| `appSecret` | 是 | 应用密钥 |
| `time` | 是 | 时间戳 |
| `token` | 是 | 访问令牌（**30 分钟有效，提前 5 分钟续期**） |
| `version` | 是 | 接口版本（**`1.0.0` 还是 `2.0.0` 待确认**，第二轮 §12-A2） |
| `sign` | 是 | **参数按字典序拼串后 MD5**（拼串格式待确认） |

### 4.2 参数加密

```
AES 密钥 = token.substring(0, 25)      ← token 前 25 位
加密范围 = 参数值（非全部参数）
```

> ⚠️ **阻塞项**：AES 模式/填充/IV 与 MD5 拼串格式**未在接口文档中给出**
> （文档称"见附件"但 PDF 内无附件）。因此实现必须**完全配置化**：

```yaml
ymd:
  iot:
    base-url: https://api.hzbit.cn:4443
    version: "1.0.0"          # 待确认
    crypto:
      aes-mode: "CBC"         # 待确认：ECB/CBC/GCM
      aes-padding: "PKCS5Padding"   # 待确认
      aes-iv-source: "TOKEN_TAIL"   # 待确认：TOKEN_HEAD/TOKEN_TAIL/FIXED/NONE
      aes-iv-config: ""             # aes-iv-source=FIXED 时使用
      aes-key-length: 25
      sign-template: "{k}={v}&"     # 待确认
      sign-include-null: false      # 待确认
      sign-exclude-self: true       # 待确认（是否排除 sign 自身）
      time-unit: "SECOND"           # 待确认：SECOND/MILLISECOND
    token:
      cache-minutes: 25           # 提前 5 分钟过期
    rate-limit:
      qps: 10                     # 待确认（IoT 限流上限）
      batch-lock-max: 50          # 待确认（单次批量 lockId 上限）
```

> **里程碑 0**：开发前必须先产出 `YmdCryptoVerify` 工具，
> 用真实凭证**逐组试出正确组合**并与 IoT 平台方核对（第二轮 §12-A2）。

### 4.3 关键调用映射

| 业务动作 | IoT 接口 | 本平台入口 |
|---|---|---|
| 人员授权（主链路） | §8.2.1 `/ymd/restful/auth/action` | `POST /api/v1/grants/person-grant` |
| 授权列表 | §8.2.2 `/ymd/restful/auth/list` | 对账任务 |
| 授权删除 | §8.2.3 `/ymd/restful/auth/delAuthById` | `POST /api/v1/grants/entitlements/{id}/revoke` |
| 期限码/访客码 | §7.4.x | 应急密码/访客授权 |
| 指纹直传（二代证模板） | §7.3.1 `fingerAuth`（`complementedFlg=1/2`） | `POST /api/v1/persons/{id}/verify` 后自动下发 |
| 清空整锁授权 | §7.1 `clearLockAuth` | 退租回收（整锁场景） |
| 权限转让/归还 | §6.4 / §6.5 | 四级权限的所有权⇄管理权 |
| 门锁清单 | §6.1 `getPtAgentLocks` | 设备同步 |
| 门锁信息 | §6.2 `getLockInfo` | 设备状态对账 |
| 开门记录拉取 | §6.3 `getOpenLockRecordesByLockId` | 对账补偿 |
| 授权任务结果 | §7.7.2 `/ymd/restful/syncTask/result/list` | 授权结果轮询 |
| 实名认证 | §9.1 `serviceV2` | `POST /api/v1/persons/{id}/verify` |
| 组织实名 | §9.2 | 组织认证 |
| 人脸比对 | §9.3（`commandId`） | 人证核验 |

---


---

## 4A. 政策类接口（C8 落地新增）

> 依据重庆、广州、成都三地保障房政策新增。业务规则见 [`01_需求与功能方案.md`](01_需求与功能方案.md) §3，
> 表结构见 [`03_数据库设计说明.md`](03_数据库设计说明.md) §3.10。

### 4A.1 申诉与异议

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/v1/appeals` | 提交申诉或公示异议（自动按政策计算 `deadlineTime`） | `biz:appeal:submit` |
| GET | `/api/v1/appeals` | 分页查询（按 `bizType`/`appealStatus`/时间） | `biz:appeal:list` |
| GET | `/api/v1/appeals/{id}` | 详情（含处理过程与复核意见） | `biz:appeal:view` |
| POST | `/api/v1/appeals/{id}/accept` | 受理 | `biz:appeal:handle` |
| POST | `/api/v1/appeals/{id}/investigate` | 录入调查核实情况 | `biz:appeal:handle` |
| POST | `/api/v1/appeals/{id}/decide` | 作出复核决定（`upheld`/`rejected` + `resultEffect`） | `biz:appeal:decide` |
| POST | `/api/v1/appeals/{id}/withdraw` | 撤回 | `biz:appeal:submit` |

**提交请求体**
```json
{
  "bizType": "APPLICATION",
  "bizId": "1856234123456790",
  "personId": "1856234123456791",
  "appealType": "SUBMIT",
  "appealReason": "对收入核对结果有异议，实际收入低于核对值",
  "appealEvidence": ["/files/2026/xxx.pdf"]
}
```
**响应**（`deadlineTime` 由后端按政策时限计算，如"收到告知起 10 个工作日"）
```json
{ "code": "0", "data": { "id": "...", "appealNo": "SS20261016001",
  "appealStatus": "SUBMITTED", "deadlineTime": "2026-10-30T18:00:00" } }
```

### 4A.2 信用惩戒

| 方法 | 路径 | 说明 | 权限 |
|---|---|---|---|
| POST | `/api/v1/credit-records` | 新增惩戒记录（自动计算 `banEndDate`） | `biz:credit:create` |
| GET | `/api/v1/credit-records` | 分页查询 | `biz:credit:list` |
| POST | `/api/v1/credit-records/{id}/push` | 推送信用平台 | `biz:credit:push` |
| POST | `/api/v1/credit-records/{id}/revoke` | 撤销惩戒 | `biz:credit:revoke` |
| GET | `/api/v1/persons/{personId}/apply-eligibility` | ⭐ **查询是否被限制申请**（申请受理前置校验） | `biz:credit:view` |

**`apply-eligibility` 响应**
```json
{ "code": "0", "data": {
  "allowed": false,
  "reason": "CREDIT_BAN",
  "banEndDate": "2031-10-16",
  "violationType": "SUBLEASE",
  "recordId": "..." } }
```

### 4A.3 送达地址

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/persons/{personId}/service-addresses` | 新增送达地址 |
| GET | `/api/v1/persons/{personId}/service-addresses` | 查询（含历史失效地址） |
| PUT | `/api/v1/service-addresses/{id}` | 修改（**新增一条，旧地址置 `is_effective=0`**） |
| POST | `/api/v1/service-addresses/{id}/confirm` | 信息确认书签收确认 |

> ⚠️ **政策要点**：变更地址必须**主动告知**；未告知时**原地址视为有效送达地址**（成都§34）。
> 因此接口设计为**只增不删**，历史地址保留以备举证。

### 4A.4 优先配租对象

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/persons/{personId}/priority-objects` | 登记优先对象（支持多类） |
| GET | `/api/v1/persons/{personId}/priority-objects` | 查询有效优先身份 |
| DELETE | `/api/v1/priority-objects/{id}` | 撤销（置 `status=REVOKED`） |

**`priorityType` 枚举**：`DIBao` 低保 / `TeKun` 分散供养特困 / `DiBaoBianYuan` 低保边缘 / `YouFu` 优抚对象 /
`CanJi` 残疾人 / `CanJiJunRen` 残疾军人 / `LieShi` 烈士遗属 / `GuEr` 孤儿 / `JiSheng` 计生特扶 /
`LaoNian` 均满60岁 / `ErHai` 二孩以上 / `FangChanZhengShou` 征收过渡 / `Other`

### 4A.5 退出与过渡期

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/terminations` | 发起退租/腾退（含 `transitionMonths`） |
| POST | `/api/v1/terminations/{id}/transition` | 设置过渡期（自动算 `transitionEndDate` 与租金倍率） |
| POST | `/api/v1/terminations/{id}/relocation` | 设置搬迁期（成都≤6 个月） |
| POST | `/api/v1/terminations/{id}/enforce` | 申请法院强制执行 |
| POST | `/api/v1/terminations/{id}/notary` | 登记公证见证收回（含物品处置人） |

**过渡期响应示例**
```json
{ "code": "0", "data": {
  "transitionStartDate": "2026-11-01",
  "transitionEndDate": "2027-01-31",
  "transitionMonths": 3,
  "transitionRentMultiplier": 1.5,
  "note": "过渡期内按1.5倍计租，过渡期满按2.0倍" } }
```

### 4A.6 换房限制校验

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/exchanges` | 发起换房（**自动校验次数上限**） |
| GET | `/api/v1/exchanges/quota?contractId=` | 查询本租期剩余换房次数 |

**`quota` 响应**（成都：限 1 次）
```json
{ "code": "0", "data": {
  "maxTimes": 1, "usedTimes": 1, "remaining": 0,
  "forcedExchange": true,
  "noExchangeMultiplier": 1.5 } }
```


## 5. 关键契约决策汇总

| # | 决策 | 理由 |
|---|---|---|
| 1 | **金额与雪花 ID 用字符串传输** | 避免 JS 浮点/大整数精度丢失 |
| 2 | **认证失败返回 HTTP 200 + 业务字段** | 区分"认证不通过"与"系统故障" |
| 3 | **授权/导出/出账全部异步** | 避免长请求占用连接；IoT 本身异步 |
| 4 | **授权接口返回 `matchedKeys` 与 `skippedKeys`** | 合规匹配的可解释性 |
| 5 | **欠费停权 `freezeScope` 可配且默认排除大门门禁** | 消防与基本出入权利的安全底线 |
| 6 | **摇号留痕 `seed` + `algorithm`，可复现** | 公证与审计合规 |
| 7 | **回调一律返回成功，失败进死信** | 避免 IoT 重推风暴 |
| 8 | **回调入口必须显式设置租户上下文** | 否则租户插件失效，存在越权风险 |
| 9 | **IoT 错误码透传到响应体** | 运维可直接对照错误码表定位 |
| 10 | **在线率/可用率的阈值与判定由服务端返回** | 避免客户端口径不一致 |
| 11 | **加解密参数完全配置化** | 应对算法附录缺失（阻塞项） |
| 12 | **开放 API 用 HMAC-SHA256 + 时间戳 + Nonce** | 防重放 |

---

## 6. 待确认事项（影响接口定稿）

| # | 事项 | 影响 |
|---|---|---|
| **A1** | IoT 是否提供**设备在线状态/电量批量查询**接口 | `/api/v1/dev/devices/online-rate` 的实现方式 |
| **A2** | **AES/MD5 算法附录**（模式/填充/IV/拼串格式）与 `version` 取值 | §4.2 全部配置项 |
| **A3** | 回调地址配置流程与多环境支持 | §3.1 |
| **A4** | IoT 限流 QPS、批量 `lockId` 上限、分页上限 | 限流配置与批量切片 |
| **A5** | 是否有授权结果回调 | §3.2 是否实现 |
| B1 | 开放 API 是否需要**政务专线/双向证书** | §2.9 认证方式 |
| B2 | Webhook 重试策略与幂等要求是否接受 | §2.9 |
| B3 | 是否需要**信创**（影响 JSON/分区/字符集实现） | 全文 |
| B4 | 手机端是否需要**长连接**（WebSocket）推送 | 接口形式（REST vs WS） |

---

*本文档为《API 契约》定稿版。回调路径、IoT 签名算法、限流约束均已定稿；
新增 §4A 政策类接口（C8 落地）。配套：`02_架构与技术方案.md` §15–§18、`03_数据库设计说明.md` §3.10。*
