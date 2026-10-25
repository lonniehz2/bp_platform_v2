# -*- coding: utf-8 -*-
"""清理重复出账：同一 (合同, 账期, 收费项) 保留最早一条，其余作废。

- 无收款的重复账单 → 直接置 CANCELLED（保留痕迹，不物理删除）
- 有收款的重复账单 → 只报告，不自动作废（涉及资金）
"""
import datetime
import json
import os

import pymysql

HERE = os.path.dirname(os.path.abspath(__file__))
BACKUP = os.path.join(HERE, '_backup')
os.makedirs(BACKUP, exist_ok=True)
STAMP = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform',
                       charset='utf8mb4', autocommit=False)
cur = conn.cursor(pymysql.cursors.DictCursor)

cur.execute("""
    select contract_id, bill_period, fee_item_id,
           count(*) n, group_concat(id order by id) ids
    from bp_fin_bill
    where coalesce(is_deleted,0) = 0
    group by contract_id, bill_period, fee_item_id
    having n > 1
""")
groups = cur.fetchall()
print('重复出账组:', len(groups))

to_cancel, keep_for_manual = [], []
for g in groups:
    ids = g['ids'].split(',')
    keep, others = ids[0], ids[1:]
    cur.execute('select id, coalesce(paid_amount,0) paid from bp_fin_bill where id in (%s)'
                % ','.join(['%s'] * len(others)), others)
    paid_map = {r['id']: float(r['paid']) for r in cur.fetchall()}
    for oid in others:
        if paid_map.get(int(oid), 0) > 0:
            keep_for_manual.append((g['contract_id'], g['bill_period'], oid,
                                    paid_map[int(oid)]))
        else:
            to_cancel.append(oid)

json.dump({'cancel': to_cancel, 'manual': keep_for_manual},
          open(os.path.join(BACKUP, 'dup-bills-%s.json' % STAMP), 'w', encoding='utf-8'),
          ensure_ascii=False, default=str)

print('可作废（无收款）:', len(to_cancel), ' 需人工（有收款）:', len(keep_for_manual))

now = datetime.datetime.now()
for oid in to_cancel:
    cur.execute('''update bp_fin_bill
                   set bill_status='CANCELLED', remark=concat(coalesce(remark,''),
                       ' [重复出账作废]'), update_time=%s
                   where id=%s''', (now, oid))
conn.commit()
print('已作废:', len(to_cancel))

cur.execute("""select count(*) c from (
    select contract_id, bill_period, fee_item_id from bp_fin_bill
    where coalesce(is_deleted,0)=0 and bill_status<>'CANCELLED'
    group by contract_id, bill_period, fee_item_id having count(*)>1) t""")
print('剩余重复组:', cur.fetchone()['c'])
conn.close()
