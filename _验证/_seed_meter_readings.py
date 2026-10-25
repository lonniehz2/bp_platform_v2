# -*- coding: utf-8 -*-
"""为多套房源补水电燃气读数，让抄表管理与能耗分析有多项目数据。

口径：同一房源同一项目，本期读数 = 上期读数 + 用量。
"""
import random
import time

import pymysql

DB = dict(host='192.168.31.153', port=33306, user='root',
          password='5677@Mysql', database='bp_platform', charset='utf8mb4')
conn = pymysql.connect(**DB)
cur = conn.cursor()

# 计费项
cur.execute("""select id, item_code, item_name, unit_price from bp_fin_fee_item
               where calc_mode='METER'""")
items = {r[1]: r for r in cur.fetchall()}
print('计量项:', [(r[1], r[2], str(r[3])) for r in items.values()])

ELEC = items.get('ELEC-P1')
WATER = items.get('WATER-P1')
GAS = items.get('GAS-P1')
if not (ELEC and WATER and GAS):
    print('缺计量项，先跑 _seed_utility_demo.py')
    raise SystemExit(1)

# 选有计量设备的房源（我们种的电表/水表所在房源）
cur.execute("""select h.id, h.house_code, min(m.device_id) as dev
               from bp_asset_house h
               join bp_dev_device m on m.space_id = h.space_id and m.device_type='ELEC_METER'
               where m.device_id like 'DEMO-ELEC-%'
               group by h.id, h.house_code limit 120""")
houses = cur.fetchall()
print('目标房源:', len(houses))

TODAY = time.strftime('%Y-%m-%d')
PREV = time.strftime('%Y-%m-%d', time.localtime(time.time() - 30 * 86400))

seq = int(time.time() * 1000) % 10 ** 8


def next_id():
    global seq
    seq += 1
    return 700000000000000000 + seq


def add(house_id, item, reading, day, device_id):
    cur.execute('''select count(*) from bp_fin_meter_reading
                   where house_id=%s and fee_item_id=%s and read_date=%s''',
                (house_id, item[0], day))
    if cur.fetchone()[0]:
        return False
    cur.execute('''insert into bp_fin_meter_reading
        (id, tenant_id, house_id, fee_item_id, reading, read_date, device_id,
         create_time, create_by)
        values (%s,'350600',%s,%s,%s,%s,%s,%s,'seed')''',
                (next_id(), house_id, item[0], reading, day, device_id, TODAY))
    return True


made = {'elec': 0, 'water': 0, 'gas': 0}
for hi, (house_id, house_code, elec_dev) in enumerate(houses):
    # 电：基线与本期
    e0 = 0
    e1 = e0 + random.randint(80, 260)
    if add(house_id, ELEC, e0, PREV, elec_dev):
        made['elec'] += 1
    if add(house_id, ELEC, e1, TODAY, elec_dev):
        made['elec'] += 1

    # 水
    w_dev = elec_dev.replace('ELEC', 'WATER')
    w0 = 0
    w1 = w0 + random.randint(8, 22)
    if add(house_id, WATER, w0, PREV, w_dev):
        made['water'] += 1
    if add(house_id, WATER, w1, TODAY, w_dev):
        made['water'] += 1

    # 燃气（每 3 套 1 个）
    if hi % 3 == 0:
        g_dev = elec_dev.replace('ELEC', 'GAS')
        g0 = 0
        g1 = g0 + random.randint(4, 14)
        if add(house_id, GAS, g0, PREV, g_dev):
            made['gas'] += 1
        if add(house_id, GAS, g1, TODAY, g_dev):
            made['gas'] += 1

conn.commit()

print('\n新增读数：', made)
cur.execute('''select f.item_name, count(*), round(sum(m.amount),2)
               from bp_fin_meter_reading m join bp_fin_fee_item f on f.id=m.fee_item_id
               group by f.item_name order by 2 desc''')
print('\n读数与金额汇总：')
for name, cnt, amt in cur.fetchall():
    print('  %-10s %4d 条  金额 %s' % (name, cnt, amt))

conn.close()
