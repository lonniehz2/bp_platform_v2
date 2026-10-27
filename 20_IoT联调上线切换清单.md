# IoT 联调上线切换清单

> 文档编号：20  
> 适用：从 mock 切换到真实 IoT 环境（预发/生产）  
> 前置：19 号报告中的 5 个阻塞项已由 IoT 侧补齐

---

## 一、切换开关一览

| 开关 | 取值 | 作用 | 默认 |
|---|---|---|---|
| `bp.device.command.mode` | `mock` / `real` | 指令下发客户端 | mock |
| `bp.device.inventory.mode` | `mock` / `real` | 设备台账同步客户端 | mock |
| `bp.meter.pull.mode` | `mock` / `real` | 表计读数拉取客户端 | mock |
| `bp.credential.mode` | `mock` / `real` | 密码/卡/人脸下发 | mock |
| `iot.callback.verify` | `true` / `false` | 回调是否验签 | true |
| `iot.callback.appId` / `appSecret` | 字符串 | 回调验签凭证 | 测试值 |
| `iot.callback.defaultTenant` | 租户编码 | 回调落地租户 | `350600` |
| `iot.callback.timestampToleranceSeconds` | 秒 | 时间戳窗口 | 300 |
| `iot.callback.nonceCacheMinutes` | 分钟 | Nonce 去重窗口 | 10 |

> 系统参数入口：系统与数据 → 系统支撑 → 系统参数（分组 `IOT`），改完即时生效，无需重启。

---

## 二、IoT 侧参数（切换前必须填）

| 参数 | 用途 | 归属 |
|---|---|---|
| 取 Token URL、appId/appSecret、签名算法 | `YmdTokenManager` | IoT 提供 |
| 指令下发基础地址 + 4 类路径 | 开锁/重启/校时/拉合闸 | IoT 提供 |
| 常开/常闭路径与 `mode` 取值（OPEN/CLOSE/NORMAL） | 持锁模式 | IoT 确认 |
| 设备台账接口（全量/增量）与字段映射（`lockId`） | 同步 | IoT 提供 |
| 表计接口（表号、倍率、读数时间、单位） | 读数 | IoT 提供 |
| 批量设备状态接口 | 在线/电量/RSSI | IoT 提供 |
| 开放平台地址（预发/生产）与白名单 | 网络 | 双方 |

---

## 二之二、先看能力清单

切换前先访问 **IoT 联调工具 → 对接能力**（或 GET /api/v1/iot/capabilities）：
它会直接列出当前客户端模式、凭证是否配齐、以及仍需 IoT 提供的 5 项能力。

eadyForReal=false 表示凭证未配齐，不要切真实环境。

## 三、切换步骤（建议窗口 30 分钟）

1. **冻结写入**：暂停设备同步/表计拉取定时任务（`IotDailySyncJob` 临时停用）。
2. **改参数**：把 6 个开关按上表切到 `real`，填入 IoT 提供的地址/凭证。
3. **验证连通**：
   - 取一次 Token（或调一次设备状态查询）确认 200；
   - 回调验签用 IoT 真实 appId/secret 重算一次签名，确认通过。
4. **小流量验证**：
   - 单台在线门锁：开锁 → 回执 SUCCESS；
   - 单台表计：拉取昨日读数 → 入库；
   - 单台门锁：常开 → 恢复正常。
5. **全量放开**：恢复定时任务，观察 30 分钟指标（`/iot/metrics`）。
6. **回归**：按 19 号报告重跑「部分/阻塞」用例。

---

## 四、验证命令（可复制）

```bash
# 健康检查
curl -s http://<host>:8080/actuator/health

# 指标（在线率/指令成功率/回调成功率）
curl -s -H "Authorization: Bearer $TOKEN" -H "X-Tenant-Id: 350600" \
  "http://<host>:8080/api/v1/iot/metrics?hours=1"

# 日对账（指令/回调/表计）
curl -s -H "Authorization: Bearer $TOKEN" -H "X-Tenant-Id: 350600" \
  "http://<host>:8080/api/v1/iot/reconcile?date=2026-10-28"

# 回调日志（看验签与处理结果）
curl -s -H "Authorization: Bearer $TOKEN" -H "X-Tenant-Id: 350600" \
  "http://<host>:8080/api/v1/iot/callback-logs?pageNum=1&pageSize=20"
```

---

## 五、回滚

| 场景 | 动作 |
|---|---|
| 指令持续失败 | `bp.device.command.mode=mock` 立即回退（不影响已下发记录） |
| 台账同步异常 | `bp.device.inventory.mode=mock` |
| 表计数据异常 | `bp.meter.pull.mode=mock` |
| 回调验签不通过 | 先核对 appId/secret 与签名串；确认无误可临时 `iot.callback.verify=false`，**仅限排障 10 分钟**并记录 |

回滚后需重跑 19 号报告中对应阶段的用例。

---

## 六、风险清单

| 风险 | 影响 | 缓解 |
|---|---|---|
| 真实超时/失败码与约定不一致 | 指令状态判定错误 | 用 `costMs`/`code` 对齐，先在单设备验证 |
| 表计倍率缺失 | 用量偏差 10 倍 | 切换前用 1 块表核对倍率 |
| 回调重复/乱序 | 事件重复 | 平台已按 `eventId` 唯一 + nonce 去重 |
| Token 过期时间过短 | 频繁取 Token | 确认有效期与缓存策略 |
| 批量状态接口限流 | 同步变慢 | 分批 + 夜间窗口 |
| 回调吞吐不足（演示环境约 10 QPS） | 高峰期回调积压 | 上 SSD / innodb_flush_log_at_trx_commit=2 / 异步日志；压测见 19 号报告四之一 |

---

## 七、切换判定（Go / No-Go）

必须同时满足：

- [ ] 19 号报告 P0 用例 100% 通过
- [ ] 单设备开锁/拉合闸/表计/常开常闭各 1 次成功
- [ ] 回调验签真实凭证通过
- [ ] `/iot/metrics` 在线率、指令成功率、回调成功率均 ≥ 95%（观察 30 分钟）
- [ ] 回滚开关演练 1 次成功
