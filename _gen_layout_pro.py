# -*- coding: utf-8 -*-
"""Layout 重做：浅色侧栏 + 面包屑 + 灰底内容区（Ant Design Pro 风格）"""
import io
import re

L = r'D:\Work\业务平台开发\frontend\src\layout\Layout.vue'
s = io.open(L, encoding='utf-8').read()

# ---------- 1) 侧栏配色：深色 → 浅色 ----------
s = s.replace('background-color="#1f2d3d"', 'background-color="#ffffff"')
s = s.replace('text-color="#c0c4cc"', 'text-color="rgba(0,0,0,0.85)"')
s = s.replace('active-text-color="#409eff"', 'active-text-color="#1890ff"')

# ---------- 2) 顶部 header 增加面包屑 ----------
old_header = '''      <el-header class="header">
        <el-button text @click="collapsed = !collapsed">
          <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
        </el-button>'''
new_header = '''      <el-header class="header">
        <el-button text @click="collapsed = !collapsed">
          <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
        </el-button>
        <el-breadcrumb class="crumb" separator="/">
          <el-breadcrumb-item>{{ groupOf($route.path) }}</el-breadcrumb-item>
          <el-breadcrumb-item>{{ titleOf($route.path) }}</el-breadcrumb-item>
        </el-breadcrumb>'''
if old_header in s:
    s = s.replace(old_header, new_header, 1)
    print('  ✓ header 增加面包屑')

# ---------- 3) main 区域加 bp-page 包裹类 ----------
s = s.replace('<el-main class="main">', '<el-main class="main">', 1)

# ---------- 4) 脚本：面包屑取值 ----------
if 'function titleOf' not in s:
    s = s.replace('function openScreen() {',
                  '''/** 当前路由所属分组（面包屑第一级） */
function groupOf(path) {
  const hit = menuRoutes.find((m) => m.path === path)
  return hit?.meta?.group || '运营总览'
}

/** 当前路由标题 */
function titleOf(path) {
  const hit = menuRoutes.find((m) => m.path === path)
  return hit?.meta?.title || '页面'
}

function openScreen() {''', 1)
    print('  ✓ 增加面包屑取值函数')

# ---------- 5) 样式：浅色侧栏 + header + 内容区 ----------
style_start = s.find('<style scoped>')
new_style = '''<style scoped>
.layout { height: 100%; }

/* 侧栏：白底 + 右侧细描边（Ant Design Pro 风格） */
.aside {
  background: #ffffff;
  border-right: 1px solid #f0f0f0;
  transition: width 0.2s;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}

/* 品牌区：主色文字 + 底部描边 */
.brand {
  height: 56px;
  line-height: 56px;
  padding: 0 16px;
  color: #1890ff;
  font-weight: 600;
  font-size: 16px;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #f0f0f0;
  flex: 0 0 56px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 菜单区可滚动 */
.aside :deep(.el-menu) {
  border-right: none;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 4px 0;
}
.aside :deep(.el-menu)::-webkit-scrollbar { width: 6px; }
.aside :deep(.el-menu)::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.16);
  border-radius: 3px;
}

/* 菜单项：选中态浅蓝底 + 主色文字 + 左侧竖条 */
.aside :deep(.el-menu-item),
.aside :deep(.el-sub-menu__title) {
  height: 40px;
  line-height: 40px;
  margin: 2px 8px;
  border-radius: 2px;
  font-size: 14px;
}
.aside :deep(.el-menu-item.is-active) {
  background: #e6f7ff !important;
  color: #1890ff !important;
  position: relative;
}
.aside :deep(.el-menu-item.is-active)::after {
  content: '';
  position: absolute;
  right: 0;
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: #1890ff;
  border-radius: 2px;
}

/* 顶栏：白底 + 描边 */
.header {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  height: 56px;
  padding: 0 16px;
}
.header .crumb { font-size: 13px; }
.header .spacer { flex: 1; }
.header .user { font-size: 14px; color: rgba(0, 0, 0, 0.85); }

/* 内容区：灰底 + 统一内边距 */
.main {
  background: #f0f2f5;
  padding: 16px;
  overflow-y: auto;
}
</style>
'''
if style_start > 0:
    s = s[:style_start] + new_style

io.open(L, 'w', encoding='utf-8').write(s)
print('  ✓ Layout.vue 重做（浅色侧栏 + 面包屑 + 灰底内容）')
