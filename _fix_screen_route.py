# -*- coding: utf-8 -*-
"""修复：驾驶舱「大屏」按钮改为打开独立入口；SPA 内 /screen 路由补样式"""
import io
import os

FE = r'D:\Work\业务平台开发\frontend\src'

# ---------- 1) 新建包装页：引入 screen.css 再渲染 ScreenApp ----------
WRAP = '''<template>
  <ScreenApp />
</template>

<script setup>
/**
 * SPA 内的大屏路由包装页。
 *
 * 为什么需要它：ScreenApp.vue 的布局完全依赖 screen.css
 * （.screen-wrap 100vh、.screen-body grid-template-rows: auto 1fr 等）。
 * 该 CSS 原本只在独立入口 src/screen/main.js 引入，
 * 因此通过路由 /screen 在 SPA 内渲染时没有样式，图表容器高度塌陷为 0，
 * 表现为「只有空白，没有图表」。
 *
 * 独立入口 view-screen.html 一直是正常的，所以也在 Layout 里把按钮
 * 直接指向 view-screen.html，双路径都可用。
 */
import ScreenApp from '@/screen/ScreenApp.vue'
import '@/screen/screen.css'
</script>
'''
p = os.path.join(FE, 'views', 'ScreenPage.vue')
io.open(p, 'w', encoding='utf-8').write(WRAP)
print('  ✓ 新建 views/ScreenPage.vue（引入 screen.css）')

# ---------- 2) 路由 /screen 指向包装页 ----------
R = os.path.join(FE, 'router', 'index.js')
s = io.open(R, encoding='utf-8').read()
old = "component: () => import('@/screen/ScreenApp.vue'),"
if old in s:
    s = s.replace(old, "component: () => import('@/views/ScreenPage.vue'),", 1)
    io.open(R, 'w', encoding='utf-8').write(s)
    print('  ✓ router：/screen 改指向 ScreenPage.vue')
else:
    print('  - router 已指向包装页或未找到原引用')

# ---------- 3) Layout 按钮改为打开独立入口 ----------
L = os.path.join(FE, 'layout', 'Layout.vue')
lay = io.open(L, encoding='utf-8').read()
old_open = "  window.open('#/screen', 'bp-screen', 'width=1600,height=900')"
new_open = ("  // 指向独立入口，避免 SPA 内渲染时的样式隔离问题（该页已验证可用）\n"
            "  window.open('./view-screen.html', 'bp-screen', 'width=1600,height=900')")
if old_open in lay:
    lay = lay.replace(old_open, new_open, 1)
    io.open(L, 'w', encoding='utf-8').write(lay)
    print('  ✓ Layout：大屏按钮改开 ./view-screen.html')
else:
    import re
    m = re.search(r"window\.open\([^\n]*screen[^\n]*\)", lay)
    if m:
        lay = lay.replace(m.group(0),
                          "window.open('./view-screen.html', 'bp-screen', "
                          "'width=1600,height=900')", 1)
        io.open(L, 'w', encoding='utf-8').write(lay)
        print('  ✓ Layout：已按正则替换大屏打开方式')
    else:
        print('  !! 未找到 openScreen 实现')
