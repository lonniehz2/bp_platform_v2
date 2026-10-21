# -*- coding: utf-8 -*-
"""从控制器/Service 抽取保障档案与实名核验的入参字段"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

for name in ('GuaranteeProfileController.java', 'VerifyRecordController.java'):
    hit = None
    for root, _, fs in os.walk(J):
        if name in fs:
            hit = os.path.join(root, name)
            break
    if not hit:
        print('□ %s 未找到' % name)
        continue
    s = io.open(hit, encoding='utf-8').read()
    print('\n=== %s ===' % name)
    base = re.search(r'@RequestMapping\("([^"]+)"\)', s)
    print('  base=%s' % (base.group(1) if base else '?'))
    for m in re.finditer(r'@(Get|Post|Put|Delete)Mapping(?:\(\s*"([^"]*)"\s*\))?'
                         r'[\s\S]{0,220}?public\s+[\w<>,\s\.\[\]]*?\s+(\w+)\(([^)]*)\)', s):
        print('  %-4s %-46s %s'
              % (m.group(1).upper(),
                 ((base.group(1) if base else '') + '/' + (m.group(2) or '')).replace('//', '/'),
                 re.sub(r'\s+', ' ', m.group(4))[:90]))
    for mm in re.finditer(r'record\s+(\w+)\s*\(([^)]*)\)', s):
        print('  record %s(%s)' % (mm.group(1),
                                   re.sub(r'\s+', ' ', mm.group(2))[:110]))

# Service 里的内嵌 Cmd
for name in ('GuaranteeProfileService.java', 'VerifyRecordService.java'):
    for root, _, fs in os.walk(J):
        if name in fs:
            s = io.open(os.path.join(root, name), encoding='utf-8').read()
            for mm in re.finditer(r'record\s+(\w+)\s*\(([^)]*)\)', s):
                print('\n  ■ %s 中的 %s(%s)'
                      % (name, mm.group(1), re.sub(r'\s+', ' ', mm.group(2))[:150]))
            break
