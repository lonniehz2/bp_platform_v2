# -*- coding: utf-8 -*-
"""完整性检查：后端资源（模块）→ SPA 页面/调用 覆盖情况"""
import io
import os
import re
from collections import OrderedDict

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FE = r'D:\Work\业务平台开发\frontend\src'

# 后端：每个 Controller 的 base path 与方法数
back = OrderedDict()
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('Controller.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        if not bm:
            continue
        base = bm.group(1).replace('/api/v1', '').strip('/')
        n = len(re.findall(r'@(?:Get|Post|Put|Delete)Mapping', s))
        key = base.split('/')[0] if base else ''
        d = back.setdefault(key, {'apis': 0, 'ctl': set()})
        d['apis'] += n
        d['ctl'].add(f[:-5])

# 前端：所有 req.* 调用路径 + 路由
fe_calls = set()
for root, _, files in os.walk(FE):
    for f in files:
        if not f.endswith(('.js', '.vue')):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        for m in re.finditer(r"['\"`](/[a-z][^'\"`\s\)]*)['\"`]", s):
            p = m.group(1)
            if not p.startswith('/api/'):
                p = '/api/v1' + p
            seg = p.split('/')
            fe_calls.add(seg[3] if len(seg) > 3 else '')

routes = re.findall(r"path:\s*'/([a-z\-]+)'", io.open(
    os.path.join(FE, 'router', 'index.js'), encoding='utf-8').read())

print('=' * 74)
print(' 后端资源 → 前端覆盖')
print('=' * 74)
print('  %-18s %-6s %-6s %s' % ('后端资源', '接口', '前端', '状态'))
no_ui = []
for k in sorted(back, key=lambda x: -back[x]['apis']):
    if not k:
        continue
    covered = k in fe_calls
    print('  %-18s %-6d %-6s %s'
          % (k, back[k]['apis'], '✓' if covered else '✗',
             '' if covered else '无前端调用'))
    if not covered:
        no_ui.append((k, back[k]['apis'], sorted(back[k]['ctl'])))

print('\n 前端路由 %d 条：%s' % (len(routes), ', '.join(routes)))

print('\n' + '=' * 74)
print(' ① 后端有接口但前端完全没调用的资源：%d' % len(no_ui))
for k, n, ctl in no_ui:
    print('    %-16s %2d 个接口  (%s)' % (k, n, ', '.join(ctl[:2])))

# ③ 页面数 vs 路由数
views = [f[:-4] for f in os.listdir(os.path.join(FE, 'views')) if f.endswith('.vue')]
print('\n ② 视图文件 %d ｜ 路由 %d ｜ 差集（应为 Login）%s'
      % (len(views), len(routes), [v for v in views if v != 'Login']))
