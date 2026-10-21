# -*- coding: utf-8 -*-
"""报告 v8 + 台账：验收检查命令与显示层机制"""
import io

REPORT = r'D:\Work\业务平台开发\05_首期功能完整性检查报告.md'
LEDGER = r'D:\Work\业务平台开发\00_文档包索引与评审台账.md'

BLOCK = '''
---

## 附录 · v8 显示层一致性机制与验收命令（2026-10-20）

### L.1 问题背景

开发过程中「界面露出英文编码 / 裸 ID / 英文字段名」这一类缺陷**反复出现 5 轮**：

| 轮次 | 现象 | 当时的修法 |
|---|---|---|
| 1 | 表格列显示 `ALLOCATED` | 逐页改模板（35 页 73 处）|
| 2 | 指标明细显示 `HOUSE_TOTAL` | 加前端中文映射 |
| 3 | 下拉选项显示编码 | 逐页改 el-option（6 页 7 处）|
| 4 | 详情显示原始 JSON | 做 DetailView 组件（21 页 39 处）|
| 5 | 详情字段名英文 `unpaidAmount` | 改为从 DB 列注释生成字典 |

**根因不在单个页面，而在缺少「数据出口处」的统一约定**。逐页修补永远有遗漏。

### L.2 三层解决机制

```
① 后端响应层补全  DisplayEnricher + DisplayEnrichAdvice
     personId → 追加 personName（JdbcTemplate/缓存批量解析）
     batchStatus → 追加 batchStatusLabel（EnumLabels 230 条）
     树形 children 递归补全（深度 8）
     ↓
② 字段中文名字典  GET /api/v1/sys/field-labels
     来源：MySQL information_schema.columns.column_comment（974 个）
     前端 DetailView 挂载时加载，新增列只要写注释即自动覆盖
     ↓
③ 前端枚举字典  constants/enums.js（248 个值）
     与后端 EnumLabels.java 同源（脚本生成，避免漂移）
```

### L.3 验收命令（可复用于每次回归）

```bash
cd 业务平台开发/_验证

# 一键验收（推荐）
python _check_all.py            # 常规
python _check_all.py --strict   # CI 用：任一项失败返回非 0
```

单项检查：

| 命令 | 检查内容 | 通过标准 |
|---|---|---|
| `python _check_api_paths.py --strict` | 前端调用的接口路径是否都存在于后端 | 0 处 404 |
| `python _check_display.py --strict` | ① 字段中文名 ② 枚举中文 ③ ID 名称 ④ 树形结构 | 4 项全 ✔，退出码 0 |
| `python _verify_all_pages.py` | 46 个页面接口是否有数据 | 失败 0 |
| `python _audit_fields_full.py` | 字段字典覆盖度（含详情接口）| 未覆盖 0 |
| `python _verify_trees.py` | 树形层级深度与节点数 | 层级成立 |

环境变量可覆盖默认连接：`BP_BASE`、`BP_TENANT`、`BP_USER`、`BP_PWD`。

### L.4 `_check_display.py` 的检查项与允许清单

| 项 | 判定 | 例外（允许项） |
|---|---|---|
| ① 字段中文名 | 接口返回的每个字段都在「远程字典 ∪ 静态字典」中 | `*Label`/`*Name`/`id`/`tenantId`；`xxxId` 可由基础名推导 |
| ② 枚举中文 | `*Status/*Type/...` 若为纯大写编码，必须带 `xxxLabel` 或在前端字典中 | — |
| ③ ID 名称 | `xxxId` 必须带 `xxxName` | `approveById`、`decideUserId`、`handleUserId`、`operatorId`、`bizId`、`sourceId`、`eventId`、`tenantId`、`assignUserId`、`createBy`、`updateBy`、`parentId`、`deviceId` |
| ④ 树形结构 | 组织至少有 2 层；空间树顶层必须有 `spaceTypeLabel` | — |

**允许清单的理由写在脚本注释里**，新增例外必须同时写理由，否则就是掩盖问题。

### L.5 当前验收结果

```
字段字典：远程 974 ｜ 静态 256
枚举字典：静态 248
① 字段中文名：✔ 全部覆盖（411 个字段）
② 枚举中文：✔ 无遗漏
③ ID 名称：✔ 无遗漏（9 个允许项除外）
④ 组织结构：✔ 28 个根 / 3 个含子节点
空间树：✔ 1 根 / 1 含子 / 类型中文 是
结论：✔ 显示层一致
退出码：0
```

### L.6 维护约定（重要）

| 场景 | 需要做的事 |
|---|---|
| 新增数据库字段 | **写列注释**即可，详情自动显示中文（无需改前端）|
| 新增枚举值 | 加到 `frontend/src/constants/enums.js`，再跑 `python _gen_enumlabels.py` 同步后端 |
| 新增后端计算字段（非 DB 列） | 加到 `constants/fieldLabels.js` 的「计算/派生字段」区块 |
| 新增列表接口 | 无需改动 —— `DisplayEnricher` 自动补 `xxxName`/`xxxLabel` |
| 新增树形接口 | 确保 `children` 嵌套，Enricher 会递归补全 |
| **改完任何界面** | **跑 `python _check_display.py --strict`** |

### L.7 已知边界（脚本发现不了的问题）

| 类型 | 说明 | 发现方式 |
|---|---|---|
| 布局/滚动/样式 | 如侧边栏 `overflow:hidden` 导致菜单不能滚动 | 只能人工看 |
| 图表渲染 | 如 grid 容器内 `flex:1` 失效导致 ECharts 画在 0 高度 | 只能人工看 |
| 交互逻辑 | 如「点树节点右侧不刷新」（前端传参后端不接）| 需人工点或写专门用例 |
| 视觉一致性 | 对齐、配色、字号 | 只能人工看 |

**结论：脚本能覆盖「数据正确性」，覆盖不了「渲染与交互」。两者都需要。**
'''

for p in (REPORT, LEDGER):
    s = io.open(p, encoding='utf-8').read()
    if 'v8 显示层一致性机制' in s:
        print('  - %s 已含' % p.split('\\')[-1])
        continue
    io.open(p, 'a', encoding='utf-8').write(
        BLOCK if p == REPORT else BLOCK.replace('## 附录 · v8', '## 附录 M · v8'))
    print('  ✓ %s 已追加' % p.split('\\')[-1])

for p in (REPORT, LEDGER):
    print('  %s：%d 行' % (p.split('\\')[-1],
                           len(io.open(p, encoding='utf-8').read().split('\n'))))
