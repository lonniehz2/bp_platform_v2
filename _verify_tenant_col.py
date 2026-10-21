# -*- coding: utf-8 -*-
"""修正种子脚本：租户存在性校验按主表实际列（干净替换，不留占位符）"""
import io

import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform',
                    charset='utf8mb4', connect_timeout=20)
cur = c.cursor()
cur.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME='bp_iam_tenant' "
            "ORDER BY ORDINAL_POSITION")
cols = [r[0] for r in cur.fetchall()]
print('bp_iam_tenant 列：%s' % ', '.join(cols))

key = 'tenant_code' if 'tenant_code' in cols else None
if key is None:
    for cand in ('code', 'tenant_no', 'id'):
        if cand in cols:
            key = cand
            break
print('用 %s 校验租户' % key)

cur.execute('SELECT %s FROM bp_iam_tenant' % key)
vals = [r[0] for r in cur.fetchall()]
print('现有租户：%s' % vals)
c.close()

P = r'D:\Work\业务平台开发\_验证\_seed_open_gov.py'
s = io.open(P, encoding='utf-8').read()
old = 'cur.execute("SELECT COUNT(*) FROM bp_iam_tenant WHERE tenant_id=%s", (TENANT,))'
new = ('# 租户主表是 bp_iam_tenant 本身（无 tenant_id 列），按 %s 校验\n'
       'cur.execute("SELECT COUNT(*) FROM bp_iam_tenant WHERE %s=%%s", (TENANT,))'
       % (key, key))

if old in s:
    s = s.replace(old, new, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('已修正租户校验语句')
else:
    print('未找到原语句（可能已改），检查当前内容：')
    for i, ln in enumerate(s.split('\n'), 1):
        if 'bp_iam_tenant' in ln:
            print('  L%d: %s' % (i, ln.strip()))
