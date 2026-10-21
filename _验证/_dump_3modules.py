# -*- coding: utf-8 -*-
"""导出三块需要的接口签名与 DTO"""
import io
import os
import re

J = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

print('=== 合同同住人接口 ===')
for root, _, fs in os.walk(J):
    if 'CohabitantController.java' in fs or 'ContractCohabitantController.java' in fs:
        p = os.path.join(root, fs[0] if False else 'CohabitantController.java')
        s = io.open(os.path.join(root, 'CohabitantController.java'), encoding='utf-8').read()
        bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        base = bm.group(1) if bm else '?'
        print('  base=%s' % base)
        for m in re.finditer(r'@(Get|Post|Put|Delete)Mapping(?:\(\s*"([^"]*)"\s*\))?'
                             r'[\s\S]{0,220}?public\s+[\w<>,\s\.\[\]]*?\s+(\w+)\(([^)]*)\)', s):
            print('  %-6s %-52s %s'
                  % (m.group(1).upper(),
                     (base + '/' + (m.group(2) or '')).replace('//', '/'),
                     re.sub(r'\s+', ' ', m.group(4))[:80]))
        for mm in re.finditer(r'record\s+(\w+)\s*\(([^)]*)\)', s):
            print('  record %s(%s)' % (mm.group(1),
                                       re.sub(r'\s+', ' ', mm.group(2))[:140]))
        break

print('\n=== 同住人 DTO 文件 ===')
for name in ('CohabitantCreateCmd', 'CohabitantCmd', 'CohabitantAddCmd',
             'GrantCmd', 'CohabitantGrantCmd'):
    for root, _, fs in os.walk(J):
        if name + '.java' in fs:
            s = io.open(os.path.join(root, name + '.java'), encoding='utf-8').read()
            m = re.search(r'record\s+' + name + r'\s*\((.*?)\)\s*(?:\{|implements)', s, re.S)
            print('\n■ %s' % name)
            if m:
                for ln in re.sub(r'/\*.*?\*/', '', m.group(1), flags=re.S).split('\n'):
                    t = ln.strip().rstrip(',')
                    if t:
                        print('   ' + t[:110])
            break

print('\n=== 计费项目接口 ===')
for root, _, fs in os.walk(J):
    for f in fs:
        if 'FeeItem' in f and f.endswith('Controller.java'):
            s = io.open(os.path.join(root, f), encoding='utf-8').read()
            bm = re.search(r'@RequestMapping\("([^"]+)"\)', s)
            print('  %s base=%s' % (f, bm.group(1) if bm else '?'))
            for m in re.finditer(r'@(Get|Post|Put|Delete)Mapping(?:\(\s*"([^"]*)"\s*\))?'
                                 r'[\s\S]{0,200}?public\s+[\w<>,\s\.\[\]]*?\s+(\w+)\(([^)]*)\)', s):
                print('    %-6s %-38s %s'
                      % (m.group(1).upper(), m.group(2) or '(root)',
                         re.sub(r'\s+', ' ', m.group(4))[:70]))
