# -*- coding: utf-8 -*-
"""重建 2026-08/09/10 三个月抄表数据（金额合理）。

每台计量设备（水/电/气）每月一条读数：
  电 80~260 kWh × 0.65    水 4~18 吨 × 3.5    气 3~14 方 × 2.8
读数区间：上月 25 日 → 本月 25 日，prev_reading 为累计值基线。
"""
import datetime
import random

import pymysql

TENANT = '350600'
random.seed(20261027)

NOW = datetime.datetime(2026, 10, 26, 9, 0, 0)

RANGES = {
    'ELEC_METER': (80, 260),
    'WATER_METER': (4, 18),
    'GAS_METER': (3, 14),
    'HEAT_METER': (2, 8),
}
PRICE = {
    'ELEC_METER': (0.65, 371722116640411648),
    'WATER_METER': (3.50, 372428940817600512),
    'GAS_METER': (2.80, 372428941413191680),
    'HEAT_METER': (3.00, 372428941413191680),
}
MONTHS = [(2026, 8), (2026, 9), (2026, 10)]

conn = pymysql.connect(host='192.168.31.153', port=33306, user='root',
                       password='5677@Mysql', database='bp_platform',
                       charset='utf8mb4', autocommit=False)
cur = conn.cursor(pymysql.cursors.DictCursor)

# 清空既有读数
cur.execute('delete from bp_fin_meter_reading where tenant_id=%s', (TENANT,))
print('清空旧读数:', cur.rowcount)

cur.execute("""
    select d.device_id, d.device_type, d.space_id, h.id house_id, h.org_id
    from bp_dev_device d
    join bp_asset_house h on h.space_id = d.space_id
    where d.device_type in ('WATER_METER','ELEC_METER','GAS_METER')
      and d.tenant_id = %s
""", (TENANT,))
devices = cur.fetchall()
print('可抄表设备:', len(devices))

_seq = [0]


def next_id():
    _seq[0] += 1
    return int(NOW.timestamp() * 1000) * 1000 + _seq[0]


made = 0
for dev in devices:
    dtype = dev['device_type']
    lo, hi = RANGES[dtype]
    price, fee_item = PRICE[dtype]
    base = random.randint(1000, 5000)
    for (y, m) in MONTHS:
        usage = round(random.uniform(lo, hi), 2)
        prev = round(base, 2)
        cur_val = round(prev + usage, 2)
        amount = round(usage * price, 2)
        read_day = 25
        read_date = datetime.date(y, m, read_day)
        cur.execute("""
            insert into bp_fin_meter_reading
            (id, tenant_id, org_id, house_id, fee_item_id, read_date, reading,
             prev_reading, usage_amount, unit_price, amount, bill_status,
             remark, create_by, create_time, is_deleted, device_id)
            values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'UNBILLED',%s,'system',%s,0,%s)
        """, (next_id(), TENANT, dev['org_id'], dev['house_id'], fee_item, read_date,
              cur_val, prev, usage, price, amount,
              '%d-%02d 抄表' % (y, m), NOW, dev['device_id']))
        made += 1
        base = cur_val

conn.commit()
print('新增读数:', made)

cur.execute("""
    select date_format(read_date,'%%Y-%%m') m, count(*) n,
           round(sum(amount),2) amt, round(avg(amount),2) avg_amt
    from bp_fin_meter_reading where tenant_id=%s group by m order by 1
""", (TENANT,))
print('按月统计:')
for r in cur.fetchall():
    print('  %s %4d 条 合计 %10.2f 均价 %7.2f' % (r['m'], r['n'], float(r['amt']),
                                               float(r['avg_amt'])))
conn.close()
