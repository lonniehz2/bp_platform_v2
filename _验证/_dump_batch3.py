# -*- coding: utf-8 -*-
"""再补 4 个页面写操作：人员/房源/设备/工单（列表已存在，追加动作与新建）"""
import io
import os
import re

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

print('=== 人员/房源/设备/工单 Controller POST 动作 ===')
for name in ('PersonController', 'HouseController', 'DeviceController',
             'WorkOrderController'):
    hit = None
    for root, _, files in os.walk(JAVA):
        if name + '.java' in files:
            hit = os.path.join(root, name + '.java')
            break
    if not hit:
        print('  □ %s 未找到' % name)
        continue
    s = io.open(hit, encoding='utf-8').read()
    bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
    base = bm.group(1) if bm else ''
    print('\n■ %s  base=%s' % (name, base.replace('/api/v1', '')))
    for mm in re.finditer(r'@PostMapping(?:\(\s*"([^"]*)"\s*\))?\s*\n\s*public\s+[\w<>,\s\.\[\]]+\s+(\w+)\(([^)]*)\)', s):
        sub = mm.group(1) or ''
        params = re.sub(r'\s+', ' ', mm.group(3))[:110]
        print('    POST %-38s %s' % ((base + '/' + sub).replace('/api/v1', '').replace('//', '/'),
                                     params))
    for mm in re.finditer(r'record\s+(\w+)\s*\(([^)]*)\)', s):
        print('    record %s(%s)' % (mm.group(1),
                                     re.sub(r'\s+', ' ', mm.group(2))[:100]))
