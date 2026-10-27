# -*- coding: utf-8 -*-
"""帮助与手册补充本轮 7 项。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HELP = os.path.join(ROOT, 'frontend', 'src', 'content', 'help.js')
MANUAL = os.path.join(ROOT, '10_业务操作流程与验收手册.md')

s = io.open(HELP, encoding='utf-8').read()
if '批次联动' not in s:
    s = s.replace('''          '批次号是业务编号（对外、合同引用），批次ID是系统内部标识，列表只展示批次号。' ''',
                  '''          '批次号是业务编号（对外、合同引用），批次ID是系统内部标识，列表只展示批次号。',
          '点批次行，下方「配租单」自动过滤为该批次；点「显示全部配租单」恢复。',
          '生成配租单：首次生成会提示生成张数；重复点击会提示已生成多少张；生成后房源状态变为「锁定」。',
          '摇号结果与配租单均显示人员姓名、手机号。' ''')
    s = s.replace('''          '报名即轮候：点「开始报名」后，同保障类型同组织的轮候人员自动计入参与人数，无需逐人报名。' ''',
                  '''          '报名即轮候：点「开始报名」后，同保障类型同组织的轮候人员自动计入参与人数，无需逐人报名。',
          '公示中签名单只列中签人，显示摇号序号、姓名、脱敏证件/手机、中签房源。' ''')
    s = re.sub(r"HELP_VERSION\s*=\s*'[^']*'", "HELP_VERSION = 'v3.2（2026-10-27）'", s, count=1)
    io.open(HELP, 'w', encoding='utf-8', newline='').write(s)
    print('帮助 → v3.2')

t = io.open(MANUAL, encoding='utf-8').read()
if '附录 AR' not in t:
    t = t.rstrip() + '''

---

## 附录 AR　配租单/公示/系统参数 7 项修正

| # | 反馈 | 处理 |
|---|---|---|
| 1 | 点批次后下方应显示该批次的配租单 | 批次表行点击联动：下方配租单按 `batchId` 过滤，顶部显示当前批次，可「显示全部配租单」 |
| 2 | 配租单缺人员姓名、手机号 | `AllocationVO` 增加 `personName/phoneMask`，列表批量补全并展示 |
| 3 | 生成配租单提示「已生成 0 张」，语义不清 | 接口返回 `{generated, existing, winners, availableHouses, message}`；首次提示「本次生成 N 张」，重复提示「该批次已生成 N 张，无需重复生成」 |
| 4 | 生成后房源仍为待配租 | 生成配租单时把 `bp_asset_house.house_status` 置为 `LOCKED`，并把批次池置 `SELECTED` |
| 5 | 摇号结果页缺姓名、手机号 | `LotteryResultVO` 增加 `personName/phoneMask`；结果表补两列；中签排在前、序号升序 |
| 6 | 公示天数参数需可改 | 系统支撑→系统参数新增「修改」按钮：弹窗改值并调 `POST /sys/configs`，即时生效（写 CRITICAL 审计） |
| 7 | 公示中签名单显示未中签、序号乱、无房号 | 后端只取 `WON`；姓名取 `personName`；序号改用选房序号（两位数）；无房号时按批次房源池顺序补；前端标签 `WON` |

### AR.1 实测（2026-10-27）

```
配租单字段：钱待审 / 139****0005、李二期 / 139****0002
摇号结果：李二期 139****0002 WON 排在前
生成（重复）：{generated:0, existing:3, winners:3, availableHouses:0,
             message:"该批次已生成 3 张配租单，无需重复生成"}
房源 LOCKED 数：3
中签名单：1 条，序号 01，姓名 李二期，房源 回归10260222回归房源
公示天数：GET 7 / POST 7 均 200
界面：批次行点击后标题显示「当前批次 LB…」，配租单表头含「人员/手机号」；
     系统参数页 100 行、出现「修改」按钮
```

### AR.2 说明

- 「批次ID」不再出现在列表；接口仍用 ID，批次号用于对外。
- 公示中签名单默认只列中签；候补/未中签不在公示名单内。
'''
    io.open(MANUAL, 'w', encoding='utf-8', newline='').write(t)
    print('手册已补附录 AR')
