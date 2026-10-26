# -*- coding: utf-8 -*-
"""帮助与手册：标准地址升级为五级（含社区编码）。"""
import io
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

# ---------- 帮助 ----------
P = os.path.join(ROOT, 'frontend', 'src', 'content', 'help.js')
s = io.open(P, encoding='utf-8').read()
OLD = """          '「新增组织」填写编码、名称、类型与标准地址：省/市/区县/街道逐级选择。',
          '系统内置区划为四级（省/市/区县/街道）；「社区/村」下拉列出同街道已录入的社区名，也可直接输入新名称。',"""
NEW = """          '「新增组织」填写编码、名称、类型与标准地址：省/市/区县/街道/社区五级逐级选择。',
          '区划库含全国五级数据（省 31 / 市 342 / 区县 3051 / 街道 41274 / 社区村 619336，共约 66 万条）；选到第五级会自动填入社区名并保存社区编码。',
          '「社区/村」也可手工输入或从历史已录入社区中选择（兼容区划库未收录的名称）。',"""
n = 0
if OLD in s:
    s = s.replace(OLD, NEW, 1)
    n += 1
io.open(P, 'w', encoding='utf-8', newline='').write(s)
print('帮助更新:', n)

# ---------- 手册附录 V ----------
P2 = os.path.join(ROOT, '10_业务操作流程与验收手册.md')
t = io.open(P2, encoding='utf-8').read()
if '附录 V' not in t:
    t = t.rstrip() + '''

---

## 附录 V　标准地址升级为五级区划

### V.1 数据来源

- 项目：`657258535/China-Area-Region-Administrative-Divisions`
- 口径：国家统计局行政区划代码（省/市/区县/街道/村社区）
- 文件：`regions.json`（35.4MB），本次仅导入第五级

### V.2 导入结果

| 层级 | 数量 | 说明 |
|---|---|---|
| 省 | 31 | 原有 |
| 市 | 342 | 原有 |
| 区县 | 3,051 | 原有 |
| 街道乡镇 | 41,274 | 原有，全部回填 `has_child=1` |
| **村/社区** | **619,336** | **本次新增** |
| 合计 | 663,034 | 约 66 万条 |

- 表结构未改：`bp_sys_region(code, name, parent_code, level, has_child)`，`code` 为 12 位，恰好容纳村级代码
- 导入方式：分批 `INSERT IGNORE`（3,000/批，共 207 批，耗时约 5 分钟），可重复执行不产生重复行
- 脚本：`_验证/_import_region_l5.py`

### V.3 接口与界面

| 项 | 变化 |
|---|---|
| `GET /sys/regions/children?parentCode=` | 传入街道代码即返回其社区（原逻辑已支持，无需改后端） |
| `GET /sys/regions/path?code=` | 返回五级路径（北京市/市辖区/东城区/东华门街道/多福巷社区居委会） |
| 组织机构 → 标准地址 | 级联从 4 级变为 5 级；选到社区自动填「社区/村」并保存 `communityCode` |

### V.4 实测

```
街道下社区：10 条（东华门街道）
路径：['北京市','市辖区','东城区','东华门街道','多福巷社区居委会']
级联逐级选择：北京市 ✓ 市辖区 ✓ 东城区 ✓ 东华门街道 ✓
第五级候选：多福巷社区居委会 / 银闸社区居委会 / 东厂社区居委会 …
```
'''
    io.open(P2, 'w', encoding='utf-8', newline='').write(t)
    print('手册已补附录 V')
