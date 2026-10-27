# -*- coding: utf-8 -*-
"""更新审计附录 AS.5：ID 输入清零情况。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
s = io.open(p, encoding='utf-8').read()

old = '''### AS.5 仍保留的 ID 输入（合理或待补）

| 位置 | 字段 | 说明 |
|---|---|---|
| 设备绑定 | 空间 ID | 需再接空间树选择器 |
| 钥匙包 | 空间 ID | 同上 |
| 计费项 | 计费项目 ID | 无对应选择器，可后续做计费项下拉 |
| 运营扩展 | 用户 ID / 房源 ID / 批量 ID | 用户选择器待做；批量粘贴保留 |
| 各列表「关键字/ID」 | 搜索框 | 本来就支持 ID，保留 |
| 登录 | 租户 ID | 登录标识，保留 |'''

new = '''### AS.5 剩余 ID 输入（已收敛为可接受范围）

| 位置 | 字段 | 说明 |
|---|---|---|
| 通行授权 | 门锁 ID（筛选） | 设备编号筛选，后续可换设备选择器 |
| 运营扩展 | 批量 ID 粘贴 | 批量操作保留粘贴多 ID |
| 各列表「关键字/ID」 | 搜索框 | 本就支持 ID，保留 |
| 登录 | 租户 ID | 登录标识，保留 |

**已补齐**：设备绑定/钥匙包的空间 ID（SpaceSelect）、通行授权的空间 ID、
计费项 ID（FeeItemSelect）、运营扩展的用户 ID（UserSelect）与房源 ID（HouseSelect）。

新增组件合计 6 个：`OrgSelect`、`HouseSelect`、`ContractSelect`、`SpaceSelect`、
`FeeItemSelect`、`UserSelect`。'''

if old in s:
    s = s.replace(old, new, 1)
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('AS.5 已更新')
else:
    print('未匹配 AS.5')
