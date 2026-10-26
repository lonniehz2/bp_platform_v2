# -*- coding: utf-8 -*-
"""生成催缴记录（bp_fin_dunning_record），供催缴管理页展示。

同时修正抄表出账账单的缴费人：改用该房源对应合同的承租人姓名。
"""
import datetime
import random

import pymysql

TENANT = '350600'
random.seed(20261030)
NOW = datetime.datetime(2026, 10, 26, 9, 0, 0)

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform',
                       charset='utf8mb4', autocommit=False)
cur = conn.cursor(pymysql.cursors.DictCursor)

# ---- 1) 修正抄表账单缴费人 ----
cur.execute("""
    update bp_fin_bill b
    join bp_biz_contract c on c.house_id = b.house_id
                           and c.contract_status = 'EFFECTIVE'
    set b.person_id = c.lessee_person_id,
        b.payer_name = c.lessee_name,
        b.payer_phone = c.lessee_phone,
        b.contract_id = c.id
    where b.generate_type = 'METER'
      and b.contract_id is null
      and b.tenant_id = %s
""", (TENANT,))
print('抄表账单补缴费人:', cur.rowcount)

# ---- 2) 催缴记录 ----
cur.execute('delete from bp_fin_dunning_record where tenant_id=%s', (TENANT,))
cur.execute("""
    select id, person_id, payable_amount, overdue_days, payer_name
    from bp_fin_bill
    where bill_status = 'OVERDUE' and payable_amount > 0 and tenant_id = %s
    order by overdue_days desc limit 40
""", (TENANT,))
bills = cur.fetchall()
print('逾期账单:', len(bills))

seq = 0
for b in bills[:30]:
    seq += 1
    did = int(NOW.timestamp() * 1000) * 1000 + 900 + seq
    dno = 900000 + seq
    dunning_time = NOW - datetime.timedelta(days=random.randint(1, 15))
    cur.execute("""
        insert into bp_fin_dunning_record
        (id, tenant_id, bill_id, person_id, dunning_no, dunning_type,
         dunning_time, dunning_content, dunning_result, operator_id, create_time)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,1,%s)
    """, (did, TENANT, b['id'], b['person_id'], dno,
          random.choice(['SMS', 'WECHAT', 'PHONE', 'VISIT', 'NOTICE']),
          dunning_time,
          '欠费 %s 元，已逾期 %s 天，请尽快缴纳' % (b['payable_amount'], b['overdue_days']),
          random.choice(['已送达', '已回复承诺缴费', '无人接听', '已上门']),
          dunning_time))
conn.commit()
print('生成催缴记录:', seq)

cur.execute('select dunning_type, count(*) n from bp_fin_dunning_record group by dunning_type')
print('按方式:', cur.fetchall())
conn.close()
