# -*- coding: utf-8 -*-
"""建日房态表（正确剥离注释）"""
import io
import re

import pymysql

sql_path = r'D:\Work\业务平台开发\03_数据库设计_P6_短租日房态.sql'
raw = io.open(sql_path, encoding='utf-8').read()

# 去掉整行注释
lines = [ln for ln in raw.split('\n') if not ln.strip().startswith('--')]
sql = '\n'.join(lines)

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4')
cur = c.cursor()
cur.execute('DROP TABLE IF EXISTS bp_asset_house_calendar')

# 按 ; 分段（本文件只有一条 CREATE）
stmts = [s.strip() for s in sql.split(';') if s.strip()]
created = 0
for st in stmts:
    if st.upper().startswith('CREATE'):
        cur.execute(st)
        created += 1
c.commit()

cur.execute("""SELECT COUNT(*) FROM information_schema.COLUMNS
               WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME='bp_asset_house_calendar'""")
cols = cur.fetchone()[0]
print('执行 CREATE 语句 %d 条，建表列数 %d' % (created, cols))

cur.execute('SHOW INDEX FROM bp_asset_house_calendar')
seen = {}
for r in cur.fetchall():
    seen.setdefault(r[2], []).append(r[4])
for k, v in seen.items():
    print('  索引 %-28s 列: %s%s' % (k, v, '  ← 唯一' if k.startswith('uk_') else ''))
c.close()
