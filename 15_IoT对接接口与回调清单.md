# IoT 对接接口与回调清单（v1.1）

> 前提：**平台不直连任何设备**。门锁、门禁、水表、电表、燃气表的所有读写，
> 均由平台调用 IoT 平台接口，IoT 平台负责与设备通信；设备侧的回调/上报统一进 IoT 平台，
> 再由 IoT 平台回调本平台。
>
> **v1.1 变更**：已确认「指令能力（开锁/重启/校时 + 回执）」「授权标识用 lockId」「表计支持拉取与主动上报」「电表支持远程拉合闸及安全策略」，据此细化契约。
> 标注 **✅ 已实现**、**🟡 已确认待实现**、**⬜ 待确认**。

---

## 一、总体链路

```
① 业务动作（前端）
   平台页面（开锁/授权/抄表/告警处理）
        │  平台内部接口（/api/v1/...）
        ▼
② 平台业务服务
   grant / dev / fin 模块 → 指令表 / 授权任务（grant_task）
        │  MQ + 定时重试
        ▼
③ 平台 → IoT 平台（HTTP，签名鉴权）
   授权：/ymd/restful/auth/*        标识统一用 lockId
   指令：/ymd/restful/lock/open、/device/reboot、/device/syncTime
   表计：/ymd/restful/meter/readings（拉取）、/meter/switch（拉合闸）
        ▼
④ IoT 平台 → 设备（MQTT/私有协议）
        ▲
        │ 设备上报（事件/开门记录/心跳/表计/任务结果）
⑤ IoT 平台 → 本平台（回调，HMAC 验签 + 幂等）
```

---

## 二、平台 → IoT 平台（下行接口）

### 2.1 已实现

| # | 用途 | 方法与路径 | 鉴权 | 代码位置 |
|---|---|---|---|---|
| D1 | 取 Token | `POST /ymd/auth-service/sys/getAccessToken` | appKey/appSecret + MD5 sign | `iot/legacy/YmdTokenManager` |
| D2 | 代理商门锁清单 | `POST /ymd/lockPt-service/pt/getPtAgentLocks` | Token | `YmdClient.PATH_AGENT_LOCKS` |
| D3 | 门锁详情 | `POST /ymd/lockPt-service/pt/getLockInfo` | Token | `YmdClient.PATH_LOCK_INFO` |
| D4 | 人员授权（按通道） | `POST /ymd/restful/channel/auth/action` | Token | `YmdGrantClient` |
| D5 | 通用介质授权（含人脸） | `POST /ymd/restful/auth/action` | Token | `YmdGrantClient` |
| D6 | 删除授权 | `POST /ymd/restful/auth/delAuthById` | Token | `YmdGrantClient` |
| D7 | 异步任务结果查询 | `POST /ymd/restful/syncTask/result/list` | Token | `YmdGrantClient.queryTaskResult` |

> **v1.1 明确**：D4/D5/D6 的门锁标识**统一用 `lockId`**，不再使用 `mac`。
> 平台侧 `GrantTask.keyringIds` 与设备表的 `device_id` 需保证可映射到 IoT 的 `lockId`。

### 2.2 待新增 —— 指令类（🟡 已确认支持）

| # | 指令 | 建议路径 | 请求要点 | 回执要点 |
|---|---|---|---|---|
| D10 | 远程开锁 | `POST /ymd/restful/lock/open` | `lockId`、`requestId`（平台生成）、`operator`、`reason` | `code/message`、`deviceTime`、`costMs` |
| D13a | 远程重启 | `POST /ymd/restful/device/reboot` | `lockId`、`requestId` | 同上 |
| D13b | 远程校时 | `POST /ymd/restful/device/syncTime` | `lockId`、`requestId`、`timestamp`（可选） | 同上 |
| D11 | 常开/常闭（门锁） | `POST /ymd/restful/lock/mode` | `lockId`、`mode=NORMAL/HOLD_OPEN` | 同上 |
| D12 | 门禁放行 | `POST /ymd/restful/access/open` | `accessId`、`direction` | 同上 |
| D18 | 电表拉合闸 | `POST /ymd/restful/meter/switch` | `meterNo`、`action=TRIP/RESTORE`、`requestId`、`reason`、`operator` | `code`、`deviceTime`、`costMs` |

**统一响应约定（平台按此解析）**

```json
{
  "code": "0",
  "message": "ok",
  "requestId": "CMD202610270001",
  "lockId": "LK00005771",
  "deviceTime": "2026-10-27 01:20:00",
  "costMs": 320
}
```

- `code != 0` 视为下发失败，平台按策略重试（最多 3 次）
- 同步未返回时按异步任务处理，等待回调 C3

### 2.3 待新增 —— 授权与设备台账

| # | 用途 | 建议路径 | 说明 |
|---|---|---|---|
| D8 | 设备台账增量同步 | `POST /ymd/restful/device/list` | 按 `updateTime` 增量，写入 `bp_dev_device` |
| D9 | 设备状态批量查询 | `POST /ymd/restful/device/status/batch` | 在线、电量、RSSI、固件、最后上报时间 |
| D14 | 密码新增/修改/删除/冻结 | `POST /ymd/restful/password/*` | 与 `bp_grant_keyring` 双向一致 |
| D15 | 离线码/一次性二维码 | `POST /ymd/restful/auth/offlineCode` | 钥匙包「离线码」 |
| D16 | 人脸介质下发/删除 | `POST /ymd/restful/auth/face` | 与实名核验照片联动 |

### 2.4 待新增 —— 表计（🟡 已确认：拉取 + 主动上报两种）

| # | 方式 | 建议路径 | 说明 |
|---|---|---|---|
| D17a | **平台拉取** | `POST /ymd/restful/meter/readings` | 入参 `meterNos[]`、`from`、`to`；出参读数列表（含倍率） |
| D17b | **设备任务上报** | 由 IoT 侧配置采集任务 | IoT 按周期主动回调 C6，平台无需轮询 |

**表计读数契约（两种来源共用）**

```json
{
  "meterNo": "M20261027001",
  "deviceId": "EM0000123",
  "meterType": "ELEC",
  "reading": 12345.67,
  "previousReading": 12300.00,
  "multiplier": 1,
  "readTime": "2026-10-27 06:00:00",
  "source": "PULL",
  "freezeFlag": true
}
```

- `meterType`：`ELEC` 电、`WATER` 水、`GAS` 气、`HEAT` 热
- `source`：`PULL` 平台拉取 / `PUSH` 设备任务上报
- 平台按 `deviceId + readTime` 幂等去重

### 2.5 电表拉合闸安全策略（🟡 已确认支持）

| 策略 | 规则 |
|---|---|
| 二次确认 | 页面二次确认 + 填写原因，提交即生成指令记录 |
| 双人复核 | `TRIP`（断电）需管理员二次审批（可配置开关）；`RESTORE`（合闸）单人可执行 |
| 前置校验 | 仅当欠费金额超阈值且账期超期 N 天才允许拉闸；缴费到账后自动/手动合闸 |
| 延迟执行 | 拉闸默认延迟 10 分钟执行，期间可撤销 |
| 操作窗口 | 22:00–07:00 禁止拉闸（可配置） |
| 通知 | 拉闸前 30 分钟短信/站内信通知住户与网格员 |
| 审计 | 指令全量留痕（操作人/原因/回执/耗时），可导出 |
| 兜底 | 合闸失败自动重试并告警；同表 24 小时内拉闸不超过 3 次 |

---

## 三、IoT 平台 → 本平台（回调）

### 3.1 现状（可用但不安全）

| # | 用途 | 路径 | 鉴权 | 缺口 |
|---|---|---|---|---|
| U1 | 设备事件上报 | `POST /api/v1/dev-events` | 仅 `X-Tenant-Id` | 无验签、无幂等 |
| U2 | 开门记录上报 | `POST /api/v1/access-records` | 仅 `X-Tenant-Id` | 同上 |
| U3 | 开门记录批量 | `POST /api/v1/access-records/batch` | 同上 | 同上 |

### 3.2 待新增统一回调入口

| # | 用途 | 路径 | 关键字段 |
|---|---|---|---|
| C1 | 设备事件 | `POST /api/callback/iot/event` | `deviceId`、`identifier`、`eventLevel`、`eventTime`、`body` |
| C2 | 开门记录 | `POST /api/callback/iot/access` | `eventId`、`lockId`、`personId`、`openType`、`openTime`、`isTrusted` |
| C3 | **指令回执** | `POST /api/callback/iot/command/ack` | `requestId`、`lockId`、`code`、`message`、`deviceTime`、`costMs` |
| C4 | 授权任务结果 | `POST /api/callback/iot/grant/ack` | `serviceId`、`success`、`failCount`、逐设备明细 |
| C5 | 心跳/状态 | `POST /api/callback/iot/heartbeat` | `deviceId`、`online`、`battery`、`rssi`、`firmware` |
| C6 | 表计读数 | `POST /api/callback/iot/meter` | 同 §2.4，`source=PUSH` |
| C7 | 上下线事件 | `POST /api/callback/iot/device-status` | `deviceId`、`status`、`time` |
| C8 | 告警恢复 | `POST /api/callback/iot/alarm-ack` | `eventId`、`recovered`、`recoverTime` |

**回调验签（建议写入契约，参数可在系统参数配置）**

```
POST /api/callback/iot/{action}
X-Iot-AppId / X-Iot-Timestamp / X-Iot-Nonce / X-Iot-Signature
Signature = HMAC-SHA256(appSecret, canonicalRequest)
响应 {"code":"SUCCESS"}；非 SUCCESS 由 IoT 重试（最多 5 次，指数退避）
```

与平台现有 `iot/sign/HmacSha256Strategy`（`v2-hmac-sha256`）一致；旧协议可保留 `MD5 + AES-CBC` 过渡。

---

## 四、平台内部接口（前端使用，非给 IoT 方）

| 模块 | 接口 | 用途 |
|---|---|---|
| 设备 | `GET /api/v1/devices`、`/types`、`/unbound`、`/inherited`、`/freshness`、`/stats`、`/{id}` | 台账、类型、未绑定、继承、在线新鲜度、统计 |
| 设备绑定 | `POST /api/v1/devices/{id}/bind` | 绑定空间/房号 |
| 设备事件 | `GET /api/v1/dev-events`、`/stats`、`POST /{id}/handle` | 告警列表、统计、标记处理 |
| 通行记录 | `GET /api/v1/access-records`、`/trace/person/{id}`、`/trace/house/{id}`、`/idle`、`/untrusted-ratio` | 记录、轨迹、长期未用、异常占比 |
| 授权 | `GET /api/v1/grants`、`/tasks/{taskId}`、`/tasks/{taskId}/details`、`POST /{id}/revoke` | 授权、任务与明细、撤销 |
| 钥匙包 | `GET /api/v1/keyring`、`/person/{id}`、`POST /api/v1/keyring`、`/{id}/freeze`、`/{id}/unfreeze`、`/{id}/remove` | 密码/卡/离线码生命周期 |
| 表计 | `GET/POST /api/v1/fin/meter-readings`、`/{id}/bill`、`/analytics` | 抄表、出账、用量分析 |
| **指令（待新增）** | `POST /api/v1/dev-commands`、`GET /api/v1/dev-commands`、`/{id}/retry`、`/{id}/cancel` | 开锁/重启/校时/拉合闸 与指令记录 |

---

## 五、指令与任务状态机

```
创建 → PENDING ─调用 IoT→ SENT ─回执 C3→ SUCCESS
                  │            │
                  │            └─超时(10s)→ TIMEOUT →重试(≤3)→ FAILED
                  └─IoT code≠0────────────────────────────→ FAILED
```

| 要素 | 规则 |
|---|---|
| 幂等键 | `tenantId + requestId`（平台生成），回调重复不重复执行 |
| 超时 | 指令 10s；授权任务 60s（可按 IoT 建议调整） |
| 重试 | 指数退避，最多 3 次，超限进死信并告警 |
| 并发 | 同一 `lockId` 串行，避免指令互相覆盖 |
| 对账 | 每日核对「已下发未回执」指令，输出差异清单 |
| 撤销 | `PENDING` 且未下发前允许撤销（拉闸延迟窗口内可撤） |

---

## 六、事件与字段映射

### 6.1 设备事件类型（12 种，已支持）

`OPEN` 开锁、`ONLINE` 上线、`OFFLINE` 离线、`LOW_BATTERY` 低电量、
`BATTERY_RESTORED` 低电解除、`TAMPER` 防拆、`TRIAL_ERROR` 试错、
`DURESS` 胁迫、`POWER_OVER` 超功率、`LOCAL_SWITCH` 本地合闸、
`METER_READ` 抄表读数、`OTHER` 其他。

### 6.2 字段对照（v1.1 明确 lockId）

| 平台字段 | 含义 | IoT 侧 |
|---|---|---|
| `DevDevice.deviceId` | 平台设备编号 | IoT `deviceId` |
| `DevDevice.deviceMac` | MAC（仅留档，**不作为授权标识**） | IoT `mac` |
| `GrantTask.keyringIds` / 明细 `lock_id` | 门锁标识 | IoT **`lockId`** |
| `GrantTask.serviceId` | 授权任务关联号 | 回调 `serviceId` |
| `GrantTask.iotTaskId` | IoT 异步任务号 | `syncTaskId` |
| `DevAccessRecord.eventId` | 记录唯一号 | IoT `eventId` |
| `FinMeterReading.deviceId` | 表计编号 | IoT `meterNo`/`deviceId` |
| `Person.id` ↔ `GrantIotPersonMap` | 人员映射 | IoT `ownerId`/`account` |

---

## 七、联调顺序与验收

| 阶段 | 内容 | 验收口径 |
|---|---|---|
| 1 | Token + 门锁清单同步 | 与平台台账一致，可对账 |
| 2 | 人员授权（lockId） | 任务 SUCCESS，锁端可开 |
| 3 | 撤销授权 | 锁端即时失效 |
| 4 | 事件回调（低电量/防拆/离线） | 事件页可见、验签通过、重复推送幂等 |
| 5 | 开门记录回调 | 可按人/房追溯 |
| 6 | 指令：开锁 / 重启 / 校时 | 回执 10s 内到达，超时重试可见 |
| 7 | 表计：拉取 + 主动上报 | 两种来源均入库，`deviceId+readTime` 去重 |
| 8 | 电表拉合闸 | 二次确认 + 审批 + 延迟 + 回执 + 审计闭环 |

---

## 八、仍待确认（v1.1 后剩余）

1. 回调地址与签名算法（`v2-hmac-sha256` 或旧 `MD5+AES`）、重放窗口
2. 心跳频率与离线阈值（建议心跳 5 分钟、离线 15 分钟）
3. QPS/并发上限、批量上限、IoT 侧重试策略
4. 指令接口的**精确参数名**与回执字段名（D10/D13/D18）
5. 授权接口的锁标识字段名（`lockId`）与有效期格式
6. 表计拉取的入参分页/时间范围上限

---

## 九、缺口与实施顺序

| 优先级 | 缺口 | 影响 | 预估 |
|---|---|---|---|
| P0 | 回调统一入口 + 验签 + 幂等（C1–C8） | IoT 无法安全回调 | 1.5 天 |
| P0 | 指令表 + 指令记录页 + 回执（D10/D13、C3） | 只能授权不能运维 | 2 天 |
| P0 | 授权任务回执关联 `serviceId`（C4） | 任务卡在 DISPATCHING | 0.5 天 |
| P1 | 设备状态/心跳 + 离线判定 Job（D9、C5） | 告警静默失效 | 1 天 |
| P1 | 表计拉取 + 上报入库 + 出账（D17、C6） | 水电气仍靠手抄 | 1.5 天 |
| P1 | 电表拉合闸 + 安全策略（D18） | 欠费断电闭环缺失 | 1.5 天 |
| P2 | 密码/离线码/人脸同步（D14–D16） | 钥匙包与锁端不一致 | 1.5 天 |

---

*配套文档：`13_泊寓IoT对接参考评估.md`（业务视角）、`_验证/IoT对接规范-定稿.md`（协议算法实测）。*

---

## 十、契约参数（可在系统参数中调整）

> 位置：**系统支撑 → 系统参数 → IoT 对接参数**（分组 IOT），改完立即生效、无需重启。
> 后端读取组件：iot/config/IotSettings.java（缺失或非法时回落到默认值）。

| 参数键 | 含义 | 当前值 |
|---|---|---|
| iot.callback.signAlgorithm | 回调签名算法 | 2-hmac-sha256 |
| iot.callback.timestampToleranceSeconds | 时间戳容忍窗口 | 300 秒 |
| iot.callback.nonceCacheMinutes | Nonce 缓存（防重放） | 10 分钟 |
| iot.callback.batchLimit | 单次批量上限 | 200 条 |
| iot.callback.qps | 回调限流 | 50 次/秒 |
| iot.command.timeoutSeconds | 指令超时 | 10 秒 |
| iot.command.maxRetry | 指令最大重试 | 3 次 |
| iot.grantTask.timeoutSeconds | 授权任务超时 | **180 秒** |
| iot.heartbeat.intervalSeconds | 心跳间隔 | **60 秒（1 分钟）** |
| iot.offline.thresholdSeconds | 离线判定阈值 | **180 秒（3 分钟）** |
| iot.meter.reportPeriod | 表计上报周期 | **ELEC:DAILY,WATER:DAILY（电表每日、水表每日）** |
| iot.meter.switch.delayMinutes | 拉闸延迟执行 | 10 分钟（窗口内可撤销） |
