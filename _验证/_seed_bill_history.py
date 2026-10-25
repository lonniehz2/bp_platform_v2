# -*- coding: utf-8 -*-
"""补 8/9 月历史账单，让账单趋势图有三个月数据。

按房源生成「应收/实收」，部分账单纯未收（体现收缴率差异）。
"""
import random
import time

import pymysql

DB = dict(host='192.168.31.153', port=33306, user='root',
          password='5677@Mysql', database='bp_platform', charset='utf8mb4')
conn = pymysql.connect(**DB)
cur = conn.cursor()

cur.execute("""select h.id, h.house_code, h.org_id, null as person_id
               from bp_asset_house h
               where h.house_status in ('OCCUPIED','RENTED','ALLOCATED')
               limit 80""")
houses = cur.fetchall()
print('目标房源:', len(houses))

cur.execute("select id, item_name, unit_price from bp_fin_fee_item where item_code='ELEC-P1'")
fee = cur.fetchone()
print('计费项:', fee)

NOW = time.strftime('%Y-%m-%d %H:%M:%S')
seq = int(time.time() * 1000) % 10 ** 8


def next_id():
    global seq
    seq += 1
    return 500000000000000000 + seq


def add(house_id, code, org, person, period, amount, paid_ratio, idx):
    cur.execute('''select count(*) from bp_fin_bill
                   where house_id=%s and bill_period=%s''', (house_id, period))
    if cur.fetchone()[0]:
        return 0
    paid = round(amount * paid_ratio, 2)
    status = 'PAID' if paid_ratio >= 1 else ('PARTIAL' if paid > 0 else 'UNPAID')
    cur.execute("""insert into bp_fin_bill
        (id, tenant_id, bill_no, org_id, house_id, person_id, fee_item_id,
         bill_period, period_start, period_end, bill_amount, discount_amount,
         late_fee, paid_amount, waived_amount, payable_amount, bill_status,
         due_date, create_time)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,0,%s,0,%s,%s,%s,%s)""",
                (next_id(), '350600', 'B' + period.replace('-', '') + str(idx).zfill(4),
                 org, house_id, person, fee[0], period, period + '-01', period + '-28',
                 amount, paid, amount, status, period + '-25', NOW))
    return 1


made = {'2026-08': 0, '2026-09': 0}
for i, (house_id, code, org, person) in enumerate(houses):
    for period, base in (('2026-08', 320), ('2026-09', 350)):
        amount = round(base + random.randint(-60, 120), 2)
        ratio = random.choice([1, 1, 1, 0.6, 0.0])
        made[period] += add(house_id, code, org, person, period, amount, ratio, i)

conn.commit()

print('\n新增账单：', made)
print('\n按月汇总：')
cur.execute('''select bill_period, count(*), round(sum(payable_amount),2), round(sum(paid_amount),2)
               from bp_fin_bill
               where bill_period in ('2026-08','2026-09','2026-10','202610')
               group by bill_period order by bill_period''')
for r in cur.fetchall():
    print('  %-8s 账单 %-5s 应收 %-12s 实收 %s' % r)

conn.close()
