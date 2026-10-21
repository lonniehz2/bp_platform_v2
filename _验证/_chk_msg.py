# -*- coding: utf-8 -*-
"""查看消息中心 4 表结构"""
import pymysql

TABLES = ('bp_msg_template', 'bp_msg_subscription', 'bp_msg_send_record', 'bp_msg_todo')
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
        print('  %-22s %-16s %-3s %s' % (n, ty, 'NO' if nul == 'NO' else '', (cm or '')[:48]))
    print()
c.close()
