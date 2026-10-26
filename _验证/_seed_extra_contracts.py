# -*- coding: utf-8 -*-
"""补充生效合同：把可租房源批量签约（含押金台账）。

每套：一份 EFFECTIVE 合同（2026-01-01 ~ 2026-12-31）+ 一笔押金台账，
房源置 OCCUPIED。租金 = 面积 × 12.5。
"""
import datetime
import random

import pymysql

TENANT = '350600'
random.seed(20261029)
NOW = datetime.datetime(2026, 10, 26, 9, 0, 0)
RENT_PRICE = 12.5

CONTRACT_SQL = """
insert into bp_biz_contract
(id, tenant_id, contract_no, contract_type, org_id, lessor_org_id,
 lessee_person_id, lessee_name, lessee_phone, lessee_id_card_mask,
 house_id, space_id, house_area, lease_start, lease_end, lease_months,
 rent_price, rent_unit, monthly_rent, deposit_amount, pay_cycle, pay_day,
 late_fee_rate, sign_type, contract_status, effective_time,
 auto_grant, auto_expire, arrears_stop, is_deleted, create_by,
 create_time, update_time)
values (%s, %s, %s, 'LEASE', %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, '2026-01-01', '2026-12-31', 12,
        %s, 'AREA_MONTH', %s, %s, 'MONTH', 10,
        0.0005, 'PAPER', 'EFFECTIVE', '2026-01-01 00:00:00',
        0, 0, 1, 0, 'system',
        %s, %s)
"""

DEPOSIT_SQL = """
insert into bp_fin_deposit
(id, tenant_id, contract_id, person_id, org_id, deposit_amount, paid_amount,
 deduct_amount, refund_amount, balance_amount, deposit_status, cap_amount,
 is_exempt, over_cap_flag, create_time, update_time)
values (%s, %s, %s, %s, %s, %s, %s, 0, 0, %s, 'RECEIVED', %s, 0, 0, %s, %s)
"""

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform',
                       charset='utf8mb4', autocommit=False)
cur = conn.cursor(pymysql.cursors.DictCursor)

_seq = [0]


def next_id():
    _seq[0] += 1
    return int(NOW.timestamp() * 1000) * 1000 + 500 + _seq[0]


cur.execute("""
    select h.id, h.org_id, h.space_id, h.area
    from bp_asset_house h
    where h.house_status = 'AVAILABLE' and h.org_id is not null
      and h.space_id is not null and h.area is not null
    order by h.id limit 900
""")
houses = cur.fetchall()
print('可签约房源:', len(houses))

cur.execute("""
    select id, person_name, phone from bp_person
    where person_status = 'NORMAL' and phone is not null
    order by rand() limit %s
""" % len(houses))
persons = cur.fetchall()
print('可用人员:', len(persons))

made = 0
for h, p in zip(houses, persons):
    area = float(h['area'] or 60)
    rent = round(area * RENT_PRICE, 2)
    deposit = round(rent, 2)
    cid = next_id()

    cur.execute(CONTRACT_SQL, (
        cid, TENANT, 'HT' + str(cid), h['org_id'], h['org_id'],
        p['id'], p['person_name'], p['phone'],
        '3301**********' + str(random.randint(1000, 9999)),
        h['id'], h['space_id'], area,
        RENT_PRICE, rent, deposit,
        NOW, NOW))

    cur.execute("update bp_asset_house set house_status='OCCUPIED' where id=%s",
                (h['id'],))

    did = next_id()
    cur.execute(DEPOSIT_SQL, (did, TENANT, cid, p['id'], h['org_id'],
                              deposit, deposit, deposit, 1000.00, NOW, NOW))
    made += 1

conn.commit()
print('新增合同:', made)

cur.execute('select contract_status, count(*) n from bp_biz_contract group by contract_status')
print('合同状态:', cur.fetchall())
cur.execute('select house_status, count(*) n from bp_asset_house group by house_status')
print('房态:', cur.fetchall())
conn.close()
