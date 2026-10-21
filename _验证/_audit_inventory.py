# -*- coding: utf-8 -*-
"""盘点：已实现接口 + 有表无服务的孤儿表"""
import io
import os
import re

BASE = r'D:\Work\业务平台开发\backend\src\main\java\com\yundao\bp'

# ---------- 1) 枚举所有 Controller 的接口 ----------
apis = []
for root, _, files in os.walk(BASE):
    for f in files:
        if not f.endswith('Controller.java'):
            continue
        path = os.path.join(root, f)
        s = io.open(path, encoding='utf-8').read()
        m = re.search(r'@RequestMapping\("([^"]+)"\)', s)
        base = m.group(1) if m else ''
        # 逐个方法
        for mm in re.finditer(
                r'@(Get|Post|Put|Delete)Mapping(?:\(([^)]*)\))?\s+'
                r'public\s+[^\{]+\{', s):
            verb = mm.group(1).upper()
            arg = (mm.group(2) or '').strip()
            sub = ''
            q = re.search(r'"([^"]*)"', arg)
            if q:
                sub = q.group(1)
            apis.append((f.replace('Controller.java', ''), verb, base + sub))

apis.sort()
print('已实现接口总数：%d' % len(apis))
by_mod = {}
for mod, v, p in apis:
    by_mod.setdefault(mod, 0)
    by_mod[mod] += 1
for k in sorted(by_mod):
    print('  %-22s %d' % (k, by_mod[k]))

# ---------- 2) 表 vs 服务覆盖 ----------
import pymysql  # noqa: E402
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = c.cursor()
cur.execute("""SELECT TABLE_NAME, TABLE_COMMENT FROM information_schema.TABLES
               WHERE TABLE_SCHEMA='bp_platform' ORDER BY TABLE_NAME""")
tables = cur.fetchall()
c.close()

# 已写过的实体（有 @TableName 的类）
entities = set()
for root, _, files in os.walk(BASE):
    for f in files:
        if not f.endswith('.java'):
            continue
        s = io.open(os.path.join(root, f), encoding='utf-8').read()
        if '@TableName' not in s:
            continue
        m = re.search(r'@TableName\("([^"]+)"\)', s)
        if m:
            entities.add(m.group(1))

orphans = [(t, cm) for t, cm in tables if t not in entities]
print()
print('表总数 %d，有实体的 %d，无实体的（孤儿表）%d'
      % (len(tables), len(entities), len(orphans)))
print()
print('=== 无实体/无服务的表（首期缺口候选）===')
for t, cm in orphans:
    print('  %-34s %s' % (t, (cm or '')[:36]))

# ---------- 3) 写报告数据 ----------
out = io.open(r'D:\Work\业务平台开发\_验证\_inventory.txt', 'w', encoding='utf-8')
out.write('接口总数 %d\n\n按模块：\n' % len(apis))
for k in sorted(by_mod):
    out.write('  %s %d\n' % (k, by_mod[k]))
out.write('\n全部接口：\n')
for mod, v, p in apis:
    out.write('  %-6s %-46s [%s]\n' % (v, p, mod))
out.write('\n孤儿表 %d：\n' % len(orphans))
for t, cm in orphans:
    out.write('  %s  %s\n' % (t, (cm or '')[:50]))
out.close()
print()
print('明细已写入 _验证/_inventory.txt')
