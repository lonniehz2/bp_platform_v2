# -*- coding: utf-8 -*-
import time

import pymysql

c = pymysql.connect(host='192.168.31.153', port=33306, user='root', password='5677@Mysql',
                    database='bp_platform', charset='utf8mb4', autocommit=True,
                    connect_timeout=20, read_timeout=120)
cur = c.cursor()

SPACE = 370832750846021632  # 101室
cur.execute("select id,item_name,calc_mode from bp_fin_fee_item where item_code in ('ELEC-P1','WATER-P1')")
items = {r[1]: r[0] for r in cur.fetchall()}
cur.execute("select item_code,id from bp_fin_fee_item where item_code in ('ELEC-P1','WATER-P1')")
code2id = {r[0]: r[1] for r in cur.fetchall()}
print('items', code2id)

# 以现有合同为模板，造 3 份同房间合同
cur.execute('select * from bp_biz_contract where id=374466995221041152')
cols = [d[0] for d in cur.description]
base = dict(zip(cols, cur.fetchone()))
names = ['M2租户A', 'M2租户B', 'M2租户C']
starts = ['2026-10-01', '2026-10-11', '2026-10-21']
ids = []
for i, name in enumerate(names):
    row = dict(base)
    nid = int(time.time() * 1000) * 1000 + i
    row['id'] = nid
    row['contract_no'] = 'M2C%d%s' % (i + 1, str(nid)[-6:])
    row['space_id'] = SPACE
    row['lessee_name'] = name
    row['lease_start'] = starts[i]
    row['lease_end'] = '2026-10-31'
    row['contract_status'] = 'EFFECTIVE'
    row['monthly_rent'] = 600
    row['billing_person_count'] = 1
    row['billing_bed_count'] = 1
    row['quantity_updated_at'] = None
    ph = ','.join(['%s'] * len(cols))
    cur.execute('insert into bp_biz_contract (%s) values (%s)' % (','.join(cols), ph),
                [row[k] for k in cols])
    ids.append(nid)
print('contracts', ids)

# B 增加 1 名同住人，验证人·天
cur.execute("""insert into bp_biz_contract_cohabitant
 (id,tenant_id,contract_id,person_id,member_name,relation,is_granted,create_time)
 values (%s,'350600',%s,%s,'M2同住人','配偶',1,now(3))""",
            (int(time.time() * 1000) * 1000 + 9, ids[1], base.get('lessee_person_id')))

# 表计点位：电、水，4 床
pids = []
for name, code in [('M2房间电表', 'ELEC-P1'), ('M2房间水表', 'WATER-P1')]:
    pid = int(time.time() * 1000) * 1000 + (10 if '电' in name else 11)
    cur.execute("""insert into bp_fin_meter_point
     (id,tenant_id,space_id,fee_item_id,meter_scope,allocation_basis,meter_name,bed_capacity,status,create_time,update_time)
     values (%s,'350600',%s,%s,'ROOM','PERSON_DAYS',%s,4,'ENABLED',now(3),now(3))""",
                (pid, SPACE, code2id[code], name))
    pids.append((pid, code))

# 读数：10 月期初/期末
for pid, code in pids:
    start, end = (100, 400) if code == 'ELEC-P1' else (50, 80)
    for rd, t in [(start, '2026-10-01 00:00:00'), (end, '2026-10-31 23:59:00')]:
        cur.execute("""insert into bp_fin_meter_point_reading
         (id,tenant_id,meter_point_id,reading,read_time,source,create_time)
         values (%s,'350600',%s,%s,%s,'MANUAL',now(3))""",
                    (int(time.time() * 1000) * 1000 + (20 if '01' in t else 21) + (pid % 1000), pid, rd, t))
print('meter points', pids)
print('space', SPACE, 'contracts', ids)
c.close()
