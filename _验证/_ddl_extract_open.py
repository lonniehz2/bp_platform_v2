# -*- coding: utf-8 -*-
"""从 DDL 提取 open/gov 9 表结构"""
import io
import re

P = r'D:\Work\业务平台开发\03_数据库设计_P5_支撑域.sql'
s = io.open(P, encoding='utf-8').read()

NAMES = ['bp_open_app', 'bp_open_api', 'bp_open_call_log', 'bp_open_webhook',
         'bp_open_webhook_log', 'bp_gov_adapter_config', 'bp_gov_adapter_log',
         'bp_gov_report_task', 'bp_gov_report_detail']

for n in NAMES:
    m = re.search(r'CREATE TABLE[^`]*`' + n + r'`\s*\((.*?)\n\)\s*ENGINE', s, re.S)
    if not m:
        print('!! 未找到 ' + n)
        continue
    cols = []
    for ln in m.group(1).split('\n'):
        ln = ln.strip().rstrip(',')
        if not ln:
            continue
        up = ln.upper()
        if up.startswith(('PRIMARY', 'UNIQUE', 'KEY', 'INDEX', 'CONSTRAINT', 'PARTITION')):
            continue
        cm = re.match(r'`(\w+)`\s+(\w+(?:\([^)]*\))?)', ln)
        if not cm:
            continue
        q = re.search(r"COMMENT\s+'([^']*)'", ln)
        cols.append((cm.group(1), cm.group(2),
                     'NO' if 'NOT NULL' in up else '', q.group(1) if q else ''))
    print('=== %s (%d) ===' % (n, len(cols)))
    for c in cols:
        print('  %-22s %-16s %-3s %s' % (c[0], c[1], c[2], c[3][:70]))
    print()
