# -*- coding: utf-8 -*-
"""重建欠费处置动作数据：多个合同、多样动作类型、合理逾期天数。

原种子数据 45 条都指向同一合同、逾期 0 天、冻结范围错填，演示效果差。
"""
import random
from datetime import datetime, timedelta

import pymysql

random.seed(20261026)

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform',
                       charset='utf8mb4', autocommit=True, connect_timeout=20, read_timeout=300)
cur = conn.cursor()

# 1) 清理旧动作
cur.execute("delete from bp_fin_arrears_action")
print('已清理旧动作')

# 2) 取欠费最多的合同（逾期账单汇总）
cur.execute("""
    select b.contract_id, b.person_id, sum(b.payable_amount) amt,
           max(datediff(curdate(), b.due_date)) days, count(*) bills
    from bp_fin_bill b
    where b.bill_status = 'OVERDUE'
      and b.payable_amount > 0
      and b.contract_id is not null
    group by b.contract_id, b.person_id
    having amt > 0
    order by amt desc
    limit 14
""")
targets = cur.fetchall()
print('候选合同:', len(targets))

rows = []
seq = 372900000000000000
for idx, (contract_id, person_id, amt, days, bills) in enumerate(targets):
    days = int(days or 30)
    if days <= 0:
        days = random.choice([31, 45, 60, 90])
    n = 2 if idx % 3 else 3
    # 动作序列：先通知，后升级
    plan = ['NOTIFY']
    if days >= 45 or idx < 6:
        plan.append('FREEZE')
    if days >= 90:
        plan.append(random.choice(['RESTRICT', 'LEGAL']))

    for step, action in enumerate(plan[:n]):
        seq += 1
        executed = (action == 'NOTIFY' and random.random() < 0.55) or \
                   (action == 'FREEZE' and random.random() < 0.25)
        status = 'EXECUTED' if executed else 'PENDING'
        freeze_scope = 'EXCLUDE_MAIN_DOOR' if action == 'FREEZE' else None
        exec_time = None
        if executed:
            exec_time = (datetime.now() - timedelta(days=random.randint(0, 20),
                                                    hours=random.randint(0, 23))
                         ).strftime('%Y-%m-%d %H:%M:%S')
        create_time = (datetime.now() - timedelta(days=days - step * 3,
                                                  hours=random.randint(0, 23))
                       ).strftime('%Y-%m-%d %H:%M:%S')
        rows.append((str(seq), 'FA%d' % seq, contract_id, person_id,
                     float(amt), days - step * 3, 'AUTO' if step == 0 else 'MANUAL',
                     action, freeze_scope, status, exec_time,
                     'system', create_time))

cur.executemany("""
    insert into bp_fin_arrears_action
      (id, tenant_id, action_no, contract_id, person_id, arrears_amount,
       overdue_days, trigger_type, action_type, freeze_scope, action_status,
       execute_time, create_by, create_time)
    values (%s, '350600', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""", rows)
print('已插入动作:', len(rows))

cur.execute("""select action_type, action_status, count(*),
                      count(distinct contract_id)
               from bp_fin_arrears_action group by action_type, action_status""")
for r in cur.fetchall():
    print('  ', r)

conn.close()
