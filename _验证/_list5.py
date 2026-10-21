# -*- coding: utf-8 -*-
"""列出 5 个模块控制器的 POST 签名（便于手工造数）"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
WANT = ['contract-changes', 'rules/rulesets', 'open/apps', 'gov/adapters',
        'gov/reports']

for root, _, fs in os.walk(J):
    for f in fs:
        if not f.endswith('Controller.java'):
            continue
        p = os.path.join(root, f)
        s = io.open(p, encoding='utf-8').read()
        bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        if not bm:
            continue
        b = bm.group(1).replace('/api/v1', '').strip('/')
        if b not in WANT:
            continue
        print('== %s  (%s)' % (b, f))
        for m in re.finditer(r'@PostMapping(?:\(\s*"([^"]*)"\s*\))?'
                             r'\s*public\s+[\w<>,\s\.\[\]]+?\s+(\w+)\(([^)]*)\)', s):
            sub = m.group(1) or ''
            print('   POST /%s/%s  ->  %s'
                  % (b, sub, re.sub(r'\s+', ' ', m.group(3))[:100]))
        # 文件内 record
        for mm in re.finditer(r'record\s+(\w+)\s*\(([^)]*)\)', s):
            print('   record %s(%s)' % (mm.group(1),
                                        re.sub(r'\s+', ' ', mm.group(2))[:90]))
        print()
