# -*- coding: utf-8 -*-
"""核对关键控制器真实路径 vs 前端调用路径"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
FE = r'D:\Work\业务平台开发\frontend\src\api\modules.js'

TARGETS = [
    'fin/controller/BillingController.java',
    'fin/controller/BillGenerationController.java',
    'fin/controller/DepositRefundController.java',
    'ops/controller/WorkOrderController.java',
    'iam/controller/OrgController.java',
    'msg/controller/MessageController.java',
    'asset/controller/HouseController.java',
    'biz/controller/ApplicationController.java',
]

print('=== 后端真实路径 ===')
for rel in TARGETS:
    p = os.path.join(J, rel.replace('/', os.sep))
    if not os.path.exists(p):
        print('  %s: 未找到' % rel)
        continue
    s = io.open(p, encoding='utf-8').read()
    m = re.search(r'@RequestMapping\("([^"]+)"\)', s)
    base = m.group(1) if m else '?'
    print('  %s' % rel.split(os.sep)[-1])
    print('     根路径: %s' % base)
    eps = re.findall(r'@(Get|Post)Mapping\(\s*(?:value\s*=\s*)?"([^"]*)"', s)
    for meth, path in eps[:6]:
        print('       %-4s %s%s' % (meth.upper(), base if base != '?' else '', path))
    print()

print('=== 前端 modules.js 中的路径 ===')
s = io.open(FE, encoding='utf-8').read()
paths = sorted(set(re.findall(r"'((?:/[a-z0-9\-/{}$\.]+))'", s)))
for p in paths:
    print('  ' + p)

print()
print('=== 可疑：前端用顶层路径但后端在子路径下 ===')
base_map = {}
for rel in TARGETS:
    fp = os.path.join(J, rel.replace('/', os.sep))
    if not os.path.exists(fp):
        continue
    txt = io.open(fp, encoding='utf-8').read()
    mm = re.search(r'@RequestMapping\("([^"]+)"\)', txt)
    if mm:
        b = mm.group(1)
        if b.count('/') > 2:      # /api/v1/xxx 之外还有层级
            base_map[b] = rel.split(os.sep)[-1]
for b, owner in base_map.items():
    last = b.rstrip('/').split('/')[-1]
    if ("'/" + last) in s:
        print('  ⚠️ 前端有 /%s，但后端实际是 %s（%s）' % (last, b, owner))
