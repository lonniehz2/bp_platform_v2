# -*- coding: utf-8 -*-
"""列出 5 个真实控制器的 POST 路径与参数"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FILES = ['ContractChangeController', 'GovReportController', 'OpenPlatformController',
         'RuleEngineController']

for root, _, fs in os.walk(J):
    for f in fs:
        name = f[:-5]
        if name not in FILES:
            continue
        p = os.path.join(root, f)
        s = io.open(p, encoding='utf-8').read()
        bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        base = bm.group(1) if bm else ''
        print('== %s  base=%s' % (name, base))
        for m in re.finditer(r'@(Post|Put)Mapping(?:\(\s*"([^"]*)"\s*\))?'
                             r'[\s\S]{0,200}?public\s+[\w<>,\s\.\[\]]*?\s+(\w+)\(([^)]*)\)', s):
            sub = m.group(2) or ''
            print('   %s %-44s %s'
                  % ('POST' if m.group(1) == 'Post' else 'PUT',
                     (base + '/' + sub).replace('//', '/'),
                     re.sub(r'\s+', ' ', m.group(4))[:90]))
        for mm in re.finditer(r'record\s+(\w+)\s*\(([^)]*)\)', s):
            print('   record %s(%s)' % (mm.group(1),
                                        re.sub(r'\s+', ' ', mm.group(2))[:80]))
        print()
