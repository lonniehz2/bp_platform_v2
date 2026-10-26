# -*- coding: utf-8 -*-
"""帮助与手册：设备告警统计口径/详情可读化/类型含义。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 帮助 ----------
P = os.path.join(ROOT, 'frontend', 'src', 'content', 'help.js')
s = io.open(P, encoding='utf-8').read()
OLD = "      { type: 'ul', items: ['设备告警：低电量、拆机、试错、胁迫、超功率、离线等，可处理/关闭/忽略', '通行记录：按人、房源、时间查询开门记录'] },"
NEW = """      { type: 'ul', items: [
        '设备告警：低电量、防拆、试错、胁迫、超功率、离线等；列表「详情」把上报的 JSON 转成中文（如「原因：外壳被打开」「次数：5」）。',
        '顶部四张卡片与列表用同一组筛选条件：事件总数 / 未处理 / 严重 / 当前告警类型（种，括号内为系统支持的 6 种）。',
        '可对未处理事件「标记处理」并填写处理说明。',
        '通行记录：按人、房源、时间查询开门记录'
      ] },"""
if OLD in s:
    s = s.replace(OLD, NEW, 1)
s = re.sub(r"HELP_VERSION\s*=\s*'[^']*'", "HELP_VERSION = 'v1.6（2026-10-26）'", s, count=1)
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('帮助已更新 → v1.6')

# ---------- 手册附录 AA ----------
P2 = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
t = io.open(P2, encoding='utf-8').read()
if '附录 AA' not in t:
    t = t.rstrip() + '''

---

## 附录 AA　设备告警页三处修正

| # | 问题 | 原因 | 处理 |
|---|---|---|---|
| 1 | 统计条数与列表不一致 | `/dev-events/stats` 不接收筛选条件，始终统计全量（5 条），而列表带 `alarmOnly=true` 只有 4 条 | 统计接口接收与列表相同的筛选参数，列表与统计共用 `buildQuery` |
| 2 | 详情列显示 JSON 字符串 | 后端 `body` 存的是 IoT 上报原文 | 前端 `fmtBody` 把 JSON 转「中文键：值」，如 `原因：外壳被打开`、`次数：5` |
| 3 | 「告警类型 6」含义不清 | 原卡片取值是 `alarmTypes.length`，即**系统支持的告警类型数**，不是当前数据条数 | 卡片改为「当前告警类型（种）N / 系统支持 6 种」，并加悬浮说明列出 6 种 |

### AA.1 系统支持的 6 种告警

| 类型 | 名称 | 默认级别 |
|---|---|---|
| OFFLINE | 离线 | 警告 |
| LOW_BATTERY | 低电量告警 | 警告 |
| TAMPER | 防拆告警 | 严重 |
| TRIAL_ERROR | 试错告警（密码连续错误） | 警告 |
| DURESS | 胁迫告警 | 严重 |
| POWER_OVER | 超功率告警 | 警告 |

### AA.2 实测

```
列表 total（alarmOnly=true）：4
统计 total / unhandled / typeCount：4 / 4 / 4
系统支持告警类型：6

详情示例：
  密码/卡号：1001
  次数：5
  原因：外壳被打开
  电量(%)：12
```
'''
    io.open(P2, 'w', encoding='utf-8', newline='').write(t)
    print('手册已补附录 AA')
