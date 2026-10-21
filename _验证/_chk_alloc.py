# -*- coding: utf-8 -*-
"""查看配租相关表结构"""
import pymysql

TABLES = ('bp_biz_waiting_queue', 'bp_biz_batch', 'bp_biz_batch_house',
          'bp_biz_allocation', 'bp_biz_lottery_result', 'bp_biz_publicity')

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4')
cur = c.cursor()
for t in TABLES:
    cur.execute("""SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT
                   FROM information_schema.COLUMNS
                   WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME=%s
                   ORDER BY ORDINAL_POSITION""", (t,))
    rows = cur.fetchall()
    cur.execute("""SELECT TABLE_COMMENT FROM information_schema.TABLES
                   WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME=%s""", (t,))
    tc = cur.fetchone()
    print('=== %s (%d 列) %s' % (t, len(rows), (tc[0] or '')[:40] if tc else ''))
    for n, ty, nul, cm in rows:
        print('  %-22s %-14s %-3s %s' % (n, ty, 'NO' if nul == 'NO' else '', (cm or '')[:60]))
    print()
c.close()
