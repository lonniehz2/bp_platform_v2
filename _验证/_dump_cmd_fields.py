# -*- coding: utf-8 -*-
"""导出各模块写操作的 Cmd record 字段"""
import io
import os
import re

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

WANT_DIRS = ['biz/dto', 'person/dto', 'asset/dto', 'ops/dto', 'fin/dto',
             'gov/dto', 'open/dto']

found = {}
for root, _, files in os.walk(JAVA):
    rel = os.path.relpath(root, JAVA).replace('\\', '/')
    if rel not in WANT_DIRS:
        continue
    for f in files:
        if not f.endswith('Cmd.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        m = re.search(r'record\s+(\w+)\((.*?)\)\s*\{', s, re.S)
        if not m:
            continue
        body = re.sub(r'/\*.*?\*/', '', m.group(2), flags=re.S)
        parts = []
        for ln in body.split('\n'):
            t = ln.strip().rstrip(',')
            if not t or t.startswith('@'):
                continue
            parts.append(t)
        found[m.group(1)] = (rel, parts)

KEY = ['TerminationCreateCmd', 'AppealCreateCmd', 'AppealDecideCmd',
       'CreditCreateCmd', 'ExchangeCreateCmd', 'ExchangeApproveCmd',
       'ComplaintCreateCmd', 'ComplaintHandleCmd', 'VisitCreateCmd',
       'VisitReportCmd', 'PersonCreateCmd', 'SpaceCreateCmd',
       'ShortRentCreateCmd', 'PublicityCreateCmd']

for name in KEY:
    if name in found:
        rel, parts = found[name]
        print('=== %s (%d) ===' % (name, len(parts)))
        for p in parts:
            print('   ' + p)
        print()
    else:
        print('=== %s : 未找到' % name)
print()
print('共发现 Cmd 类 %d 个：%s' % (len(found), ', '.join(sorted(found)[:20])))
