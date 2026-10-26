# -*- coding: utf-8 -*-
"""查看对账单/收款单现状，便于设计页面。"""
import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                    password='5677@Mysql', database='bp_platform',
                    charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=120)
cur = c.cursor()
for t in ['bp_fin_payment', 'bp_fin_reconcile']:
    try:
        cur.execute('select count(*) from %s' % t)
        print(t, cur.fetchone()[0])
    except Exception as e:
        print(t, 'skip', str(e)[:50])
try:
    cur.execute('select pay_status, count(*) from bp_fin_payment group by pay_status')
    print('收款单状态:', cur.fetchall())
except Exception as e:
    print('pay_status 查询失败', str(e)[:60])
try:
    cur.execute('select reconcile_status, count(*) from bp_fin_reconcile group by reconcile_status')
    print('对账状态:', cur.fetchall())
except Exception as e:
    print('reconcile 查询失败', str(e)[:60])
cur.execute('show columns from bp_fin_payment')
print('收款单字段:', [r[0] for r in cur.fetchall()][:20])
c.close()
