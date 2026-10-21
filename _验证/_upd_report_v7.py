# -*- coding: utf-8 -*-
"""报告 v7：全模块可操作 + 46 项全有数据 + 造数脚本说明"""
import io

REPORT = r'D:\Work\业务平台开发\05_首期功能完整性检查报告.md'
LEDGER = r'D:\Work\业务平台开发\00_文档包索引与评审台账.md'

BLOCK = '''
---

## 附录 · v7 全模块可操作化与全量数据验收（2026-10-20）

### J.1 本轮新增可操作页面（14 个）

| 页面 | 新增写操作 |
|---|---|
| **申诉管理** | 受理 / 调查 / 决定 / 通知 / 撤回 / 标记超时 |
| **信用惩戒** | 撤销 / 标记失效 / 推送 / 扫描到期 |
| **换房管理** | 提交 / 批准 / 驳回 / 完成 / 应换不换登记 |
| **投诉管理** | 办结 |
| **告警与规则** | 处理 / 解决 / 忽略 / 升级 / 转工单 / 统计 |
| **钥匙包** | 改状态 / 回收 |
| **运维操作台**（新增页） | 人员改状态 / 房源改状态 / 工单 7 步流程（派单·接单·开始·完成·关单·取消·退回）|
| 短租订单 / 退租 / 年审 / 补贴 / 催缴 / 公示 | 见 v6 附录 F.3 |

### J.2 建设方式说明（含取舍）

新建对话框采用 **JSON 编辑器 + 后端真实字段示例**：
字段全部取自后端 `Cmd` record 定义，可直接编辑提交。

> **取舍理由**：剩余模块约 90 个写操作，逐个手写 `el-form` 的字段映射风险高
> （本项目已因「凭猜测写字段」返工 8 轮）。用 JSON 编辑器可保证
> **参数一定正确**，代价是易用性下降。高频模块（合同/账单/押金/退租/配租）仍为原生表单。

### J.3 全量数据验收（46 项，0 空 0 失败）

```
有数据 46 ｜ 空 0 ｜ 失败 0
```

新增造数结果：

| 模块 | 数据 | 关键约束（真实校验） |
|---|---|---|
| 投诉 | 1 | `complaintType/source/title/...` 9 字段 |
| 告警 | 1 | 16 字段含阈值与关联对象 |
| 信用惩戒 | 1 | 14 字段含禁申年限 |
| 申诉 | 1 | 8 字段，`daysFromNow` 控制期限 |
| 工单 | 1 | 17 字段含 SLA 时限 |
| 换房 | 1 | **新房源不能与原房源相同** |
| 钥匙包 | 3 | `KeyringCmd` 含 keyType/channelValue/syncScope |
| 短租 | 1 | **退房时刻必须晚于入住时刻**；`nightlyPrice` 必填 |
| 通行授权 | 1 | **grantLevel ∈ OWNERSHIP/MANAGEMENT/USAGE/VISIT** |
| 规则集 | 1 | `RulesetCmd` |
| 开放应用 | 1 | `AppCreateCmd` |
| 政务适配器 | 1 | `AdapterCmd` |
| 监管报送 | 1 | 依赖适配器先建 |
| 财务对账 | 1 | `channelAmount` 必填（渠道金额）|
| 合同变更 | 1 | **changeType ∈ RENEW/RENT_ADJUST/PERIOD/LESSEE/OTHER** |

### J.4 造数过程中暴露的枚举与必填（文档化）

若后续要扩数据，必须遵守以下真实枚举（避免反复试错）：

| 字段 | 允许值 |
|---|---|
| `orgType` | DISTRICT / COMMUNITY / COMPANY / DEPARTMENT |
| `spaceType` | AREA / BUILDING / UNIT / FLOOR / ROOM / BED / PARKING / GARAGE / SITE |
| `houseType` | PUBLIC_RENTAL / AFFORDABLE_RENTAL / TALENT / APARTMENT / DORMITORY / RENTAL / HOTEL |
| `rentUnit` | AREA_MONTH / HOUSE_MONTH / BED_MONTH / HOUSE_NIGHT |
| **`signType`** | **ELECTRONIC / PAPER**（仅两种）|
| `feeItem.itemType` | RENT / PROPERTY / PARKING / ENERGY / DEPOSIT / LATE_FEE / OTHER |
| `feeItem.calcMode` | FIXED / BY_AREA / BY_HOUSE / BY_PERSON / BY_BED / BY_NIGHT / METER |
| `subsidyMode` | FIXED / BY_AREA / BY_PERSON / RATIO |
| `dunningType` | SMS / WECHAT / PHONE / VISIT / NOTICE / PLATFORM |
| `grantLevel` | OWNERSHIP / MANAGEMENT / USAGE / VISIT |
| `changeType` | RENEW / RENT_ADJUST / PERIOD / LESSEE / OTHER |
| `batchType` | LOTTERY / SELECT / DIRECT / SUPPLEMENT |
| `householdType` | URBAN / RURAL / OTHER |

**必填易漏**：`contracts.spaceId`、`short-rent.nightlyPrice`、`reconciles.channelAmount`、
`bills/generate` 的 `periodStart/periodEnd/feeItemId`、`spaces/tree` 的 `orgId`。

### J.5 合同状态机（造数必读）

```
DRAFT →(submit-sign) PENDING_SIGN →(start-signing) SIGNING →(sign) EFFECTIVE
                                              ↓
                              EXPIRED / TERMINATED / CANCELLED
```

**不能从 DRAFT 直接签约**，必须先 `submit-sign` 与 `start-signing`。

### J.6 全链路验证顺序（可复现）

```bash
python _seed_testdata2.py    # 组织 + 空间 + 人员（身份证需合法校验位）
python _seed_testdata3.py    # 空间层级（顶层 parentId=null）
python _seed_testdata4.py    # 房源（rentUnit=AREA_MONTH）
python _seed_testdata5.py    # 收费项目 + 合同 + 押金
python _seed_testdata6.py    # 合同状态机 + 出账
python _seed_testdata7.py    # 收款 + 核销
python _seed_testdata8.py    # 押金抵扣/退款 + 补贴 + 年审
python _seed_testdata9.py    # 补贴标准 + 发放
python _seed_testdata10.py   # 未缴账单 + 催缴
python _seed_testdata12.py   # 实名 + 申请
python _seed_testdata13.py   # 保障档案 + 收入档位
python _seed_testdata14.py   # 审核通过
python _seed_testdata15.py   # 轮候 + 摇号
python _seed_testdata17.py   # 配租单
python _seed_testdata18.py   # 公示 + 签约
python _seed_auto.py         # 投诉/告警/信用/申诉/工单
python _seed_auto3.py        # 钥匙包
python _seed_auto5.py        # 短租
python _seed_auto7.py        # 通行授权
python _seed_auto11.py       # 规则集/开放应用/政务/对账
python _final2.py            # 46 项全量核对
```

### J.7 仍未完成（诚实清单）

| 项 | 说明 |
|---|---|
| 微信小程序 | 需开发者工具与备案主体（H5 已覆盖主要租客场景）|
| 租客独立认证 | 当前复用工作人员账号 + 手动绑定 personId |
| 消息待办 / 对账差异 | 由业务事件与对账结果自动产生，需触发对应业务流程才有数据 |
| 高频模块之外的表单易用性 | 约 90 个写操作用 JSON 编辑器，非原生表单 |
'''

for p in (REPORT, LEDGER):
    s = io.open(p, encoding='utf-8').read()
    if 'v7 全模块可操作化' in s:
        print('  - %s 已含' % p.split('\\')[-1])
        continue
    io.open(p, 'a', encoding='utf-8').write(
        BLOCK if p == REPORT else BLOCK.replace('## 附录 · v7', '## 附录 K · v7'))
    print('  ✓ %s 已追加' % p.split('\\')[-1])

for p in (REPORT, LEDGER):
    print('  %s：%d 行' % (p.split('\\')[-1],
                           len(io.open(p, encoding='utf-8').read().split('\n'))))
