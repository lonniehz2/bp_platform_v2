# -*- coding: utf-8 -*-
"""逐页功能缺口审计：后端可用接口 vs 页面已有操作"""
import io
import os
import re

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
V = r'D:\Work\业务平台开发\frontend\src\views'

# 1) 后端：按 base path 收集接口
back = {}
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('Controller.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        if not bm:
            continue
        base = bm.group(1).replace('/api/v1', '').strip('/')
        eps = []
        for m in re.finditer(r'@(Get|Post|Put|Delete)Mapping'
                             r'(?:\(\s*(?:value\s*=\s*)?"([^"]*)"?\s*\))?', s):
            verb, sub = m.group(1).upper(), m.group(2) or ''
            full = '/' + base + ('/' + sub if sub else '')
            full = re.sub(r'/+', '/', full)
            if full.endswith('/'):
                full = full[:-1]
            eps.append((verb, full))
        back.setdefault(base.split('/')[0], []).extend(eps)

# 2) 前端：每页调用的接口
page_eps = {}
for f in sorted(os.listdir(V)):
    if not f.endswith('.vue'):
        continue
    s = io.open(os.path.join(V, f), encoding='utf-8').read()
    calls = set()
    for m in re.finditer(r"req\.(get|post|put|delete)\(\s*[`'\"](/[^`'\"$]*)", s):
        p = m.group(2)
        if not p.startswith('/api/'):
            p = '/api/v1' + p
        calls.add((m.group(1).upper(), re.sub(r'/api/v1', '', p)))
    # api 模块里定义的函数也可能被用
    page_eps[f[:-4]] = calls

# 3) 打印关键模块缺口
KEY = ['persons', 'guarantee-profiles', 'houses', 'spaces', 'verify-records',
       'devices', 'contracts', 'applications', 'fee-items', 'keyring', 'grants']

print('=' * 74)
print(' 后端各资源接口数 / 前端是否覆盖')
print('=' * 74)
for res, eps in sorted(back.items()):
    writes = [e for e in eps if e[0] != 'GET']
    print('\n■ %-20s 共 %2d 个（写 %d）' % (res, len(eps), len(writes)))
    if res in KEY:
        for verb, full in sorted(set(eps)):
            print('     %-6s %s' % (verb, full))

print('\n' + '=' * 74)
print(' 人员/保障对象相关页面的已有调用')
print('=' * 74)
for p in ('Persons', 'Houses', 'Spaces'):
    print('\n■ %s' % p)
    for verb, full in sorted(page_eps.get(p, [])):
        print('     %-6s %s' % (verb, full))
