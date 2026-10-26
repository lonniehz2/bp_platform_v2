# -*- coding: utf-8 -*-
"""核对报告补 P0 结果（第二轮）。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 '14_前后端接口与页面匹配核对.md')
s = io.open(P, encoding='utf-8').read()

if '## 十一、P0 整改结果' not in s:
    s = s.rstrip() + '''

## 十一、P0 整改结果（2026-10-26 下午）

### 11.1 数字变化

| 指标 | 整改前 | 整改后 |
|---|---|---|
| 后端接口 | 422 | 422 |
| 前端调用 | 413 | **425** |
| 后端有、前端未调用 | 42 | **29** |
| 前端调用、后端无 | 2（动态） | 2（动态） |
| 静态检查 15 项 | 14 通过 | **15 通过** |

### 11.2 已补齐的 13 个接口

| 模块 | 接口 | 界面位置 |
|---|---|---|
| 催缴 | `GET /fin/arrears/scan` | 催缴管理 → 扫描建议 |
| 催缴 | `POST /fin/arrears` | 催缴管理 → 新建处置 |
| 催缴 | `GET /fin/arrears` | 催缴管理 → 欠费处置列表 |
| 催缴 | `POST /fin/arrears/{id}/execute` | 行操作「执行」 |
| 催缴 | `POST /fin/arrears/{id}/revoke` | 行操作「撤销」 |
| 退租 | `POST /terminations/{id}/submit` | 行操作「提交」 |
| 退租 | `POST /terminations/{id}/reject` | 行操作「驳回」 |
| 退租 | `POST /terminations/{id}/cancel` | 行操作「取消」 |
| 退租 | `POST /terminations/{id}/complete` | 行操作「办结」 |
| 工单 | `POST /workorders/{id}/close` | 行操作「关单」 |
| 工单 | `POST /workorders/{id}/cancel` | 行操作「取消」 |
| 工单 | `POST /workorders/{id}/reject` | 行操作「退回」 |
| 告警 | `POST /alerts/{id}/escalate` | 行操作「升级」 |

### 11.3 催缴模型结论

两套模型**不是重复，而是分工**，已按此落地：

- `fin_arrears_action`（`/fin/arrears`）= 可执行的处置动作（通知/冻结/限制/司法），有状态机与执行留痕
- 催缴单（`/fin/dunnings`）= 已发出的通知记录，只读 + 手工登记

页面用两个页签并列，避免“二选一”丢掉任一侧能力。

### 11.4 顺带修的数据问题

| 问题 | 处理 |
|---|---|
| 欠费动作类型与后端枚举不符（SMS/PHONE/NOTICE/VISIT） | 归一为 `NOTIFY` |
| 非冻结动作也写了冻结范围 | 仅 `FREEZE` 保留，其余置空 |
| 演示数据 45 条全指向同一合同 | 重建为 14 合同 / 28 条动作，逾期 43–77 天 |
| 测试残留（合同/申请/换房引用 `id=1`） | 清理 5 条；`_check_data_health.py` 新增「悬空引用」检查 |
| 合同生效但房源未占用 | 房源状态置 OCCUPIED |
| 旅程 12「报送任务可查询」偶发失败 | 加重试（最多 5 次） |

### 11.5 仍待处理（P1/P2，29 个）

- **P1**：投诉处理/评价/转工单、公示发布、候补退出、补贴失败与标准启停、资金对账处理、收款确认、押金收/扣（页面走动态 URL，已实测可用，工具判定为缺口）、合同变更创建路径统一、走访转工单、年审调租
- **P2**：Webhook 订阅与投递日志、报表导出任务详情、规则引擎维护、字段标签刷新、设备批量上报、对账批量处置
'''
    io.open(P, 'w', encoding='utf-8', newline='').write(s)
    print('核对报告已补 P0 结果')
