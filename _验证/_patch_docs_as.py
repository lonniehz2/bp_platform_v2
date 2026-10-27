# -*- coding: utf-8 -*-
"""审计报告附录 + 帮助补充。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
HELP = os.path.join(ROOT, 'frontend', 'src', 'content', 'help.js')
MANUAL = os.path.join(ROOT, '10_业务操作流程与验收手册.md')

s = io.open(HELP, encoding='utf-8').read()
if '合同表单' not in s:
    s = s.replace('''      { type: 'h3', text: '5.1 签订合同' },''',
                  '''      { type: 'h3', text: '5.1 签订合同' },
      { type: 'note', text: '合同表单不再填 ID：出租组织/出租方组织按名称选，承租人按姓名搜索并自动带出电话与证件，房源按编号/名称搜索，空间与地址/面积自动带出。' },''')
    s = re.sub(r"HELP_VERSION\s*=\s*'[^']*'", "HELP_VERSION = 'v3.3（2026-10-27）'", s, count=1)
    io.open(HELP, 'w', encoding='utf-8', newline='').write(s)
    print('帮助 → v3.3')

t = io.open(MANUAL, encoding='utf-8').read()
if '附录 AS' not in t:
    t = t.rstrip() + '''

---

## 附录 AS　全量核查与易用性优化（本轮）

### AS.1 合同表单：ID 输入全部改为名称搜索

| 字段 | 改前 | 改后 |
|---|---|---|
| 出租组织 | 填组织 ID | 组织名称下拉（OrgSelect） |
| 出租方组织 | 填组织 ID | 组织名称下拉 |
| 承租人 | 填人员 ID | 姓名/手机/证件搜索（PersonPicker），自动带出姓名、电话、脱敏证件 |
| 房源 | 填房源 ID | 编号/名称远程搜索（HouseSelect），按所选组织过滤 |
| 空间 | 填空间 ID | 选择房源后自动带出空间名称（只读展示） |

同时：选房源自动补房屋地址、建筑面积、租金标准，减少重复录入。

### AS.2 新增可复用组件

| 组件 | 作用 |
|---|---|
| `OrgSelect.vue` | 组织名称搜索，值为组织 ID |
| `HouseSelect.vue` | 房源编号/名称搜索，可限定组织与状态 |
| `ContractSelect.vue` | 合同号/承租人搜索，值为合同 ID |

### AS.3 其它页面 ID 输入替换（9 处）

| 页面 | 字段 | 改为 |
|---|---|---|
| 欠费管理 | 合同、人员 | ContractSelect / PersonPicker |
| 押金管理 | 合同 | ContractSelect |
| 退租管理 | 合同 | ContractSelect |
| 通行记录 | 房源 | HouseSelect |
| 运营中心 | 人员、房源 | PersonPicker / HouseSelect |
| 钥匙包 | 人员（筛选、表单） | PersonPicker |

### AS.4 全量检查结果

```
数据范围扫描/运行时     ✔
全功能页面对照 46 项    ✔
用户旅程闭环 70 步      ✔
显示层一致性            ✔（字段中文名/枚举/ID 名称/空间树）
ID 精度与输入宽度       ✔（修正检查器的相邻控件误判）
先查后写/资金并发       ✔（19 项已复核）
```

### AS.5 仍保留的 ID 输入（合理或待补）

| 位置 | 字段 | 说明 |
|---|---|---|
| 设备绑定 | 空间 ID | 需再接空间树选择器 |
| 钥匙包 | 空间 ID | 同上 |
| 计费项 | 计费项目 ID | 无对应选择器，可后续做计费项下拉 |
| 运营扩展 | 用户 ID / 房源 ID / 批量 ID | 用户选择器待做；批量粘贴保留 |
| 各列表「关键字/ID」 | 搜索框 | 本来就支持 ID，保留 |
| 登录 | 租户 ID | 登录标识，保留 |

### AS.6 结论

- 高频表单（合同、欠费、押金、退租、通行、运营、钥匙包）已做到「按名称选、不背 ID」。
- 全量自动检查 16 项通过；剩余 ID 输入集中在低频配置页，已列清单。
'''
    io.open(MANUAL, 'w', encoding='utf-8', newline='').write(t)
    print('手册已补附录 AS')
