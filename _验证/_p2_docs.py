# -*- coding: utf-8 -*-
"""帮助与手册：P2 四项（Webhook / 报表任务 / 规则引擎 / 补贴标准）。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 帮助 ----------
P = os.path.join(ROOT, 'frontend', 'src', 'content', 'help.js')
s = io.open(P, encoding='utf-8').read()
n = 0

OLD_HOOK = """      { type: 'h3', text: '9.4 开放平台' },"""
if OLD_HOOK in s and 'Webhook 订阅' not in s:
    s = s.replace(OLD_HOOK, """      { type: 'h3', text: '9.4 开放平台' },
      {
        type: 'ul', items: [
          '应用：创建应用、重置密钥、启停；AppSecret 只在创建/重置时显示一次。',
          'Webhook 订阅：填写回调地址与「订阅事件」（逗号分隔，* 表示全部），可启停；「发布测试」会推一条测试事件。',
          '投递日志：查看每次推送的状态/HTTP 码/重试次数/响应，「重试失败」批量补推最近失败记录。'
        ]
      },""", 1)
    n += 1

OLD_REPORT = """      { type: 'h3', text: '6.8 资金流水与报表' },"""
if OLD_REPORT in s:
    s = s.replace("""          '报表导出：选择报表与时间范围导出。'""",
                  """          '报表导出：选择报表与时间范围导出；下方「导出任务」可筛选状态、查看任务详情、补跑待执行任务、预览与下载文件。'""", 1)
    n += 1

OLD_RULE = """      { type: 'h3', text: '8.2 告警处理' },"""
if OLD_RULE in s and '规则引擎' not in s.split('8.2 告警处理')[1][:200]:
    s = s.replace(OLD_RULE, """      { type: 'h3', text: '8.2 告警处理' },
      { type: 'p', text: '阈值告警由「已发布」的规则集产生；下方「规则引擎」区块可维护规则集与规则。' },""", 1)
    n += 1

OLD_SUB = """      { type: 'h3', text: '6.7 补贴管理' },"""
if OLD_SUB in s and '补贴标准' not in s.split('6.7 补贴管理')[1][:400]:
    s = s.replace("""          '发放后可抵扣该期间租金账单。'""",
                  """          '发放后可抵扣该期间租金账单。',
          '下方「补贴标准」维护标准（保障类型 + 补贴方式 + 补贴值 + 有效期），可停用；停用后不再参与发放。'""", 1)
    n += 1

s = re.sub(r"HELP_VERSION\s*=\s*'[^']*'", "HELP_VERSION = 'v1.7（2026-10-26）'", s, count=1)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('帮助更新段落:', n, '→ v1.7')

# ---------- 手册附录 AB ----------
P2 = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
t = io.open(P2, encoding='utf-8').read()
if '附录 AB' not in t:
    t = t.rstrip() + '''

---

## 附录 AB　P2 四项界面补齐

### AB.1 开放平台 → Webhook 订阅 + 投递日志

| 区块 | 能力 | 接口 |
|---|---|---|
| Webhook 订阅 | 列表、新建（名称/回调地址/订阅事件/重试/超时）、启停、发布测试 | `GET/POST /open/webhooks`、`POST /open/webhooks/{id}/status`、`POST /open/webhooks/publish` |
| 投递日志 | 列表（按状态筛选）、重试失败 | `GET /open/webhook-logs`、`POST /open/webhook-logs/retry` |

回调地址做了 `http(s)://` 校验；发布测试会按事件类型推送到所有已启用且订阅该事件的地址。

### AB.2 报表导出 → 导出任务

新增：状态筛选、任务详情（`GET /rpt/exports/{id}`）、补跑待执行（`POST /rpt/exports/run-pending`）、刷新；原有预览与下载保留。

### AB.3 告警处理 → 规则引擎

| 能力 | 接口 |
|---|---|
| 规则集列表（按域/状态筛选） | `GET /rules/rulesets` |
| 新建规则集（同编码自动升版本） | `POST /rules/rulesets` |
| 发布 / 停用 | `POST /rules/rulesets/{id}/publish`、`/disable` |
| 查看规则 / 新增规则 | `GET/POST /rules/rulesets/{id}/rules` |
| 规则启停 | `POST /rules/rules/{id}/status` |

阈值与动作必须为合法 JSON，前端会在提交前校验并提示示例。

### AB.4 补贴管理 → 补贴标准

| 能力 | 接口 |
|---|---|
| 标准列表（保障类型/补贴方式/关键字） | `GET /fin/subsidies/standards` |
| 新建标准 | `POST /fin/subsidies/standards` |
| 启停 | `POST /fin/subsidies/standards/{id}/status` |

补贴值含义随方式变化：定额=元/月；按面积=元/㎡·月；按人=元/人·月；比例=0~1。

### AB.5 实测

```
Webhook：创建 200 → 停用 200 → 发布测试 200
规则集：创建 DRAFT v1 → 加规则 ENABLED → 发布 PUBLISHED → 停用 DISABLED
补贴标准：创建 ENABLED → 停用 DISABLED
报表补跑：返回 0（当前无待执行）
```

> 验证用数据（P2验证订阅 / P2_ALERT 规则集 / SUB-P2-2026 标准）均已置为停用，不影响演示口径。
'''
    io.open(P2, 'w', encoding='utf-8', newline='').write(t)
    print('手册已补附录 AB')
