# IoT 对接接口与回调清单（v1.0）

> 前提：**平台不直连任何设备**。门锁、门禁、水表、电表、燃气表的所有读写，
> 均由平台调用 IoT 平台接口，IoT 平台负责与设备通信；设备侧的回调/上报统一进 IoT 平台，
> 再由 IoT 平台回调本平台。
>
> 本文把「平台 → IoT」与「IoT → 平台」两个方向的接口、字段、状态机、验签、幂等与待确认项一次列清。
> 标注 **✅ 已实现** 的为代码中已有；**⬜ 待新增** 的为对接前需补齐。

---

## 一、总体链路

```
① 业务动作（前端）
   平台页面（开锁/授权/抄表/告警处理）
        │  平台内部接口（/api/v1/...）
        ▼
② 平台业务服务
   grant / dev / fin 模块 → 生成任务（grant_task / 指令表）
        │  MQ（bp.grant.dispatch）+ 定时重试
        ▼
③ 平台 → IoT 平台（HTTP，签名鉴权）
   /ymd/restful/...  授权、门锁、任务结果
   /callback/...     事件、开门记录、心跳、表计读数、指令回执
        ▼
④ IoT 平台 → 设备（MQTT/私有协议，平台不关心）
        ▲
        │ 设备上报
⑤ IoT 平台 → 本平台（回调，HMAC 验签 + 幂等）
```

---

## 二、平台 → IoT 平台（下行接口）

### 2.1 已实现（现有代码）

| # | 用途 | 方法与路径 | 鉴权 | 代码位置 | 说明 |
|---|---|---|---|---|---|
| D1 | 取 Token | `POST /ymd/restful/...token` | appKey/appSecret + MD5 sign | `iot/legacy/YmdTokenManager`、`Md5Signer` | Token 缓存与刷新已实现 |
| D2 | 代理商门锁清单 | `POST /ymd/lockPt-service/pt/getPtAgentLocks` | Token | `YmdClient.PATH_AGENT_LOCKS` | 已实测可返回锁列表 |
| D3 | 门锁详情 | `POST /ymd/lockPt-service/pt/getLockInfo` | Token | `YmdClient.PATH_LOCK_INFO` | 已实测 |
| D4 | 人员授权（按通道） | `POST /ymd/restful/channel/auth/action` | Token | `YmdGrantClient.PATH_PERSON_AUTH` | **参数待联调确认** |
| D5 | 通用介质授权（含人脸） | `POST /ymd/restful/auth/action` | Token | `YmdGrantClient.PATH_AUTH_ACTION` | 参数待确认 |
| D6 | 删除授权 | `POST /ymd/restful/auth/delAuthById` | Token | `YmdGrantClient.PATH_DEL_AUTH` | 参数待确认 |
| D7 | 异步任务结果查询 | `POST /ymd/restful/syncTask/result/list` | Token | `YmdGrantClient.PATH_TASK_RESULT` | 轮询用，已接在 `queryTaskResult` |

> 配置：`bp.grant.iot-mode=mock|real`；真实实现 `YmdGrantClient`，联调前默认 mock。

### 2.2 待新增（按设备类）

| # | 类别 | 用途 | 建议方法与路径（待 IoT 方确认） | 平台侧落点 |
|---|---|---|---|---|
| D8 | 设备台账 | 拉取/增量同步设备（锁、门禁、表计） | `POST /ymd/restful/device/list`、`/device/detail` | 同步到 `bp_dev_device` |
| D9 | 设备状态 | 批量查在线状态、电量、信号、最后上报时间 | `POST /ymd/restful/device/status/batch` | 回写 `online_status/battery/rssi/last_report_time` |
| D10 | 远程开锁 | 单台/多台远程开门（运维场景） | `POST /ymd/restful/lock/open` | 新增「设备指令」表 + 页面 |
| D11 | 常开/常闭 | 门锁常开、恢复 | `POST /ymd/restful/lock/mode` | 指令记录 |
| D12 | 门禁放行 | 远程放行/闸机常开 | `POST /ymd/restful/access/open` | 指令记录 |
| D13 | 设备重启/校时 | 运维远程操作 | `POST /ymd/restful/device/reboot`、`/device/syncTime` | 指令记录 |
| D14 | 密码管理 | 新增/修改/删除/冻结密码 | `POST /ymd/restful/password/add|update|del|freeze` | 与 `bp_grant_keyring` 同步 |
| D15 | 离线码/二维码 | 下发一次性离线开锁码 | `POST /ymd/restful/auth/offlineCode` | 钥匙包「离线码」 |
| D16 | 人脸介质 | 下发/删除人脸 | `POST /ymd/restful/auth/face`（或复用 D5） | 与实名核验照片联动 |
| D17 | 表计读数 | 拉取水/电/气表读数（按时间段） | `POST /ymd/restful/meter/readings` | `bp_fin_meter_reading` |
| D18 | 远程拉合闸 | 欠费断电、缴费合闸 | `POST /ymd/restful/meter/switch` | 指令记录 + 账单联动 |
| D19 | 批量任务状态 | 大批量授权/指令的进度查询 | `POST /ymd/restful/task/progress` | 复用 D7 或新增 |

> D8/D9 建议做成**定时同步**（如 10 分钟增量），D10–D16 走指令表（见 §五）。

---

## 三、IoT 平台 → 本平台（回调 / 上报）

### 3.1 已实现（现状）

| # | 用途 | 方法与路径 | 鉴权现状 | 代码位置 | 缺口 |
|---|---|---|---|---|---|
| U1 | 设备事件上报（低电量/防拆/试错/胁迫/离线…） | `POST /api/v1/dev-events` | ⚠️ 仅 `X-Tenant-Id`，无签名 | `DevEventController#report` | 缺验签、缺幂等键 |
| U2 | 开门记录上报 | `POST /api/v1/access-records` | ⚠️ 同上 | `AccessRecordController#create` | 同上 |
| U3 | 开门记录批量上报 | `POST /api/v1/access-records/batch` | ⚠️ 同上 | `AccessRecordController#batch` | 前端未接，供 IoT 推送可用 |

> `TenantFilter` 已预留 `/api/callback` 前缀跳过租户解析，但**尚未实现回调控制器**。

### 3.2 待新增（建议统一入口）

| # | 用途 | 方法与路径（建议） | 说明 |
|---|---|---|---|
| C1 | 设备事件 | `POST /api/callback/iot/event` | 等价 U1，增加验签与幂等 |
| C2 | 开门记录 | `POST /api/callback/iot/access` | 等价 U2，支持批量数组 |
| C3 | **指令回执** | `POST /api/callback/iot/command/ack` | 指令 ID + 结果 + 设备耗时 + 错误码 |
| C4 | **授权任务结果** | `POST /api/callback/iot/grant/ack` | `serviceId` 关联 `grant_task`，更新成功/失败/部分 |
| C5 | **设备心跳/状态** | `POST /api/callback/iot/heartbeat` | 在线、电量、RSSI、固件版本，批量数组 |
| C6 | **表计读数** | `POST /api/callback/iot/meter` | 读数、倍率、时间、表号（自动进抄表记录） |
| C7 | 设备上下线 | `POST /api/callback/iot/device-status` | 上线/离线事件（也可并入 C5） |
| C8 | 告警确认 | `POST /api/callback/iot/alarm-ack` | IoT 侧告警被处理/恢复，回写本平台事件 |

**回调统一约定（建议写入对接契约）**

```
POST /api/callback/iot/{action}
Headers:
  X-Iot-AppId: <appId>
  X-Iot-Timestamp: <秒级时间戳>
  X-Iot-Nonce: <随机串>
  X-Iot-Signature: HMAC-SHA256(appSecret, canonicalRequest)
Body: { "eventId": "...", "occurredAt": "...", ... }
响应: { "code": "SUCCESS", "message": "ok" }   // 非 SUCCESS 时 IoT 重试
```

验签规则与平台现有 `iot/sign/HmacSha256Strategy` 保持一致（`v2-hmac-sha256`，含 `appId/timestamp/nonce/body-md5`）；
兼容 ymd 旧协议时可保留 `MD5 + AES-CBC` 作为过渡（见 `_验证/IoT对接规范-定稿.md`）。

---

## 四、平台内部接口（前端使用，非给 IoT 方）

> 列全只为说明「页面已有哪些能力」，对接时不必给 IoT 方。

| 模块 | 接口 | 用途 |
|---|---|---|
| 设备 | `GET /api/v1/devices`、`/types`、`/unbound`、`/inherited`、`/freshness`、`/stats`、`/{id}` | 台账、类型、未绑定、继承关系、在线新鲜度、统计 |
| 设备绑定 | `POST /api/v1/devices/{id}/bind` | 绑定到空间/房号 |
| 设备事件 | `GET /api/v1/dev-events`、`/stats`、`POST /{id}/handle` | 告警列表、统计、标记处理 |
| 通行记录 | `GET /api/v1/access-records`、`/trace/person/{id}`、`/trace/house/{id}`、`/idle`、`/untrusted-ratio` | 开门记录、人员/房屋轨迹、长期未用、异常开门占比 |
| 授权 | `GET /api/v1/grants`、`/tasks/{taskId}`、`/tasks/{taskId}/details`、`POST /{id}/revoke` | 通行授权、下发任务与明细、撤销 |
| 钥匙包 | `GET /api/v1/keyring`、`/person/{id}`、`POST /api/v1/keyring`、`/{id}/freeze`、`/{id}/unfreeze`、`/{id}/remove` | 密码/卡/离线码生命周期 |
| 表计 | `GET/POST /api/v1/fin/meter-readings`、`/{id}/bill`、`/analytics` | 手工抄表、出账、用量分析 |

---

## 五、指令与任务状态机（平台侧，待新增）

```
创建指令 → PENDING ──调用 IoT──> SENT ──回调 ACK──> SUCCESS
                    │                 │
                    │                 └─超时(默认 10s)──> TIMEOUT ─重试(最多 3 次)──> FAILED
                    └─IoT 返回失败────────────────────────────> FAILED
```

| 要素 | 规则 |
|---|---|
| 幂等键 | `tenantId + taskNo/commandId`，回调重复到达不重复落库 |
| 超时 | 指令 10s，授权任务 60s（按 IoT 建议调整） |
| 重试 | 指数退避，最多 3 次，超限进死信并告警 |
| 并发 | 同一设备串行（避免开锁/常开指令互相覆盖） |
| 对账 | 每日核对「已下发未回执」指令，输出差异清单 |

---

## 六、事件与字段映射

### 6.1 设备事件类型（平台已支持 12 种）

`OPEN` 开锁、`ONLINE` 上线、`OFFLINE` 离线、`LOW_BATTERY` 低电量、
`BATTERY_RESTORED` 低电解除、`TAMPER` 防拆、`TRIAL_ERROR` 试错、
`DURESS` 胁迫、`POWER_OVER` 超功率、`LOCAL_SWITCH` 本地合闸、
`METER_READ` 抄表读数、`OTHER` 其他。

### 6.2 关键字段对照

| 平台字段 | 含义 | IoT 侧对应（待确认） |
|---|---|---|
| `DevDevice.deviceId` | 平台设备编号 | IoT `deviceId` |
| `DevDevice.deviceMac` | 设备 MAC | IoT `mac` |
| `GrantTask.keyringIds` / `lockIds` | 锁标识 | `lockId` 或 `macList` |
| `GrantTask.serviceId` | 授权任务关联号 | IoT 回调 `serviceId` |
| `GrantTask.iotTaskId` | IoT 异步任务号 | `syncTaskId` |
| `DevAccessRecord.eventId` | 记录唯一号 | IoT `eventId`（幂等用） |
| `FinMeterReading.deviceId` | 表计编号 | IoT `meterNo` |
| `Person.id` ↔ `GrantIotPersonMap` | 人员映射 | IoT `ownerId`/`account` |

---

## 七、联调顺序与验收

| 阶段 | 内容 | 验收口径 |
|---|---|---|
| 1 | 取 Token + 门锁清单同步 | 拉取锁列表与平台一致，差异可对账 |
| 2 | 人员授权下发（单人单锁） | 任务 SUCCESS，明细逐设备成功；锁端可开 |
| 3 | 撤销授权 | 撤销后锁端即时失效 |
| 4 | 事件回调（低电量/防拆/离线） | 平台事件页出现记录，验签通过，重复推送幂等 |
| 5 | 开门记录回调 | 记录可查、可按人/房追溯 |
| 6 | 远程指令（开锁/常开/重启） | 回执 10s 内到达，超时重试可见 |
| 7 | 表计读数（水/电/气） | 读数入库并可一键出账 |
| 8 | 欠费拉闸/缴费合闸 | 指令+回执+账单联动闭环 |

---

## 八、待 IoT 方确认清单（对接前必须闭环）

1. 回调地址是否由平台提供固定域名 + 路径（建议 `/api/callback/iot/*`）
2. 回调签名算法：`v2-hmac-sha256` 还是沿用 MD5+AES；重放窗口
3. 指令接口：是否支持「远程开锁/常开/重启/校时」，参数与回执字段
4. 授权接口：门锁标识用 `lockId` 还是 `mac`；有效期格式；是否按锁逐个下发
5. 表计：是否支持主动拉取 + 上报两种方式；倍率/冻结值/阶梯读数口径
6. 拉合闸：电表是否支持远程拉合闸，安全策略（是否需二次确认）
7. 上报频率与离线阈值（建议心跳 5 分钟、离线判定 15 分钟）
8. QPS/并发限制、失败重试策略、批量上限

---

## 九、当前缺口一览（按实现优先级）

| 优先级 | 缺口 | 影响 |
|---|---|---|
| P0 | 回调统一入口 + 验签 + 幂等（C1–C8） | 没有它，IoT 无法安全回调 |
| P0 | 指令表 + 指令记录页 + 回执处理（D10–D13、C3） | 只能授权不能运维 |
| P1 | 设备状态/心跳同步 + 离线判定 Job（D9、C5） | 告警会静默失效 |
| P1 | 表计读数入库 + 出账联动（D17、C6） | 水电气仍靠手抄 |
| P1 | 授权任务回执关联 `serviceId`（C4） | 任务长期停在 DISPATCHING |
| P2 | 密码/离线码/人脸介质同步（D14–D16） | 钥匙包与锁端不一致 |
| P2 | 拉合闸（D18） | 欠费断电闭环缺失 |

---

*本文与 `13_泊寓IoT对接参考评估.md`、`_验证/IoT对接规范-定稿.md` 配套使用：前者是业务视角评估，后者是协议算法实测记录，本文是对接接口与回调清单。*
