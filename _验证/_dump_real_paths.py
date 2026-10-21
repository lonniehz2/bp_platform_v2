# -*- coding: utf-8 -*-
"""按真实后端路径修正 modules.js（消除 16 处 404）"""
import io
import os
import re

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FE = r'D:\Work\业务平台开发\frontend\src\api\modules.js'

# 需要确认根路径的控制器
WANT = ['Device', 'Subsidy', 'HouseCalendar', 'Credit', 'Publicity',
        'Rbac', 'Visit', 'Application', 'Allocation', 'Space', 'Person',
        'Termination', 'Appeal', 'Exchange', 'Complaint', 'ShortRent']

print('=== 后端根路径（用于修正）===')
roots = {}
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('Controller.java'):
            continue
        name = f.replace('Controller.java', '')
        if name not in WANT:
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        m = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        if m:
            roots[name] = m.group(1)
            print('  %-16s %s' % (name, m.group(1)))

# 关键子路径
print()
print('=== 关键子路径 ===')
KEY = {'ApplicationController.java': ['submit', 'reviews'],
       'PublicityController.java': ['finish'],
       'CreditController.java': ['penalt'],
       'RbacController.java': ['user-role', 'roles', 'permission'],
       'VisitController.java': ['approve'],
       'AllocationController.java': ['lottery', 'sign', 'allocations', 'waiting'],
       'HouseCalendarController.java': ['house'],
       'SubsidyController.java': [],
       'DeviceController.java': []}
for root, _, files in os.walk(JAVA):
    for f in files:
        if f not in KEY:
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        base = bm.group(1) if bm else '?'
        for mm in re.finditer(
                r'@(Get|Post|Put|Delete)Mapping'
                r'(?:\s*\(\s*(?:value\s*=\s*)?"([^"]*)"?\s*\))?', s):
            p = mm.group(2) or ''
            joined = (base + ('/' + p if p else ''))
            if any(k in joined for k in KEY[f]) or not KEY[f]:
                print('  %-6s %-46s %s' % (mm.group(1).upper(), joined, f))
