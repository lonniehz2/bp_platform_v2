# -*- coding: utf-8 -*-
"""建短租订单表 + 同步 verify 断言"""
import io

import pymysql

sql_path = r'D:\Work\业务平台开发\03_数据库设计_P7_短租订单.sql'
raw = io.open(sql_path, encoding='utf-8').read()
sql = '\n'.join(ln for ln in raw.split('\n') if not ln.strip().startswith('--'))

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4')
cur = c.cursor()
cur.execute('DROP TABLE IF EXISTS bp_biz_short_rent_order')
n = 0
for st in [s.strip() for s in sql.split(';') if s.strip()]:
    if st.upper().startswith('CREATE'):
        cur.execute(st)
        n += 1
c.commit()

cur.execute("""SELECT COUNT(*) FROM information_schema.COLUMNS
               WHERE TABLE_SCHEMA='bp_platform' AND TABLE_NAME='bp_biz_short_rent_order'""")
cols = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='bp_platform'")
tables = cur.fetchone()[0]
cur.execute("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='bp_platform'")
allcols = cur.fetchone()[0]
print('CREATE %d 条；短租订单表 %d 列' % (n, cols))
print('当前总表数 %d，总列数 %d' % (tables, allcols))

# 同步 verify 断言
cfg = r'D:\Work\业务平台开发\_验证\config.json'
s = io.open(cfg, encoding='utf-8').read()
import re
s = re.sub(r'"tables":\s*\d+', '"tables": %d' % tables, s)
s = re.sub(r'"columns":\s*\d+', '"columns": %d' % allcols, s)
io.open(cfg, 'w', encoding='utf-8').write(s)
print('config.json 断言已同步为 %d 表 / %d 列' % (tables, allcols))
c.close()
