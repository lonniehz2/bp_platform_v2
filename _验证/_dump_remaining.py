# -*- coding: utf-8 -*-
"""导出剩余模块的写接口与 DTO"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
WANT = ['messages', 'rules', 'open', 'rbac', 'grants', 'access-records',
        'house-calendar', 'sys']

for root, _, fs in os.walk(J):
    for f in fs:
        if not f.endswith('Controller.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        if not bm:
            continue
        base = bm.group(1).replace('/api/v1', '').strip('/')
        if base.split('/')[0] not in WANT:
            continue
        writes = []
        for m in re.finditer(r'@(Post|Put|Delete)Mapping(?:\(\s*"([^"]*)"\s*\))?'
                             r'[\s\S]{0,200}?public\s+[\w<>,\s\.\[\]]*?\s+(\w+)\(([^)]*)\)', s):
            writes.append((m.group(1).upper(),
                           '/' + base + '/' + (m.group(2) or ''),
                           re.sub(r'\s+', ' ', m.group(4))[:78]))
        if not writes:
            continue
        print('\n■ %-22s %s' % (base, f))
        for verb, path, params in writes:
            print('   %-6s %-52s %s' % (verb, re.sub('/+', '/', path), params))
        for mm in re.finditer(r'record\s+(\w+)\s*\(([^)]*)\)', s):
            print('   rec %s(%s)' % (mm.group(1),
                                     re.sub(r'\s+', ' ', mm.group(2))[:80]))
