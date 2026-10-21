# -*- coding: utf-8 -*-
"""对比：console 已实现的接口 vs SPA 已接入的接口 → 精确缺口清单"""
import io
import os
import re

CONSOLE = r'D:\Work\业务平台开发\backend\src\main\resources\static\console.html'
FE = r'D:\Work\业务平台开发\frontend\src'


def norm(p):
    p = (p or '').split('?')[0]
    p = re.sub(r'\$\{[^}]+\}', '{}', p)
    p = re.sub(r'\{[^}]+\}', '{}', p)
    p = re.sub(r'/+\d+', '/{}', p)        # /1234 → /{}
    p = re.sub(r'/+', '/', p)
    return p.rstrip('/') if len(p) > 1 else p


c = io.open(CONSOLE, encoding='utf-8').read()
console = {norm(x) for x in re.findall(r"['\"`](/api/v1/[^'\"`\s\)]+)['\"`]", c)}

fe = set()
for root, _, files in os.walk(FE):
    for f in files:
        if not f.endswith(('.js', '.vue')):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        for raw in re.findall(r"['\"`](/[a-z][^'\"`\s\)]*)['\"`]", s):
            fe.add(norm(raw if raw.startswith('/api/') else '/api/v1' + raw))

gap = sorted(console - fe)
print('console 使用接口 %d 个；SPA 已覆盖其中 %d 个；缺口 %d 个\n'
      % (len(console), len(console) - len(gap), len(gap)))

by_mod = {}
for p in gap:
    seg = p.split('/')
    mod = seg[3] if len(seg) > 3 else 'root'
    by_mod.setdefault(mod, []).append(p)

for mod in sorted(by_mod, key=lambda m: -len(by_mod[m])):
    print('%-18s %2d 个' % (mod, len(by_mod[mod])))
    for p in by_mod[mod][:8]:
        print('    ' + p)
    if len(by_mod[mod]) > 8:
        print('    … 其余 %d 个' % (len(by_mod[mod]) - 8))
