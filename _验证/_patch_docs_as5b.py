# -*- coding: utf-8 -*-
"""AS.5 再更新：设备选择器完成后剩余清单。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
p = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
s = io.open(p, encoding='utf-8').read()

old_start = s.find('### AS.5')
old_end = s.find('### AS.6')
if old_start > 0 and old_end > old_start:
    new = '''### AS.5 剩余 ID 输入（已收敛为可接受范围）

| 位置 | 字段 | 说明 |
|---|---|---|
| 运营扩展 | 批量 ID 粘贴 | 批量操作需一次贴多个，保留 |
| 各列表 | 关键字/ID 搜索框 | 本就支持 ID，属正常 |
| 登录 | 租户 ID | 登录标识，保留 |

**已补齐**：设备/门锁（DeviceSelect，设备列表新增 `keyword` 模糊查询）、空间
（SpaceSelect）、计费项（FeeItemSelect）、用户（UserSelect）、房源（HouseSelect）、
组织（OrgSelect）、合同（ContractSelect）、人员（PersonPicker）。

选择器组件合计 7 个；设备指令、设备事件、抄表、通行授权、设备管理的设备/门锁
输入均已改为按编号/名称搜索。

'''
    s = s[:old_start] + new + s[old_end:]
    io.open(p, 'w', encoding='utf-8', newline='').write(s)
    print('AS.5 已更新')
else:
    print('未找到 AS.5 段落')
