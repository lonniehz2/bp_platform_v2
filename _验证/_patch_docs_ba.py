# -*- coding: utf-8 -*-
"""附录 BA：短租工具补齐 + 参数审计器修正。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
s = io.open(p, encoding='utf-8').read()
if '附录 BA' not in s:
    s = s.rstrip() + '''

---

## 附录 BA　剩余缺口补齐（短租）

### BA.1 新增

| 功能 | 入口 | 接口 |
|---|---|---|
| 按房源查订单 | 短租订单 → 工具栏「按房源查」 | `GET /short-rent-orders/by-house` |
| 住晚计算 | 短租订单 → 工具栏「住晚计算」 | `GET /short-rent-orders/calc-nights` |
| 合同换床（上一轮） | 合同列表「换床」 | `POST /contracts/{id}/swap-bed` |
| 设备数据新鲜度（上一轮） | 设备页顶部告警条 | `GET /devices/freshness` |

「按房源查」：选房源 + 日期 → 列出该房源当日订单（订单号/入住/退房/状态/金额）。
「住晚计算」：选入住/退房时间 → 显示共 N 晚；退房早于入住会提示不合法。

### BA.2 实测（2026-10-28）

```
calc-nights：2026-10-28 14:00 → 2026-10-31 12:00 = 3 晚
by-house：houseId=1000000000000012162, date=2026-10-27 → 0 条（当日无单）
```

### BA.3 顺带修正：参数审计器

`_audit_params.py` 解析后端 `@RequestParam` 时，遇到 `@RequestParam @DateTimeFormat(...) LocalDate date`
这种「无括号 + 中间夹注解」的写法会漏参数，误报前端多传 `date/houseId`。
已修正正则：允许 `@RequestParam` 无括号、且允许多个中间注解。

### BA.4 仍未补的 UI（都已确认后端存在）

| 接口 | 说明 |
|---|---|
| `GET /exchanges/count` | 换房页显示某合同已完成换房次数 |
| `GET /house-calendar/{houseId}/availability` | 短租预订前查可用性 |
| `GET /spaces/{id}/subtree` | 空间选择器按子树过滤 |
| `GET /files/{id}/download` | 附件统一下载入口 |

这四项属“锦上添花”，不影响主流程闭环。
'''
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('附录 BA 已加')
