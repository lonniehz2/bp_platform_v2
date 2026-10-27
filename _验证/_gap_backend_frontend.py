# -*- coding: utf-8 -*-
"""对比后端接口与前端调用，列出未被前端使用的接口。"""
import io
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
BE = os.path.join(ROOT, 'backend', 'src', 'main', 'java')
FE = os.path.join(ROOT, 'frontend', 'src')

# 1) 收集后端接口：class 级 @RequestMapping + 方法级 mapping
endpoints = []  # (method, path, file)
for dirpath, _, files in os.walk(BE):
    for fn in files:
        if not fn.endswith('.java'):
            continue
        path = os.path.join(dirpath, fn)
        text = io.open(path, encoding='utf-8', errors='replace').read()
        base_m = re.search(r'@RequestMapping\("([^"]+)"\)', text)
        base = base_m.group(1) if base_m else ''
        for m in re.finditer(r'@(Get|Post|Put|Delete)Mapping\((?:value\s*=\s*)?"([^"]*)"\)', text):
            method = m.group(1).upper()
            sub = m.group(2)
            if not sub.startswith('/'):
                sub = '/' + sub
            full = (base + sub).replace('//', '/')
            endpoints.append((method, full, fn))

# 2) 收集前端所有 /api 路径字面量（含模板拼接的静态前缀）
fe_text = []
for dirpath, _, files in os.walk(FE):
    for fn in files:
        if fn.endswith(('.vue', '.js')):
            fe_text.append(io.open(os.path.join(dirpath, fn), encoding='utf-8', errors='replace').read())
fe_all = '\n'.join(fe_text)

def used(path):
    # 去掉路径变量，按静态前缀匹配
    p = re.sub(r'\{[^}]+\}', '', path)
    p = re.sub(r':[^/]+', '', p)
    p = p.replace('/api/v1', '')
    if not p:
        return True
    # 取前两段做匹配
    parts = [x for x in p.split('/') if x]
    probe = '/'.join(parts[:2])
    return probe in fe_all

missing = []
for method, path, fn in endpoints:
    if not used(path):
        missing.append((method, path, fn))

print('后端接口总数:', len(endpoints))
print('疑似前端未使用:', len(missing))
for m in sorted(set(missing)):
    print(' ', m[0], m[1], '  <-', m[2])
