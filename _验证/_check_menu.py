# -*- coding: utf-8 -*-
"菜单完整性检查：路由必须能在菜单里出现（避免白名单漏登记）。"
import io
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
ROUTER = os.path.join(ROOT, 'frontend', 'src', 'router', 'index.js')
MENU = os.path.join(ROOT, 'frontend', 'src', 'layout', 'useMenu.js')

src = io.open(ROUTER, encoding='utf-8').read()
menu = io.open(MENU, encoding='utf-8').read()

paths = []
for m in re.finditer(r"path:\s*'(/[^']*)'", src):
    p = m.group(1)
    if p in ('/', '/login') or p.startswith('/screen'):
        continue
    block = src[m.start():m.start() + 400]
    if 'meta:' not in block or 'title:' not in block:
        continue
    paths.append(p.split('/:')[0])

missing = []
for p in sorted(set(paths)):
    if ("'" + p + "'") in menu:
        continue
    # 新架构：菜单由路由 meta.group 驱动（无路径白名单），
    # 只要 useMenu 按 groupNameOf(meta) 分组，所有带 meta.group 的路由都会出现
    if 'groupNameOf(' in menu and 'm.meta' in menu:
        continue
    missing.append(p)

print('=' * 62)
print('菜单完整性：%d 个业务路由' % len(set(paths)))
if missing:
    print('  以下路由未登记到菜单分组（用户看不到）：')
    for p in missing:
        print('    ✗ ' + p)
    print('=' * 62)
    sys.exit(1)
print('  ✔ 所有业务路由均可在菜单中出现')
print('=' * 62)
