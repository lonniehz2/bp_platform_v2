# -*- coding: utf-8 -*-
"""查看 IAM 权限相关表结构（精简输出）"""
import pymysql

TABLES = ('bp_iam_user', 'bp_iam_role', 'bp_iam_permission',
          'bp_iam_user_role', 'bp_iam_role_permission', 'bp_iam_session')

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4',
                    connect_timeout=10)
cur = c.cursor()
for t in TABLES:
    cur.execute("""SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT
                   FROM information_schema.COLUMNS
                   WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME=%s
                   ORDER BY ORDINAL_POSITION""", (t,))
    rows = cur.fetchall()
    print('=== %s (%d) ===' % (t, len(rows)))
    for n, ty, nul, cm in rows:
        print('  %-22s %-14s %-3s %s' % (n, ty, 'NO' if nul == 'NO' else '', (cm or '')[:44]))
c.close()
