# -*- coding: utf-8 -*-
"""导出 P0 相关控制器内定义的全部 Cmd record 字段（含嵌套 record）"""
import io
import json
import os
import re

JAVA = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
OUT = r'D:\Work\业务平台开发\_验证\_p0_cmds.json'

TARGETS = ['ContractController', 'AllocationController', 'BillingController',
           'BillGenerationController', 'PaymentController', 'DepositRefundController',
           'PublicityController', 'PublicityReviewController', 'AnnualReviewController',
           'FinLedgerController', 'SubsidyController', 'TerminationController']

spec = {}
for root, _, files in os.walk(JAVA):
    for f in files:
        if not f.endswith('.java'):
            continue
        base = f[:-5]
        if base not in TARGETS:
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        for mm in re.finditer(r'record\s+(\w+)\s*\((.*?)\)\s*(?:\{|implements)', s, re.S):
            name = mm.group(1)
            if name in spec:
                continue
            body = re.sub(r'/\*.*?\*/', '', mm.group(2), flags=re.S)
            body = re.sub(r'//[^\n]*', '', body)
            fields = []
            for ln in body.split('\n'):
                t = ln.strip().rstrip(',')
                if not t:
                    continue
                t = re.sub(r'^@\w+(\([^)]*\))?\s*', '', t)
                t = t.strip()
                if re.match(r'^[\w<>\[\],\.\s]+\s+\w+$', t):
                    fields.append(t)
            spec[name] = {'controller': base, 'fields': fields}

json.dump(spec, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('导出 %d 个 Cmd record\n' % len(spec))
for k in sorted(spec):
    v = spec[k]
    print('■ %-22s (%s) %d 字段' % (k, v['controller'], len(v['fields'])))
    for x in v['fields']:
        print('     ' + x)
