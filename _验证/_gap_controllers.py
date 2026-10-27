# -*- coding: utf-8 -*-
"""控制器级覆盖：后端每个控制器是否被前端引用。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java')
FE = os.path.join(ROOT, 'frontend', 'src')

fe = []
for dirpath, _, files in os.walk(FE):
    for fn in files:
        if fn.endswith(('.vue', '.js')):
            fe.append(io.open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read())
fe_all = '\n'.join(fe)

rows = []
for dirpath, _, files in os.walk(BE):
    for fn in files:
        if not fn.endswith('Controller.java'):
            continue
        text = io.open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read()
        m = re.search(r'@RequestMapping\("([^"]+)"\)', text)
        if not m:
            continue
        base = m.group(1)
        seg = [x for x in base.split('/') if x and x != 'api' and x != 'v1']
        probe = seg[0] if seg else ''
        hits = fe_all.count("'/" + probe) + fe_all.count('"/' + probe) + fe_all.count("`/" + probe)
        rows.append((base, hits, fn))

rows.sort(key=lambda x: x[1])
print('控制器数:', len(rows))
for base, hits, fn in rows:
    if hits == 0:
        print('  未引用:', base, '<-', fn)
