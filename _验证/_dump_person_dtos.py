# -*- coding: utf-8 -*-
"""导出人员/保障档案/实名核验的 DTO 字段"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

WANT = ['PersonCreateCmd', 'PersonUpdateCmd', 'GuaranteeProfileCreateCmd',
        'VerifyRecordCreateCmd', 'IncomeRecalcCmd', 'ProfileQualifyCmd',
        'ProfileExitCmd', 'HouseCreateCmd', 'SpaceCreateCmd', 'FeeItemCreateCmd']

for name in WANT:
    found = False
    for root, _, fs in os.walk(J):
        if name + '.java' not in fs:
            continue
        s = io.open(os.path.join(root, name + '.java'), encoding='utf-8').read()
        m = re.search(r'record\s+' + name + r'\s*\((.*?)\)\s*(?:\{|implements)', s, re.S)
        print('\n■ %s  (%s)' % (name, root.replace(J, '').strip('\\')))
        if m:
            body = re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S)
            for ln in body.split('\n'):
                t = ln.strip().rstrip(',')
                if t:
                    print('   ' + t[:118])
        else:
            # 可能是普通类
            for mm in re.finditer(r'private\s+[\w<>\.]+\s+(\w+)\s*;', s):
                pass
            print('   （非 record）')
        found = True
        break
    if not found:
        print('\n□ %s 未找到' % name)
