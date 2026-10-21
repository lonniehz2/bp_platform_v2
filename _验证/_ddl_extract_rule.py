# -*- coding: utf-8 -*-
"""提取告警规则引擎 4 表结构 + 检查实体是否已存在"""
import io
import os
import re

DDL_DIR = r'D:\Work\业务平台开发'
SRC = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'
NAMES = ['bp_ops_alert_rule', 'bp_rule_ruleset', 'bp_rule_rule', 'bp_rule_execute_log']

existing = set()
for root, _, files in os.walk(SRC):
    for f in files:
        if f.endswith('.java'):
            s = io.open(os.path.join(root, f), encoding='utf-8').read()
            m = re.search(r'@TableName\("([^"]+)"\)', s)
            if m:
                existing.add(m.group(1))

bodies = {}
for f in os.listdir(DDL_DIR):
    if not f.endswith('.sql'):
        continue
    s = io.open(os.path.join(DDL_DIR, f), encoding='utf-8').read()
    for n in NAMES:
        m = re.search(r'CREATE TABLE[^`]*`' + n + r'`\s*\((.*?)\n\)\s*ENGINE', s, re.S)
        if m:
            bodies[n] = (f, m.group(1))

for n in NAMES:
    if n not in bodies:
        print('!! 未找到 %s' % n)
        continue
    f, body = bodies[n]
    cols = []
    for ln in body.split('\n'):
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
    flag = '有实体' if n in existing else '❌ 无实体'
    print('=== %s (%d) %s ===' % (n, len(cols), flag))
    for c in cols:
        print('  %-22s %-14s %-3s %s' % (c[0], c[1], c[2], c[3][:58]))
    print()
