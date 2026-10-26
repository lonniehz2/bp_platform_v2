# -*- coding: utf-8 -*-
"""P0 收尾：同步文档、帮助文案与权限名。"""
import io
import os

import pymysql

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 1) 帮助文案 ----------
P = os.path.join(ROOT, 'frontend', 'src', 'content', 'help.js')
s = io.open(P, encoding='utf-8').read()
n = 0
PAIRS = [
    ('「告警规则」', '「告警处理」'),
    ('告警规则 → ', '告警处理 → '),
    ('催缴管理用于', '催缴管理分「欠费处置」与「催缴通知」两个页签，欠费处置用于'),
]
for a, b in PAIRS:
    if a in s:
        s = s.replace(a, b)
        n += 1
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('帮助文案替换:', n)

# ---------- 2) 权限名 ----------
try:
    conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                           password='5677@Mysql', database='bp_platform',
                           charset='utf8mb4', autocommit=True,
                           connect_timeout=20, read_timeout=120)
    cur = conn.cursor()
    cur.execute("select perm_code, perm_name from bp_iam_permission "
                "where perm_code like '%alert%' or perm_name like '%告警%'")
    before = cur.fetchall()
    cur.execute("update bp_iam_permission set perm_name='告警处理' "
                "where perm_code='page:alerts:view'")
    cur.execute("select perm_code, perm_name from bp_iam_permission "
                "where perm_code='page:alerts:view'")
    print('告警权限名:', before, '→', cur.fetchall())
    conn.close()
except Exception as e:
    print('权限名更新跳过:', type(e).__name__, str(e)[:80])

# ---------- 3) 手册附录 S ----------
P = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
s = io.open(P, encoding='utf-8').read()
if '附录 S' not in s:
    s = s.rstrip() + '''

---

## 附录 S　P0 整改落地（接口↔页面缺口）

### S.1 催缴：双模型明确分工

| 页签 | 模型 | 接口 | 用途 |
|---|---|---|---|
| 欠费处置 | `fin_arrears_action` | `/fin/arrears`（scan/page/create/execute/revoke） | **可执行动作**：通知催缴 / 冻结权限 / 解冻 / 限制续租 / 到期不续 / 司法程序 |
| 催缴通知 | 催缴单 | `/fin/dunnings` | 已发出的短信/电话/上门/书面通知记录，只读 + 登记 |

页面能力：

- 扫描建议：按逾期天数聚合欠费合同，标记「建议冻结」，一键生成处置
- 新建处置：合同/人员/欠费/逾期天数/动作类型；冻结时选范围（默认 `EXCLUDE_MAIN_DOOR`）并勾选安全风险
- 执行 / 撤销：执行联动通行授权；撤销需填原因（如已缴清）

### S.2 退租：补齐四个动作

| 动作 | 接口 | 权限 |
|---|---|---|
| 提交 | `POST /terminations/{id}/submit` | `biz:termination:submit` |
| 驳回 | `POST /terminations/{id}/reject` | `biz:termination:create` |
| 取消 | `POST /terminations/{id}/cancel` | `biz:termination:cancel` |
| 办结 | `POST /terminations/{id}/complete` | `biz:termination:create` |

连同原有 审批 / 查验 / 结算 / 强制腾退 / 释放房源，退租全流程闭环。

### S.3 工单：补齐关单/取消/退回

`POST /workorders/{id}/close|cancel|reject`，统一传 `ActionCmd{operatorId, operatorName, content}`。

### S.4 告警页更名与升级动作

| 项 | 变化 |
|---|---|
| 菜单/标题 | 告警规则 → **告警处理** |
| 行操作 | 处理 / 解决 / 忽略 / **升级** / 转工单 |

规则维护（`/rules/*`）尚未做界面，已在核对报告列入 P2。

### S.5 数据修正

| 项 | 处理 |
|---|---|
| 欠费动作类型 | `SMS/PHONE/NOTICE/VISIT` 归一为 `NOTIFY`（旧种子与后端枚举不符） |
| 冻结范围 | 仅 `FREEZE` 动作填写，其余置空 |
| 演示数据 | 重建为 14 个合同 / 28 条动作，逾期 43–77 天，含冻结与通知，状态含待执行/已执行 |

### S.6 核对结果变化

| 指标 | 整改前 | 整改后 |
|---|---|---|
| 后端接口 | 422 | 422 |
| 前端调用 | 413 | **425** |
| 后端有、前端未调用 | 42 | **29** |
| 前端调用、后端无 | 2（动态） | 2（动态） |
'''
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('手册已补附录 S')
