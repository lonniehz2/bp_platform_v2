# -*- coding: utf-8 -*-
"""生成 2026-08 / 09 / 10 三个月的完整财务演示数据。

规则（贴近真实业务）：
  * 每个生效合同每月一张「租金」+ 一张「物业费」账单（金额 = 面积 × 单价）
  * 水电燃气：按该房源当月抄表读数出账（有读数的才出）
  * 缴费比例：08 月 92% 缴清 / 09 月 85% 缴清 + 5% 部分 / 10 月 25% 缴清 + 10% 部分
  * 缴费同时写核销明细与资金流水，保证「应收 / 实收 / 流水」三者一致
"""
import datetime
import random

import pymysql

TENANT = '350600'
random.seed(20261026)

RENT_ITEM = 370832922074288128
PROP_ITEM = 370832922627936256
RENT_PRICE = 12.5
PROP_PRICE = 2.5

PERIODS = [
    ('2026-08', datetime.date(2026, 8, 1), datetime.date(2026, 8, 31),
     datetime.date(2026, 8, 10), 0.92, 0.00),
    ('2026-09', datetime.date(2026, 9, 1), datetime.date(2026, 9, 30),
     datetime.date(2026, 9, 10), 0.85, 0.05),
    ('2026-10', datetime.date(2026, 10, 1), datetime.date(2026, 10, 31),
     datetime.date(2026, 10, 10), 0.25, 0.10),
]

NOW = datetime.datetime(2026, 10, 26, 9, 0, 0)
TODAY = datetime.date(2026, 10, 26)

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform',
                       charset='utf8mb4', autocommit=False)
cur = conn.cursor(pymysql.cursors.DictCursor)

_seq = [0]


def next_id():
    _seq[0] += 1
    return int(NOW.timestamp() * 1000) * 1000 + _seq[0]


def money(v):
    return round(float(v or 0), 2)


cur.execute("""
    select c.id, c.contract_no, c.org_id, c.house_id, c.space_id,
           c.lessee_person_id, c.lessee_name, c.lessee_phone, c.monthly_rent,
           c.house_area
    from bp_biz_contract c
    where c.contract_status = 'EFFECTIVE' and c.tenant_id = %s
""", (TENANT,))
contracts = cur.fetchall()
print('生效合同:', len(contracts))

cur.execute("""
    select id, house_id, org_id, fee_item_id, read_date,
           usage_amount, unit_price, amount
    from bp_fin_meter_reading
    where tenant_id = %s and read_date >= '2026-08-01' and read_date < '2026-11-01'
""", (TENANT,))
readings = cur.fetchall()
print('可用抄表读数:', len(readings))

cur.execute('select id, org_id from bp_asset_house where org_id is not null')
house_org = {r['id']: r['org_id'] for r in cur.fetchall()}
DEFAULT_ORG = next(iter(house_org.values()), None)

created_bills = 0
created_payments = 0
created_flows = 0


def insert_bill(period, pstart, pend, due, org_id, contract_id, house_id, space_id,
                person_id, payer_name, payer_phone, fee_item_id, amount,
                generate_type, remark):
    """写入一张账单，返回 (id, status)。"""
    global created_bills
    bid = next_id()
    overdue_days = (TODAY - due).days if TODAY > due else 0
    status = 'OVERDUE' if overdue_days > 0 else 'UNPAID'
    cur.execute("""
        insert into bp_fin_bill
        (id, tenant_id, bill_no, org_id, contract_id, house_id, space_id,
         person_id, payer_name, payer_phone, fee_item_id, bill_period,
         period_start, period_end, bill_amount, discount_amount, late_fee,
         paid_amount, waived_amount, payable_amount, due_date, bill_status,
         overdue_days, generate_type, remark, is_deleted, create_by,
         create_time, update_time)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,0,0,0,0,%s,%s,%s,%s,%s,%s,0,'system',%s,%s)
    """, (bid, TENANT, 'FB' + str(bid), org_id, contract_id, house_id, space_id,
          person_id, payer_name, payer_phone, fee_item_id, period,
          pstart, pend, amount, amount, due, status, overdue_days,
          generate_type, remark, NOW, NOW))
    created_bills += 1
    return bid, status


def pay_bill(bill_id, amount, org_id, person_id, name, phone, pay_time):
    """写收款单 + 核销明细 + 资金流水。"""
    global created_payments, created_flows
    pid = next_id()
    cur.execute("""
        insert into bp_fin_payment
        (id, tenant_id, payment_no, org_id, person_id, payer_name, pay_amount,
         pay_channel, pay_time, trade_no, pay_status, reconcile_status,
         reconciled_amount, unknown_flag, create_by, create_time, update_time)
        values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'SUCCESS','RECONCILED',%s,0,'system',%s,%s)
    """, (pid, TENANT, 'PY' + str(pid), org_id, person_id, name, amount,
          random.choice(['BANK', 'WECHAT', 'ALIPAY', 'CASH']), pay_time,
          'TR' + str(pid)[-10:], amount, pay_time, pay_time))
    created_payments += 1

    cur.execute("""
        insert into bp_fin_payment_allocate
        (id, tenant_id, payment_id, bill_id, allocate_amount, allocate_type,
         create_by, create_time)
        values (%s,%s,%s,%s,%s,'PAY','system',%s)
    """, (next_id(), TENANT, pid, bill_id, amount, pay_time))

    cur.execute("""
        insert into bp_fin_cash_flow
        (id, tenant_id, flow_no, flow_type, biz_type, biz_id, amount,
         flow_time, verify_status, create_time)
        values (%s,%s,%s,'IN','PAYMENT',%s,%s,%s,'VERIFIED',%s)
    """, (next_id(), TENANT, 'CF' + str(next_id())[-10:], pid, amount, pay_time, pay_time))
    created_flows += 1


for period, pstart, pend, due, pay_ratio, partial_ratio in PERIODS:
    print('--- 账期', period, '缴清', pay_ratio, '部分', partial_ratio)
    bills_this = 0

    for c in contracts:
        area = float(c['house_area'] or 60)
        rent = money(c['monthly_rent']) if c['monthly_rent'] else money(area * RENT_PRICE)
        if rent <= 0:
            rent = money(area * RENT_PRICE)
        prop = money(area * PROP_PRICE)

        for item, amount, note in [(RENT_ITEM, rent, '月租金'),
                                   (PROP_ITEM, prop, '物业费')]:
            bid, _ = insert_bill(period, pstart, pend, due, c['org_id'], c['id'],
                                 c['house_id'], c['space_id'],
                                 c['lessee_person_id'], c['lessee_name'],
                                 c['lessee_phone'], item, amount, 'AUTO',
                                 '%s %s' % (period, note))
            bills_this += 1
            pay_time = datetime.datetime.combine(
                pstart + datetime.timedelta(days=8), datetime.time(10, 0))

            r = random.random()
            if r < pay_ratio:
                pay_bill(bid, amount, c['org_id'], c['lessee_person_id'],
                         c['lessee_name'], c['lessee_phone'], pay_time)
                cur.execute("""
                    update bp_fin_bill set paid_amount=payable_amount,
                           bill_status='PAID', overdue_days=0 where id=%s
                """, (bid,))
            elif r < pay_ratio + partial_ratio:
                half = money(amount * 0.5)
                pay_bill(bid, half, c['org_id'], c['lessee_person_id'],
                         c['lessee_name'], c['lessee_phone'], pay_time)
                cur.execute("""
                    update bp_fin_bill set paid_amount=%s, payable_amount=%s,
                           bill_status='PARTIAL' where id=%s
                """, (half, money(amount - half), bid))

    for rd in readings:
        if rd['read_date'].strftime('%Y-%m') != period:
            continue
        amt = money(rd['amount'])
        if amt <= 0:
            continue
        org_id = rd['org_id'] or house_org.get(rd['house_id']) or DEFAULT_ORG
        bid, _ = insert_bill(period, pstart, pend, due, org_id, None,
                             rd['house_id'], None, None, '抄表缴费', None,
                             rd['fee_item_id'], amt, 'METER',
                             '%s 抄表出账' % period)
        cur.execute("""
            update bp_fin_meter_reading set bill_status='BILLED', bill_id=%s
            where id=%s
        """, (bid, rd['id']))
        bills_this += 1

        if random.random() < pay_ratio:
            pay_time = datetime.datetime.combine(
                pstart + datetime.timedelta(days=9), datetime.time(15, 0))
            pay_bill(bid, amt, org_id, None, '抄表缴费', None, pay_time)
            cur.execute("""
                update bp_fin_bill set paid_amount=payable_amount,
                       bill_status='PAID', overdue_days=0 where id=%s
            """, (bid,))

    print('   本月账单数:', bills_this)

conn.commit()

cur.execute("""
    select bill_period, bill_status, count(*) n, sum(bill_amount) amt
    from bp_fin_bill where tenant_id=%s and is_deleted=0
    group by bill_period, bill_status order by 1,2
""", (TENANT,))
print('\n账单分布:')
for r in cur.fetchall():
    print('  %s %-10s %4d 张 应收 %12.2f' % (r['bill_period'], r['bill_status'],
                                           r['n'], float(r['amt'] or 0)))

cur.execute("""
    select bill_period, sum(bill_amount) due, sum(paid_amount) paid
    from bp_fin_bill where tenant_id=%s and is_deleted=0
    group by bill_period order by 1
""", (TENANT,))
print('\n应收/实收:')
for r in cur.fetchall():
    due_amt, paid = float(r['due'] or 0), float(r['paid'] or 0)
    rate = paid / due_amt * 100 if due_amt else 0
    print('  %s 应收 %12.2f  实收 %12.2f  收缴率 %5.1f%%'
          % (r['bill_period'], due_amt, paid, rate))

print('\n新增 账单 %d / 收款单 %d / 流水 %d'
      % (created_bills, created_payments, created_flows))
conn.close()
