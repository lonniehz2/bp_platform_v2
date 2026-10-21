# -*- coding: utf-8 -*-
"""检查 bp_iam_role 结构并修正种子脚本"""
import io
import re

import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform',
                    charset='utf8mb4', connect_timeout=20)
cur = c.cursor()
cur.execute("SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME='bp_iam_role' "
            "ORDER BY ORDINAL_POSITION")
cols = [r[0] for r in cur.fetchall()]
print('bp_iam_role 列：%s' % ', '.join(cols))
cur.execute("SELECT COUNT(*) FROM bp_iam_role")
print('角色数：%d' % cur.fetchone()[0])
sel = ['id'] + [x for x in ('role_code', 'role_name', 'role_type', 'status',
                            'tenant_id', 'is_deleted') if x in cols]
cur.execute('SELECT %s FROM bp_iam_role LIMIT 10' % ', '.join(sel))
print('样例：')
for r in cur.fetchall():
    print('  ' + ' | '.join(str(v) for v in r))

# 修正种子脚本中的角色查询
P = r'D:\Work\业务平台开发\_验证\_seed_open_gov.py'
s = io.open(P, encoding='utf-8').read()
old = '''cur.execute("""SELECT id, role_code, role_name FROM bp_iam_role
               WHERE tenant_id=%s AND is_deleted=0""", (TENANT,))'''
if old in s:
    cond = []
    if 'tenant_id' in cols:
        cond.append('tenant_id=%s')
    if 'is_deleted' in cols:
        cond.append('is_deleted=0')
    where = (' WHERE ' + ' AND '.join(cond)) if cond else ''
    args = '(TENANT,)' if 'tenant_id' in cols else '()'
    s = s.replace(old,
                  'cur.execute("SELECT id, role_code, role_name FROM bp_iam_role%s")\n'
                  '# 角色表列因环境而异，上面已按实际列拼条件' % where, 1)
    io.open(P, 'w', encoding='utf-8').write(s)
    print('\n已修正种子脚本角色查询')
c.close()
