# -*- coding: utf-8 -*-
"""列出 bp_grant_* 表：DDL 结构 + 是否已有实体"""
import io
import os
import re

DDL_DIR = r'D:\Work\业务平台开发'
SRC = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# 收集已有实体
existing = set()
for root, _, files in os.walk(SRC):
    for f in files:
        if f.endswith('.java'):
            s = io.open(os.path.join(root, f), encoding='utf-8').read()
            m = re.search(r'@TableName\("([^"]+)"\)', s)
            if m:
                existing.add(m.group(1))

# 收集 DDL 中 grant 相关表
tables = {}
for f in os.listdir(DDL_DIR):
    if not f.endswith('.sql'):
        continue
    s = io.open(os.path.join(DDL_DIR, f), encoding='utf-8').read()
    for m in re.finditer(r'CREATE TABLE[^`]*`(bp_grant_\w+)`\s*\((.*?)\n\)\s*ENGINE',
                         s, re.S):
        tables[m.group(1)] = (f, m.group(2))

print('=== bp_grant_* 表清单 ===')
for t in sorted(tables):
    flag = '有实体' if t in existing else '❌ 无实体'
    print('  %-32s %-28s %s' % (t, tables[t][0][:26], flag))

missing = [t for t in sorted(tables) if t not in existing]
print()
print('缺实体 %d 张：%s' % (len(missing), ', '.join(missing)))
print()

for t in missing:
    body = tables[t][1]
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
    print('=== %s (%d) ===' % (t, len(cols)))
    for c in cols:
        print('  %-24s %-16s %-3s %s' % (c[0], c[1], c[2], c[3][:64]))
    print()
