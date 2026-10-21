# -*- coding: utf-8 -*-
"""UI 设计规范文档（参照 Ant Design 后台）"""
import io

DOC = r'D:\Work\业务平台开发\06_UI设计规范.md'

CONTENT = '''# UI 设计规范（参照参考系统 rework）

> 参考系统：`https://saas.yumeng.work`（"寓盟管家"公寓智能管理系统）
>
> **重要说明**：该站点是需登录的 SaaS，无法用演示账号在其前端登录浏览。
> 本次通过抓取其公开前端资源（HTML + 3.6MB 主 JS bundle）分析得出技术特征与设计语言：
> - 技术栈：**Vue 2 + Ant Design Vue**（`chunk-ant-vue.*.js`），Webpack 分块
> - 业务域：房源 / 房间 / 楼栋 / 合同 / 账单 / 租客 / 客户 / 审批 / 工单 / 报表 / 角色
> - 交互特征：Ant Design 后台范式——浅色侧边栏、面包屑、搜索卡 + 表格卡、
>   2px 小圆角、`#1890ff` 主色、`#f0f2f5` 内容区灰底
>
> 据此把本系统（Element Plus）**统一到同一套设计语言**，而不是逐页手写样式。

---

## 一、设计 Token

在 `frontend/src/styles/theme.css` 中通过覆盖 Element Plus CSS 变量实现，
对全部 40+ 页面**全局生效**，不需要改组件用法。

| Token | 值 | 说明 |
|---|---|---|
| 主色 | `#1890ff` | Ant Design 蓝，含 light-3/5/7/8/9 与 dark-2 完整色阶 |
| 成功 | `#52c41a` | 同 AntD |
| 警告 | `#faad14` | 同 AntD |
| 危险 | `#ff4d4f` | 同 AntD |
| 主文本 | `rgba(0,0,0,0.85)` | AntD 一级文本 |
| 次文本 | `rgba(0,0,0,0.65)` | 正文 |
| 辅助文本 | `rgba(0,0,0,0.45)` | 说明/标签 |
| 描边 | `#d9d9d9` / `#e8e8e8` / `#f0f0f0` | 三级描边 |
| 圆角 | **2px** | 比 Element 默认 4px 更利落，是 AntD 的关键特征 |
| 内容区底色 | `#f0f2f5` | AntD Layout 标准底 |
| 栅格间距 | 16px | `--bp-gap` |

## 二、布局骨架

```
┌────────────┬──────────────────────────────────────────┐
│ 品牌区 56px │ 顶栏 56px：折叠按钮 ｜ 面包屑 ｜ 用户 ｜ 操作 │
├────────────┼──────────────────────────────────────────┤
│            │ 内容区（#f0f2f5，padding 16px）            │
│  侧边栏     │  ┌ 页头：标题 + 描述 + 右侧操作按钮 ┐      │
│  208px     │  ├ 搜索卡（白底 1px 描边）          ┤      │
│  白底       │  ├ 主内容卡（表格/表单）            ┤      │
│  1px 描边   │  └ 其他卡片                        ┘      │
└────────────┴──────────────────────────────────────────┘
```

要点：
- **侧边栏改浅色**（原为深色 `#1f2d3d`），白底 + 右侧 `#f0f0f0` 细描边
- 菜单选中态：`#e6f7ff` 浅蓝底 + `#1890ff` 文字 + **右侧 3px 竖条**
- 顶栏增加**面包屑**：`所属分组 / 当前页面`（由路由 `meta.group` 与 `meta.title` 自动生成）
- 内容区统一灰底，卡片白底 + 1px 描边 + **几乎无阴影**（AntD Card 特征）

## 三、页面骨架组件 `PageShell`

新页面统一用这个组件，避免每页重复写 head/card：

```vue
<template>
  <PageShell title="房源台账" desc="共 5,776 套房源">
    <template #actions>
      <el-button type="primary" @click="openCreate">新增房源</el-button>
    </template>

    <template #search>
      <div class="item">
        <label>房源编号</label>
        <el-input v-model="q.keyword" clearable style="width:180px" />
      </div>
      <div class="item">
        <label>状态</label>
        <el-select v-model="q.status" clearable style="width:140px" />
      </div>
      <el-button type="primary" @click="reload">查询</el-button>
      <el-button @click="reset">重置</el-button>
    </template>

    <template #toolbar>
      <el-button @click="exportCsv">导出</el-button>
    </template>

    <el-table :data="rows" size="small" border />
  </PageShell>
</template>
```

提供 4 个插槽：`actions`（页头右侧）、`search`（筛选区）、`title`/`toolbar`（卡片头）、`extra`（额外卡片）。

## 四、可复用样式类

| 类名 | 用途 |
|---|---|
| `.bp-page` | 页面容器（灰底 + 16px 内边距）|
| `.bp-page-head` | 页头（标题 + 描述 + actions）|
| `.bp-card` | 白底描边卡片 |
| `.bp-search` | 内联筛选行（label 在左，控件紧凑）|
| `.bp-stat-row` / `.bp-stat` | 指标卡网格（4 列自适应）|
| `.page-card` / `.toolbar` | **兼容老页面**，已映射到新视觉 |

## 五、表格规范

- 字号 13px，表头 `#fafafa` 底、字重 500
- 单元格内边距 8px（AntD small）
- 边框色 `#f0f0f0`
- 分页**右对齐**
- 状态列用 `<el-tag size="small">`：成功绿 / 警告黄 / 危险红 / 其他灰

## 六、改造进度

| 范围 | 状态 |
|---|---|
| 设计 Token（theme.css） | ✅ 已完成，全局生效 |
| 布局（浅色侧栏 + 面包屑 + 灰底） | ✅ 已完成 |
| `PageShell` 组件 | ✅ 已完成 |
| 运营驾驶舱（含图表） | ✅ 已按新规范重做 |
| 其余 40 个页面 | ⬜ 视觉已统一（token 生效），但页面结构仍是旧的 `page-card` + `toolbar` |

### 剩余页面改造建议顺序

1. **高频业务页**：申请与审核、合同管理、账单与缴费、保障对象
2. **资产页**：房源台账、空间层级、设备管理
3. **配置页**：计费项目、用户与权限、系统支撑

改造方式：把页面根节点换成 `<PageShell>`，筛选控件包进 `#search` 插槽，
表格放进默认插槽即可，其余逻辑不动。

## 七、为什么这样改（对照参考系统的差距）

| 维度 | 改造前 | 改造后 |
|---|---|---|
| 主色 | `#409eff`（Element 默认） | `#1890ff`（AntD） |
| 圆角 | 4px | 2px |
| 侧边栏 | 深色 `#1f2d3d` | 白底 + 细描边 |
| 顶栏 | 无面包屑 | 分组/页面面包屑 |
| 内容区 | 白底 | `#f0f2f5` 灰底 + 白卡片 |
| 页头 | 各页自己写 `<h3>` | 统一 `PageShell`（标题+描述+操作区）|
| 筛选区 | 散落在 toolbar 里 | 独立搜索卡，label 在左 |
| 指标卡 | 简单色块 | `.bp-stat`（标签小字 + 数值 26px + 单位）|
| 表格 | 默认 14px / 内边距大 | 13px / 8px / 表头灰底 / 分页右对齐 |

## 八、说明与限制

- **未能登录参考系统**，因此菜单分组与具体页面布局无法 1:1 复制；
  本次对齐的是**设计语言与后台范式**（这是"看起来专业"的主要来源）。
- 参考系统的菜单结构（从 bundle 可见的业务域）：房源、房间、楼栋、合同、账单、
  租客、客户、员工、审批、工单、报表、设置、角色——与本系统覆盖范围基本一致，
  因此信息架构不需要大改，主要是**视觉与页面骨架**的规范化。
- 若后续能提供参考系统的**截图**，可以进一步做像素级对齐（间距、卡片布局、
  表单排列方式）。
'''

io.open(DOC, 'w', encoding='utf-8').write(CONTENT)
print('  ✓ 06_UI设计规范.md（%d 行）' % CONTENT.count('\n'))
