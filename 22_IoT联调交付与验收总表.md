# IoT 联调交付与验收总表

> 文档编号：22  
> 版本：v1.0（2026-10-28）  
> 用途：向业务/管理方与 IoT 方一次性说明「已交付什么、怎么配、怎么验、还差什么」

---

## 一、结论先行

| 维度 | 状态 |
|---|---|
| 平台侧功能（回调、指令、授权、表计、离线、拉合闸、同步、监控、对账、工具） | ✅ 已完成 |
| 平台侧配置（21 项 IoT 参数，页面可改、即时生效） | ✅ 已完成 |
| 文档（15–22 号 8 份） | ✅ 已完成 |
| 联调用例 57 条 | ✅ 42 通过 / 13 部分（待真机）/ 2 阻塞（需环境） |
| 与 IoT 真实环境联调 | ⏳ 待 IoT 提供 5 项（见第五节） |

---

## 二、功能矩阵

| 能力 | 页面入口 | 主要接口 | 关键配置 | 证据 |
|---|---|---|---|---|
| 回调网关（验签/时间戳/nonce/幂等） | IoT 联调工具 | `POST /api/callback/iot/{action}` | `iot.callback.*` | 19 号 M3 全通过 |
| 设备事件与告警 | 设备告警 / 告警管理 | 回调 `event` | — | 20 号附录 AY/BC |
| 开门记录 | 通行记录 | 回调 `access` | — | M3-07/08/09 |
| 指令开锁/重启/校时 | 设备指令 | `POST /dev-commands` | `iot.command.timeoutSeconds/maxRetry` | M4-01/02/05/06 |
| 常开/常闭/恢复 | 设备指令 | 同上（`LOCK_ALWAYS_OPEN` 等） | — | 20 号 |
| 指令回执 | 设备指令详情 | 回调 `command/ack` | — | M4-02/04 |
| 授权/撤销回执 | 钥匙包/通行授权 | 回调 `grant/ack` | `iot.grantTask.timeoutSeconds` | M2 全通过 |
| 密码/卡/人脸下发 | 凭据同步 | 回调/工具页 | `bp.credential.mode` | 工具页凭据同步 |
| 心跳与离线判定 | 设备管理/监控 | 回调 `heartbeat` | `iot.offline.thresholdSeconds` | M5 全通过 |
| 表计拉取/上报 | 抄表管理 | `POST /iot/meter/pull`、回调 `meter` | `iot.meter.reportPeriod` | M6 全通过（倍率/周期已支持） |
| 电表拉合闸 | 设备指令 | `METER_SWITCH` + 审批 | `iot.meter.switch.*` | M7 全通过 |
| 批量设备状态 | 设备管理「同步状态」 | `POST /iot/devices/status-sync` | `bp.iot.status-mode` | 本轮新增，mock 2/2 |
| 取 Token/续期 | 自动 | `bp.iot.token-mode` | `ymd.iot.credential.*` | 客户端已实现（mock 通过） |
| 设备台账同步 | 设备管理「同步设备」 | `POST /iot/devices/sync` | `bp.dev.device-mode` | M1-03/04 |
| 监控与对账 | IoT 监控 / 日对账 | `/iot/metrics`、`/iot/reconcile` | — | 监控页、对账页 |
| 回调重放（断线补推） | 联调工具 → 回调日志 | `POST /iot/callback-logs/replay-range` | — | 实测 2/2 |
| 对接能力自检 | 联调工具 → 对接能力 | `GET /iot/capabilities` | — | 模式/凭证/待办一览 |
| 指令时延统计 | IoT 监控 | `/iot/metrics` 的 `commands.cost` | — | 平均 71ms/P95 210ms（样本 10） |

---

## 三、配置清单（21 项，页面：系统与数据 → 系统参数，分组 IOT）

| 参数 | 默认值 | 说明 |
|---|---|---|
| `iot.callback.signAlgorithm` | v2-hmac-sha256 | 验签算法 |
| `iot.callback.appId` / `appSecret` | bp-test-app / bp-test-secret | 回调凭证（切生产必须替换） |
| `iot.callback.verify` | true | 是否验签（排障可临时关闭） |
| `iot.callback.defaultTenant` | 350600 | 回调落地租户 |
| `iot.callback.timestampToleranceSeconds` | 300 | 时间戳窗口 |
| `iot.callback.nonceCacheMinutes` | 10 | nonce 去重窗口 |
| `iot.callback.batchLimit` | 200 | 单批上限 |
| `iot.callback.qps` | 50 | 回调限流（预留） |
| `iot.command.timeoutSeconds` | 10 | 指令超时 |
| `iot.command.maxRetry` | 3 | 指令重试次数 |
| `iot.grantTask.timeoutSeconds` | 180 | 授权任务超时 |
| `iot.heartbeat.intervalSeconds` | 60 | 心跳期望间隔 |
| `iot.offline.thresholdSeconds` | 180 | 判离线阈值 |
| `iot.meter.reportPeriod` | ELEC:DAILY,WATER:DAILY | 表计上报周期（可 HOURLY） |
| `iot.meter.switch.delayMinutes` | 10 | 拉闸延迟执行窗口 |
| `iot.meter.switch.arrearsThreshold` | 0.01 | 欠费阈值 |
| `iot.meter.switch.overdueDays` | 30 | 逾期天数门槛 |
| `iot.meter.switch.nightFrom` / `nightTo` | 22:00 / 07:00 | 夜间禁拉闸 |
| `iot.meter.switch.dailyLimit` | 3 | 每日拉闸上限 |

> 切换开关：`bp.dev.command-mode`、`bp.dev.device-mode`、`bp.dev.meter-mode`、`bp.credential.mode`、`bp.iot.token-mode`、`bp.iot.status-mode`（mock / real）。

---

## 四、文档索引

| 文档 | 内容 |
|---|---|
| 15 号 | 对接接口与回调清单（平台 ↔ IoT） |
| 17 号 | 联调方案与 57 条测试用例 |
| 18 号 | IoT 平台需增加或完善的内容清单 |
| 19 号 | 测试执行报告（42/13/2）+ 压测基线 |
| 20 号 | 上线切换清单（开关/步骤/回滚/Go-No-Go） |
| 21 号 | IoT 侧需求规格说明书（5 项接口规格） |
| 22 号 | 本表 |

---

## 五、仍需 IoT 提供（5 项，验收见 21 号）

| ID | 事项 | 影响用例 | 平台侧状态 |
|---|---|---|---|
| IOT-TOKEN | 取 Token / 续期 | M1-01/02 | 客户端已实现（mock） |
| IOT-DEVICE-STATUS-BATCH | 批量设备状态 | M1-05 | 客户端+同步接口已实现 |
| IOT-LOCK-MODE | 常开/常闭端点 | M4-07 | 指令已支持，缺 IoT 实现 |
| IOT-METER-SPEC | 上报周期同频 | M6-07 | 平台可配 DAILY/HOURLY |
| IOT-LOAD-ENV | 压测/断网环境 | M8-02/03 | 平台压测脚本与批量重放已就绪 |

---

## 六、已知限制

1. **吞吐**：演示环境约 23 QPS（50 QPS 目标），需生产磁盘与异步日志优化，见 19 号「四之一」。
2. **回调日志**：当前同步写库，未做异步批量（可靠性优先）。
3. **真实设备行为**：开锁成功、断电生效等需接入真机验证（19 号标「部分」）。
4. **单租户压测**：多租户并发未压测。

---

## 七、验收路径

1. IoT 按 21 号实现 5 项 → 提供环境与凭证；
2. 按 20 号切换清单切 real，小流量验证；
3. 按 19 号重跑「部分/阻塞」用例，更新状态；
4. 满足 Go/No-Go（P0 全通过、指标 ≥95%、回滚演练）后上线。
