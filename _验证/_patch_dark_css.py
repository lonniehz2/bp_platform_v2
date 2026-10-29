# -*- coding: utf-8 -*-
"""深色模式样式：变量 + 全局/布局替换。"""
import io

# ---------- theme.css ----------
p = r'..\frontend\src\styles\theme.css'
s = io.open(p, encoding='utf-8').read()
if '--bp-card-bg' not in s:
    s = s.replace("--bp-page-bg: #f0f2f5;",
                  "--bp-page-bg: #f0f2f5;\n  --bp-card-bg: #ffffff;\n"
                  "  --bp-header-bg: #ffffff;\n  --bp-hover-bg: #f5f5f5;", 1)
if 'html.dark' not in s:
    s = s.rstrip() + """

/* ================= 深色模式 ================= */
html.dark {
  color-scheme: dark;
  --bp-page-bg: #0f141a;
  --bp-card-bg: #151b23;
  --bp-sider-bg: #151b23;
  --bp-header-bg: #151b23;
  --bp-hover-bg: #1e2833;
  --bp-sider-active-bg: #1f3a5f;

  --el-bg-color: #151b23;
  --el-bg-color-page: #0f141a;
  --el-bg-color-overlay: #1b232d;
  --el-fill-color-blank: #151b23;
  --el-fill-color-light: #1b232d;
  --el-fill-color-lighter: #19212a;

  --el-border-color: #2a3441;
  --el-border-color-light: #242d38;
  --el-border-color-lighter: #202832;

  --el-text-color-primary: rgba(255, 255, 255, 0.88);
  --el-text-color-regular: rgba(255, 255, 255, 0.72);
  --el-text-color-secondary: rgba(255, 255, 255, 0.5);
  --el-text-color-placeholder: rgba(255, 255, 255, 0.38);
}

html.dark .el-overlay { background-color: rgba(0, 0, 0, 0.55); }
html.dark .el-table tr,
html.dark .el-table th.el-table__cell { background-color: transparent; }
html.dark .el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell {
  background: #19212a;
}
html.dark .el-card,
html.dark .el-dialog,
html.dark .el-drawer { background: var(--el-bg-color-overlay); }
"""
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('theme dark vars added')

# ---------- index.css ----------
p = r'..\frontend\src\styles\index.css'
s = io.open(p, encoding='utf-8').read()
s = s.replace("background: #f5f7fa;", "background: var(--bp-page-bg, #f5f7fa);", 1)
s = s.replace(".page-card {\n  background: #fff;", ".page-card {\n  background: var(--bp-card-bg, #fff);", 1)
s = s.replace(".stat-card {\n  background: #fff;", ".stat-card {\n  background: var(--bp-card-bg, #fff);", 1)
s = s.replace(".stat-card .label { color: #909399;", ".stat-card .label { color: var(--el-text-color-secondary);", 1)
s = s.replace(".stat-card .value { font-size: 26px; font-weight: 600; margin-top: 6px; color: #303133; }",
              ".stat-card .value { font-size: 26px; font-weight: 600; margin-top: 6px; color: var(--el-text-color-primary); }", 1)
s = s.replace(".muted { color: #909399;", ".muted { color: var(--el-text-color-secondary);", 1)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('index dark-safe')

# ---------- 布局颜色变量化 ----------
for f in (r'..\frontend\src\layout\LayoutRail.vue', r'..\frontend\src\layout\LayoutClassic.vue'):
    s = io.open(f, encoding='utf-8').read()
    s = s.replace('color: #a8abb2;', 'color: var(--el-text-color-secondary);')
    s = s.replace('color: #c0c4cc;', 'color: var(--el-text-color-secondary);')
    s = s.replace('background: #fff;', 'background: var(--bp-sider-bg);')
    s = s.replace('background: #f5f5f5;', 'background: var(--bp-hover-bg);')
    s = s.replace('background: #e6f7ff;', 'background: var(--bp-sider-active-bg);')
    s = s.replace('color: #1890ff;', 'color: var(--el-color-primary);')
    s = s.replace('background: #e6f7ff !important;', 'background: var(--bp-sider-active-bg) !important;')
    s = s.replace('color: #1890ff !important;', 'color: var(--el-color-primary) !important;')
    s = s.replace('border-bottom: 1px solid #f0f0f0;', 'border-bottom: 1px solid var(--el-border-color-light);')
    s = s.replace('background: #f0f2f5;', 'background: var(--bp-page-bg);')
    io.open(f, 'w', encoding='utf-8', newline='').write(s)
print('layouts dark-safe')
