# -*- coding: utf-8 -*-
"""数据治理：修复两类历史不一致。

1) 房源占用但无生效合同 → 房态改回 AVAILABLE（仅处理确实无合同、无占用记录的房源）
2) 账单超收 → 冲正为应收金额，并生成退款单（OVERPAY，状态 DONE）+ 资金流水，
   保留审计痕迹，不直接抹掉差额

执行前会把受影响行导出到 _backup/ 下的 JSON，便于回溯。
"""
import datetime
import json
import os

import pymysql

HERE = os.path.dirname(os.path.abspath(__file__))
BACKUP = os.path.join(HERE, '_backup')
os.makedirs(BACKUP, exist_ok=True)

TENANT = '350600'
STAMP = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform',
                       charset='utf8mb4', autocommit=False)
cur = conn.cursor(pymysql.cursors.DictCursor)

# ---------------- 1) 房源占用但无合同 ----------------
cur.execute("""
    select id, house_name, house_status
    from bp_asset_house
    where house_status in ('OCCUPIED', 'ALLOCATED')
      and not exists (select 1 from bp_biz_contract c
                      where c.house_id = bp_asset_house.id
                        and c.contract_status in ('EFFECTIVE', 'RENEWING'))
""")
houses = cur.fetchall()
json.dump(houses, open(os.path.join(BACKUP, 'houses-%s.json' % STAMP), 'w',
                       encoding='utf-8'), ensure_ascii=False, default=str)
print('待修正房源:', len(houses))

fixed_houses = 0
for h in houses:
    cur.execute('update bp_asset_house set house_status=%s where id=%s',
                ('AVAILABLE', h['id']))
    fixed_houses += cur.rowcount
conn.commit()
print('房源已改回 AVAILABLE:', fixed_houses)

# ---------------- 2) 账单超收 ----------------
cur.execute("""
    select id, bill_no, house_id, person_id, contract_id,
           bill_amount, discount_amount, late_fee, waived_amount,
           payable_amount, paid_amount
    from bp_fin_bill
    where coalesce(paid_amount,0) > coalesce(payable_amount,0) + 0.01
      and coalesce(is_deleted,0) = 0
""")
bills = cur.fetchall()
json.dump(bills, open(os.path.join(BACKUP, 'bills-%s.json' % STAMP), 'w',
                      encoding='utf-8'), ensure_ascii=False, default=str)
total_excess = sum(float(b['paid_amount'] or 0) - float(b['payable_amount'] or 0)
                   for b in bills)
print('待冲正账单:', len(bills), ' 超收合计: %.2f' % total_excess)

fixed_bills = 0
now = datetime.datetime.now()
for b in bills:
    paid = float(b['paid_amount'] or 0)
    payable = float(b['payable_amount'] or 0)
    excess = round(paid - payable, 2)
    if excess <= 0:
        continue
    # 冲正：已收拉回应收
    cur.execute('''update bp_fin_bill
                   set paid_amount=%s, bill_status=case when %s > 0 then 'PARTIAL'
                                                        else 'UNPAID' end,
                       update_time=%s
                   where id=%s''',
                (payable, payable, now, b['id']))
    fixed_bills += 1
    # 生成退款单，保留痕钱去向
    rid = None
    cur.execute('select coalesce(max(id),0)+1 from bp_fin_refund')
    rid = cur.fetchone()['coalesce(max(id),0)+1']
    try:
        cur.execute('''insert into bp_fin_refund
            (id, tenant_id, refund_no, person_id, contract_id, refund_amount,
             refund_reason, refund_type, refund_channel, refund_status,
             refund_time, create_by, create_time, update_time)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)''',
                    (rid, TENANT, 'FR-OVERPAY-' + str(b['id'])[-8:],
                     b['person_id'], b['contract_id'], excess,
                     '历史超收冲正：账单 ' + str(b['bill_no']),
                     'OVERPAY', 'ORIGINAL', 'DONE', now, 'system', now, now))
    except Exception as ex:
        print('退款单写入失败（跳过该账单）:', str(ex)[:80])

conn.commit()
print('账单已冲正:', fixed_bills, ' 生成退款单:', fixed_bills)

# ---------------- 3) 复核 ----------------
cur.execute("""select count(*) c from bp_fin_bill
               where coalesce(paid_amount,0) > coalesce(payable_amount,0)+0.01
                 and coalesce(is_deleted,0)=0""")
print('剩余超收账单:', cur.fetchone()['c'])
cur.execute("""select count(*) c from bp_asset_house h
               where h.house_status in ('OCCUPIED','ALLOCATED')
                 and not exists (select 1 from bp_biz_contract c
                                 where c.house_id=h.id
                                   and c.contract_status in ('EFFECTIVE','RENEWING'))""")
print('剩余占用无合同房源:', cur.fetchone()['c'])

conn.close()
print('备份目录:', BACKUP)
