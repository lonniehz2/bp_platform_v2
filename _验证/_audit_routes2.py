# -*- coding: utf-8 -*-
"""核查路由重复定义与菜单结构"""
import io
import re
from collections import Counter

R = r'D:\Work\业务平台开发\frontend\src\router\index.js'
s = io.open(R, encoding='utf-8').read()

paths = re.findall(r"path:\s*'([^']+)'", s)
cnt = Counter(paths)
print('路由定义 %d 处，唯一 %d 个' % (len(paths), len(cnt)))

dup = {k: v for k, v in cnt.items() if v > 1}
print('\n重复定义的路径：')
for k, v in dup.items():
    print('  %-14s 出现 %d 次' % (k, v))

# 打印 login 相关块
print('\n--- 含 login 的定义上下文 ---')
for m in re.finditer(r"path:\s*'/login'", s):
    print('  ...%s...' % s[max(0, m.start() - 90):m.start() + 130]
          .replace('\n', ' ')[:210])

# 菜单树结构：是否有分组（children）
print('\n--- 是否有子路由（分组菜单）---')
print('  children 出现 %d 次' % s.count('children'))

# 检查 el-menu 是否支持分组
L = r'D:\Work\业务平台开发\frontend\src\layout\Layout.vue'
lay = io.open(L, encoding='utf-8').read()
print('  Layout 中 el-sub-menu（二级菜单）：%d 处' % lay.count('el-sub-menu'))
print('  Layout 中 el-menu-item（一级）：%d 处' % lay.count('el-menu-item'))
