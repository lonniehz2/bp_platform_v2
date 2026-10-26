# -*- coding: utf-8 -*-
"""核对报告与手册：P1 第一批结果。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 核对报告 ----------
P = os.path.join(ROOT, '14_前后端接口与页面匹配核对.md')
s = io.open(P, encoding='utf-8').read()
if '## 十二、P1 整改进展' not in s:
    s = s.rstrip() + '''

## 十二、P1 整改进展（2026-10-26 傍晚）

### 12.1 数字

| 指标 | P0 后 | P1 后 |
|---|---|---|
| 前端调用 | 425 | **438** |
| 后端有、前端未调用 | 29 | **17** |
| 前端调用、后端无 | 2（动态） | 2（动态） |

### 12.2 本轮接上的接口（12 个）

| 页面 | 新动作 | 接口 |
|---|---|---|
| 投诉管理 | 处理 | `POST /complaints/{id}/resolve` |
| 投诉管理 | 评价（满意度 1-5） | `POST /complaints/{id}/evaluate` |
| 投诉管理 | 转工单 | `POST /complaints/{id}/to-workorder` |
| 公示管理 | 发布 | `POST /publicities/{id}/publish` |
| 轮候管理 | 候补退出 | `POST /allocation/waiting/{id}/exit` |
| 入户走访 | 转工单 | `POST /visits/{id}/to-workorder` |
| 年审复核 | 调租（生成变更单） | `POST /annual-reviews/{id}/rent-change` |
| 补贴管理 | 发放失败 | `POST /fin/subsidies/records/{id}/fail` |
| 合同变更 | 从合同发起变更 | `POST /contracts/{id}/changes` |
| 资金流水 | 核验 | `POST /fin/cash-flows/{id}/verify` |

### 12.3 顺带修掉的 4 个坏调用（点按钮必失败）

| 页面 | 原代码 | 问题 |
|---|---|---|
| 申请受理 | `req.post(/applications//accept, {})` | 路径丢变量，成非法表达式 |
| 设备告警 | `req.post(/dev-events//handle, …)` | 同上 |
| 钥匙包 | `req.post(/keyring//freeze)` / `unfreeze` | 同上 |

新增扫描脚本 `_scan_bad_paths.py`，当前**坏调用 0 处**。

### 12.4 仍未接线（17 个，P2 为主）

| 类别 | 接口 |
|---|---|
| 开放平台 Webhook | `open/webhooks*`、`open/webhook-logs*`（5） |
| 报表 | `rpt/exports/{id}`、`rpt/metrics/trend/{id}`（2） |
| 规则引擎 | `rules/rules/{id}/status`（1） |
| 字段标签 | `sys/field-labels/refresh`（1） |
| 设备上报 | `access-records/batch`（1） |
| 对账批处理 | `grant-reconcile/diffs/handle-batch`（1） |
| 消息模板 | `messages/templates/{id}/render`（1） |
| 催缴按合同查 | `fin/arrears/by-contract/{id}`（1，页面已按合同筛选，接口冗余） |
| 补贴标准启停 | `fin/subsidies/standards/{id}/status`（1，无标准维护界面） |
| 资金对账处理 | `fin/reconciles/{id}/handle`（1，无对账单列表） |
| 收款确认 | `fin/payments/{id}/confirm`（1，无支付单列表） |
| 押金收/扣 | `fin/deposits/{id}/receive|deduct`（2，页面走动态 URL，实测可用，工具误报） |
'''
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('核对报告已补 P1 进展')

# ---------- 手册附录 T ----------
P2 = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
t = io.open(P2, encoding='utf-8').read()
if '附录 T' not in t:
    t = t.rstrip() + '''

---

## 附录 T　P1 整改落地（服务与收费动作补齐）

| 页面 | 新增动作 | 说明 |
|---|---|---|
| 投诉管理 | 处理 / 评价 / 转工单 | 处理记录结果；评价记满意度 1-5；转工单生成服务工单 |
| 公示管理 | 发布 | 发布后进入公示期，不可重复发布 |
| 轮候管理 | 候补退出 | 需填原因，退出后需重新申请 |
| 入户走访 | 转工单 | 走访发现问题转维修/整改 |
| 年审复核 | 调租 | 生成合同变更单（新租金 + 原因） |
| 补贴管理 | 发放失败 | 记录失败原因，便于补发 |
| 合同变更 | 从合同发起变更 | 统一 `POST /contracts/{id}/changes` |
| 资金流水 | 核验 | 与渠道核对后标记 |

### T.1 修复的坏调用

申请受理「受理」、设备告警「处理」、钥匙包「冻结/解冻」四个按钮原先路径拼接错误（`/applications//accept` 等），点击必失败；已修正，并加扫描脚本防回归。

### T.2 待办

开放平台 Webhook 管理、报表导出任务、规则引擎维护、补贴标准启停、资金对账单、收款确认等 17 项列入 P2。
'''
    io.open(P2, 'w', encoding='utf-8', newline='').write(t)
    print('手册已补附录 T')
