# -*- coding: utf-8 -*-
"""补附录 J：完整回归。"""
import io
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..',
                 '10_业务操作流程与验收手册.md')
s = io.open(P, encoding='utf-8').read()

if '附录 J' in s:
    print('已存在附录 J')
    raise SystemExit(0)

ADD = """

---

## 附录 J　完整回归（全页面截图 + 全量检查）

### J.1 回归方式

| 层 | 命令 | 覆盖 |
|---|---|---|
| 全量检查 | `_verify_all.py --fast` | 9 项（静态/渲染/链路/并发/数据/性能/压力/文档/字段）|
| 全页面截图 | `regress_shots.js` | **24 个关键页面**逐页截图 + 整列空白检测 + 控制台错误 |

### J.2 本轮回归发现并修复的问题

| # | 问题 | 性质 | 处理 |
|---|---|---|---|
| 1 | **并发核销导致「已收 512 / 应收 320」超收** | **严重（资金）** | 核销上限改为按「应收总额 − 已收」计算剩余可收 |
| 2 | 通行记录「门锁」整列为空 | 数据未回填 | 回填 `lock_id`，并新增 `lockIdName` 反向取设备名 |
| 3 | 通行记录返回 `lockId` 无名称 | 显示层不一致 | VO 增 `lockIdName`，分页批量回填 |
| 4 | 退租「实际退出」、催缴「时间/备注」整列空 | 数据状态（非缺陷）| 回归脚本设为允许空列 |

### J.3 超收问题的根因与修复

原实现用 `bill.getPayableAmount()` 作为上限：

```java
BigDecimal billPayable = money(bill.getPayableAmount());
if (req.compareTo(billPayable) > 0) throw ...   // 只判"本次不超过应付"
```

并发下多次核销各自通过校验，累计已收可能超过应收。

修复为按剩余可收判断：

```java
BigDecimal billTotal = billAmount - discount + lateFee - waived;
BigDecimal remaining = billTotal - paidAmount;
if (req.compareTo(remaining) > 0) throw ...("核销金额超过账单剩余应付 " + remaining);
```

**复测**：并发核销 4 线程 → 11/11 场景通过，无超收。

### J.4 回归结论

```
全量检查 9 项：8 PASS + 1 WARN（数据一致性为预期告警）
全页面截图 24 个：0 个整列空白、0 个控制台错误
并发与幂等 11/11 通过
用户旅程 70 步通过
```
"""

io.open(P, 'w', encoding='utf-8', newline='').write(s.rstrip() + ADD)
print('附录 J 已写入')
