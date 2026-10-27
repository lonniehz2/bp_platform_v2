# -*- coding: utf-8 -*-
"""端点级缺口：路径末段静态词是否出现在前端。"""
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
        base_m = re.search(r'@RequestMapping\("([^"]+)"\)', text)
        base = base_m.group(1) if base_m else ''
        for m in re.finditer(r'@(Get|Post|Put|Delete)Mapping\((?:value\s*=\s*)?"([^"]*)"\)', text):
            method, sub = m.group(1).upper(), m.group(2)
            path = (base + '/' + sub).replace('//', '/')
            segs = [s for s in re.split(r'[/{}]', path) if s and not s.startswith(':')
                    and not s.isdigit() and s not in ('api', 'v1')]
            if not segs:
                continue
            last = segs[-1]
            if last in ('', 'list', 'page'):
                continue
            # 末段词出现在前端即认为有入口（粗判）
            if (last in fe_all) or (segs[0] in fe_all):
                continue
            rows.append((method, path, fn))

print('疑似缺 UI 的端点:', len(rows))
for r in sorted(set(rows)):
    print(' ', r[0], r[1], '<-', r[2])
