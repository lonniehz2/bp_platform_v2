# -*- coding: utf-8 -*-
"""查看年审表结构 + 公示表枚举"""
import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = c.cursor()

cur.execute("""SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT
               FROM information_schema.COLUMNS
               WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME='bp_biz_annual_review'
               ORDER BY ORDINAL_POSITION""")
rows = cur.fetchall()
print('=== bp_biz_annual_review (%d 列) ===' % len(rows))
for n, ty, nul, cm in rows:
    print('  %-22s %-14s %-3s %s' % (n, ty, 'NO' if nul == 'NO' else '', (cm or '')[:62]))
print()

for t, cols in (('bp_biz_annual_review',
                 ['review_status', 'review_result', 'income_check_status']),
                ('bp_biz_publicity', ['publicity_type', 'publicity_status'])):
    for col in cols:
        cur.execute("""SELECT COLUMN_COMMENT FROM information_schema.COLUMNS
                       WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME=%s
                       AND COLUMN_NAME=%s""", (t, col))
        r = cur.fetchone()
        if r:
            print('  %-20s %s' % (col, r[0]))
c.close()
