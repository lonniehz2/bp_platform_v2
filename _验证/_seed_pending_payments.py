# -*- coding: utf-8 -*-
"""造 5 笔「待支付」收款单，用于「确认收款」演示。

真实渠道回调前，收款单处于 PENDING；确认后才计入流水。
"""
import pymysql
from datetime import datetime, timedelta
import random

random.seed(20261027)
conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform',
                       charset='utf8mb4', autocommit=True,
                       connect_timeout=20, read_timeout=180)
cur = conn.cursor()

cur.execute("""select org_id, person_id, payer_name, pay_amount, pay_channel
               from bp_fin_payment where pay_status='SUCCESS'
               order by id desc limit 20""")
base = cur.fetchall()
if not base:
    raise SystemExit('没有可参考的历史收款单')

seq = 373200000000000000
made = 0
for i in range(5):
    org_id, person_id, payer, amount, channel = base[i % len(base)]
    seq += 1
    # 金额取历史值的 0.6~1.2 倍，保留两位
    amt = round(float(amount) * random.uniform(0.6, 1.2), 2)
    pay_time = (datetime.now() - timedelta(minutes=30 * (i + 1))).strftime('%Y-%m-%d %H:%M:%S')
    cur.execute("""insert into bp_fin_payment
        (id, tenant_id, payment_no, org_id, person_id, payer_name, pay_amount,
         pay_channel, pay_time, pay_status, reconciled_amount, unknown_flag,
         remark, create_by, create_time)
        values (%s,'350600',%s,%s,%s,%s,%s,%s,%s,'PENDING',0,0,%s,'system',%s)""",
        (str(seq), 'PAY-PENDING-%04d' % (i + 1), org_id, person_id,
         payer or '待确认缴费人', amt, channel, pay_time,
         '渠道待确认（演示数据）', pay_time))
    made += 1

cur.execute("select pay_status, count(*) from bp_fin_payment group by pay_status")
print('已插入待确认收款单:', made)
print('收款单状态分布:', cur.fetchall())
conn.close()
