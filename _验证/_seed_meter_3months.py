# -*- coding: utf-8 -*-
"""三段式读数：8 月基线 → 9 月 → 10 月，让能耗趋势有三个点。

口径：每月用量 = 本月读数 − 上月读数；8 月为首月（基线 0，用量 0）。
"""
import random
import time

import pymysql

DB = dict(host='192.168.31.153', port=33306, user='root',
          password='5677@Mysql', database='bp_platform', charset='utf8mb4')
conn = pymysql.connect(**DB)
cur = conn.cursor()

cur.execute("""select id, item_code, item_name, unit_price from bp_fin_fee_item
               where calc_mode='METER'""")
items = {r[1]: r for r in cur.fetchall()}
ELEC, WATER, GAS = items.get('ELEC-P1'), items.get('WATER-P1'), items.get('GAS-P1')
if not (ELEC and WATER and GAS):
    print('缺计量项')
    raise SystemExit(1)

# 清掉此前种的三类读数（只删我们种的）
cur.execute("delete from bp_fin_meter_reading where create_by='seed'")
print('清理旧读数:', cur.rowcount)

cur.execute("""select h.id, h.house_code, min(m.device_id) as dev
               from bp_asset_house h
               join bp_dev_device m on m.space_id = h.space_id and m.device_type='ELEC_METER'
               where m.device_id like 'DEMO-ELEC-%'
               group by h.id, h.house_code limit 120""")
houses = cur.fetchall()
print('目标房源:', len(houses))

M8 = '2026-08-25'
M9 = '2026-09-25'
M10 = '2026-10-25'
NOW = time.strftime('%Y-%m-%d %H:%M:%S')

seq = int(time.time() * 1000) % 10 ** 8


def next_id():
    global seq
    seq += 1
    return 600000000000000000 + seq


def add(house_id, item, reading, day, device_id):
    usage, amount = 0.0, 0.0
    if day != M8:
        cur.execute('''select reading from bp_fin_meter_reading
                       where house_id=%s and fee_item_id=%s and read_date < %s
                       order by read_date desc limit 1''', (house_id, item[0], day))
        row = cur.fetchone()
        base = float(row[0]) if row else 0.0
        usage = max(0.0, float(reading) - base)
        amount = usage * float(item[3] or 0)
    cur.execute('''insert into bp_fin_meter_reading
        (id, tenant_id, house_id, fee_item_id, reading, read_date, device_id,
         usage_amount, amount, create_time, create_by)
        values (%s,'350600',%s,%s,%s,%s,%s,%s,%s,%s,'seed')''',
                (next_id(), house_id, item[0], reading, day, device_id,
                 round(usage, 2), round(amount, 2), NOW))
    return usage, amount


stat = {'elec': [0, 0, 0], 'water': [0, 0, 0], 'gas': [0, 0, 0]}
for hi, (house_id, house_code, elec_dev) in enumerate(houses):
    # 电：8 月基线 0，9 月用量 u1，10 月再增 u2
    u1 = random.randint(90, 240)
    u2 = random.randint(90, 240)
    add(house_id, ELEC, 0, M8, elec_dev)
    add(house_id, ELEC, u1, M9, elec_dev)
    add(house_id, ELEC, u1 + u2, M10, elec_dev)
    stat['elec'][0] += 1 if u1 else 0

    # 水
    w1 = random.randint(8, 20)
    w2 = random.randint(8, 20)
    wdev = elec_dev.replace('ELEC', 'WATER')
    add(house_id, WATER, 0, M8, wdev)
    add(house_id, WATER, w1, M9, wdev)
    add(house_id, WATER, w1 + w2, M10, wdev)

    # 燃气（每 3 套 1 个）
    if hi % 3 == 0:
        g1 = random.randint(4, 12)
        g2 = random.randint(4, 12)
        gdev = elec_dev.replace('ELEC', 'GAS')
        add(house_id, GAS, 0, M8, gdev)
        add(house_id, GAS, g1, M9, gdev)
        add(house_id, GAS, g1 + g2, M10, gdev)

conn.commit()

print('\n按月汇总：')
cur.execute('''select substring(m.read_date,1,7) as mon, count(*),
                      round(sum(m.usage_amount),2), round(sum(m.amount),2)
               from bp_fin_meter_reading m
               group by mon order by mon''')
for mon, cnt, usage, amt in cur.fetchall():
    print('  %s  读数 %3d  用量 %-10s 金额 %s' % (mon, cnt, usage, amt))

conn.close()
