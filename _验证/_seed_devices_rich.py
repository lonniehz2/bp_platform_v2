# -*- coding: utf-8 -*-
"""丰富设备演示数据：补门禁/道闸/水表/电表/燃气表/摄像头/传感器。

目的：让「设备类型」等多值筛选可以真实演示与验证，
而不是 5778 台全是门锁。
"""
import random
import time

import pymysql

DB = dict(host='192.168.31.153', port=33306, user='root',
          password='5677@Mysql', database='bp_platform', charset='utf8mb4')

conn = pymysql.connect(**DB)
cur = conn.cursor()

now = time.strftime('%Y-%m-%d %H:%M:%S')
seq = int(time.time() * 1000) % 10 ** 9


def next_id():
    global seq
    seq += 1
    return 900000000000000000 + seq


def exists(device_id):
    cur.execute('select count(*) from bp_dev_device where device_id=%s', (device_id,))
    return cur.fetchone()[0] > 0


def insert(device_id, name, dtype, org_id, space_id, online=1, battery=None):
    if exists(device_id):
        return False
    cur.execute('''insert into bp_dev_device
        (id, tenant_id, device_id, device_name, device_type, org_id, space_id,
         online_status, is_public, is_deleted, create_time, last_report_time, battery)
        values (%s,%s,%s,%s,%s,%s,%s,%s,0,0,%s,%s,%s)''',
                (next_id(), '350600', device_id, name, dtype, org_id, space_id,
                 online, now, now, battery))
    return True


# ---------- 1) 按空间类型取样本 ----------
cur.execute('''select id, space_code, space_name, space_type, org_id
               from bp_asset_space where space_type='BUILDING' limit 20''')
buildings = cur.fetchall()

cur.execute('''select id, space_code, space_name, space_type, org_id
               from bp_asset_space where space_type='UNIT' limit 40''')
units = cur.fetchall()

cur.execute('''select id, space_code, space_name, space_type, org_id
               from bp_asset_space where space_type in ('COMMUNITY','PROJECT','ORG') limit 10''')
communities = cur.fetchall()

cur.execute('''select h.id, h.house_code, h.space_id, h.org_id
               from bp_asset_house h where h.space_id is not null
                 and h.house_code like 'ZZ-H-%' limit 300''')
houses = cur.fetchall()

print('样本：楼栋 %d / 单元 %d / 小区 %d / 房源 %d'
      % (len(buildings), len(units), len(communities), len(houses)))

created = {}

# ---------- 2) 门禁：每个楼栋 1 个 ----------
n = 0
for sp_id, code, name, _t, org in buildings:
    if insert('DEMO-ACCESS-' + str(code or sp_id)[-8:],
              '门禁-%s' % (name or code), 'ACCESS', org, sp_id):
        n += 1
created['ACCESS'] = n

# ---------- 3) 道闸：每个小区 1 个 ----------
n = 0
for i, (sp_id, code, name, _t, org) in enumerate(communities[:6]):
    if insert('DEMO-BARRIER-%02d' % i, '道闸-%s' % (name or code), 'BARRIER', org, sp_id):
        n += 1
created['BARRIER'] = n

# ---------- 4) 摄像头：每 2 个楼栋 1 个 ----------
n = 0
for i, (sp_id, code, name, _t, org) in enumerate(buildings[::2]):
    if insert('DEMO-CAMERA-%02d' % i, '摄像头-%s' % (name or code), 'CAMERA', org, sp_id):
        n += 1
created['CAMERA'] = n

# ---------- 5) 单元烟感（传感器） ----------
n = 0
for i, (sp_id, code, name, _t, org) in enumerate(units[:24]):
    if insert('DEMO-SENSOR-%02d' % i, '烟感-%s' % (name or code), 'SENSOR', org, sp_id):
        n += 1
created['SENSOR'] = n

# ---------- 6) 三表：每套房 1 电表 + 1 水表（燃气表每 3 套 1 个） ----------
n_elec = n_water = n_gas = 0
for i, (house_id, house_code, space_id, org) in enumerate(houses):
    tail = str(house_code or house_id)[-6:]
    if insert('DEMO-ELEC-' + tail, '电表-%s' % house_code, 'ELEC_METER', org, space_id,
              battery=None):
        n_elec += 1
    if insert('DEMO-WATER-' + tail, '水表-%s' % house_code, 'WATER_METER', org, space_id):
        n_water += 1
    if i % 3 == 0 and insert('DEMO-GAS-' + tail, '燃气表-%s' % house_code, 'GAS_METER',
                             org, space_id):
        n_gas += 1
created.update({'ELEC_METER': n_elec, 'WATER_METER': n_water, 'GAS_METER': n_gas})

conn.commit()

print('\n新增设备：')
for k, v in created.items():
    print('  %-12s %d' % (k, v))

print('\n当前设备类型分布：')
cur.execute('''select device_type, count(*) from bp_dev_device
               group by device_type order by 2 desc''')
for t, c in cur.fetchall():
    print('  %-12s %s' % (t, c))

conn.close()
