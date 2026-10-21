# -*- coding: utf-8 -*-
"""ScreenPage 增加全屏承载层，避免被 Layout 侧边栏挤压"""
import io

P = r'D:\Work\业务平台开发\frontend\src\views\ScreenPage.vue'
s = io.open(P, encoding='utf-8').read()

if 'screen-host' not in s:
    s = s.replace('<template>\n  <ScreenApp />\n</template>',
                  '''<template>
  <div class="screen-host">
    <ScreenApp />
  </div>
</template>''', 1)
    s = s.rstrip() + '''

<style scoped>
/* 覆盖整个视口：ScreenApp 自身是 100vw/100vh 的全屏布局，
   若嵌在 Layout 的内容区会被侧边栏挤压导致比例错乱 */
.screen-host {
  position: fixed;
  inset: 0;
  z-index: 2000;
  overflow: hidden;
  background: #050d1a;
}
</style>
'''
    io.open(P, 'w', encoding='utf-8').write(s)
    print('  ✓ ScreenPage.vue：加 .screen-host 全屏承载层')
else:
    print('  - 已存在承载层')

print(io.open(P, encoding='utf-8').read()[:260])
