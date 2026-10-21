# -*- coding: utf-8 -*-
"""查看 rpt 5 表结构（精简）"""
import pymysql

TABLES = ('bp_rpt_report_def', 'bp_rpt_export_task', 'bp_rpt_metric_daily',
          'bp_rpt_metric_hourly', 'bp_rpt_screen_def')
c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform', charset='utf8mb4',
                    connect_timeout=15)
cur = c.cursor()
for t in TABLES:
    cur.execute("""SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_COMMENT
                   FROM information_schema.COLUMNS
                   WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME=%s
                   ORDER BY ORDINAL_POSITION""", (t,))
    rows = cur.fetchall()
    print('=== %s (%d) ===' % (t, len(rows)))
    for n, ty, nul, cm in rows:
        print('  %-20s %-14s %-3s %s' % (n, ty, 'NO' if nul == 'NO' else '', (cm or '')[:44]))
    print()
c.close()
