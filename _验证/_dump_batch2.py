# -*- coding: utf-8 -*-
"""导出第二批待补模块的 DTO 字段：申诉/信用/换房/投诉/来访/工单/告警"""
import io
import os
import re

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

TARGETS = {
    'appeals': 'biz/dto', 'credits': 'biz/dto', 'exchanges': 'biz/dto',
    'complaints': 'biz/dto', 'visits': 'biz/dto',
    'workorders': 'workorder/dto', 'alerts': 'ops/dto', 'rules': 'rule/dto',
    'keyring': 'grant/dto', 'shortrent': 'biz/dto',
}

print('=== 各模块 Controller 的 POST 动作 ===')
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('Controller.java'):
            continue
        base = f[:-5]
        low = base.lower()
        if not any(k in low for k in ('appeal', 'credit', 'exchange', 'complaint',
                                      'visit', 'workorder', 'alert', 'rule',
                                      'keyring', 'shortrent')):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        pbase = bm.group(1) if bm else ''
        acts = []
        for mm in re.finditer(r'@(Post|Put)Mapping(?:\(\s*"([^"]*)"\s*\))?', s):
            acts.append('%s %s' % ('POST' if mm.group(1) == 'Post' else 'PUT',
                                   (pbase + (mm.group(2) or '')).replace('/api/v1', '')))
        print('\n■ %s' % base)
        for a in acts[:8]:
            print('    ' + a)
        # 内嵌 record
        for mm in re.finditer(r'record\s+(\w+)\s*\(([^)]*)\)', s):
            body = re.sub(r'\s+', ' ', mm.group(2)).strip()
            print('    record %s(%s)' % (mm.group(1), body[:110]))
