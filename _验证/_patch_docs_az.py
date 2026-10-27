# -*- coding: utf-8 -*-
"""附录 AZ：后端接口与前端页面核对。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
s = io.open(p, encoding='utf-8').read()
if '附录 AZ' not in s:
    s = s.rstrip() + '''

---

## 附录 AZ　后端接口与前端页面核对

### AZ.1 核对方法

1. 扫描后端 `*Controller.java`，提取类级 `@RequestMapping` 与方法级 Mapping，共 **391 个接口 / 58 个控制器**；
2. 扫描前端 `src` 下所有 `.vue/.js` 中的接口路径字面量做匹配；
3. 对模板字符串拼接的路径做人工复核，排除误报。

**结论**：58 个控制器全部有前端入口（唯一例外是 `/api/callback/iot`，那是 IoT 调平台的回调，本就不需要页面）。
缺口集中在**控制器内部的部分端点**，不是整个模块缺失。

### AZ.2 本轮补齐

| 缺项 | 处理 |
|---|---|
| 设备批量导入 | 新增 `POST /devices/import`（CSV：设备编号/名称/类型/MAC/房源编号），设备页新增「批量导入」三步向导（选择→校验预览→结果+导出失败行） |
| 设备数据新鲜度 | 设备页新增「24h 未上报」告警条与静默设备清单（`GET /devices/freshness`） |
| 合同换床 | 合同列表新增「换床」：选目标房源+原因，调 `POST /contracts/{id}/swap-bed` |
| 申请审核轨迹 | 修复 `openRecords` 中被注释掉的加载逻辑，轨迹抽屉现在真的会请求 `/applications/{id}/reviews` |

### AZ.3 实测（2026-10-28）

```
设备导入：4 行 → 成功 2、跳过 1（编号重复）、失败 1（未知类型），失败行可导出
界面：设备导入三步步骤条；导入后列表刷新
新鲜度：总 6539 / 24h 内 5 / 静默 6534（99.92%），设备页顶部告警可见
合同换床：列表出现 20 个「换床」按钮（履约中/续签中合同）
```

### AZ.4 仍缺 UI 的端点（按优先级）

| 优先级 | 接口 | 建议 |
|---|---|---|
| P1 | `POST /alerts/{id}/escalate` | 告警页加「升级」按钮（升级为工单/加急） |
| P1 | `POST /annual-reviews/{id}/start`、`/finish` | 年审页加「开始年审」「完成年审」 |
| P1 | `POST /credits/{id}/expire`、`/push`、`/revoke` | 信用页加「置为过期」「推送信用平台」「撤销」 |
| P2 | `GET /house-calendar/{houseId}/availability` | 短租预订前查询房源可用性 |
| P2 | `GET /short-rent-orders/by-house`、`/calc-nights` | 短租页按房源查订单、自动算住晚数 |
| P2 | `GET /exchanges/count` | 换房页显示可换房数量 |
| P3 | `GET /spaces/{id}/subtree` | 空间选择器按子树过滤 |
| P3 | `GET /files/{id}/download` | 附件统一下载入口 |
| — | `POST /access-records/batch` | IoT/设备侧批量上报，不需要页面 |

### AZ.5 说明

- 「有控制器无页面」的情况没有；所谓“功能缺失”多是**单个动作没有按钮**；
- 上述 P1 三项都是“加一个按钮 + 一个确认框”的量级，可按业务优先级继续补。
'''
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('附录 AZ 已加')
