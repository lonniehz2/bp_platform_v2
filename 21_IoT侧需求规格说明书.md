# IoT 侧需求规格说明书（待实现项）

> 文档编号：21  
> 版本：v1.0（2026-10-28）  
> 对象：IoT 平台研发  
> 说明：本文件把 18 号清单里**仍未实现**的能力写成可实现、可验收的规格；其余已完成项见 18/19 号文档。

---

## 0. 通用约定

| 项 | 约定 |
|---|---|
| 传输 | HTTPS，JSON（`Content-Type: application/json; charset=utf-8`） |
| 鉴权 | 平台 → IoT：`appId + timestamp + nonce + sign`（HMAC-SHA256，与回调同一套规范）；IoT → 平台回调按 15 号文档 |
| 响应包络 | `{ "code": "0", "message": "ok", "data": { ... }, "costMs": 123 }`；`code=0` 或 `SUCCESS` 视为成功 |
| 幂等 | 带 `requestId` 的写操作必须幂等：重复 requestId 返回首次结果，不重复执行 |
| 超时 | 平台连接 3s / 读取 10s；IoT 侧超过 10s 应返回受理中并异步回执 |
| 时间 | ISO-8601 带时区，或 `yyyy-MM-dd HH:mm:ss`（平台两者都兼容） |
| 错误 | 业务错误用非 0 `code` + 可读 `message`；禁止只返回 HTTP 500 无 message |

---

## 1. IOT-TOKEN　取 Token / 续期

**优先级：P0（阻塞 TC-M1-01/02）**

### 请求

```
POST /ymd/restful/token
{
  "appId": "xxx",
  "timestamp": 1793090000,        // 秒
  "nonce": "9f2c...",             // 随机串
  "sign": "hmac-sha256(...)"      // 见下
}
```

签名串：`appId + "\n" + timestamp + "\n" + nonce`，HMAC-SHA256，密钥为 appSecret，输出小写 hex。

### 响应

```json
{ "code": "0", "message": "ok",
  "data": { "token": "eyJ...", "expiresIn": 7200, "pwdSeed": "可选：派生密钥前 25 位" } }
```

### 要求

- `expiresIn` 单位秒，平台在到期前 5 分钟续期；
- 续期接口与取 Token 相同（重新取即可），旧 token 在 `expiresIn` 内仍有效；
- Token 失效时业务接口应返回可识别错误码（建议 `40101`），平台据此重取一次。

### 验收

- TC-M1-01：取 Token 成功且 `expiresIn>0`；
- TC-M1-02：过期后业务调用触发重取，业务无感。

---

## 2. IOT-DEVICE-STATUS-BATCH　批量设备状态

**优先级：P1（阻塞 TC-M1-05）**

### 请求

```
POST /ymd/restful/device/status
{ "lockIds": ["LK00000001","LK00000002"] }     // 单次最多 200 个
```

### 响应

```json
{ "code": "0", "data": [
  { "lockId": "LK00000001", "online": true, "battery": 87, "rssi": -62,
    "lastReportTime": "2026-10-28 10:00:00", "firmware": "1.2.3" }
] }
```

### 要求

- 不在 IoT 台账的 lockId 返回 `online:false` 且 `message:"not found"`（不要整批失败）；
- 单批 >200 返回 `code=40002`，平台会分批重试。

### 验收

- TC-M1-05：查 2 台，字段与 IoT 后台一致。

---

## 3. IOT-LOCK-MODE　常开 / 常闭 / 恢复

**优先级：P1（平台已支持，待 IoT 实现；TC-M4-07）**

### 请求

```
POST /ymd/restful/lock/mode
{ "requestId": "REQ...", "lockId": "LK00000001", "mode": "OPEN" }   // OPEN | CLOSE | NORMAL
```

### 响应

```json
{ "code": "0", "message": "ok", "costMs": 180,
  "data": { "lockId": "LK00000001", "mode": "OPEN", "effective": true } }
```

### 要求

- 幂等：同 `requestId` 重复调用返回首次结果；
- 设备离线时返回 `code=50001"设备离线"`，平台按失败处理并允许重试；
- 断电恢复后的默认模式由 IoT 与业务约定（建议 `NORMAL`），并在回执中返回 `powerOnMode`。

### 验收

- TC-M4-07：常开→恢复，状态与断电默认值符合约定。

---

## 4. IOT-METER-SPEC　表计字段口径

**优先级：P0（影响出账；TC-M6-04/07）**

### 上报字段（平台回调 `/api/callback/iot/meter` 已支持）

| 字段 | 必填 | 说明 |
|---|---|---|
| `meterNo` / `deviceId` | 是 | 表号，须与平台台账设备编号一致 |
| `reading` | 是 | 本次读数（表盘值，未乘倍率） |
| `readTime` / `readDate` | 是 | 读数时间；平台按「设备+日期」去重 |
| `multiplier` | 否 | 倍率，缺省 1；平台用量 =（本次−上次）× 倍率 |
| `unit` | 否 | kWh / m³ / m³(气)，缺省 kWh |
| `source` | 否 | `PUSH`（默认）/ `PULL` |

### 需要 IoT 明确的点

1. 倍率是否随读数上报（推荐上报，避免平台配置漂移）；
2. 上报周期：电表/水表每日几点、失败重试几次；
3. 表计与房间/房源的绑定关系由谁维护（当前平台按设备编号匹配）。

### 验收

- TC-M6-04：倍率 10 的表，用量换算正确；
- TC-M6-07：改周期后按新周期上报，旧任务不重复。

---

## 5. IOT-LOAD-ENV　压测与断网演练环境

**优先级：P1（TC-M8-02/03）**

| 项 | 要求 |
|---|---|
| 压测 | 回调接口 50 QPS 持续 5 分钟；允许平台侧限流 20 QPS 时返回 429 |
| 断网演练 | IoT 侧停止回调 10 分钟，恢复后补推；平台按 `eventId` 去重 |
| 数据清理 | 演练后提供清理脚本或测试租户，避免污染生产 |
| 观察指标 | 平台 `/iot/metrics` 的在线率、指令成功率、回调成功率 |

### 验收

- TC-M8-02：无丢失、无重复，`callbacks.successRate ≥ 99%`；
- TC-M8-03：恢复后 10 分钟内补齐，重复不落库。

---

## 6. 交付方式

| 项 | 方式 |
|---|---|
| 接口文档 | Swagger/YAPI 或按本文格式回填 |
| 联调环境 | 提供 base URL、appId/appSecret、测试 lockId 列表 |
| 完成判据 | 上述 5 项各自验收用例通过，并在 19 号报告中把对应状态改为 ✅ |

---

*平台侧已就绪：指令（含常开/常闭）、回调网关、表计入库、拉合闸、离线判定、同步、监控、对账。*
