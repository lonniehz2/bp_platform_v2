# -*- coding: utf-8 -*-
"""按逾期账单生成一批催缴动作（供催缴管理 / 欠费趋势演示）。"""
import datetime
import random

import pymysql

TENANT = '350600'
random.seed(20261028)
NOW = datetime.datetime(2026, 10, 26, 9, 0, 0)

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform',
                       charset='utf8mb4', autocommit=False)
cur = conn.cursor(pymysql.cursors.DictCursor)

cur.execute('delete from bp_fin_dunning_record where tenant_id=%s', (TENANT,))
cur.execute('delete from bp_fin_arrears_action where tenant_id=%s', (TENANT,))
print('清理既有催缴数据')

cur.execute("""
    select id, bill_no, contract_id, person_id, org_id, payable_amount,
           due_date, overdue_days
    from bp_fin_bill
    where bill_status = 'OVERDUE' and payable_amount > 0 and tenant_id = %s
    order by overdue_days desc, payable_amount desc
    limit 40
""", (TENANT,))
bills = cur.fetchall()
print('逾期账单:', len(bills))

seq = 0
for b in bills[:30]:
    seq += 1
    aid = int(NOW.timestamp() * 1000) * 1000 + seq
    cur.execute("""
        insert into bp_fin_arrears_action
        (id, tenant_id, action_no, contract_id, person_id, arrears_amount,
         overdue_days, trigger_type, action_type, freeze_scope, action_status,
         execute_time, create_by, create_time, update_time)
        values (%s,%s,%s,%s,%s,%s,%s,'AUTO',%s,'EXCLUDE_MAIN_DOOR',%s,%s,'system',%s,%s)
    """, (aid, TENANT, 'AR' + str(aid), b['contract_id'], b['person_id'],
          b['payable_amount'], b['overdue_days'],
          random.choice(['SMS', 'PHONE', 'VISIT', 'NOTICE']),
          random.choice(['PENDING', 'EXECUTED']),
          NOW if seq % 3 == 0 else None, NOW, NOW))
conn.commit()
print('生成催缴动作:', seq)

cur.execute('select action_status, count(*) n from bp_fin_arrears_action group by action_status')
print('催缴状态:', cur.fetchall())
conn.close()
