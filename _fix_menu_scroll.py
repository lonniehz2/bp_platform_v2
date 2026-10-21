# -*- coding: utf-8 -*-
"""修复左侧菜单不能滚动"""
import io
import os
import re

FE = r'D:\Work\业务平台开发\frontend\src'
L = os.path.join(FE, 'layout', 'Layout.vue')
s = io.open(L, encoding='utf-8').read()

old_style = s[s.find('<style scoped>'):]
new_style = '''<style scoped>
/* 整体撑满视口 */
.layout { height: 100%; }

/*
 * 侧边栏：品牌区固定，菜单区可滚动。
 * 之前 .aside 用了 overflow: hidden，菜单项超过视口高度时被直接裁剪，
 * 且鼠标滚轮无效——菜单一多就看不到下面的项。
 */
.aside {
  background: #1f2d3d;
  transition: width 0.2s;
  overflow: hidden;          /* 防止横向溢出 */
  display: flex;
  flex-direction: column;
  height: 100%;
}

.brand {
  height: 56px;
  line-height: 56px;
  text-align: center;
  color: #fff;
  font-weight: 600;
  letter-spacing: 1px;
  border-bottom: 1px solid #2b3a4a;
  flex: 0 0 56px;            /* 不参与伸缩，始终可见 */
}

/* 菜单区：占满剩余高度并可纵向滚动 */
.aside :deep(.el-menu) {
  border-right: none;
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 滚动条样式（深色背景上细一点，不突兀） */
.aside :deep(.el-menu)::-webkit-scrollbar { width: 6px; }
.aside :deep(.el-menu)::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.22);
  border-radius: 3px;
}
.aside :deep(.el-menu)::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.35);
}
.aside :deep(.el-menu)::-webkit-scrollbar-track { background: transparent; }

.header {
  display: flex;
  align-items: center;
  gap: 12px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
  height: 56px;
}
.header .spacer { flex: 1; }
.header .user { font-size: 14px; color: #303133; }
.main { background: #f5f7fa; padding: 16px; overflow-y: auto; }
</style>
'''
s = s[:s.find('<style scoped>')] + new_style
io.open(L, 'w', encoding='utf-8').write(s)
print('  ✓ Layout.vue：侧边栏改为「品牌固定 + 菜单滚动」')

# 检查全局样式里 html/body/#app 是否撑满
for name in ('style.css', 'main.css', 'index.css', 'App.vue'):
    p = os.path.join(FE, name)
    if os.path.exists(p):
        t = io.open(p, encoding='utf-8').read()
        has = ('height: 100%' in t)
        print('   %-12s height:100%% → %s' % (name, '有' if has else '无'))

# main.js 里 import 的全局样式
mj = io.open(os.path.join(FE, 'main.js'), encoding='utf-8').read()
print('\n  main.js 引入的样式：')
for m in re.finditer(r"import\s+'([^']+\.css)'", mj):
    print('    ' + m.group(1))
