# -*- coding: utf-8 -*-
"""查看换房表结构"""
import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = c.cursor()
cur.execute("""SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT
               FROM information_schema.COLUMNS
               WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME='bp_biz_exchange'
               ORDER BY ORDINAL_POSITION""")
rows = cur.fetchall()
print('=== bp_biz_exchange (%d 列) ===' % len(rows))
for n, ty, nul, cm in rows:
    print('  %-22s %-14s %-3s %s' % (n, ty, 'NO' if nul == 'NO' else '', (cm or '')[:68]))
print()
for col in ('exchange_type', 'exchange_status', 'approve_status'):
    cur.execute("""SELECT COLUMN_COMMENT FROM information_schema.COLUMNS
                   WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME='bp_biz_exchange'
                   AND COLUMN_NAME=%s""", (col,))
    r = cur.fetchone()
    if r:
        print('  %-16s %s' % (col, r[0]))
c.close()
