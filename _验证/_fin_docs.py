# -*- coding: utf-8 -*-
"""帮助/手册/菜单说明：资金流水页新增对账单与收款确认。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 帮助 ----------
P = os.path.join(ROOT, 'frontend', 'src', 'content', 'help.js')
s = io.open(P, encoding='utf-8').read()
OLD = """      { type: 'h3', text: '6.8 资金流水与报表' },
      { type: 'ul', items: ['资金流水：按收入/支出、时间、业务类型查询', '报表导出：选择报表与时间范围导出'] }"""
NEW = """      { type: 'h3', text: '6.8 资金流水与报表' },
      {
        type: 'ul', items: [
          '资金流水：按收入/支出、时间、业务类型查询；可对单笔流水「核验」。',
          '对账单：新建对账（渠道对账 / 日终对账 / 手工对账），系统金额留空时按「日期+渠道」自动汇总已确认收款；不一致即标记「有差异」，需人工「处理差异」后归档。',
          '收款确认：列出待支付（PENDING）的收款单，确认后才计入资金流水；确认后可在「账单与缴费」核销到具体账单。',
          '报表导出：选择报表与时间范围导出。'
        ]
      },"""
n = 0
if OLD in s:
    s = s.replace(OLD, NEW, 1)
    n += 1
s = re.sub(r"HELP_VERSION\s*=\s*'[^']*'", "HELP_VERSION = 'v1.5（2026-10-26）'", s, count=1)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('帮助更新:', n, '→ v1.5')

# ---------- 菜单说明 ----------
P = os.path.join(ROOT, 'frontend', 'src', 'layout', 'menuConfig.js')
m = io.open(P, encoding='utf-8').read()
if "'/cashflow': '收入支出流水与核账'," in m:
    m = m.replace("'/cashflow': '收入支出流水与核账',",
                  "'/cashflow': '流水 / 对账单 / 收款确认',")
    io.open(P, 'w', encoding='utf-8', newline='').write(m)
    print('菜单说明已更新')

# ---------- 手册附录 Z ----------
P2 = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
t = io.open(P2, encoding='utf-8').read()
if '附录 Z' not in t:
    t = t.rstrip() + '''

---

## 附录 Z　资金对账单与收款确认

### Z.1 页面结构（收费与账务 → 资金流水）

| 页签 | 内容 | 主要接口 |
|---|---|---|
| 资金流水 | 收支流水列表 + 单笔「核验」 | `GET /fin/cash-flows`、`POST /fin/cash-flows/{id}/verify` |
| **对账单** | 对账单列表（筛选日期/类型/状态）+ 新建对账 + 处理差异 | `GET/POST /fin/reconciles`、`POST /fin/reconciles/{id}/handle` |
| **收款确认** | 待支付收款单列表 + 「确认收款」 | `GET /fin/payments`、`POST /fin/payments/{id}/confirm` |

### Z.2 对账规则

- 对账类型：`CHANNEL` 渠道对账 / `DAILY` 日终对账 / `MANUAL` 手工对账
- 系统金额：留空时按「对账日期 + 支付渠道」汇总当日已确认收款（`pay_status=SUCCESS`）
- 差异 = 系统金额 − 渠道金额；为 0 → 「一致」，否则「有差异」
- 有差异的单据需「处理差异」（必填说明）→ 状态变「已处理」

### Z.3 收款确认规则

- 仅 `PENDING`（待支付）可确认；确认后写资金流水（`PAYMENT` 业务类型）
- 已确认的收款单可在「账单与缴费」核销到具体账单，核销额度受可核销余额限制

### Z.4 实测

```
新建渠道对账（微信，渠道 1000）→ 系统 0.00 / 差异 -1000.00 / 有差异
处理差异                → HANDLED（已处理）
新建日终对账（渠道 780.29）→ 系统 780.29 / 差异 0.00 / 一致
确认收款 PAY-PENDING-0005 → SUCCESS，写入资金流水
```

### Z.5 演示数据

新增 5 笔 `PENDING` 收款单（`PAY-PENDING-0001~0005`，渠道含现金/银行/支付宝），
用于演示「确认收款」；实测确认 2 笔后剩余 3 笔待确认。
'''
    io.open(P2, 'w', encoding='utf-8', newline='').write(t)
    print('手册已补附录 Z')
