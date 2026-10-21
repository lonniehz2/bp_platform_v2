# -*- coding: utf-8 -*-
"""给 v4 报告追加「校验接入矩阵」与「待内网执行」更新"""
import io

P = r'D:\Work\业务平台开发\05_首期功能完整性检查报告.md'
s = io.open(P, encoding='utf-8').read()

if '校验接入矩阵' in s:
    print('已追加，跳过')
    raise SystemExit

anchor = '''---

## 五、缺口清单（按对验收的影响排序）'''

block = '''### 4.6 ⭐⭐ 校验接入矩阵（本报告最重要的一节）

> **背景**：本项目在开发过程中<b>出现过 4 次「接口提供了但没接入业务链路」</b>
> （公示校验、信用校验、实名校验、档案判定）。这类问题最危险——
> Service 写好了、单测也过，但实际流程根本不调用，功能形同虚设。

因此 v4 起对每一条「应当拦住业务」的校验，都要求：
**① 真的接入调用链 ② 有单测证明它拦得住 ③ 在报告中登记**。

| # | 校验 | 接入位置 | 拦截效果 | 单测证明 |
|---|---|---|---|---|
| 1 | **公示未结束不得签约** | `AllocationServiceImpl.sign` | 未完成配租公示（≥7 自然日且已结束）→ 拒绝签约 | `_verify_pubgate.py`（真机 17 项）+ `PublicityGateTest`（10 项）|
| 2 | **信用惩戒阻止申请** | `ApplicationServiceImpl.create`（最前） | 处于限制申请期 → 拒绝申请 | `_verify_creditgate.py`（真机 10 项）|
| 3 | **实名认证阻止申请** | `ApplicationServiceImpl.create`（信用之后） | 未通过实名认证 → 拒绝申请 | `ApplicationVerifyGateTest`（8 项）|
| 4 | **保障档案参与资格判定** | `ApplicationServiceImpl.review`（PASS 前） | 收入超线/人口不一致/人才过期/名下有房无依据 → 拒绝通过 | `ApplicationQualifyGateTest`（12 项）|
| 5 | 欠费停权不停大门 | `FinLedger`/`BillingServiceImpl` | 默认 `EXCLUDE_MAIN_DOOR`，`ALL` 需二次确认 | 真机验证覆盖 |
| 6 | ⚠️ **通行记录驱动空置判定** | — | **未接入违规判定**（仅有 `/access-records/idle` 查询接口）| — |

**结论**：「提供了但没接入」问题从 4 处降至 **1 处**（第 6 项，且属可选能力——
空置违规也可由人工巡检认定）。

### 4.7 关键校验的设计取舍

| 校验 | 取舍 | 原因 |
|---|---|---|
| 实名认证 | 开关 `biz.apply.requireVerify` 可关 | 部分地区「先申请、线下认证」 |
| 保障档案 | 只作用于 PASS，不影响 REJECT/SUPPLEMENT | 否则档案数据出问题时申请单会卡死，既不能过也不能退 |
| 名下有房 | 拒绝「无依据」，允许「有备注」 | 确有合法例外（离婚析产等），直接拒会误伤真实需求 |
| 服务未部署 | 放行 | 灰度环境不阻断；但单测保证「服务在+开关开」必拦 |

''' + anchor

assert anchor in s
s = s.replace(anchor, block, 1)

# 更新「待内网执行」清单，补新增表
s = s.replace(
    "python verify.py ddl          # 确认 9 张新表存在",
    "python verify.py ddl          # 确认 13 张新表存在（open/gov/keyring/rule/person）")
s = s.replace(
    "| 1 | `verify.py ddl` | 确认 9 张新表 |",
    "| 1 | `verify.py ddl` | 确认 13 张新表 |")

# 证据来源补测试类
s = s.replace(
    "| 压测结果 | `_验证/_loadtest_result.json` |",
    "| 压测结果 | `_验证/_loadtest_result.json` |\n"
    "| 校验接入证明 | `ApplicationVerifyGateTest`、`ApplicationQualifyGateTest`、"
    "`PublicityGateTest` |")

io.open(P, 'w', encoding='utf-8').write(s)
print('已追加 4.6 校验接入矩阵 / 4.7 设计取舍，报告行数 %d'
      % len(s.split('\n')))
